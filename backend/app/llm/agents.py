"""LLM-backed pipeline agents with deterministic fallback.

Each function tries the configured model, validates against the same schema
the deterministic agent produces, and silently-but-loggedly falls back if
anything goes wrong. The golden path can therefore never be broken by a
model outage or a hallucinated field.
"""

import logging

from app.agents.architecture import generate_architecture as det_generate_architecture
from app.agents.requirements import extract_requirements as det_extract_requirements
from app.config import get_settings
from app.llm.gates import check_feasibility
from app.llm.provider import LLMUnavailable, complete_json
from app.schemas import ArchitectureSpec, EngineeringAssumption, Requirements

logger = logging.getLogger(__name__)

_REQUIREMENTS_SYSTEM = (
    "You are a senior mechanical engineer converting a customer request into "
    "structured requirements. Fill gaps with conservative assumptions and record "
    "every assumption in the `assumptions` list with a rationale. List genuinely "
    "open questions in `unknowns`. Use SI units per the schema field names."
)


def extract_requirements(prompt: str) -> Requirements:
    """LLM extraction if configured; deterministic fallback otherwise."""
    try:
        req = complete_json(
            _REQUIREMENTS_SYSTEM,
            f"Customer request: {prompt}",
            Requirements,
        )
        # The model must echo the prompt faithfully; enforce it.
        req.prompt = prompt
        settings = get_settings()
        req.assumptions.append(EngineeringAssumption(
            field="provenance",
            assumed_value=f"Requirements extracted by LLM "
                          f"({settings.model_provider}:{settings.model_name})",
            rationale="Model output validated against the Requirements schema; "
                      "deterministic extractor remains the fallback.",
            confidence="high"))
        logger.info("requirements extracted via LLM provider")
        return req
    except LLMUnavailable as exc:
        logger.info("LLM unavailable (%s); using deterministic extractor", exc)
        return det_extract_requirements(prompt)


_ARCHITECTURE_SYSTEM = (
    "You are a senior mechatronics engineer proposing a system architecture for "
    "a mobile robot. Choose drivetrain, wheel count/diameter, chassis topology "
    "and material (with real density kg/m^3 and yield MPa), motor class with "
    "realistic torque/power/mass figures, and a battery pack (real chemistry, "
    "plausible Wh and pack mass). Explain each tradeoff in `rationale`. Prefer "
    "commercially available component classes; do not invent impossible parts. "
    "The proposal will be checked against physics feasibility gates and rejected "
    "if implausible."
)


def propose_architecture(req: Requirements) -> ArchitectureSpec:
    """LLM architecture proposal, gated by the deterministic rules layer.

    Order of defense: schema validation (types/bounds) -> feasibility gates
    (physics plausibility) -> downstream simulation checks (quantitative
    verification). Any failure falls back to the deterministic generator.
    """
    try:
        arch = complete_json(
            _ARCHITECTURE_SYSTEM,
            "Requirements JSON:\n" + req.model_dump_json(indent=2),
            ArchitectureSpec,
        )
    except LLMUnavailable as exc:
        logger.info("LLM unavailable (%s); using deterministic architecture", exc)
        return det_generate_architecture(req)

    violations = check_feasibility(req, arch)
    if violations:
        logger.warning(
            "LLM architecture rejected by feasibility gates (%s); "
            "using deterministic architecture", "; ".join(violations))
        return det_generate_architecture(req)

    arch.rationale.append("Proposed by LLM; passed deterministic feasibility gates.")
    logger.info("architecture proposed via LLM provider (gates passed)")
    return arch
