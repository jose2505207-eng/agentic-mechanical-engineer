# Sprint Log — Generative CAD (ADR-009)

Date: 2026-07-02.

## What shipped
- `cad/sandbox.py`: AST safety validator (import whitelist cadquery/math/
  numpy; forbids open/exec/eval/getattr/…; blocks all dunder attribute
  access) + isolated subprocess runner (`python -I`, 120 s timeout, temp
  cwd). 6 adversarial validator tests.
- `cad/runner.py`: standalone subprocess entry — executes the validated
  script, measures volume/bbox/kernel-validity, exports STL + STEP.
- `cad/generative.py`: LLM writes a parametric CadQuery script; failures
  (validator, execution, degenerate geometry) are fed back verbatim for up
  to 3 attempts. Banned ops in the prompt: fillet/chamfer/shell/loft/sweep.
- `llm/provider.py`: refactored around `_chat_once`; new `complete_text()`
  for code generation alongside `complete_json()`.
- Pipeline: `select_mode()` — robot-class prompts -> template mode;
  everything else -> generative; generative failure -> template fallback;
  deterministic provider -> always template. New generic-mode artifacts:
  `model.stl`, `model.step`, `cad_script.py` (editable parametric source),
  `geometry_metrics.json` (measured volume/bbox/mass/print-bed fit),
  `risk_report.json`, generic `engineering_report.md`.
- `/designs/{id}/model` now serves whichever STL the manifest lists;
  frontend links any stl artifact; proxy timeout 600 s.

## Bugs found by live testing (both fixed + regression-tested)
1. Model-generated scripts died on `.fillet()` twice out of three attempts
   -> banned cosmetic ops in the system prompt.
2. Sandbox subprocess runs with cwd=tempdir while the API passes RELATIVE
   output paths -> the successful attempt's STL was written into the
   tempdir and deleted with it. Fixed by resolving paths before spawn;
   pytest never saw it because tmp_path is absolute.

## Verified live (design-c22a8236ebf3)
Prompt: "create a drone that can carry a 2kg payload ... 300$ budget" ->
generative mode, 3 attempts, valid solid quadcopter frame 658x658x204 mm
(X-config arms, motor mounts, payload bay, battery compartment as named
parameters), STL 329 KB + STEP 629 KB + editable script. ~4.8 min run.

## Test suite: 49 passing (incl. real sandboxed CadQuery subprocess runs).

## Notes
- AMD sponsorship: $200–400 GPU credits available; production inference
  target stays vLLM-on-MI300X via MODEL_PROVIDER=vllm (no code change).
- Honest gaps: generative iteration is error-driven only (no
  simulation-feedback optimization yet); wall-thickness/overhang
  printability not analyzed (slicer required); components not yet placed
  into generated geometry.
