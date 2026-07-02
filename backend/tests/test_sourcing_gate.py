"""ALLOW_EXTERNAL_PART_SEARCH gate contract:
- gate closed: zero network calls, BOM untouched
- gate open without credentials: zero network calls, honest disclaimer
- gate open with credentials but API failing: curated fallback + disclaimer
"""

import httpx
import pytest

from app.agents.cad_params import generate_cad_params
from app.agents.requirements import extract_requirements
from app.bom import sourcing
from app.bom.generator import generate_bom
from app.config import get_settings
from app.llm import agents as llm_agents

PROMPT = "Design a mobile robot that can inspect manufacturing equipment for 8 hours."


@pytest.fixture(autouse=True)
def reset_settings_cache(monkeypatch):
    # Neutralize the developer's local .env so tests control the gate fully.
    monkeypatch.delenv("ALLOW_EXTERNAL_PART_SEARCH", raising=False)
    monkeypatch.setenv("MODEL_PROVIDER", "deterministic")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def bom(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # keep pydantic-settings from reading repo .env
    get_settings.cache_clear()
    req = extract_requirements(PROMPT)
    arch = llm_agents.propose_architecture(req)
    return generate_bom("test", req, arch, generate_cad_params(req, arch))


def _forbid_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call attempted despite gate state")
    monkeypatch.setattr(sourcing.httpx, "post", boom)


def test_gate_closed_no_network_no_changes(monkeypatch, bom):
    monkeypatch.setenv("ALLOW_EXTERNAL_PART_SEARCH", "false")
    get_settings.cache_clear()
    _forbid_network(monkeypatch)
    before = bom.model_dump_json()
    assert sourcing.enrich_bom(bom).model_dump_json() == before


def test_gate_open_without_credentials_is_honest(monkeypatch, bom):
    monkeypatch.setenv("ALLOW_EXTERNAL_PART_SEARCH", "true")
    monkeypatch.delenv("NEXAR_CLIENT_ID", raising=False)
    get_settings.cache_clear()
    _forbid_network(monkeypatch)
    out = sourcing.enrich_bom(bom)
    assert "credentials are not configured" in out.pricing_disclaimer
    assert "curated estimates" in out.pricing_disclaimer
    total_before = round(sum(i.total_cost_usd for i in out.items), 2)
    assert out.total_cost_usd == total_before  # prices untouched


def test_gate_open_api_failure_falls_back(monkeypatch, bom):
    monkeypatch.setenv("ALLOW_EXTERNAL_PART_SEARCH", "true")
    monkeypatch.setenv("NEXAR_CLIENT_ID", "test-id")
    monkeypatch.setenv("NEXAR_CLIENT_SECRET", "test-secret-not-real")
    get_settings.cache_clear()

    def fail(*a, **k):
        raise httpx.ConnectError("no route to nexar in tests")
    monkeypatch.setattr(sourcing.httpx, "post", fail)

    out = sourcing.enrich_bom(bom)
    assert "attempted but failed" in out.pricing_disclaimer
    assert all(i.supplier.startswith("TBD") for i in out.items)
