# Roadmap

## MVP — DONE (you are here)
- [x] Deterministic golden path: prompt → 9 artifacts in `outputs/`
- [x] CadQuery chassis template with STL + STEP export
- [x] Six engineering checks with formulas-in-output
- [x] Rule-based risk report, curated BOM, Markdown report
- [x] FastAPI design endpoints
- [x] LLM provider abstraction + requirements extraction w/ fallback
- [x] Wiki + auto-update system, 21-test suite, CI workflow

## V1 — Make the AI layer real
- [x] LLM-backed architecture proposals gated by feasibility rules
      (`llm/gates.py`; wired into the pipeline with deterministic fallback)
- [x] Next.js frontend: prompt box, artifact list, Markdown report viewer,
      React-Three-Fiber STL viewer, status panel (`make frontend`)
- [x] External part-search gate implemented end to end
      (`bom/sourcing.py`; Nexar enrichment when credentialed, honest
      curated fallback otherwise)
- [ ] LangGraph orchestration replacing sequential `run_pipeline`
      (same state object, same tests)
- [ ] Multi-prompt robustness: 10 canned prompts across payload/runtime/
      environment variations, all passing checks or failing honestly
- [ ] PDF report export
- [ ] Background pipeline runs + status polling in the API

- [x] Generative CAD mode: model-written CadQuery scripts, sandboxed
      execution, error-feedback iteration, STL/STEP + editable source
      (ADR-009; verified live: quadcopter frame from a drone prompt)

## V2 — Deeper engineering
- [x] Generative-mode sim-feedback optimization loop: engineering checks
      (validity, envelope, material cost) run on every build; failures are
      fed back as redesign instructions until convergence or budget
      (CAD_MAX_ITERATIONS) exhaustion; full iteration history in the report
- [ ] Component-aware generative design: discoverable real components
      (curated DB + Nexar) placed as mount envelopes in generated geometry
- [ ] PyBullet: URDF from CAD mass properties, tip-over and clearance in
      actual physics instead of statics
- [ ] More CAD templates: sensor arm, enclosure with ventilation, tracked
      base; template registry keyed by `CADParams.template`
- [ ] Material selection agent (PLA/PETG/CF-Nylon/Al6061) driving density &
      yield in checks
- [ ] Nexar/Octopart enrichment hardening: response caching, alternatives
      per line item (gate + client shipped in V1)
- [ ] Postgres/Supabase design history; auth
- [ ] Design iteration loop: failed check → parameter adjustment → re-run

## Moonshot
- [ ] Upload-your-parts workflow: STEP files in, mounts and chassis designed
      around them
- [ ] Real FEA integration (CalculiX/Fenics) with honest meshing limits
- [ ] Multi-objective optimization (mass/cost/runtime) via PyMOO
- [ ] Agent-vs-agent design review panel before report generation
- [ ] AMD MI300X / ROCm-hosted open-weights models as first-class provider

## Non-goals (so we stop re-litigating)
- Arbitrary robot morphologies in the template system (bounded library only)
- Claiming certified analysis of any kind — see ADR-007
- Building a general CAD editor; we generate packages, not a modeling UI
