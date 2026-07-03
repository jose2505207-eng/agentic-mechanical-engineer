"""Deterministic checks for generatively-built geometry.

These are the checks the optimization loop iterates AGAINST: after a script
builds, these run on the measured geometry; failures are fed back to the
model as redesign instructions. Same honesty rules as the robot checks —
formula and assumptions ride inside every CheckResult.

Driving checks (can force a redesign): kernel validity, envelope fit,
material cost vs budget. Print-bed fit is deliberately NOT a driving check:
many legitimate objects (a 2 kg-payload drone) physically cannot fit a
256 mm bed, and forcing it would fight physics — it stays informational in
GeometryMetrics/risks.
"""

from app.schemas import CheckResult, Requirements

PLA_DENSITY_KG_M3 = 1240.0
PLA_USD_PER_KG = 25.0
ENVELOPE_TOLERANCE = 1.02  # 2% slack for mesh-export noise

LIMITATIONS = [
    "Checks cover geometric soundness, envelope, and material cost only.",
    "No FEA, kinematics, tolerance, assembly-fit, or thermal analysis.",
    "Mass/cost assume a uniform solid; printed parts with infill weigh less.",
    "Wall thickness and overhangs are not analyzed — verify in a slicer.",
]


def run_geometry_checks(req: Requirements, volume_mm3: float,
                        bbox_mm: tuple[float, float, float],
                        is_valid_solid: bool) -> list[CheckResult]:
    checks: list[CheckResult] = []

    checks.append(CheckResult(
        name="valid_solid", value=1.0 if is_valid_solid else 0.0, unit="bool",
        threshold=1.0, passed=is_valid_solid,
        formula="OCCT BRepCheck on the final solid",
        assumptions=["kernel validity != functional correctness"]))

    ratios = [b / e for b, e in zip(bbox_mm, req.max_dimensions_mm, strict=True)]
    worst = max(ratios)
    axis = "XYZ"[ratios.index(worst)]
    checks.append(CheckResult(
        name="envelope_fit", value=round(worst, 3), unit="ratio (worst axis)",
        threshold=ENVELOPE_TOLERANCE, passed=worst <= ENVELOPE_TOLERANCE,
        formula="max(bbox_axis / envelope_axis) <= 1.02",
        assumptions=[f"worst axis {axis}: {bbox_mm[ratios.index(worst)]:.0f} mm vs "
                     f"limit {req.max_dimensions_mm[ratios.index(worst)]:.0f} mm",
                     "2% tolerance absorbs mesh-export noise"]))

    mass_kg = volume_mm3 * 1e-9 * PLA_DENSITY_KG_M3
    cost = mass_kg * PLA_USD_PER_KG
    checks.append(CheckResult(
        name="material_cost_budget", value=round(cost, 2), unit="USD",
        threshold=req.max_cost_usd, passed=cost <= req.max_cost_usd,
        formula="volume * PLA_density * $/kg <= max_cost_usd",
        assumptions=[f"solid PLA at {PLA_DENSITY_KG_M3:.0f} kg/m^3, "
                     f"${PLA_USD_PER_KG:.0f}/kg — upper bound (infill is cheaper)",
                     "material only; motors/electronics priced separately"]))
    return checks


def render_check_feedback(checks: list[CheckResult]) -> str:
    """Turn failed checks into redesign instructions for the model."""
    failed = [c for c in checks if not c.passed]
    lines = ["The geometry BUILT successfully but FAILED these engineering checks:"]
    for c in failed:
        lines.append(f"- {c.name}: value {c.value} {c.unit} vs allowed {c.threshold} "
                     f"({c.formula}). " + "; ".join(c.assumptions))
    lines.append("Revise the design so ALL checks pass while keeping the object "
                 "functional. Adjust the named dimension variables; do not just "
                 "delete features.")
    return "\n".join(lines)
