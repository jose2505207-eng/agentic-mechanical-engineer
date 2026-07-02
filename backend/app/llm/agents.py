"""LLM-backed pipeline agents with deterministic fallback.

Each function tries the configured model, validates against the same schema
the deterministic agent produces, and silently-but-loggedly falls back if
anything goes wrong. The golden path can therefore never be broken by a
model outage or a hallucinated field.
"""

import logging

from app.agents.requirements import extract_requirements as det_extract_requirements
from app.llm.provider import LLMUnavailable, complete_json
from app.schemas import Requirements

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
        logger.info("requirements extracted via LLM provider")
        return req
    except LLMUnavailable as exc:
        logger.info("LLM unavailable (%s); using deterministic extractor", exc)
        return det_extract_requirements(prompt)
