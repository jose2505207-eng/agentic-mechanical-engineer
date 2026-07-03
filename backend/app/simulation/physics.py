"""Headless physics testing of generated geometry (PyBullet).

What "test it in simulation" honestly means here:
- drop test: spawn the part 20 mm above a ground plane, simulate 3 s,
  measure whether it settles and how far it tips from its design-up axis.
- push test: apply a lateral force of 0.3x its own weight at the CoM for
  0.5 s, settle 2 s, check it hasn't toppled (> 45 deg counts as toppled).

Both results become checks the optimization loop iterates against, so the
AI redesigns geometry that falls over.

Honesty notes baked into every result:
- PyBullet uses the CONVEX HULL of the mesh for dynamic collision — cavities
  and overhangs don't collide (industry-standard simplification for single
  rigid bodies; noted in limitations).
- This is rigid-body dynamics on a flat plane: no aerodynamics, no motors,
  no terrain. A drone frame "passing" means it sits stably — not that it flies.

The same mass properties are exported as `model.urdf`, loadable directly in
Gazebo, Webots (via urdf2webots), or any URDF-speaking simulator, so users
can continue testing in a full robot simulator.

If PyBullet is not installed, results carry engine="unavailable" and the
physics checks are skipped (never faked).
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)

try:
    import pybullet as p
    PYBULLET_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    PYBULLET_AVAILABLE = False

GRAVITY = 9.81
DROP_HEIGHT_M = 0.02
SETTLE_STEPS = 720          # 3 s @ 240 Hz
PUSH_STEPS = 120            # 0.5 s push
POST_PUSH_STEPS = 480       # 2 s recovery
PUSH_FRACTION = 0.30        # lateral force = 0.3 x weight
TIP_LIMIT_DEG = 45.0

LIMITATIONS = [
    "Rigid-body dynamics on a flat plane: no aerodynamics, no actuation, "
    "no terrain, no contact with other parts.",
    "Collision uses the mesh's convex hull — cavities and concave features "
    "do not collide.",
    "Passing means the part rests and resists a 0.3g lateral push — it says "
    "nothing about the object's actual function (flight, load, motion).",
]


class PhysicsResults(BaseModel):
    engine: str  # pybullet | unavailable
    settled: bool
    tilt_after_drop_deg: float
    survived_push: bool
    tilt_after_push_deg: float
    rest_height_mm: float
    notes: list[str] = []
    limitations: list[str] = LIMITATIONS


def _tilt_deg(client: int, body: int) -> float:
    """Angle between the body's current up-axis and world up."""
    _, orn = p.getBasePositionAndOrientation(body, physicsClientId=client)
    rot = p.getMatrixFromQuaternion(orn)
    # third column of rotation matrix = body z-axis in world frame
    up_z = rot[8]
    return math.degrees(math.acos(max(-1.0, min(1.0, up_z))))


def simulate_stl(stl_path: Path, mass_kg: float, bbox_mm: tuple[float, float, float]
                 ) -> PhysicsResults:
    if not PYBULLET_AVAILABLE:
        return PhysicsResults(
            engine="unavailable", settled=False, tilt_after_drop_deg=0.0,
            survived_push=False, tilt_after_push_deg=0.0, rest_height_mm=0.0,
            notes=["PyBullet not installed — physics tests skipped, not faked. "
                   "pip install pybullet to enable."])

    # Mesh origin is wherever the CAD script put it; place the LOWEST point
    # of the mesh DROP_HEIGHT above the plane, in design orientation.
    # CRITICAL: pass the real CoM to Bullet — by default it assumes CoM at
    # the mesh origin, which makes bottom-origin parts unrealistically stable
    # (caught by the known-answer tall-stick test).
    import trimesh
    tm = trimesh.load(str(stl_path))
    z_min_m = float(tm.bounds[0][2]) / 1000.0
    com_m = [float(c) / 1000.0 for c in tm.center_mass]

    client = p.connect(p.DIRECT)
    try:
        p.setGravity(0, 0, -GRAVITY, physicsClientId=client)
        plane = p.createMultiBody(
            0, p.createCollisionShape(p.GEOM_PLANE, physicsClientId=client),
            physicsClientId=client)
        p.changeDynamics(plane, -1, lateralFriction=0.8, physicsClientId=client)

        # STL is in mm; bullet wants meters.
        col = p.createCollisionShape(
            p.GEOM_MESH, fileName=str(stl_path), meshScale=[0.001] * 3,
            physicsClientId=client)
        start_z = -z_min_m + DROP_HEIGHT_M
        body = p.createMultiBody(mass_kg, col, basePosition=[0, 0, start_z],
                                 baseInertialFramePosition=com_m,
                                 physicsClientId=client)
        p.changeDynamics(body, -1, lateralFriction=0.8, physicsClientId=client)

        for _ in range(SETTLE_STEPS):
            p.stepSimulation(physicsClientId=client)

        lin, _ang = p.getBaseVelocity(body, physicsClientId=client)
        settled = all(abs(v) < 0.05 for v in lin)
        tilt_drop = _tilt_deg(client, body)

        # Push test: lateral force through the LIVE CoM each step
        # (getBasePositionAndOrientation returns the inertial/CoM frame).
        force = PUSH_FRACTION * mass_kg * GRAVITY
        for _ in range(PUSH_STEPS):
            pos, _ = p.getBasePositionAndOrientation(body, physicsClientId=client)
            p.applyExternalForce(body, -1, [force, 0, 0], pos, p.WORLD_FRAME,
                                 physicsClientId=client)
            p.stepSimulation(physicsClientId=client)
        for _ in range(POST_PUSH_STEPS):
            p.stepSimulation(physicsClientId=client)

        tilt_push = _tilt_deg(client, body)
        pos_end, _ = p.getBasePositionAndOrientation(body, physicsClientId=client)
        return PhysicsResults(
            engine="pybullet",
            settled=settled,
            tilt_after_drop_deg=round(tilt_drop, 1),
            survived_push=tilt_push < TIP_LIMIT_DEG,
            tilt_after_push_deg=round(tilt_push, 1),
            rest_height_mm=round(pos_end[2] * 1000.0, 1),
            notes=[f"drop from {DROP_HEIGHT_M * 1000:.0f} mm, "
                   f"push {PUSH_FRACTION:.0%} of weight for 0.5 s"])
    finally:
        p.disconnect(physicsClientId=client)


def physics_to_checks(phys: PhysicsResults) -> list:
    """Convert sim results into CheckResults for the optimization loop.
    Engine unavailable -> no checks (skipped honestly, never faked)."""
    from app.schemas import CheckResult
    if phys.engine != "pybullet":
        return []
    return [
        CheckResult(
            name="physics_settles_upright",
            value=phys.tilt_after_drop_deg, unit="deg tilt",
            threshold=15.0,
            passed=phys.settled and phys.tilt_after_drop_deg < 15.0,
            formula="PyBullet drop from 20 mm, 3 s rigid-body sim; "
                    "final tilt from design-up < 15 deg and velocity ~ 0",
            assumptions=["convex-hull collision", "flat plane, friction 0.8"]),
        CheckResult(
            name="physics_push_stability",
            value=phys.tilt_after_push_deg, unit="deg tilt",
            threshold=TIP_LIMIT_DEG,
            passed=phys.survived_push,
            formula=f"lateral force {PUSH_FRACTION:.0%} of weight at CoM for "
                    f"0.5 s + 2 s settle; tilt < {TIP_LIMIT_DEG:.0f} deg",
            assumptions=["convex-hull collision", "rigid body, no anchoring"]),
    ]


def export_urdf(stl_name: str, mass_kg: float, bbox_mm: tuple[float, float, float],
                urdf_path: Path, design_id: str) -> None:
    """Minimal URDF referencing the STL — loadable in Gazebo/Webots/PyBullet.

    Inertia: solid-box approximation from the bounding box (stated in the
    file). Good enough to open and test; refine in the target simulator."""
    x, y, z = (v / 1000.0 for v in bbox_mm)
    ixx = mass_kg / 12.0 * (y * y + z * z)
    iyy = mass_kg / 12.0 * (x * x + z * z)
    izz = mass_kg / 12.0 * (x * x + y * y)
    urdf_path.write_text(f"""<?xml version="1.0"?>
<!-- Generated by Agentic Mechanical Engineer for design {design_id}.
     Inertia is a solid-box approximation from the bounding box.
     Load in Gazebo (spawn_entity), Webots (urdf2webots), or PyBullet. -->
<robot name="{design_id}">
  <link name="base_link">
    <inertial>
      <mass value="{mass_kg:.4f}"/>
      <inertia ixx="{ixx:.6f}" ixy="0" ixz="0" iyy="{iyy:.6f}" iyz="0" izz="{izz:.6f}"/>
    </inertial>
    <visual>
      <geometry><mesh filename="{stl_name}" scale="0.001 0.001 0.001"/></geometry>
    </visual>
    <collision>
      <geometry><mesh filename="{stl_name}" scale="0.001 0.001 0.001"/></geometry>
    </collision>
  </link>
</robot>
""")
