#!/usr/bin/env python3
"""Golden path demo: canned prompt -> full engineering package in outputs/.

Usage:
    make demo
    # or: .venv/bin/python scripts/run_demo.py ["custom prompt"]
"""

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.pipeline import run_pipeline  # noqa: E402

DEMO_PROMPT = "Design a mobile robot that can inspect manufacturing equipment for 8 hours."


def main() -> int:
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEMO_PROMPT
    output_dir = REPO_ROOT / "outputs"
    print(f"Prompt: {prompt}")
    print(f"Output: {output_dir}\n")

    t0 = time.time()
    state = run_pipeline(prompt, output_dir, design_id="demo")
    dt = time.time() - t0

    assert state.manifest is not None
    print(f"Pipeline complete in {dt:.1f}s — design_id={state.design_id}\n")
    print("Artifacts:")
    for ref in state.manifest.artifacts:
        size = Path(ref.path).stat().st_size
        print(f"  [{ref.kind:4s}] {ref.name:28s} {size:>10,} bytes  {ref.description}")
    for note in state.manifest.notes:
        print(f"\nNote: {note}")

    sim = state.simulation
    assert sim is not None
    passed = sum(1 for c in sim.checks if c.passed)
    print(f"\nChecks passed: {passed}/{len(sim.checks)} | "
          f"mass {sim.total_mass_kg} kg | runtime {sim.estimated_runtime_hr} h | "
          f"torque margin {sim.torque_margin}x")
    print(f"\nRead the report: {output_dir / 'engineering_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
