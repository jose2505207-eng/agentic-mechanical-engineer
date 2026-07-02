"""Map architecture spec -> validated CAD parameters.

The CADParams schema enforces hard bounds, so an insane mapping fails loudly
here instead of inside the CAD kernel (risk R1 mitigation).
"""

from app.schemas import ArchitectureSpec, CADParams, Requirements


def generate_cad_params(req: Requirements, arch: ArchitectureSpec) -> CADParams:
    max_l, max_w, _max_h = req.max_dimensions_mm
    # Chassis fits inside envelope with clearance for wheels/bumpers
    chassis_length = min(500.0, max_l - 100.0)
    chassis_width = min(380.0, max_w - 70.0)

    return CADParams(
        chassis_length_mm=chassis_length,
        chassis_width_mm=chassis_width,
        chassis_thickness_mm=8.0,
        corner_radius_mm=20.0,
        wheel_diameter_mm=arch.wheel_diameter_mm,
        wheel_width_mm=30.0,
        wheelbase_mm=chassis_length - 180.0,
        track_width_mm=chassis_width + 20.0,
        mast_height_mm=400.0,
        mast_diameter_mm=30.0,
        battery_bay_mm=(180.0, 130.0, 90.0),
        electronics_bay_mm=(160.0, 120.0, 60.0),
        mounting_hole_diameter_mm=4.5,
        template="mobile_robot_base_v1",
    )
