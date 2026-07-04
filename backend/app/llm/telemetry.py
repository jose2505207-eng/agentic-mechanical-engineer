"""Per-run LLM call telemetry — the data behind the provenance panel.

Every provider round-trip records: purpose (pipeline stage), provider,
model, endpoint, token usage, latency. The pipeline writes the collected
calls to provenance.json so the UI can show exactly which model produced
which stage — and which stages were deterministic code (equally important
for honesty).

contextvars isolate concurrent runs.
"""

from __future__ import annotations

import contextvars

_calls: contextvars.ContextVar[list[dict] | None] = contextvars.ContextVar(
    "llm_calls", default=None)


def start_run() -> None:
    _calls.set([])


def record(purpose: str, provider: str, model: str, endpoint: str,
           prompt_tokens: int | None, completion_tokens: int | None,
           latency_s: float, status: str = "ok") -> None:
    calls = _calls.get()
    if calls is None:
        return
    calls.append({
        "purpose": purpose or "unlabeled",
        "provider": provider,
        "model": model,
        "endpoint": endpoint,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_s": round(latency_s, 2),
        "status": status,
    })


def get_calls() -> list[dict]:
    return list(_calls.get() or [])
