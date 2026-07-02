"""Sandboxed execution of model-generated CadQuery scripts.

SECURITY MODEL (see ADR-009): model output is untrusted. Before execution,
the script is statically validated by AST walk:
  - imports restricted to a whitelist (cadquery, math, numpy)
  - dangerous builtins forbidden (open, exec, eval, __import__, ...)
  - all dunder attribute access forbidden (blocks __class__/__globals__
    escape chains)
Then it runs in a SEPARATE python process (-I isolated mode) with a hard
timeout, a scratch working directory, and output limited to the two export
paths we hand it. It cannot touch app state; worst case is a dead subprocess.

This is a pragmatic sandbox, not a security boundary against a determined
attacker with local access — the threat model is a misbehaving model, not a
hostile user on the same machine.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ALLOWED_IMPORTS = {"cadquery", "math", "numpy"}
FORBIDDEN_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "input", "breakpoint",
    "globals", "locals", "vars", "getattr", "setattr", "delattr", "memoryview",
    "exit", "quit", "help",
}

RUNNER = Path(__file__).parent / "runner.py"


class CADScriptError(Exception):
    """Validation or execution failure; message is fed back to the model."""


@dataclass
class ScriptResult:
    volume_mm3: float
    bbox_mm: tuple[float, float, float]
    is_valid_solid: bool
    stl_path: Path
    step_path: Path | None


def validate_script(code: str) -> list[str]:
    """Static safety check. Returns violations; empty list = OK to run."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"syntax error: {exc}"]

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    violations.append(f"import of '{alias.name}' not allowed "
                                      f"(whitelist: {sorted(ALLOWED_IMPORTS)})")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in ALLOWED_IMPORTS:
                violations.append(f"import from '{node.module}' not allowed")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            violations.append(f"use of '{node.id}' not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            violations.append(f"dunder attribute access '{node.attr}' not allowed")
    return violations


def run_script(code: str, stl_path: Path, step_path: Path | None,
               timeout_s: int = 120) -> ScriptResult:
    """Validate then execute the script in an isolated subprocess."""
    violations = validate_script(code)
    if violations:
        raise CADScriptError("script rejected by safety validator: " + "; ".join(violations))

    # Resolve to absolute paths: the subprocess runs with cwd=tempdir, so a
    # relative output path would land in the tempdir and vanish with it.
    stl_path = stl_path.resolve()
    step_path = step_path.resolve() if step_path is not None else None
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cad-sandbox-") as tmp:
        script_file = Path(tmp) / "cad_script.py"
        script_file.write_text(code)
        cmd = [sys.executable, "-I", str(RUNNER), str(script_file),
               str(stl_path), str(step_path or "")]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=timeout_s, cwd=tmp)
        except subprocess.TimeoutExpired as exc:
            raise CADScriptError(
                f"CAD script exceeded {timeout_s}s timeout — simplify the geometry") from exc

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "no output").strip().splitlines()[-12:]
        raise CADScriptError("CAD script failed:\n" + "\n".join(tail))

    try:
        metrics = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise CADScriptError(f"runner produced no metrics: {proc.stdout[-300:]}") from exc

    if not stl_path.exists() or stl_path.stat().st_size <= 84:
        raise CADScriptError("script ran but produced no usable STL")
    if metrics["volume_mm3"] <= 0:
        raise CADScriptError("resulting solid has zero volume — geometry is degenerate")

    step_out = Path(metrics["step_path"]) if metrics.get("step_path") else None
    return ScriptResult(
        volume_mm3=float(metrics["volume_mm3"]),
        bbox_mm=tuple(metrics["bbox_mm"]),
        is_valid_solid=bool(metrics["is_valid_solid"]),
        stl_path=stl_path,
        step_path=step_out,
    )
