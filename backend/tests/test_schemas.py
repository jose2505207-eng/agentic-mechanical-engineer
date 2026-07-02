"""Schema contract tests: validation works, bad values are rejected."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    CADParams,
    EngineeringAssumption,
    EnvironmentType,
    LocomotionType,
    Requirements,
)


def _valid_requirements(**overrides):
    base = dict(
        prompt="test", payload_kg=5.0, runtime_hr=8.0,
        max_dimensions_mm=(600, 450, 900),
        environment=EnvironmentType.indoor_industrial,
        max_cost_usd=1500.0, locomotion_type=LocomotionType.wheeled_4,
        sensors_required=["rgb_camera"],
    )
    base.update(overrides)
    return Requirements(**base)


def test_requirements_valid():
    req = _valid_requirements()
    assert req.payload_kg == 5.0
    assert req.assumptions == []


def test_requirements_rejects_nonpositive_payload():
    with pytest.raises(ValidationError):
        _valid_requirements(payload_kg=0)


def test_requirements_rejects_nonpositive_runtime():
    with pytest.raises(ValidationError):
        _valid_requirements(runtime_hr=-1)


def test_cad_params_bounds_enforced():
    """Risk R1: out-of-range CAD parameters must fail before the kernel runs."""
    valid = dict(
        chassis_length_mm=500, chassis_width_mm=380, chassis_thickness_mm=8,
        wheel_diameter_mm=120, wheel_width_mm=30, wheelbase_mm=320,
        track_width_mm=400, mast_height_mm=400, mast_diameter_mm=30,
        battery_bay_mm=(180, 130, 90), electronics_bay_mm=(160, 120, 60),
    )
    assert CADParams(**valid).chassis_length_mm == 500
    with pytest.raises(ValidationError):
        CADParams(**{**valid, "chassis_length_mm": 5000})
    with pytest.raises(ValidationError):
        CADParams(**{**valid, "chassis_thickness_mm": 0.5})


def test_assumption_roundtrip():
    a = EngineeringAssumption(field="payload_kg", assumed_value="5 kg", rationale="default")
    assert EngineeringAssumption.model_validate_json(a.model_dump_json()) == a
