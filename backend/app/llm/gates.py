"""Feasibility gates for LLM-proposed architectures.

The rules layer between model creativity and the CAD/simulation stages.
An LLM proposal that fails ANY gate is rejected wholesale and the pipeline
falls back to the deterministic architecture generator. Gates are physics
sanity, not taste: they catch impossible batteries and cartoon motors, not
unconventional-but-valid choices.

Constants document plausible ranges for prototype-class mobile robots;
sources are pack-level/catalog figures, deliberately generous so we only
reject the impossible.
"""

from app.schemas import ArchitectureSpec, Requirements

# Pack-level specific energy plausibility (Wh/kg) across supported chemistries
BATTERY_WH_PER_KG = {"min": 30.0, "max": 300.0}
ALLOWED_WHEEL_COUNTS = {2, 3, 4, 6}
DENSITY_RANGE_KG_M3 = (500.0, 20000.0)     # foams..heavy alloys
YIELD_RANGE_MPA = (10.0, 2000.0)           # soft plastics..high-strength steel
MOTOR_RATED_TORQUE_MAX_NM = 50.0           # beyond this is not "mobile robot class"


def check_feasibility(req: Requirements, arch: ArchitectureSpec) -> list[str]:
    """Return a list of violations; empty list means the proposal passes."""
    violations: list[str] = []

    if arch.wheel_count not in ALLOWED_WHEEL_COUNTS:
        violations.append(
            f"wheel_count={arch.wheel_count} not in supported set {sorted(ALLOWED_WHEEL_COUNTS)}")
    if arch.motor.count < arch.wheel_count // 2:
        violations.append(
            f"motor count {arch.motor.count} cannot drive a {arch.wheel_count}-wheel platform")
    if arch.motor.stall_torque_nm <= arch.motor.rated_torque_nm:
        violations.append("stall torque must exceed rated torque")
    if arch.motor.rated_torque_nm > MOTOR_RATED_TORQUE_MAX_NM:
        violations.append(
            f"rated torque {arch.motor.rated_torque_nm} Nm outside mobile-robot class")

    # Battery: specific energy must be physically plausible for the pack
    wh_per_kg = arch.battery.capacity_wh / arch.battery.mass_kg
    if not (BATTERY_WH_PER_KG["min"] <= wh_per_kg <= BATTERY_WH_PER_KG["max"]):
        violations.append(
            f"battery specific energy {wh_per_kg:.0f} Wh/kg implausible "
            f"(allowed {BATTERY_WH_PER_KG['min']}-{BATTERY_WH_PER_KG['max']})")

    # Necessary (not sufficient) runtime condition: even with zero locomotion,
    # electronics draw alone must not exceed the usable battery over runtime.
    usable_wh = arch.battery.capacity_wh * arch.battery.usable_fraction
    if usable_wh < arch.electronics_avg_draw_w * req.runtime_hr:
        violations.append(
            f"battery {usable_wh:.0f} Wh usable cannot cover electronics draw "
            f"{arch.electronics_avg_draw_w} W for {req.runtime_hr} h")

    lo, hi = DENSITY_RANGE_KG_M3
    if not (lo <= arch.chassis_material_density_kg_m3 <= hi):
        violations.append(
            f"chassis density {arch.chassis_material_density_kg_m3} kg/m^3 implausible")
    lo, hi = YIELD_RANGE_MPA
    if not (lo <= arch.chassis_material_yield_mpa <= hi):
        violations.append(
            f"chassis yield {arch.chassis_material_yield_mpa} MPa implausible")

    if arch.wheel_diameter_mm < 40 or arch.wheel_diameter_mm > 400:
        violations.append(
            f"wheel diameter {arch.wheel_diameter_mm} mm outside CAD template bounds (40-400)")

    return violations
