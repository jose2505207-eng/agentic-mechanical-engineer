# Sprint Log — Live LLM provider connected (OpenRouter)

Date: 2026-07-02.

## What changed
- `.env` (gitignored, never committed): MODEL_PROVIDER=openrouter,
  MODEL_NAME=deepseek/deepseek-v3.2 (open-weights — same class the real
  product will serve via vLLM on sponsored AMD MI300X; switching later is
  MODEL_PROVIDER=vllm + MODEL_NAME, zero code changes).
- `llm/provider.py`: one retry on transient failures; enforced JSON mode
  (`response_format: json_object`) on the OpenAI-compatible branch.
  Root cause found in live testing: deepseek-v3.2 emitted a glitch token
  mid-JSON (`"payload_kg": II`) without JSON mode; with it, extraction is
  reliable.
- `llm/agents.py`: LLM-extracted requirements now carry a provenance
  assumption (provider:model) so reports are honest about which stations
  were AI vs deterministic.
- `app/main.py` + `run_demo.py`: INFO logging configured — silent
  fallbacks are now visible fallbacks (no-silent-failures rule applies to
  the AI layer too).
- `tests/conftest.py`: forces MODEL_PROVIDER=deterministic and
  ALLOW_EXTERNAL_PART_SEARCH=false before settings load — the suite stays
  offline regardless of the developer's .env.
- Frontend: proxy timeout raised to 180 s (LLM runs take ~1 min); status
  message says so.

## Verified live (design-a66c38d875a8, via the frontend proxy)
- Requirements: LLM-extracted, provenance marked, 5 sensors.
- Architecture: LLM-proposed, PASSED feasibility gates — chose 2x 6.5 Nm
  motors (vs deterministic 4x 1.2 Nm), 600 Wh LiFePO4; simulation
  independently confirmed 6/6 checks, 7.7x torque margin, 11.1 h runtime.
- Earlier the gates also demonstrably REJECTED nothing valid and the retry
  path caught a real glitch-token failure — defense in depth observed
  working, not just designed.

## Security notes
- API key lives only in gitignored .env; verified untracked before commit.
- Key was shared in chat -> flagged for rotation after the demo.
