"""Rule-based risk report generation.

Deterministic rules over requirements + architecture + simulation results.
Severity reflects engineering judgment encoded as thresholds — no LLM
guessing. Every design also carries the standing 'analysis fidelity' risks.
"""

from app.agents.requirements import OUT_OF_SCOPE_RE
from app.schemas import (
    BOM,
    ArchitectureSpec,
    Requirements,
    RiskItem,
    RiskReport,
    RiskSeverity,
    SimulationResults,
)


def generate_risk_report(
    design_id: str,
    req: Requirements,
    arch: ArchitectureSpec,
    sim: SimulationResults,
    bom: BOM | None = None,
) -> RiskReport:
    items: list[RiskItem] = []

    def add(rid: str, title: str, sev: RiskSeverity, desc: str, mit: str) -> None:
        items.append(RiskItem(id=rid, title=title, severity=sev, description=desc, mitigation=mit))

    # Scope risk — the single most important honesty item; checked on the raw
    # prompt so it fires regardless of which extractor (LLM or rules) ran.
    scope = OUT_OF_SCOPE_RE.search(req.prompt)
    if scope:
        term = scope.group(1)
        add("R-001", f"Requested platform ('{term}') is outside system scope",
            RiskSeverity.critical,
            f"The prompt asks for a {term}, but this system currently designs ONE "
            "robot class: a 4-wheel ground mobile robot. Everything in this package "
            f"is a ground-robot reinterpretation and does not represent a {term} design.",
            "Do not use this package for the requested platform. Confirm with the "
            "customer whether a ground robot is acceptable; aerial/other platforms "
            "are on the roadmap, not in the product.")

    # Standing fidelity risk — always present
    add("R-000", "Analysis fidelity limits", RiskSeverity.high,
        "All structural and stability numbers are first-order analytical estimates. "
        "No FEA, no dynamic simulation, no physical testing has been performed.",
        "Treat this package as a concept design. Perform FEA and prototype testing "
        "before fabrication or deployment.")

    if bom is not None and bom.total_cost_usd > req.max_cost_usd:
        add("R-103", "Estimated cost exceeds budget", RiskSeverity.high,
            f"BOM total ${bom.total_cost_usd:.0f} exceeds the stated budget "
            f"${req.max_cost_usd:.0f} by "
            f"{(bom.total_cost_usd / req.max_cost_usd - 1) * 100:.0f}%.",
            "Reduce the sensor suite, choose lower-cost component classes, or "
            "revisit the budget with the customer before proceeding.")

    for check in sim.checks:
        if not check.passed:
            add(f"R-CHK-{check.name}", f"Failed check: {check.name}", RiskSeverity.high,
                f"{check.name} = {check.value} {check.unit}, threshold {check.threshold}. "
                f"Formula: {check.formula}",
                "Revise architecture or CAD parameters until this check passes.")

    if sim.runtime_margin < 1.25:
        add("R-101", "Thin battery runtime margin", RiskSeverity.medium,
            f"Estimated runtime {sim.estimated_runtime_hr} h vs required {req.runtime_hr} h "
            f"(margin {sim.runtime_margin}x). Real-world draw is usually higher than modeled.",
            "Increase battery capacity one pack size or reduce electronics duty cycle.")

    if sim.torque_margin < 2.0:
        add("R-102", "Modest drivetrain torque margin", RiskSeverity.low,
            f"Torque margin {sim.torque_margin}x on worst-case ramp+acceleration.",
            "Acceptable for flat floors; increase gearing if thresholds/ramps exceed spec.")

    if req.environment.value == "indoor_industrial":
        add("R-201", "Industrial environment hazards", RiskSeverity.medium,
            "Factory floors bring dust, oil films, EMI near VFDs/welders, and forklift traffic.",
            "Seal electronics bay (target IP54), add e-stop and visual/audible presence "
            "indicators, validate sensor performance under factory lighting.")

    add("R-202", "Thermal load in enclosed electronics bay", RiskSeverity.medium,
        "SBC + motor drivers in a walled bay can exceed component temperature ratings "
        "during sustained operation; no thermal analysis was performed.",
        "Add ventilation slots or a small fan; measure bay temperature during endurance "
        "testing.")

    if arch.battery.chemistry.lower().startswith("li"):
        add("R-203", "Lithium battery handling", RiskSeverity.medium,
            "Lithium pack requires protected mounting, BMS, and charging discipline.",
            "Use a pack with integrated BMS, fuse the main bus, mechanically restrain the "
            "pack in its bay, follow the cell vendor's charge spec.")

    if sim.chassis_safety_factor > 20:
        add("R-301", "Chassis likely overbuilt", RiskSeverity.info,
            f"Bending safety factor ~{sim.chassis_safety_factor} suggests the plate is much "
            "thicker than static loads require (stiffness/mounting may still justify it).",
            "Consider thinner plate or lightening pockets in a mass-optimization pass.")

    failed = [c for c in sim.checks if not c.passed]
    overall = (
        f"{len(failed)} of {len(sim.checks)} engineering checks failed."
        if failed else
        f"All {len(sim.checks)} engineering checks passed. Design is plausible at "
        "concept level; see R-000 for fidelity limits."
    )
    return RiskReport(design_id=design_id, items=items, overall_assessment=overall)
