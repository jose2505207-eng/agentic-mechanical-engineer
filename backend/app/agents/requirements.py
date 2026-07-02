"""Deterministic requirements extraction.

Parses what it can from the prompt with simple rules (runtime hours, payload,
robot-ness) and fills the rest with documented defaults. Every gap filled
becomes an explicit EngineeringAssumption — nothing is silently invented.

Upgrade path: app.llm.extract_requirements() replaces this behind the same
signature, with this function as the validated fallback.
"""

import re

from app.schemas import EngineeringAssumption, EnvironmentType, LocomotionType, Requirements

_RUNTIME_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours|hour|hrs|hr|h)\b", re.IGNORECASE)
_PAYLOAD_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)\b", re.IGNORECASE)


def extract_requirements(prompt: str) -> Requirements:
    assumptions: list[EngineeringAssumption] = []
    unknowns: list[str] = []

    m = _RUNTIME_RE.search(prompt)
    if m:
        runtime_hr = float(m.group(1))
    else:
        runtime_hr = 4.0
        assumptions.append(EngineeringAssumption(
            field="runtime_hr", assumed_value="4.0 h",
            rationale="No runtime stated in prompt; typical inspection shift fraction.",
            confidence="low"))

    m = _PAYLOAD_RE.search(prompt)
    if m:
        payload_kg = float(m.group(1))
    else:
        payload_kg = 5.0
        assumptions.append(EngineeringAssumption(
            field="payload_kg", assumed_value="5.0 kg",
            rationale="No payload stated; 5 kg covers a typical sensor/tooling package.",
            confidence="medium"))

    lower = prompt.lower()
    if any(w in lower for w in ("manufactur", "factory", "plant", "industrial", "equipment")):
        environment = EnvironmentType.indoor_industrial
        assumptions.append(EngineeringAssumption(
            field="environment", assumed_value="indoor_industrial",
            rationale="Prompt mentions manufacturing/industrial context.",
            confidence="high"))
    elif any(w in lower for w in ("outdoor", "field", "farm", "terrain")):
        environment = EnvironmentType.outdoor
    else:
        environment = EnvironmentType.indoor_office
        assumptions.append(EngineeringAssumption(
            field="environment", assumed_value="indoor_office",
            rationale="No environment stated; defaulting to benign indoor.",
            confidence="low"))

    sensors = ["rgb_camera", "imu"]
    if "inspect" in lower:
        sensors += ["thermal_camera", "lidar_2d"]
        assumptions.append(EngineeringAssumption(
            field="sensors_required", assumed_value="rgb + thermal camera, 2D lidar, IMU",
            rationale="Equipment inspection typically needs visual + thermal sensing "
                      "and lidar for navigation.",
            confidence="medium"))

    assumptions.append(EngineeringAssumption(
        field="max_cost_usd", assumed_value="1500 USD",
        rationale="No budget stated; prototype-class budget assumed.",
        confidence="low"))
    assumptions.append(EngineeringAssumption(
        field="max_dimensions_mm", assumed_value="600 x 450 x 900 mm",
        rationale="Must pass standard doorways and navigate factory aisles.",
        confidence="medium"))
    unknowns.append("Floor surface and worst ramp/threshold the robot must cross")
    unknowns.append("Wireless connectivity and docking/charging strategy")
    unknowns.append("Required inspection standoff distance and camera resolution")

    return Requirements(
        prompt=prompt,
        payload_kg=payload_kg,
        runtime_hr=runtime_hr,
        max_dimensions_mm=(600.0, 450.0, 900.0),
        environment=environment,
        max_cost_usd=1500.0,
        locomotion_type=LocomotionType.wheeled_4,
        sensors_required=sensors,
        max_speed_m_s=1.0,
        max_ramp_deg=8.0,
        assumptions=assumptions,
        unknowns=unknowns,
    )
