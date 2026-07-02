"""API tests using FastAPI's TestClient against a temp storage dir."""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    yield TestClient(app)
    get_settings.cache_clear()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "model_provider" in body


def test_create_and_fetch_design(client):
    resp = client.post("/api/v1/designs", json={
        "prompt": "Design a mobile robot that can inspect manufacturing equipment for 8 hours."
    })
    assert resp.status_code == 200
    body = resp.json()
    design_id = body["design_id"]
    assert len(body["manifest"]["artifacts"]) >= 8

    assert client.get(f"/api/v1/designs/{design_id}").status_code == 200

    artifacts = client.get(f"/api/v1/designs/{design_id}/artifacts").json()
    assert any(a["name"] == "robot_chassis.stl" for a in artifacts)

    report = client.get(f"/api/v1/designs/{design_id}/report")
    assert report.status_code == 200
    assert "Engineering Report" in report.text

    model = client.get(f"/api/v1/designs/{design_id}/model")
    assert model.status_code == 200
    assert len(model.content) > 84


def test_unknown_design_404(client):
    assert client.get("/api/v1/designs/design-doesnotexist1").status_code == 404


def test_prompt_too_short_rejected(client):
    assert client.post("/api/v1/designs", json={"prompt": "robot"}).status_code == 422
