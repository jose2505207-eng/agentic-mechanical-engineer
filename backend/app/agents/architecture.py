"""Deterministic system architecture generation.

Sizes battery from required runtime and a power budget, picks a motor class
with headroom, and selects chassis material. All numbers are engineering
estimates for a prototype-class robot; the simulation stage re-verifies them
independently (so a sizing bug here gets caught there).
"""

import math

from app.schemas import ArchitectureSpec, BatterySpec, MotorSpec, Requirements

# Power budget model constants (documented in docs/wiki/simulation-system.md)
ROLLING_RESISTANCE_COEFF = 0.015   # hard indoor floor, rubber wheels
DRIVETRAIN_EFFICIENCY = 0.70       # motor + gearbox + driver, conservative
ELECTRONICS_DRAW_W = 30.0          # SBC + lidar + cameras + radios
MOTOR_IDLE_OVERHEAD_W = 5.0
AVG_GRADE_DEG = 1.0                # long-run average slope while patrolling
ESTIMATED_LOADED_MASS_KG = 20.0    # a-priori guess; simulation recomputes from CAD
GRAVITY = 9.81


def generate_architecture(req: Requirements) -> ArchitectureSpec:
    # Average locomotion power: F * v / eta, F = m g (Crr + sin(avg grade))
    force_n = ESTIMATED_LOADED_MASS_KG * GRAVITY * (
        ROLLING_RESISTANCE_COEFF + math.sin(math.radians(AVG_GRADE_DEG))
    )
    locomotion_w = force_n * (req.max_speed_m_s * 0.8) / DRIVETRAIN_EFFICIENCY
    avg_draw_w = locomotion_w + ELECTRONICS_DRAW_W + MOTOR_IDLE_OVERHEAD_W

    # Battery: required Wh with 90% usable fraction and 20% design margin
    required_wh = avg_draw_w * req.runtime_hr / 0.9 * 1.2
    # Snap to a realistic commercial LiFePO4 pack size (Wh)
    pack_sizes = [256, 384, 512, 768, 1024, 1536]
    capacity_wh = next((s for s in pack_sizes if s >= required_wh), pack_sizes[-1])
    battery = BatterySpec(
        chemistry="LiFePO4",
        nominal_voltage_v=25.6,
        capacity_wh=float(capacity_wh),
        usable_fraction=0.9,
        mass_kg=round(capacity_wh / 110.0, 2),  # ~110 Wh/kg pack-level LiFePO4
    )

    motor = MotorSpec(
        motor_class="brushed DC gearmotor 24V, ~100 RPM output",
        count=4,
        rated_torque_nm=1.2,
        stall_torque_nm=3.5,
        rated_power_w=25.0,
        mass_kg=0.65,
    )

    return ArchitectureSpec(
        drivetrain="differential drive (skid-steer), 4 driven wheels",
        wheel_count=4,
        wheel_diameter_mm=120.0,
        chassis_topology="single aluminum plate with battery bay, electronics bay, sensor mast",
        chassis_material="Aluminum 6061-T6",
        chassis_material_density_kg_m3=2700.0,
        chassis_material_yield_mpa=276.0,
        motor=motor,
        battery=battery,
        sensor_placement={
            "rgb_camera": "top of sensor mast, forward-facing",
            "thermal_camera": "top of sensor mast, forward-facing, beside RGB",
            "lidar_2d": "front chassis edge, 150 mm above floor",
            "imu": "chassis center, inside electronics bay",
        },
        electronics_avg_draw_w=ELECTRONICS_DRAW_W,
        rationale=[
            "Skid-steer 4-wheel: simplest reliable drivetrain for flat industrial floors; "
            "no steering linkage to design or fail.",
            f"Battery sized from avg draw ~{avg_draw_w:.0f} W x {req.runtime_hr} h "
            f"/ 0.9 usable x 1.2 margin = {required_wh:.0f} Wh -> {capacity_wh} Wh pack.",
            "LiFePO4 over Li-ion: safer chemistry for unattended industrial operation, "
            "longer cycle life, at a mass penalty.",
            "Al 6061 plate chassis: stiff, cheap, machinable anywhere, well-known allowables.",
            "Motors chosen with torque headroom; verified quantitatively in simulation stage.",
        ],
    )
