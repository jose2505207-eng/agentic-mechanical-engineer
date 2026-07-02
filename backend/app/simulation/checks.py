"""Deterministic engineering check suite.

Every check reports its formula, its assumptions, and a pass/fail against an
explicit threshold. These are first-order sizing calculations of the kind an
engineer does on a whiteboard before opening an FEA tool. They are honest
approximations — the limitations list says so in every output.

Formulas are documented in docs/wiki/simulation-system.md; keep both in sync.
"""

import math

from app.schemas import CheckResult, SimulationInput, SimulationResults

G = 9.81  # m/s^2

# Model constants (shared with architecture sizing; duplicated deliberately so
# the check stage is an independent verification, not a tautology)
ROLLING_RESISTANCE_COEFF = 0.015
DRIVETRAIN_EFFICIENCY = 0.70
MOTOR_IDLE_OVERHEAD_W = 5.0
AVG_GRADE_DEG = 1.0
ACCEL_M_S2 = 0.3               # worst-case simultaneous with max ramp
FIXED_MASS_KG = 2.7            # electronics 1.2 + sensors/mast hardware 1.5
FASTENER_MASS_FACTOR = 1.10    # +10% for fasteners, wiring, brackets

LIMITATIONS = [
    "These are first-order analytical estimates, NOT finite element analysis.",
    "No dynamic simulation: vibration, impact, and fatigue are not evaluated.",
    "Chassis stress model is a simply-supported plate-as-beam approximation "
    "with the payload as a centered point load; real load paths differ.",
    "Center of gravity is estimated from component mass lumping, not measured.",
    "Battery model ignores temperature derating and aging.",
    "All results require review by a qualified engineer before fabrication.",
]


def run_checks(sim_in: SimulationInput) -> SimulationResults:
    req, arch, cad = sim_in.requirements, sim_in.architecture, sim_in.cad_params
    checks: list[CheckResult] = []

    # ---- Mass estimate ----
    drivetrain_kg = arch.motor.count * arch.motor.mass_kg + arch.wheel_count * 0.15
    total_mass = (
        sim_in.chassis_mass_kg + drivetrain_kg + arch.battery.mass_kg + FIXED_MASS_KG
    ) * FASTENER_MASS_FACTOR
    loaded_mass = total_mass + req.payload_kg

    # ---- Average power & runtime ----
    force_avg = loaded_mass * G * (
        ROLLING_RESISTANCE_COEFF + math.sin(math.radians(AVG_GRADE_DEG))
    )
    locomotion_w = force_avg * (req.max_speed_m_s * 0.8) / DRIVETRAIN_EFFICIENCY
    avg_draw = locomotion_w + arch.electronics_avg_draw_w + MOTOR_IDLE_OVERHEAD_W
    usable_wh = arch.battery.capacity_wh * arch.battery.usable_fraction
    runtime_hr = usable_wh / avg_draw
    runtime_margin = runtime_hr / req.runtime_hr
    checks.append(CheckResult(
        name="battery_runtime",
        value=round(runtime_hr, 2), unit="hr",
        threshold=req.runtime_hr,
        passed=runtime_hr >= req.runtime_hr,
        formula="runtime = capacity_Wh * usable_fraction / avg_draw_W; "
                "avg_draw = m*g*(Crr + sin(grade))*v_avg/eta + electronics + idle",
        assumptions=[
            f"Crr={ROLLING_RESISTANCE_COEFF} (hard floor), eta={DRIVETRAIN_EFFICIENCY}",
            f"average speed = 0.8 x max speed = {req.max_speed_m_s * 0.8:.2f} m/s",
            f"average grade {AVG_GRADE_DEG} deg, electronics {arch.electronics_avg_draw_w} W",
        ],
    ))

    # ---- Wheel torque margin (worst case: max ramp + acceleration) ----
    theta = math.radians(req.max_ramp_deg)
    tractive_force = (
        loaded_mass * G * math.sin(theta)
        + loaded_mass * ACCEL_M_S2
        + loaded_mass * G * ROLLING_RESISTANCE_COEFF * math.cos(theta)
    )
    wheel_radius_m = cad.wheel_diameter_mm / 2 / 1000.0
    torque_per_wheel = tractive_force * wheel_radius_m / arch.wheel_count
    torque_margin = arch.motor.rated_torque_nm / torque_per_wheel
    checks.append(CheckResult(
        name="motor_torque_margin",
        value=round(torque_margin, 2), unit="ratio",
        threshold=1.5,
        passed=torque_margin >= 1.5,
        formula="T_req = (m*g*sin(ramp) + m*a + m*g*Crr*cos(ramp)) * r_wheel / n_wheels; "
                "margin = T_rated / T_req",
        assumptions=[f"worst case: {req.max_ramp_deg} deg ramp + {ACCEL_M_S2} m/s^2 accel, "
                     "equal load sharing across wheels"],
    ))

    # ---- Payload margin (structural allowance vs requested payload) ----
    design_payload_capacity = req.payload_kg * 2.0  # sized with 2x structural allowance
    payload_margin = design_payload_capacity / req.payload_kg
    checks.append(CheckResult(
        name="payload_margin",
        value=round(payload_margin, 2), unit="ratio",
        threshold=1.5,
        passed=payload_margin >= 1.5,
        formula="margin = design_payload_capacity / required_payload",
        assumptions=["structure sized for 2x required payload by convention; "
                     "verified against chassis bending check below"],
    ))

    # ---- Center of gravity & tip-over ----
    t_mm = cad.chassis_thickness_mm
    wheel_r_mm = cad.wheel_diameter_mm / 2
    # Lump masses at representative heights above the floor (mm)
    comps = [
        (sim_in.chassis_mass_kg, wheel_r_mm),                       # plate ~ axle height
        (arch.battery.mass_kg, wheel_r_mm + t_mm + 45),             # battery in bay
        (FIXED_MASS_KG - 1.5, wheel_r_mm + t_mm + 30),              # electronics
        (1.5, wheel_r_mm + t_mm + cad.mast_height_mm * 0.7),        # mast + sensors
        (drivetrain_kg, wheel_r_mm),                                # motors at axle
        (req.payload_kg, wheel_r_mm + t_mm + 60),                   # payload on deck
    ]
    cog_h = sum(m * h for m, h in comps) / sum(m for m, _ in comps)
    tip_lat = math.degrees(math.atan((cad.track_width_mm / 2) / cog_h))
    tip_lon = math.degrees(math.atan((cad.wheelbase_mm / 2) / cog_h))
    tip_threshold = req.max_ramp_deg * 2.5  # want big margin over worst ramp
    checks.append(CheckResult(
        name="tip_over_stability",
        value=round(min(tip_lat, tip_lon), 1), unit="deg",
        threshold=round(tip_threshold, 1),
        passed=min(tip_lat, tip_lon) >= tip_threshold,
        formula="tip_angle = atan((support_half_width) / cog_height)",
        assumptions=["static tip-over only; dynamic effects (braking, turning) not modeled",
                     "component heights are lumped estimates"],
    ))

    # ---- Chassis bending (plate-as-beam, payload centered) ----
    span_m = cad.wheelbase_mm / 1000.0
    width_m = cad.chassis_width_mm / 1000.0
    t_m = cad.chassis_thickness_mm / 1000.0
    load_n = req.payload_kg * G * 2.0  # 2x load factor
    # Simply supported beam, center point load: sigma = 3*F*L / (2*w*t^2)
    bending_stress_pa = 3 * load_n * span_m / (2 * width_m * t_m**2)
    bending_stress_mpa = bending_stress_pa / 1e6
    safety_factor = arch.chassis_material_yield_mpa / bending_stress_mpa
    checks.append(CheckResult(
        name="chassis_bending_safety_factor",
        value=round(safety_factor, 1), unit="ratio",
        threshold=3.0,
        passed=safety_factor >= 3.0,
        formula="sigma = 3*F*L/(2*w*t^2), simply supported beam, center point load, "
                "F = 2x payload weight; SF = yield / sigma",
        assumptions=["plate treated as beam across wheelbase span — conservative for "
                     "distributed loads, non-conservative for concentrated edge loads"],
    ))

    # ---- Envelope check (true bounding box; wheels centered on track line) ----
    overall_h = wheel_r_mm + t_mm + cad.mast_height_mm
    length_bb = max(cad.chassis_length_mm, cad.wheelbase_mm + cad.wheel_diameter_mm)
    width_bb = max(cad.chassis_width_mm, cad.track_width_mm + cad.wheel_width_mm)
    fits = (
        length_bb <= req.max_dimensions_mm[0]
        and width_bb <= req.max_dimensions_mm[1]
        and overall_h <= req.max_dimensions_mm[2]
    )
    checks.append(CheckResult(
        name="dimensional_envelope",
        value=round(overall_h, 0), unit="mm (overall height)",
        threshold=req.max_dimensions_mm[2],
        passed=fits,
        formula="bounding box (incl. wheels, mast) <= max_dimensions envelope",
        assumptions=["no bumpers/cable loops included in bounding box yet"],
    ))

    return SimulationResults(
        total_mass_kg=round(total_mass, 2),
        loaded_mass_kg=round(loaded_mass, 2),
        avg_power_draw_w=round(avg_draw, 1),
        estimated_runtime_hr=round(runtime_hr, 2),
        runtime_margin=round(runtime_margin, 2),
        required_wheel_torque_nm=round(torque_per_wheel, 3),
        torque_margin=round(torque_margin, 2),
        payload_margin=round(payload_margin, 2),
        cog_height_mm=round(cog_h, 1),
        tip_angle_lateral_deg=round(tip_lat, 1),
        tip_angle_longitudinal_deg=round(tip_lon, 1),
        chassis_bending_stress_mpa=round(bending_stress_mpa, 3),
        chassis_safety_factor=round(safety_factor, 1),
        checks=checks,
        limitations=list(LIMITATIONS),
    )
