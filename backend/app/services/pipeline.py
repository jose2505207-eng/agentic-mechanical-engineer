"""The golden path: prompt -> full engineering artifact package.

This is a plain, readable, sequential function on purpose. When the AI agent
layer matures, this becomes a LangGraph graph with the same state object
(EngineeringReportState) — the contracts are already graph-shaped.
"""

import uuid
from pathlib import Path

from app.agents.architecture import generate_architecture
from app.agents.cad_params import generate_cad_params
from app.agents.requirements import extract_requirements
from app.bom.generator import generate_bom, write_bom_csv
from app.cad.chassis import generate_chassis
from app.reports.markdown import render_report
from app.schemas import EngineeringReportState, SimulationInput
from app.simulation.checks import run_checks
from app.simulation.risk import generate_risk_report
from app.storage.artifacts import ArtifactStore


def run_pipeline(prompt: str, output_dir: Path, design_id: str | None = None
                 ) -> EngineeringReportState:
    design_id = design_id or f"design-{uuid.uuid4().hex[:8]}"
    store = ArtifactStore(output_dir)
    state = EngineeringReportState(design_id=design_id, prompt=prompt)

    # 1. Requirements
    state.requirements = extract_requirements(prompt)
    store.write_json("requirements.json", state.requirements,
                     "Structured requirements with explicit assumptions")

    # 2. Architecture
    state.architecture = generate_architecture(state.requirements)
    store.write_json("architecture.json", state.architecture,
                     "System architecture: drivetrain, battery, motors, materials")

    # 3. CAD parameters (schema-validated bounds)
    state.cad_params = generate_cad_params(state.requirements, state.architecture)
    store.write_json("cad_params.json", state.cad_params,
                     "Validated parameters for CAD template " + state.cad_params.template)

    # 4. CAD generation + export
    cad_result = generate_chassis(
        state.cad_params,
        stl_path=store.path("robot_chassis.stl"),
        step_path=store.path("robot_chassis.step"),
    )
    state.cad_export_note = cad_result.note
    store.track_file("robot_chassis.stl", "stl", "Robot chassis 3D model")
    if cad_result.step_path is not None:
        store.track_file("robot_chassis.step", "step", "Robot chassis STEP (interop)")

    # 5. Engineering checks (chassis mass from real solid volume x density)
    chassis_mass_kg = (
        cad_result.chassis_volume_mm3 * 1e-9
        * state.architecture.chassis_material_density_kg_m3
    )
    sim_input = SimulationInput(
        requirements=state.requirements,
        architecture=state.architecture,
        cad_params=state.cad_params,
        chassis_mass_kg=chassis_mass_kg,
    )
    state.simulation = run_checks(sim_input)
    store.write_json("simulation_results.json", state.simulation,
                     "Deterministic engineering checks (not FEA)")

    # 6. Risk report
    state.risk_report = generate_risk_report(
        design_id, state.requirements, state.architecture, state.simulation)
    store.write_json("risk_report.json", state.risk_report, "Rule-based risk assessment")

    # 7. BOM
    state.bom = generate_bom(design_id, state.requirements, state.architecture, state.cad_params)
    store.write_json("bom.json", state.bom, "Bill of materials (JSON form)")
    write_bom_csv(state.bom, store.path("bom.csv"))
    store.track_file("bom.csv", "csv", "Bill of materials with cost estimates")

    # 8. Report
    store.write_text("engineering_report.md", render_report(state), "md",
                     "Human-readable engineering report")

    # 9. Manifest
    notes = ["Deterministic MVP pipeline; AI agent layer can replace stages 1-3."]
    if not cad_result.used_cadquery:
        notes.append("CAD placeholder mode was used: " + cad_result.note)
    state.manifest = store.write_manifest(design_id, prompt, notes)
    return state
