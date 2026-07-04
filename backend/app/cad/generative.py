"""Generative CAD with sim-feedback optimization.

The loop a real engineer runs — write, build, TEST, revise — with a hard
iteration budget (LLM calls cost money; CAD_MAX_ITERATIONS is the knob):

    model writes script
      -> AST safety validation      (fail -> feedback, retry)
      -> sandboxed build            (fail -> feedback, retry)
      -> engineering checks         (fail -> check feedback, REDESIGN)
      -> all checks pass            -> done

If the budget runs out with a buildable-but-failing design, we return the
last successful build and report the failing checks honestly — a real part
with known problems beats no part and beats a lie.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from app.cad.sandbox import CADScriptError, ScriptResult, run_script, validate_script
from app.config import get_settings
from app.llm.provider import LLMUnavailable, complete_text
from app.schemas import CheckResult
from app.simulation.geometry_checks import render_check_feedback
from app.utils.events import emit

logger = logging.getLogger(__name__)

CheckFn = Callable[[ScriptResult], list[CheckResult]]

_SYSTEM = """You are a senior mechanical engineer who models parts in CadQuery 2 (Python).
Write a COMPLETE, runnable CadQuery script for the requested object.

Hard rules:
- Imports allowed: `import cadquery as cq`, `import math`, `import numpy as np`. Nothing else.
- Assign the FINAL combined solid to a variable named `result` (a cq.Workplane).
- Units are millimeters. Build real, manufacturable-looking geometry with
  sensible wall thicknesses (>= 1.6 mm for 3D printing) and all parts unioned
  into one connected solid (no floating bodies).
- Define key dimensions as named variables at the top (parametric style).
- No file I/O, no printing, no exec/eval, no dunder attributes.
- FORBIDDEN operations (they fail constantly in the OCCT kernel on generated
  geometry): fillet(), chamfer(), shell() on unioned solids, loft(), sweep().
  Build from boxes, cylinders, extrudes, cuts, and unions ONLY. Square edges
  are fine — reliability beats cosmetics.
- Every union() operand must physically overlap its neighbor (share volume),
  otherwise the solid is disconnected and unprintable.

Your design will be built and then TESTED: engineering checks (envelope fit,
solid validity, material cost) plus rigid-body physics simulation — the part
is dropped 20 mm onto a plane and pushed laterally with 30% of its weight.
Design a stable base/stance in the part's natural resting orientation (z-up).
If any test fails you will receive the numbers and must revise the dimension
variables to satisfy them.

Respond with ONLY the Python code (a single ```python block or bare code)."""


@dataclass
class GenerativeCADResult:
    script: str
    metrics: ScriptResult
    attempts: int
    note: str
    checks: list[CheckResult] = field(default_factory=list)
    all_checks_passed: bool = True
    iterations: list[str] = field(default_factory=list)


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def generate_model(description: str, envelope_mm: tuple[float, float, float],
                   stl_path: Path, step_path: Path | None,
                   check_fn: CheckFn | None = None,
                   max_iterations: int | None = None) -> GenerativeCADResult:
    """Iterate model-written CAD until it builds AND passes the checks.

    Raises only if NO attempt ever produced buildable geometry — a buildable
    design with failing checks is returned with the failures attached.
    """
    budget = max_iterations or get_settings().cad_max_iterations
    ex, ey, ez = envelope_mm
    task = (f"Object to design: {description}\n"
            f"Maximum bounding box: {ex:.0f} x {ey:.0f} x {ez:.0f} mm.")

    history: list[str] = []
    feedback = ""
    script = ""
    last_error: Exception | None = None
    best: GenerativeCADResult | None = None  # last SUCCESSFUL build (file on disk)

    for attempt in range(1, budget + 1):
        prompt = task if not feedback else (
            f"{task}\n\nYour previous script needs revision. Return the FULL "
            f"corrected script.\n\nPrevious script:\n```python\n{script}\n```\n\n"
            f"Feedback:\n{feedback}")
        emit("iteration", f"iteration {attempt}/{budget}: asking model for CAD script...")
        script = _extract_code(complete_text(_SYSTEM, prompt, purpose=f"cad_script_iter_{attempt}"))

        violations = validate_script(script)
        if violations:
            feedback = "Safety validator rejected the script: " + "; ".join(violations)
            last_error = CADScriptError(feedback)
            history.append(f"iteration {attempt}: rejected by safety validator")
            emit("iteration_failed", history[-1])
            logger.warning("generative CAD attempt %d rejected: %s", attempt, feedback)
            continue

        try:
            metrics = run_script(script, stl_path, step_path)
        except CADScriptError as exc:
            feedback = str(exc)
            last_error = exc
            history.append(f"iteration {attempt}: build failed "
                           f"({str(exc).splitlines()[0][:90]})")
            emit("iteration_failed", history[-1])
            logger.warning("generative CAD attempt %d failed: %s", attempt, feedback)
            continue

        checks = check_fn(metrics) if check_fn else []
        failed = [c for c in checks if not c.passed]
        history.append(
            f"iteration {attempt}: built OK "
            f"({metrics.volume_mm3 / 1000:.0f} cm^3, bbox "
            f"{'x'.join(f'{b:.0f}' for b in metrics.bbox_mm)} mm); checks "
            f"{len(checks) - len(failed)}/{len(checks)} passed"
            + (f" (failed: {', '.join(c.name for c in failed)})" if failed else ""))
        emit("iteration_result" if failed else "iteration_ok", history[-1])

        best = GenerativeCADResult(
            script=script, metrics=metrics, attempts=attempt,
            note="", checks=checks, all_checks_passed=not failed,
            iterations=list(history))

        if not failed:
            best.note = (f"Model-generated CadQuery script; converged in {attempt} "
                         f"iteration(s); all {len(checks)} engineering checks passed.")
            logger.info("generative CAD converged on iteration %d", attempt)
            return best

        feedback = render_check_feedback(checks)
        logger.info("generative CAD iteration %d: %d check(s) failed, feeding back",
                    attempt, len(failed))

    if best is not None:
        failed_names = [c.name for c in best.checks if not c.passed]
        best.note = (f"Iteration budget ({budget}) exhausted. Returning the last "
                     f"buildable design; checks still failing: {', '.join(failed_names)}. "
                     "See the risk report before using this geometry.")
        # The file on disk is from the LAST successful build — rebuild if a
        # later failed attempt could have clobbered it. run_script only writes
        # on success, so disk state == `best` unless a later build succeeded
        # (impossible: a later success would have replaced `best`).
        logger.warning("generative CAD budget exhausted; returning design with "
                       "failing checks: %s", failed_names)
        return best

    raise last_error if last_error else LLMUnavailable("generative CAD produced nothing")
