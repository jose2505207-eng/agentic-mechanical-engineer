"""Honesty rules for out-of-scope prompts and budget overruns.

A 'drone' prompt must NOT silently become a ground robot: the requirements
must carry a platform_scope assumption, the risk report a CRITICAL scope
item, and the manifest a loud note. A BOM over budget must raise a HIGH risk.
"""

from app.agents.requirements import extract_requirements
from app.services.pipeline import run_pipeline

DRONE_PROMPT = ("create a drone that can carry a 2kg payload and is as fast "
                "as possible with a 300$ budget")


def test_extractor_flags_out_of_scope_platform():
    req = extract_requirements(DRONE_PROMPT)
    assert any(a.field == "platform_scope" for a in req.assumptions)
    assert any("drone" in u.lower() for u in req.unknowns)
    assert req.payload_kg == 2.0
    assert req.max_cost_usd == 300.0  # budget parsed from prompt


def test_in_scope_prompt_not_flagged():
    req = extract_requirements(
        "Design a mobile robot that can inspect manufacturing equipment for 8 hours.")
    assert not any(a.field == "platform_scope" for a in req.assumptions)


def test_pipeline_surfaces_scope_and_budget_risks(tmp_path):
    state = run_pipeline(DRONE_PROMPT, tmp_path, design_id="test-drone")
    risk_ids = {i.id: i for i in state.risk_report.items}

    assert "R-001" in risk_ids, "out-of-scope platform must be a risk item"
    assert risk_ids["R-001"].severity.value == "critical"

    if state.bom.total_cost_usd > state.requirements.max_cost_usd:
        assert "R-103" in risk_ids, "over-budget BOM must be a risk item"

    notes = " | ".join(state.manifest.notes)
    assert "CRITICAL" in notes, "manifest notes must surface the scope problem"
    assert "deterministic" in notes or "LLM" in notes, "notes must state provenance"


def test_manifest_notes_report_failed_checks(tmp_path):
    state = run_pipeline(DRONE_PROMPT, tmp_path, design_id="test-drone2")
    failed = [c for c in state.simulation.checks if not c.passed]
    joined = " ".join(state.manifest.notes)
    if failed:
        assert "FAILED" in joined
    else:
        assert "FAILED" not in joined
