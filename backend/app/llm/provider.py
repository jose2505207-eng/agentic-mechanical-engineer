"""Provider-agnostic LLM client.

Design rules:
- The rest of the app only ever calls `complete_json(system, user, schema)`.
- Provider selection is configuration (MODEL_PROVIDER/MODEL_NAME), not code.
- Anthropic uses its native Messages API; openai/openrouter/ollama/vllm all
  speak the OpenAI-compatible chat API, differing only in base URL and key.
- Output is validated against a Pydantic schema. On any failure (no key,
  network, bad JSON, schema violation) callers fall back to the
  deterministic implementation — the pipeline must never die because a
  model misbehaved.
"""

from __future__ import annotations

import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

OPENAI_COMPAT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
    "vllm": "http://localhost:8001/v1",
    "local": "http://localhost:8001/v1",
}


class LLMUnavailable(Exception):
    """Raised when the configured provider cannot produce a valid result."""


def _extract_json(text: str) -> dict:
    """Tolerate models that wrap JSON in prose or code fences."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMUnavailable("no JSON object found in model output")
    return json.loads(text[start:end + 1])


def complete_json(
    system: str, user: str, schema: type[T], timeout_s: float = 60.0, retries: int = 1
) -> T:
    """Ask the configured model for a JSON object matching `schema`.

    Retries once on transient failure (network error, malformed output) —
    models occasionally fumble a JSON response; a second attempt is cheap
    compared to losing the whole LLM stage to a hiccup.
    """
    last_exc: LLMUnavailable | None = None
    for attempt in range(retries + 1):
        try:
            return _complete_json_once(system, user, schema, timeout_s)
        except LLMUnavailable as exc:
            last_exc = exc
            if "no LLM configured" in str(exc) or "not set" in str(exc):
                raise  # configuration problems don't improve on retry
            logger.warning("LLM attempt %d/%d failed: %s", attempt + 1, retries + 1, exc)
    raise last_exc  # type: ignore[misc]


def _complete_json_once(system: str, user: str, schema: type[T], timeout_s: float) -> T:
    settings = get_settings()
    provider = settings.model_provider.lower()

    if provider == "deterministic":
        raise LLMUnavailable("MODEL_PROVIDER=deterministic — no LLM configured")

    instruction = (
        f"{user}\n\nRespond with ONLY a JSON object matching this JSON schema:\n"
        f"{json.dumps(schema.model_json_schema())}"
    )

    try:
        if provider == "anthropic":
            if not settings.anthropic_api_key:
                raise LLMUnavailable("ANTHROPIC_API_KEY not set")
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": settings.model_name or "claude-fable-5",
                    "max_tokens": 4096,
                    "system": system,
                    "messages": [{"role": "user", "content": instruction}],
                },
                timeout=timeout_s,
            )
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"]
        elif provider in OPENAI_COMPAT_BASE_URLS:
            key = settings.openrouter_api_key if provider == "openrouter" \
                else settings.openai_api_key
            if provider in ("openai", "openrouter") and not key:
                raise LLMUnavailable(f"API key for provider '{provider}' not set")
            resp = httpx.post(
                f"{OPENAI_COMPAT_BASE_URLS[provider]}/chat/completions",
                headers={"Authorization": f"Bearer {key or 'none'}"},
                json={
                    "model": settings.model_name,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": instruction},
                    ],
                    # Enforced JSON mode: without it, models occasionally emit
                    # glitch tokens mid-object (observed: '"payload_kg": II').
                    # Models that reject this parameter fail the request and
                    # land in the normal retry->fallback path.
                    "response_format": {"type": "json_object"},
                },
                timeout=timeout_s,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
        else:
            raise LLMUnavailable(f"unknown MODEL_PROVIDER '{provider}'")
    except httpx.HTTPError as exc:
        raise LLMUnavailable(f"provider request failed: {exc}") from exc

    try:
        return schema.model_validate(_extract_json(text))
    except (json.JSONDecodeError, ValueError) as exc:
        raise LLMUnavailable(f"model output failed schema validation: {exc}") from exc
