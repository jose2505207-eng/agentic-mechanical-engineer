---
name: golden-path-tester
description: Run the MVP demo and verify that all expected artifacts are produced.
---

# Golden Path Tester

## Procedure
1. `make clean-outputs && make demo`
2. Verify every expected artifact exists and is non-trivial:
   - outputs/requirements.json (runtime_hr == 8.0 for the canned prompt,
     assumptions non-empty)
   - outputs/architecture.json
   - outputs/cad_params.json
   - outputs/robot_chassis.stl (>84 bytes, nonzero triangle count) and
     robot_chassis.step when CadQuery is installed
   - outputs/simulation_results.json (all checks carry formula strings;
     limitations non-empty)
   - outputs/risk_report.json (R-000 fidelity item always present)
   - outputs/bom.csv (≥8 data rows + TOTAL row)
   - outputs/engineering_report.md (contains "Assumptions", "Limitations",
     "not a certified design")
   - outputs/artifact_manifest.json (every referenced file exists)
3. `make test` — the same assertions run as pytest (backend/tests/
   test_golden_path.py); the manual pass is for eyeballing content quality,
   the automated pass is the gate.
4. Check the demo summary line: all checks should pass for the canned
   prompt. A failed check on the reference design is a regression, full stop.
5. If CAD ran in placeholder mode, confirm the manifest note and report say
   so explicitly.

## Report format
"N/9 artifacts OK, checks X/Y passed, [what broke + suspected stage]".
