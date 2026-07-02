# Setup

## Prerequisites

- Python 3.11+ (3.12 works; that's what CI and dev use)
- ~1.5 GB disk for the venv (CadQuery ships an OCCT kernel — it's chunky)
- No API keys, no database, no GPU. The MVP is fully offline.

## Install & run

```bash
git clone <repo> && cd mech-eng
make install     # venv + backend deps + CadQuery
make demo        # the golden path → outputs/
make test        # 21 tests
make api         # FastAPI on http://localhost:8000 (docs at /docs)
```

If `make install`'s CadQuery step fails on your platform, everything still
works — the demo writes a clearly-labeled placeholder STL and says so in the
report. Fix later with `.venv/bin/pip install -e "backend[cad]"`.

## Environment variables

**You need none for the MVP.** When you do:

1. Read `env-space` at the repo root — every variable documented: what it
   does, when it's needed, where to get it.
2. `cp .env.example .env`, fill in only what you're enabling.
3. `make check-env` shows what's set (never prints values) and what each
   unlocks.

Never commit `.env`. It's gitignored; keep it that way.

## Enabling the AI agent layer

```bash
# .env
MODEL_PROVIDER=anthropic        # or openai / openrouter / ollama / vllm
MODEL_NAME=claude-fable-5
ANTHROPIC_API_KEY=<your key>
```

With no key or a failing provider, LLM stations fall back to deterministic
automatically — you cannot break the demo by misconfiguring a model.

## Make targets

| Command | Does |
|---|---|
| `make install` | venv + deps (+ CadQuery, tolerated failure) |
| `make demo` | run golden path into `outputs/` |
| `make test` | pytest suite |
| `make api` | uvicorn dev server, port 8000 |
| `make wiki` | regenerate auto-generated wiki sections |
| `make clean-outputs` | wipe `outputs/` |
| `make check-env` | environment report |
| `make lint` | ruff over backend + scripts |
