# Backend

Python 3.11+ / FastAPI / Pydantic backend for the Agentic Mechanical
Engineer. Install from the repo root with `make install`; run the pipeline
with `make demo`, the API with `make api`.

- `app/schemas/` — the data contracts (start here)
- `app/services/pipeline.py` — the golden path orchestrator
- `app/agents/`, `app/cad/`, `app/simulation/`, `app/bom/`, `app/reports/` —
  the pipeline stations
- `app/llm/` — provider-agnostic AI layer with deterministic fallback
- `tests/` — run with `make test`

Full documentation: [../docs/wiki/index.md](../docs/wiki/index.md).
