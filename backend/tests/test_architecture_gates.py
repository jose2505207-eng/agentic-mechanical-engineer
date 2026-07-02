"""Sprint 8: LLM architecture proposals must pass deterministic feasibility
gates or be replaced by the deterministic generator. Mocked models only."""

import json

import pytest

from app.agents.requirements import extract_requirements
from app.config import get_settings
from app.llm import agents as llm_agents
from app.llm import provider as llm_provider
from app.llm.gates import check_feasibility

PROMPT = "Design a mobile robot that can inspect manufacturing equipment for 8 hours."


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _plausible_arch_payload() -> dict:
    return {
        "drivetrain": "differential drive, 4 driven wheels",
        "wheel_count": 4, "wheel_diameter_mm": 150.0,
        "chassis_topology": "plate with bays", "chassis_material": "Aluminum 6061-T6",
        "chassis_material_density_kg_m3": 2700.0, "chassis_material_yield_mpa": 276.0,
        "motor": {"motor_class": "BLDC gearmotor 24V", "count": 4,
                  "rated_torque_nm": 1.5, "stall_torque_nm": 4.0,
                  "rated_power_w": 30.0, "mass_kg": 0.7},
        "battery": {"chemistry": "LiFePO4", "nominal_voltage_v": 25.6,
                    "capacity_wh": 512.0, "usable_fraction": 0.9, "mass_kg": 4.7},
        "sensor_placement": {"rgb_camera": "mast"},
        "electronics_avg_draw_w": 30.0,
        "rationale": ["test proposal"],
    }


class _FakeResp:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return {"content": [{"text": json.dumps(self._payload)}]}


def _use_anthropic(monkeypatch, payload: dict):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm_provider.httpx, "post", lambda *a, **k: _FakeResp(payload))


def test_plausible_llm_architecture_is_used(monkeypatch):
    _use_anthropic(monkeypatch, _plausible_arch_payload())
    req = extract_requirements(PROMPT)
    arch = llm_agents.propose_architecture(req)
    assert arch.wheel_diameter_mm == 150.0  # LLM value, not deterministic 120
    assert any("passed deterministic feasibility gates" in r for r in arch.rationale)


def test_impossible_battery_is_gated_to_deterministic(monkeypatch):
    payload = _plausible_arch_payload()
    payload["battery"]["capacity_wh"] = 5000.0
    payload["battery"]["mass_kg"] = 0.5  # 10,000 Wh/kg — fantasy physics
    _use_anthropic(monkeypatch, payload)
    req = extract_requirements(PROMPT)
    arch = llm_agents.propose_architecture(req)
    assert arch.wheel_diameter_mm == 120.0  # deterministic fallback fingerprint
    assert not any("passed deterministic feasibility gates" in r for r in arch.rationale)


def test_undersized_battery_for_runtime_is_gated(monkeypatch):
    payload = _plausible_arch_payload()
    payload["battery"]["capacity_wh"] = 100.0  # < 30 W x 8 h electronics floor
    payload["battery"]["mass_kg"] = 1.0
    _use_anthropic(monkeypatch, payload)
    arch = llm_agents.propose_architecture(extract_requirements(PROMPT))
    assert arch.wheel_diameter_mm == 120.0


def test_llm_unavailable_falls_back(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "deterministic")
    arch = llm_agents.propose_architecture(extract_requirements(PROMPT))
    assert arch.battery.capacity_wh == 512.0


def test_gate_function_reports_specific_violations():
    from app.schemas import ArchitectureSpec
    req = extract_requirements(PROMPT)
    bad = _plausible_arch_payload()
    bad["wheel_count"] = 7
    bad["motor"]["stall_torque_nm"] = 1.0  # below rated
    violations = check_feasibility(req, ArchitectureSpec.model_validate(bad))
    assert len(violations) >= 2
    assert any("wheel_count" in v for v in violations)
    assert any("stall torque" in v for v in violations)
