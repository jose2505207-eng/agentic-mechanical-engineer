# Sprint Log — Sim-feedback optimization loop

Date: 2026-07-02.

## What shipped
- `simulation/geometry_checks.py`: deterministic check suite for generative
  geometry — valid_solid (OCCT), envelope_fit (worst-axis ratio, 2%
  tolerance), material_cost_budget (solid-PLA upper bound vs
  max_cost_usd) — each with formula + assumptions in the output, plus
  `render_check_feedback()` turning failures into redesign instructions.
  Print-bed fit intentionally NOT a driving check (would fight physics on
  large objects); stays informational.
- `cad/generative.py` rework: build loop -> after each successful build the
  check_fn runs; failures feed back to the model with the actual numbers;
  loop converges or exhausts CAD_MAX_ITERATIONS (new env knob, default 5 —
  the cost control on metered credits). Budget exhaustion returns the LAST
  BUILDABLE design with failing checks attached — never an exception,
  never a silent success.
- New schema `GeometryCheckReport` (checks, all_passed, iteration history,
  optimization note) persisted as `simulation_results.json` in generative
  mode; failed checks become HIGH risk items; report gains an
  "Engineering Checks & Optimization" section with iteration history;
  manifest notes say converged / NOT converged.
- env-space + .env.example: CAD_MAX_ITERATIONS documented.

## Tests: 54 passing
New: check-failure-drives-redesign (oversize box -> feedback with real
numbers -> smaller box converges, history verified), budget exhaustion
returns geometry + failures, cost check math, feedback renderer, pipeline
persistence of the check report.

## Open
- Checks are geometric/cost only; physics checks for generative objects
  (e.g., drone thrust-to-weight) need object-class detection — roadmap.
