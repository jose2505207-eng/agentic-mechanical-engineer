"""Generative CAD: the model writes a parametric CadQuery script; we
validate, execute in the sandbox, and feed failures back for revision.

This is how a real engineer iterates — write, build, inspect, fix — with a
hard attempt budget so a confused model can't spin forever. Every attempt's
error becomes explicit feedback in the next prompt.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from app.cad.sandbox import CADScriptError, ScriptResult, run_script, validate_script
from app.llm.provider import LLMUnavailable, complete_text

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

_SYSTEM = """You are a senior mechanical engineer who models parts in CadQuery 2 (Python).
Write a COMPLETE, runnable CadQuery script for the requested object.

Hard rules:
- Imports allowed: `import cadquery as cq`, `import math`, `import numpy as np`. Nothing else.
- Assign the FINAL combined solid to a variable named `result` (a cq.Workplane).
- Units are millimeters. Build real, manufacturable-looking geometry with
  sensible wall thicknesses (>= 1.6 mm for 3D printing), fillets where cheap,
  and all parts unioned into one connected solid (no floating bodies).
- Define key dimensions as named variables at the top (parametric style).
- No file I/O, no printing, no exec/eval, no dunder attributes.
- FORBIDDEN operations (they fail constantly in the OCCT kernel on generated
  geometry): fillet(), chamfer(), shell() on unioned solids, loft(), sweep().
  Build from boxes, cylinders, extrudes, cuts, and unions ONLY. Square edges
  are fine — reliability beats cosmetics.
- Every union() operand must physically overlap its neighbor (share volume),
  otherwise the solid is disconnected and unprintable.

Respond with ONLY the Python code (a single ```python block or bare code)."""


@dataclass
class GenerativeCADResult:
    script: str
    metrics: ScriptResult
    attempts: int
    note: str


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return (m.group(1) if m else text).strip()


def generate_model(description: str, envelope_mm: tuple[float, float, float],
                   stl_path: Path, step_path: Path | None) -> GenerativeCADResult:
    """Iterate model-written CAD code until it builds valid geometry.

    Raises LLMUnavailable or CADScriptError if all attempts fail — callers
    decide the fallback (the pipeline falls back to template mode).
    """
    ex, ey, ez = envelope_mm
    task = (f"Object to design: {description}\n"
            f"Maximum bounding box: {ex:.0f} x {ey:.0f} x {ez:.0f} mm.")

    feedback = ""
    last_error: Exception | None = None
    script = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = task if not feedback else (
            f"{task}\n\nYour previous script failed. Fix it and return the FULL "
            f"corrected script.\n\nPrevious script:\n```python\n{script}\n```\n\n"
            f"Failure:\n{feedback}")
        script = _extract_code(complete_text(_SYSTEM, prompt))

        violations = validate_script(script)
        if violations:
            feedback = "Safety validator rejected the script: " + "; ".join(violations)
            last_error = CADScriptError(feedback)
            logger.warning("generative CAD attempt %d rejected: %s", attempt, feedback)
            continue

        try:
            metrics = run_script(script, stl_path, step_path)
        except CADScriptError as exc:
            feedback = str(exc)
            last_error = exc
            logger.warning("generative CAD attempt %d failed: %s", attempt, feedback)
            continue

        oversize = [f"{axis}={got:.0f}mm > {limit:.0f}mm"
                    for axis, got, limit in zip("XYZ", metrics.bbox_mm, envelope_mm,
                                                strict=False)
                    if got > limit * 1.02]  # 2% tolerance on export noise
        note = (f"Model-generated CadQuery script, attempt {attempt}/{MAX_ATTEMPTS}; "
                f"geometry valid={metrics.is_valid_solid}.")
        if oversize:
            note += " WARNING: exceeds requested envelope (" + ", ".join(oversize) + ")."
        logger.info("generative CAD succeeded on attempt %d (volume %.0f mm^3)",
                    attempt, metrics.volume_mm3)
        return GenerativeCADResult(script=script, metrics=metrics,
                                   attempts=attempt, note=note)

    raise last_error if last_error else LLMUnavailable("generative CAD produced nothing")
