"""Provider routing: fireworks entry, per-provider key requirement, and the
configurable vLLM base URL (AMD Developer Cloud target)."""

import pytest

from app.config import get_settings
from app.llm.provider import OPENAI_COMPAT_BASE_URLS, LLMUnavailable, _chat_once


@pytest.fixture(autouse=True)
def reset_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_fireworks_base_url_registered():
    assert OPENAI_COMPAT_BASE_URLS["fireworks"] == "https://api.fireworks.ai/inference/v1"


def test_fireworks_requires_its_own_key(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "fireworks")
    # explicit empty overrides any value in the developer's local .env
    monkeypatch.setenv("FIREWORKS_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "not-the-right-key")
    get_settings.cache_clear()
    with pytest.raises(LLMUnavailable, match="fireworks"):
        _chat_once("s", "u", 5.0, json_mode=False)


def test_vllm_uses_configured_base_url(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "vllm")
    monkeypatch.setenv("VLLM_BASE_URL", "http://amd-instance.example:8000/v1")
    get_settings.cache_clear()
    seen = {}

    def fake_post(url, **kw):
        seen["url"] = url
        raise __import__("httpx").ConnectError("stop here")

    import app.llm.provider as prov
    monkeypatch.setattr(prov.httpx, "post", fake_post)
    with pytest.raises(LLMUnavailable):
        _chat_once("s", "u", 5.0, json_mode=False)
    assert seen["url"] == "http://amd-instance.example:8000/v1/chat/completions"
