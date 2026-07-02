"""Golden-path regression tests: the demo must produce every artifact,
and each artifact must be substantive, not an empty husk."""

import csv
import json
import struct

EXPECTED_ARTIFACTS = [
    "requirements.json",
    "architecture.json",
    "cad_params.json",
    "robot_chassis.stl",
    "simulation_results.json",
    "risk_report.json",
    "bom.csv",
    "engineering_report.md",
    "artifact_manifest.json",
]


def test_all_expected_artifacts_exist(demo_output_dir):
    for name in EXPECTED_ARTIFACTS:
        path = demo_output_dir / name
        assert path.exists(), f"missing artifact: {name}"
        assert path.stat().st_size > 0, f"empty artifact: {name}"


def test_stl_is_valid_and_nonempty(demo_output_dir):
    data = (demo_output_dir / "robot_chassis.stl").read_bytes()
    assert len(data) > 84, "STL smaller than header"
    if not data[:5].lower() == b"solid":  # binary STL
        (n_tri,) = struct.unpack("<I", data[80:84])
        assert n_tri > 0, "binary STL has zero triangles"
        assert len(data) >= 84 + n_tri * 50


def test_requirements_json_parsed_runtime(demo_output_dir):
    req = json.loads((demo_output_dir / "requirements.json").read_text())
    assert req["runtime_hr"] == 8.0, "should parse '8 hours' from the demo prompt"
    assert req["payload_kg"] > 0
    assert len(req["assumptions"]) > 0, "gap-filling must be documented as assumptions"


def test_simulation_results_required_fields(demo_output_dir):
    sim = json.loads((demo_output_dir / "simulation_results.json").read_text())
    for field in ("total_mass_kg", "estimated_runtime_hr", "torque_margin",
                  "tip_angle_lateral_deg", "chassis_safety_factor", "checks", "limitations"):
        assert field in sim, f"simulation_results missing {field}"
    assert len(sim["checks"]) >= 5
    assert len(sim["limitations"]) > 0, "results must state their limitations"
    for check in sim["checks"]:
        assert check["formula"], f"check {check['name']} must expose its formula"


def test_bom_csv_has_rows_and_total(demo_output_dir):
    with open(demo_output_dir / "bom.csv") as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "part_number"
    data_rows = [r for r in rows[1:] if r and r[0] and r[0] != "TOTAL"]
    assert len(data_rows) >= 8, "BOM should contain a real parts list"
    assert any(r and r[0] == "TOTAL" for r in rows), "BOM must include a total row"


def test_report_includes_assumptions_and_limitations(demo_output_dir):
    report = (demo_output_dir / "engineering_report.md").read_text()
    assert "## Summary" in report
    assert "Assumptions" in report
    assert "## Limitations" in report
    assert "NOT finite element analysis" in report
    assert "not a certified design" in report


def test_manifest_references_existing_files(demo_output_dir):
    manifest = json.loads((demo_output_dir / "artifact_manifest.json").read_text())
    assert manifest["design_id"] == "test-demo"
    assert len(manifest["artifacts"]) >= 8
    for ref in manifest["artifacts"]:
        assert (demo_output_dir / ref["name"]).exists(), f"manifest references missing {ref['name']}"


def test_all_checks_pass_for_demo_prompt(demo_state):
    """The canned demo design must be healthy; a regression here means a
    sizing or geometry change broke the reference design."""
    sim = demo_state.simulation
    failed = [c.name for c in sim.checks if not c.passed]
    assert not failed, f"demo design failed checks: {failed}"
    assert sim.estimated_runtime_hr >= 8.0
    assert demo_state.bom.total_cost_usd <= demo_state.requirements.max_cost_usd
