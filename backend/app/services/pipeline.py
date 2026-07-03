"""The golden path: prompt -> full engineering artifact package.

Two modes (ADR-009):
- template:   the original wheeled-robot vertical — engineer-authored CAD
              template + full physics checks. Always available, fully offline.
- generative: the model writes a parametric CadQuery script for ARBITRARY
              objects; sandboxed execution + validation + retry loop. Needs
              an LLM provider. Falls back to template mode if it fails.

Plain sequential functions on purpose. When the AI layer matures further,
this becomes a LangGraph graph with the same state object
(EngineeringReportState) — the contracts are already graph-shaped.
"""

import logging
import re
import uuid
from pathlib import Path

from app.agents.cad_params import generate_cad_params
from app.agents.requirements import OUT_OF_SCOPE_RE
from app.bom.generator import generate_bom, write_bom_csv
from app.bom.sourcing import enrich_bom
from app.cad.chassis import generate_chassis
from app.cad.generative import generate_model
from app.cad.sandbox import CADScriptError
from app.config import get_settings
from app.llm.agents import extract_requirements, propose_architecture
from app.llm.provider import LLMUnavailable
from app.reports.generic_markdown import render_generic_report
from app.reports.markdown import render_report
from app.schemas import (
    EngineeringReportState,
    GeometryCheckReport,
    GeometryMetrics,
    RiskItem,
    RiskReport,
    RiskSeverity,
    SimulationInput,
)
from app.simulation.checks import run_checks
from app.simulation.geometry_checks import LIMITATIONS as GEOMETRY_CHECK_LIMITATIONS
from app.simulation.geometry_checks import run_geometry_checks
from app.simulation.physics import export_urdf, physics_to_checks, simulate_stl
from app.simulation.risk import generate_risk_report
from app.storage.artifacts import ArtifactStore

logger = logging.getLogger(__name__)

_GROUND_ROBOT_RE = re.compile(
    r"\b(robot|rover|agv|amr|inspection (?:vehicle|platform)|mobile platform)\b",
    re.IGNORECASE)

PRINT_BED_MM = 256.0
PLA_DENSITY_KG_M3 = 1240.0
PLA_USD_PER_KG = 25.0


def select_mode(prompt: str) -> str:
    """template for the proven wheeled-robot vertical; generative for
    everything else — but generative needs a configured LLM provider."""
    if get_settings().model_provider.lower() == "deterministic":
        return "template"
    if OUT_OF_SCOPE_RE.search(prompt):
        return "generative"
    if _GROUND_ROBOT_RE.search(prompt):
        return "template"
    return "generative"


def run_pipeline(prompt: str, output_dir: Path, design_id: str | None = None
                 ) -> EngineeringReportState:
    design_id = design_id or f"design-{uuid.uuid4().hex[:8]}"
    mode = select_mode(prompt)
    if mode == "generative":
        try:
            return _run_generative(prompt, output_dir, design_id)
        except (LLMUnavailable, CADScriptError) as exc:
            logger.warning("generative mode failed (%s); falling back to template", exc)
    return _run_template(prompt, output_dir, design_id)


# ---------------------------------------------------------------------------
# Generative mode: arbitrary objects via model-written CadQuery code
# ---------------------------------------------------------------------------

def _run_generative(prompt: str, output_dir: Path, design_id: str
                    ) -> EngineeringReportState:
    store = ArtifactStore(output_dir)
    state = EngineeringReportState(design_id=design_id, prompt=prompt, mode="generative")

    # 1. Requirements (LLM w/ deterministic fallback — same station as ever)
    state.requirements = extract_requirements(prompt)
    store.write_json("requirements.json", state.requirements,
                     "Structured requirements with explicit assumptions")

    # 2. Generative CAD with sim-feedback: model writes code -> sandbox ->
    #    geometry checks + PHYSICS SIM (PyBullet drop/push) -> failures fed
    #    back for redesign (bounded loop)
    req = state.requirements
    last_physics: dict = {}

    def check_fn(m):
        checks = run_geometry_checks(req, m.volume_mm3, m.bbox_mm, m.is_valid_solid)
        mass_kg = m.volume_mm3 * 1e-9 * PLA_DENSITY_KG_M3
        phys = simulate_stl(m.stl_path, mass_kg, m.bbox_mm)
        last_physics["result"] = phys
        return checks + physics_to_checks(phys)

    gen = generate_model(
        prompt, req.max_dimensions_mm,
        stl_path=store.path("model.stl"), step_path=store.path("model.step"),
        check_fn=check_fn)
    state.cad_export_note = gen.note
    store.write_text("cad_script.py", gen.script, "py",
                     "Model-written parametric CadQuery source (editable)")
    store.track_file("model.stl", "stl", "AI-designed 3D model (print-ready mesh)")
    if gen.metrics.step_path is not None:
        store.track_file("model.step", "step", "AI-designed model, STEP interop")

    # 3. Geometry metrics — measured, not guessed
    env = state.requirements.max_dimensions_mm
    bbox = gen.metrics.bbox_mm
    mass_kg = gen.metrics.volume_mm3 * 1e-9 * PLA_DENSITY_KG_M3
    state.geometry = GeometryMetrics(
        volume_mm3=round(gen.metrics.volume_mm3, 1),
        bbox_mm=tuple(round(v, 1) for v in bbox),
        is_valid_solid=gen.metrics.is_valid_solid,
        density_kg_m3=PLA_DENSITY_KG_M3,
        est_mass_kg=round(mass_kg, 4),
        est_material_cost_usd=round(mass_kg * PLA_USD_PER_KG, 2),
        fits_envelope=all(b <= e * 1.02 for b, e in zip(bbox, env, strict=True)),
        fits_print_bed=all(b <= PRINT_BED_MM for b in bbox),
        generation_attempts=gen.attempts,
        notes=[gen.note],
    )
    store.write_json("geometry_metrics.json", state.geometry,
                     "Measured geometry properties (volume, bbox, printability)")

    # 3b. Physics results (final iteration) + URDF for Gazebo/Webots/PyBullet
    if last_physics.get("result") is not None:
        store.write_json("physics_results.json", last_physics["result"],
                         "PyBullet drop/push simulation of the final geometry")
    mass_for_urdf = gen.metrics.volume_mm3 * 1e-9 * PLA_DENSITY_KG_M3
    export_urdf("model.stl", mass_for_urdf, gen.metrics.bbox_mm,
                store.path("model.urdf"), design_id)
    store.track_file("model.urdf", "urdf",
                     "Robot description — load in Gazebo, Webots (urdf2webots) "
                     "or PyBullet to continue testing")

    # 4. Check report — what the optimization loop iterated against
    state.geometry_checks = GeometryCheckReport(
        design_id=design_id, checks=gen.checks,
        all_passed=gen.all_checks_passed,
        iterations=gen.iterations,
        optimization_note=gen.note,
        limitations=list(GEOMETRY_CHECK_LIMITATIONS))
    store.write_json("simulation_results.json", state.geometry_checks,
                     "Engineering checks + optimization iteration history")

    # 5. Risks — geometry-level honesty; failed checks become HIGH items
    items = [RiskItem(
        id="R-000", title="Analysis fidelity limits", severity=RiskSeverity.high,
        description="Geometry is AI-generated and validated for geometric soundness "
                    "only. No FEA, kinematics, tolerance, or assembly-fit analysis "
                    "was performed.",
        mitigation="Engineer review + slicer checks before printing; FEA before "
                   "any load-bearing use.")]
    for c in gen.checks:
        if not c.passed:
            items.append(RiskItem(
                id=f"R-CHK-{c.name}", title=f"Failed check: {c.name}",
                severity=RiskSeverity.high,
                description=f"{c.name} = {c.value} {c.unit}, allowed {c.threshold}. "
                            f"Formula: {c.formula}. The optimization loop could not "
                            f"converge within its iteration budget.",
                mitigation="Re-run with a larger CAD_MAX_ITERATIONS, relax the "
                           "constraint, or edit cad_script.py dimensions by hand."))
    if not state.geometry.fits_print_bed:
        items.append(RiskItem(
            id="R-403", title="Too large for a consumer print bed",
            severity=RiskSeverity.medium,
            description=f"Largest dimension exceeds {PRINT_BED_MM:.0f} mm.",
            mitigation="Split into parts with joints, or print on a large-format machine."))
    state.risk_report = RiskReport(
        design_id=design_id, items=items,
        overall_assessment=(
            f"Converged: all checks passed in {gen.attempts} iteration(s). "
            if gen.all_checks_passed else
            f"DID NOT CONVERGE in {gen.attempts} iteration(s); see failed checks. ")
        + "Concept-level only.",
        generated_by="generative-rules-v2")
    store.write_json("risk_report.json", state.risk_report, "Rule-based risk assessment")

    # 6. Report + manifest
    store.write_text("engineering_report.md", render_generic_report(state), "md",
                     "Human-readable engineering report")
    notes = ["Mode: GENERATIVE — model-written parametric CAD with sim-feedback "
             f"optimization ({gen.attempts} iteration(s), "
             + ("converged" if gen.all_checks_passed else "NOT converged") + ")."]
    for item in state.risk_report.items:
        if item.severity.value in ("critical", "high") and item.id != "R-000":
            notes.append(f"{item.severity.value.upper()}: {item.title}")
    state.manifest = store.write_manifest(design_id, prompt, notes)
    return state


# ---------------------------------------------------------------------------
# Template mode: the original wheeled-robot vertical (unchanged behavior)
# ---------------------------------------------------------------------------

def _run_template(prompt: str, output_dir: Path, design_id: str
                  ) -> EngineeringReportState:
    store = ArtifactStore(output_dir)
    state = EngineeringReportState(design_id=design_id, prompt=prompt, mode="template")

    # 1. Requirements
    state.requirements = extract_requirements(prompt)
    store.write_json("requirements.json", state.requirements,
                     "Structured requirements with explicit assumptions")

    # 2. Architecture (LLM proposal gated by feasibility rules, det. fallback)
    state.architecture = propose_architecture(state.requirements)
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

    # 6. BOM (curated; enriched via external sourcing only if gate is enabled).
    #    Generated before the risk report so budget compliance can be checked.
    state.bom = generate_bom(design_id, state.requirements, state.architecture, state.cad_params)
    state.bom = enrich_bom(state.bom)
    store.write_json("bom.json", state.bom, "Bill of materials (JSON form)")
    write_bom_csv(state.bom, store.path("bom.csv"))
    store.track_file("bom.csv", "csv", "Bill of materials with cost estimates")

    # 7. Risk report (sees requirements, architecture, simulation, and BOM)
    state.risk_report = generate_risk_report(
        design_id, state.requirements, state.architecture, state.simulation, state.bom)
    store.write_json("risk_report.json", state.risk_report, "Rule-based risk assessment")

    # 8. Report
    store.write_text("engineering_report.md", render_report(state), "md",
                     "Human-readable engineering report")

    # 9. Manifest — notes report what ACTUALLY happened on this run
    req_llm = any(a.field == "provenance" for a in state.requirements.assumptions)
    arch_llm = any("feasibility gates" in r for r in state.architecture.rationale)
    notes = [
        "Mode: TEMPLATE — Requirements: "
        + ("LLM-extracted, schema-validated" if req_llm else "deterministic extractor")
        + " | Architecture: "
        + ("LLM-proposed, passed feasibility gates" if arch_llm
           else "deterministic generator"),
    ]
    failed = [c.name for c in state.simulation.checks if not c.passed]
    if failed:
        notes.append(f"{len(failed)} of {len(state.simulation.checks)} engineering "
                     f"checks FAILED: {', '.join(failed)} — see risk report.")
    for item in state.risk_report.items:
        if item.severity.value in ("critical", "high") and item.id != "R-000":
            notes.append(f"{item.severity.value.upper()}: {item.title}")
    if not cad_result.used_cadquery:
        notes.append("CAD placeholder mode was used: " + cad_result.note)
    state.manifest = store.write_manifest(design_id, prompt, notes)
    return state
