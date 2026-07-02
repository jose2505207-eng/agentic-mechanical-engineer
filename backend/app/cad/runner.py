"""Subprocess entry point for sandboxed CAD script execution.

Invoked as: python -I runner.py <script.py> <out.stl> [<out.step>]
The script has ALREADY passed AST validation (sandbox.validate_script).
Prints one JSON line of geometry metrics to stdout on success.

Standalone by design: no app imports, so it runs under `python -I`.
"""

import json
import sys


def main() -> int:
    script_path, stl_path = sys.argv[1], sys.argv[2]
    step_path = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None

    import cadquery as cq

    namespace: dict = {"cq": cq, "cadquery": cq}
    with open(script_path) as f:
        code = f.read()
    exec(compile(code, "cad_script.py", "exec"), namespace)  # noqa: S102

    result = namespace.get("result")
    if result is None:
        print("ERROR: script must assign the final solid to a variable named 'result'",
              file=sys.stderr)
        return 2

    shape = result.val() if hasattr(result, "val") else result
    volume = float(shape.Volume())
    bb = shape.BoundingBox()
    bbox = (float(bb.xlen), float(bb.ylen), float(bb.zlen))
    is_valid = bool(shape.isValid())

    cq.exporters.export(result, stl_path, tolerance=0.1)
    exported_step = None
    if step_path:
        try:
            cq.exporters.export(result, step_path)
            exported_step = step_path
        except Exception:  # STEP is best-effort; STL is the contract
            exported_step = None

    print(json.dumps({
        "volume_mm3": volume,
        "bbox_mm": bbox,
        "is_valid_solid": is_valid,
        "step_path": exported_step,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
