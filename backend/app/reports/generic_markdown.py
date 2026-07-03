"""Report renderer for generative-mode designs (arbitrary objects).

Shorter than the robot report because less is verifiable: we have real
geometry metrics but no drivetrain physics. The limitations section is
correspondingly blunter.
"""

from app.schemas import EngineeringReportState

LIMITATIONS = [
    "Geometry was produced by an AI model writing parametric CAD code, then "
    "validated for buildability (valid solid, non-zero volume, envelope fit) — "
    "NOT for function, strength, tolerance, or assembly fit.",
    "No FEA, no kinematic simulation, no thermal analysis was performed.",
    "Mass and material cost assume a uniform solid of the stated material; "
    "actual prints use infill and will weigh and cost less.",
    "Printability check covers bounding size only — overhangs, bridging, and "
    "wall thickness must be checked in a slicer.",
    "Review by a qualified engineer is required before manufacturing or use.",
]


def render_generic_report(state: EngineeringReportState) -> str:
    req, geo, risk = state.requirements, state.geometry, state.risk_report
    assert req and geo and risk, "generic report requires requirements, geometry, risks"

    md: list[str] = []
    md.append(f"# Engineering Report — {state.design_id}\n")
    md.append(f"**Prompt:** {state.prompt}\n")
    md.append("> **AI-generated concept geometry.** The 3D model was designed by an "
              "AI engineer-agent writing parametric CadQuery code and validated for "
              "geometric soundness only. It is not a certified design.\n")

    md.append("## Geometry\n")
    bx, by, bz = geo.bbox_mm
    md.append(f"- Bounding box: **{bx:.0f} x {by:.0f} x {bz:.0f} mm** "
              f"(envelope limit {' x '.join(f'{d:.0f}' for d in req.max_dimensions_mm)} mm — "
              f"{'fits' if geo.fits_envelope else 'EXCEEDED'})\n"
              f"- Solid volume: {geo.volume_mm3 / 1000:.1f} cm^3 | valid solid: "
              f"{'yes' if geo.is_valid_solid else 'NO'}\n"
              f"- Material (assumed): {geo.material} @ {geo.density_kg_m3:.0f} kg/m^3\n"
              f"- Estimated mass (solid): {geo.est_mass_kg:.3f} kg | material cost: "
              f"~${geo.est_material_cost_usd:.2f}\n"
              f"- Single-piece 3D printable (256 mm bed): "
              f"{'yes' if geo.fits_print_bed else 'no — split into parts or scale down'}\n"
              f"- CAD generation attempts: {geo.generation_attempts}\n")
    for n in geo.notes:
        md.append(f"- {n}\n")

    if state.geometry_checks is not None:
        gc = state.geometry_checks
        md.append("\n## Engineering Checks & Optimization\n")
        md.append(f"**{gc.optimization_note}**\n\n")
        md.append("| Check | Value | Allowed | Result | Formula |\n|---|---|---|---|---|\n")
        for c in gc.checks:
            md.append(f"| {c.name} | {c.value} {c.unit} | {c.threshold} | "
                      f"{'PASS' if c.passed else '**FAIL**'} | `{c.formula}` |\n")
        md.append("\n### Iteration history\n")
        md.extend(f"- {line}\n" for line in gc.iterations)

    md.append("\n## Requirements & Assumptions\n")
    md.append(f"- Payload: {req.payload_kg} kg | runtime: {req.runtime_hr} h | "
              f"budget: ${req.max_cost_usd:.0f} | environment: {req.environment.value}\n")
    if req.assumptions:
        md.append("\n| Field | Assumed | Rationale |\n|---|---|---|\n")
        for a in req.assumptions:
            md.append(f"| {a.field} | {a.assumed_value} | {a.rationale} |\n")
    if req.unknowns:
        md.append("\n**Open questions:**\n")
        md.extend(f"- {u}\n" for u in req.unknowns)

    md.append("\n## Risks\n")
    md.append(f"**Overall:** {risk.overall_assessment}\n\n")
    md.append("| ID | Severity | Risk | Mitigation |\n|---|---|---|---|\n")
    for i in risk.items:
        md.append(f"| {i.id} | {i.severity.value.upper()} | **{i.title}** — "
                  f"{i.description} | {i.mitigation} |\n")

    md.append("\n## Files\n")
    md.append("- `model.stl` — print-ready mesh\n- `model.step` — CAD interop "
              "(when export succeeded)\n- `cad_script.py` — the parametric CadQuery "
              "source; edit dimensions at the top and re-run to iterate\n")

    md.append("\n## Limitations\n")
    md.extend(f"- {lim}\n" for lim in LIMITATIONS)
    return "".join(md)
