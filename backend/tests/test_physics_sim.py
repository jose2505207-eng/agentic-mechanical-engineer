"""Physics simulation: known-answer stability tests + URDF export.

Known-answer discipline: a flat wide box MUST survive the push test; a tall
skinny box MUST topple. If both pass or both fail, the sim is decorative."""

import xml.etree.ElementTree as ET

import pytest

from app.cad.sandbox import run_script
from app.simulation.physics import (
    PYBULLET_AVAILABLE,
    export_urdf,
    physics_to_checks,
    simulate_stl,
)

needs_pybullet = pytest.mark.skipif(not PYBULLET_AVAILABLE, reason="pybullet not installed")

FLAT_BOX = """
import cadquery as cq
result = cq.Workplane("XY").box(120, 120, 20, centered=(True, True, False))
"""

TALL_STICK = """
import cadquery as cq
result = cq.Workplane("XY").box(12, 12, 300, centered=(True, True, False))
"""


@pytest.fixture(scope="module")
def flat_stl(tmp_path_factory):
    d = tmp_path_factory.mktemp("phys")
    res = run_script(FLAT_BOX, d / "flat.stl", None)
    return d / "flat.stl", res


@pytest.fixture(scope="module")
def tall_stl(tmp_path_factory):
    d = tmp_path_factory.mktemp("phys2")
    res = run_script(TALL_STICK, d / "tall.stl", None)
    return d / "tall.stl", res


@needs_pybullet
def test_flat_box_is_stable(flat_stl):
    path, res = flat_stl
    phys = simulate_stl(path, 0.3, res.bbox_mm)
    assert phys.engine == "pybullet"
    assert phys.settled
    assert phys.survived_push
    assert phys.tilt_after_push_deg < 15


@needs_pybullet
def test_tall_stick_topples(tall_stl):
    path, res = tall_stl
    phys = simulate_stl(path, 0.3, res.bbox_mm)
    assert not phys.survived_push, "a 12x12x300 stick must fail the 0.3g push test"


@needs_pybullet
def test_physics_checks_feed_the_loop(flat_stl):
    path, res = flat_stl
    checks = physics_to_checks(simulate_stl(path, 0.3, res.bbox_mm))
    names = {c.name for c in checks}
    assert names == {"physics_settles_upright", "physics_push_stability"}
    assert all(c.formula for c in checks)


def test_unavailable_engine_yields_no_checks():
    from app.simulation.physics import PhysicsResults
    phys = PhysicsResults(engine="unavailable", settled=False,
                          tilt_after_drop_deg=0, survived_push=False,
                          tilt_after_push_deg=0, rest_height_mm=0)
    assert physics_to_checks(phys) == [], "skipped physics must never fake checks"


def test_urdf_export_is_valid_xml(tmp_path):
    export_urdf("model.stl", 1.234, (200.0, 150.0, 80.0), tmp_path / "m.urdf", "d-1")
    tree = ET.parse(tmp_path / "m.urdf")
    root = tree.getroot()
    assert root.tag == "robot"
    mass = root.find("./link/inertial/mass")
    assert abs(float(mass.get("value")) - 1.234) < 1e-6
    assert root.find("./link/collision/geometry/mesh").get("filename") == "model.stl"
