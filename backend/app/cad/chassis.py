"""Mobile robot base template (mobile_robot_base_v1).

Geometry (all mm, chassis plate top face at z=0..thickness):
- rectangular chassis plate with rounded corners
- four corner mounting holes
- battery bay and electronics bay (walled open boxes on the plate)
- sensor mast (cylinder) at the front-center
- four wheel placeholder cylinders at wheelbase/track positions

The LLM never freehands geometry — it only produces CADParams, which are
bound-checked by the schema before this code runs.

If CadQuery is unavailable, a labeled placeholder STL (plain box, pure
Python) is written instead so the golden path still completes; the artifact
manifest and report state this clearly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.cad.stl_fallback import write_box_stl
from app.schemas import CADParams

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    CADQUERY_AVAILABLE = False


@dataclass
class CADResult:
    stl_path: Path
    step_path: Path | None
    chassis_volume_mm3: float
    used_cadquery: bool
    note: str


def _build_model(p: CADParams) -> tuple[cq.Workplane, float]:
    """Return (full assembly solid, chassis-structure volume in mm^3)."""
    t = p.chassis_thickness_mm

    plate = (
        cq.Workplane("XY")
        .box(p.chassis_length_mm, p.chassis_width_mm, t, centered=(True, True, False))
        .edges("|Z")
        .fillet(p.corner_radius_mm)
    )

    # Corner mounting holes, inset 15 mm from plate edges
    inset = 15.0
    hx = p.chassis_length_mm / 2 - inset
    hy = p.chassis_width_mm / 2 - inset
    plate = (
        plate.faces(">Z").workplane()
        .pushPoints([(hx, hy), (-hx, hy), (hx, -hy), (-hx, -hy)])
        .hole(p.mounting_hole_diameter_mm)
    )

    def bay(center_x: float, dims: tuple[float, float, float], wall: float = 3.0):
        length, width, height = dims
        outer = (
            cq.Workplane("XY", origin=(center_x, 0, t))
            .box(length + 2 * wall, width + 2 * wall, height, centered=(True, True, False))
        )
        inner = (
            cq.Workplane("XY", origin=(center_x, 0, t + wall))
            .box(length, width, height, centered=(True, True, False))
        )
        return outer.cut(inner)

    battery_bay = bay(-p.chassis_length_mm / 4, p.battery_bay_mm)
    elec_bay = bay(p.chassis_length_mm / 8, p.electronics_bay_mm)

    mast_x = p.chassis_length_mm / 2 - 60.0
    mast = (
        cq.Workplane("XY", origin=(mast_x, 0, t))
        .circle(p.mast_diameter_mm / 2)
        .extrude(p.mast_height_mm)
    )

    structure = plate.union(battery_bay).union(elec_bay).union(mast)
    structure_volume = structure.val().Volume()

    # Wheel placeholders, centered on the track line (visual only; excluded
    # from chassis mass). Bounding width = track + wheel_width.
    wheels = None
    wx = p.wheelbase_mm / 2
    wy = p.track_width_mm / 2
    for x in (wx, -wx):
        for y in (wy, -wy):
            w = (
                cq.Workplane("XZ")
                .circle(p.wheel_diameter_mm / 2)
                .extrude(p.wheel_width_mm / 2, both=True)
                .translate((x, y, 0))
            )
            wheels = w if wheels is None else wheels.union(w)

    return structure.union(wheels), structure_volume


def _analytic_chassis_volume_mm3(p: CADParams) -> float:
    """Approximate structure volume when CadQuery is unavailable (labeled)."""
    plate = p.chassis_length_mm * p.chassis_width_mm * p.chassis_thickness_mm
    mast = 3.14159 * (p.mast_diameter_mm / 2) ** 2 * p.mast_height_mm
    bays = 0.0
    for length, width, height in (p.battery_bay_mm, p.electronics_bay_mm):
        wall = 3.0
        bays += (length + 2 * wall) * (width + 2 * wall) * height - length * width * (height - wall)
    return plate + mast + bays


def generate_chassis(params: CADParams, stl_path: Path, step_path: Path | None = None) -> CADResult:
    stl_path.parent.mkdir(parents=True, exist_ok=True)

    if not CADQUERY_AVAILABLE:
        write_box_stl(
            stl_path,
            params.chassis_length_mm, params.chassis_width_mm, params.chassis_thickness_mm,
        )
        return CADResult(
            stl_path=stl_path,
            step_path=None,
            chassis_volume_mm3=_analytic_chassis_volume_mm3(params),
            used_cadquery=False,
            note="PLACEHOLDER: CadQuery not installed — STL is a plain chassis-sized box, "
                 "volume is an analytic approximation. Install backend[cad] for real geometry.",
        )

    model, structure_volume = _build_model(params)
    cq.exporters.export(model, str(stl_path), tolerance=0.1)
    exported_step = None
    if step_path is not None:
        try:
            cq.exporters.export(model, str(step_path))
            exported_step = step_path
        except Exception:  # STEP export is best-effort; STL is the contract
            exported_step = None

    return CADResult(
        stl_path=stl_path,
        step_path=exported_step,
        chassis_volume_mm3=structure_volume,
        used_cadquery=True,
        note="Generated with CadQuery template mobile_robot_base_v1. "
             "Chassis mass computed from actual solid volume.",
    )
