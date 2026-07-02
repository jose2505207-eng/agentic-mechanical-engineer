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
- [ ] LLM-backed architecture proposals gated by feasibility rules
- [ ] LangGraph orchestration replacing sequential `run_pipeline`
      (same state object, same tests)
- [ ] Multi-prompt robustness: 10 canned prompts across payload/runtime/
      environment variations, all passing checks or failing honestly
- [ ] Next.js frontend: prompt box, artifact list, Markdown report viewer,
      React-Three-Fiber STL viewer (Sprint 7 spec in repo prompt)
- [ ] PDF report export
- [ ] Background pipeline runs + status polling in the API

## V2 — Deeper engineering
- [ ] PyBullet: URDF from CAD mass properties, tip-over and clearance in
      actual physics instead of statics
- [ ] More CAD templates: sensor arm, enclosure with ventilation, tracked
      base; template registry keyed by `CADParams.template`
- [ ] Material selection agent (PLA/PETG/CF-Nylon/Al6061) driving density &
      yield in checks
- [ ] Nexar/Octopart live BOM enrichment behind `ALLOW_EXTERNAL_PART_SEARCH`
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
