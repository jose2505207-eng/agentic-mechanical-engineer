"""AI agent layer tests with mocked model responses.

The contract under test: LLM output that validates is used; anything else
falls back to the deterministic extractor without raising."""

import json

import pytest

from app.config import get_settings
from app.llm import agents as llm_agents
from app.llm import provider as llm_provider

PROMPT = "Design a mobile robot that can inspect manufacturing equipment for 8 hours."


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_deterministic_provider_falls_back(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "deterministic")
    req = llm_agents.extract_requirements(PROMPT)
    assert req.runtime_hr == 8.0  # deterministic extractor parsed the prompt


def test_valid_llm_response_is_used(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    fake_payload = {
        "prompt": "will-be-overwritten",
        "payload_kg": 7.5, "runtime_hr": 8.0,
        "max_dimensions_mm": [600, 450, 900],
        "environment": "indoor_industrial", "max_cost_usd": 2000,
        "locomotion_type": "wheeled_4", "sensors_required": ["rgb_camera"],
        "assumptions": [], "unknowns": [],
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"text": json.dumps(fake_payload)}]}

    monkeypatch.setattr(llm_provider.httpx, "post", lambda *a, **k: FakeResponse())
    req = llm_agents.extract_requirements(PROMPT)
    assert req.payload_kg == 7.5
    assert req.prompt == PROMPT, "pipeline must overwrite model-echoed prompt"


def test_invalid_llm_json_falls_back(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"text": "sorry, I cannot produce JSON today"}]}

    monkeypatch.setattr(llm_provider.httpx, "post", lambda *a, **k: FakeResponse())
    req = llm_agents.extract_requirements(PROMPT)
    assert req.runtime_hr == 8.0, "must fall back to deterministic extraction"


def test_schema_violating_llm_output_falls_back(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):  # payload_kg=-5 violates gt=0
            return {"content": [{"text": json.dumps({"prompt": "x", "payload_kg": -5})}]}

    monkeypatch.setattr(llm_provider.httpx, "post", lambda *a, **k: FakeResponse())
    req = llm_agents.extract_requirements(PROMPT)
    assert req.payload_kg > 0
