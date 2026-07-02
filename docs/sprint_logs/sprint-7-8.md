# Sprint Log — Sprints 7 & 8 (+ sourcing gate)

Date: 2026-07-02.

## Sprint 8 — LLM architecture proposals, wired ✅
- `app/llm/gates.py`: deterministic feasibility gates for LLM-proposed
  architectures (wheel-count sanity, motor torque ordering + class ceiling,
  battery specific-energy plausibility 30–300 Wh/kg, necessary runtime
  condition vs electronics draw, material density/yield ranges, wheel
  diameter within CAD template bounds). Any violation -> wholesale rejection.
- `app/llm/agents.py::propose_architecture`: LLM proposal -> schema
  validation -> feasibility gates -> accepted (with rationale note) or
  deterministic fallback. Defense in depth: schema, then gates, then the
  downstream simulation checks still verify quantitatively.
- `services/pipeline.py` now routes stages 1–2 through the LLM wrappers.
  With MODEL_PROVIDER=deterministic (current default) behavior is
  byte-identical to before; with a configured provider, proposals flow in
  gated. 5 new tests (mocked models): plausible proposal used, fantasy
  battery gated, undersized battery gated, unavailable falls back, gate
  function reports specific violations.

## External part search gate — ALLOW_EXTERNAL_PART_SEARCH ✅
- `app/bom/sourcing.py`: Nexar/Octopart enrichment (OAuth + GraphQL median
  pricing + authorized sellers) for electronics/sensors/power categories.
- Gate contract (3 tests): gate closed -> zero network, BOM untouched;
  gate open w/o credentials -> zero network, disclaimer states curated
  estimates remain; API failure -> curated fallback + honest disclaimer.
- `.env` created (gitignored) with ALLOW_EXTERNAL_PART_SEARCH=true per
  user request. Without NEXAR credentials the BOM stays curated and the
  disclaimer says exactly that — verified in the live run.

## Sprint 7 — Frontend ✅ (gate was met: backend stable + tested)
- Next.js 15 + React 19 app in `frontend/` (plain CSS, dark theme):
  prompt input + run button, status log panel, artifact list (STL
  downloadable), rendered Markdown report (marked), React Three Fiber STL
  viewer (orbit controls, grid, z-up correction).
- Same-origin via next.config.mjs rewrites -> :8000 (no CORS surface).
- Makefile: `make install-frontend`, `make frontend`.
- Verified end-to-end: POST through :3000 proxy created
  design-04335f536f1e; report + 309 KB STL served through the proxy.

## Integration
29/29 tests, ruff clean, `make demo` 6/6 checks, wiki regenerated
(agents.md, roadmap.md updated; repo map now includes frontend sources).

## Still placeholder / open
- Nexar client is fallback-hardened but untested against the live API
  (no credentials); first credentialed run should be watched.
- LangGraph orchestration, PDF export, background runs: next up.
