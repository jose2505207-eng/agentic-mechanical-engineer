"""Async pipeline runs, live status feed, provenance ledger, artifact serving."""

import json
import time

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.llm import telemetry
from app.main import app

PROMPT = "Design a mobile robot that can inspect manufacturing equipment for 8 hours."


@pytest.fixture
def client(tmp_path, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    yield TestClient(app)
    get_settings.cache_clear()


def _wait_complete(client, design_id, timeout_s=60):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = client.get(f"/api/v1/designs/{design_id}/status")
        if resp.status_code == 200:
            status = resp.json()
            if status["state"] != "running":
                return status
        time.sleep(0.2)
    raise TimeoutError("pipeline did not finish in time")


def test_async_run_streams_events_and_completes(client):
    resp = client.post("/api/v1/designs/async", json={"prompt": PROMPT})
    assert resp.status_code == 200
    design_id = resp.json()["design_id"]

    status = _wait_complete(client, design_id)
    assert status["state"] == "complete", status.get("error")
    messages = [e["message"] for e in status["events"]]
    assert any("pipeline started" in m for m in messages)
    assert any("pipeline complete" in m for m in messages)
    assert any("requirements" in m for m in messages)

    # design is fully retrievable afterwards
    man = client.get(f"/api/v1/designs/{design_id}").json()
    assert any(a["name"] == "provenance.json" for a in man["artifacts"])


def test_provenance_ledger_deterministic_run(client):
    resp = client.post("/api/v1/designs/async", json={"prompt": PROMPT})
    design_id = resp.json()["design_id"]
    _wait_complete(client, design_id)

    prov = client.get(f"/api/v1/designs/{design_id}/artifacts/provenance.json")
    assert prov.status_code == 200
    ledger = json.loads(prov.content)
    # deterministic test run: zero LLM calls, and the ledger says so honestly
    assert ledger["totals"]["calls"] == 0
    assert "engineering_checks" in ledger["deterministic_stages"]
    assert ledger["mode"] == "template"


def test_artifact_endpoint_rejects_unlisted_names(client):
    resp = client.post("/api/v1/designs", json={"prompt": PROMPT})
    design_id = resp.json()["design_id"]
    assert client.get(
        f"/api/v1/designs/{design_id}/artifacts/requirements.json").status_code == 200
    assert client.get(
        f"/api/v1/designs/{design_id}/artifacts/..%2F..%2Fsecrets").status_code == 404
    assert client.get(
        f"/api/v1/designs/{design_id}/artifacts/status.json").status_code == 404


def test_telemetry_records_usage(monkeypatch):
    """Provider layer must record purpose/provider/tokens per call."""
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    get_settings.cache_clear()

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"text": "hello"}],
                    "usage": {"input_tokens": 11, "output_tokens": 7}}

    from app.llm import provider as prov
    monkeypatch.setattr(prov.httpx, "post", lambda *a, **k: FakeResp())

    telemetry.start_run()
    prov.complete_text("sys", "user", purpose="unit_test")
    calls = telemetry.get_calls()
    assert len(calls) == 1
    assert calls[0]["purpose"] == "unit_test"
    assert calls[0]["prompt_tokens"] == 11
    assert calls[0]["completion_tokens"] == 7
    get_settings.cache_clear()
