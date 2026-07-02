# Sprint Log — Foundation build (Sprints 0–6 + Sprint 8 core)

Date: 2026-07-02. Executed sequentially with per-sprint integration
(tests + demo + wiki), per the parallel-sprint protocol's fallback mode.

## Sprint 0 — Repo foundation ✅
pyproject, Makefile (install/demo/test/api/wiki/clean-outputs/check-env/lint),
env-space (every variable documented), .env.example (placeholders only),
.gitignore, README, wiki skeleton.

## Sprint 1 — Schemas & contracts ✅
All 12+ Pydantic models in backend/app/schemas/models.py with validation
bounds (CADParams hard limits = risk R1 mitigation). Schema tests. Sample
JSONs in examples/.

## Sprint 2 — Deterministic golden path ✅
requirements extractor (regex + documented assumptions), architecture
generator (power-budget battery sizing), CAD param mapper,
services/pipeline.py orchestrator, scripts/run_demo.py. All JSON artifacts
produced.

## Sprint 3 — CAD generation ✅
CadQuery template mobile_robot_base_v1 (plate, bays, mast, mounting holes,
wheel placeholders), STL + STEP export, real solid volume -> chassis mass
(risk R2 mitigation), labeled pure-Python placeholder fallback when CadQuery
absent. Fixed: wheels recentered on track line + true bounding-box envelope
check (first integration pass caught a false envelope failure).

## Sprint 4 — Simulation / risk / BOM / report ✅
Six checks with formulas-in-output (runtime, torque, payload, tip-over,
bending SF, envelope), rule-based risk report (standing R-000 fidelity item),
curated BOM ($774 demo total vs $1500 budget), Markdown report with mandatory
assumptions + limitations sections, artifact manifest.

## Sprint 5 — API ✅
FastAPI: GET /health, POST /api/v1/designs, GET designs/{id},
/artifacts, /report, /model. Path traversal guard on design ids. API tests.

## Sprint 6 — Wiki automation ✅
scripts/update_wiki.py (AUTO-GENERATED markers, human text preserved,
idempotent — verified with --check), make wiki, auto code-map/schemas/api
pages, wiki update log, .github/workflows/wiki-check.yml (staleness + tests).
Fixed during integration: first-run non-idempotence (pages pre-created before
mapping; sprint_logs excluded from map).

## Sprint 8 (core, pulled forward) — Model provider abstraction ✅
llm/provider.py: complete_json() over anthropic-native + OpenAI-compatible
(openai/openrouter/ollama/vllm/local), schema-validated output.
llm/agents.py: LLM requirements extraction with automatic deterministic
fallback. 4 tests with mocked responses (valid used / invalid falls back /
schema-violation falls back / deterministic mode).

## Still placeholder (labeled)
- BOM prices: curated estimates, supplier "TBD" (Nexar integration future,
  gated by ALLOW_EXTERNAL_PART_SEARCH).
- Simulation: first-order analytics only, stated in every output.
- LLM architecture/cad-params stations: abstraction ready, not yet wired.
- Sprint 7 frontend: intentionally not started (gate: stable backend — now met).

## State at end of log
`make test`: 21/21 passing. `make demo`: 10 artifacts, 6/6 checks pass,
0.2 s. `make wiki --check`: clean.
