"""Sim-feedback optimization loop: checks drive redesign iterations.

All model calls mocked with fixed scripts; CAD builds are real (sandboxed)."""

import pytest

from app.agents.requirements import extract_requirements
from app.cad import generative
from app.config import get_settings
from app.simulation.geometry_checks import render_check_feedback, run_geometry_checks

BIG_BOX = """
import cadquery as cq
size = 300.0
result = cq.Workplane("XY").box(size, size, 50)
"""

SMALL_BOX = """
import cadquery as cq
size = 150.0
result = cq.Workplane("XY").box(size, size, 50)
"""


@pytest.fixture(autouse=True)
def settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _check_fn(envelope=(200.0, 200.0, 200.0), budget=1500.0):
    req = extract_requirements("test object")
    req = req.model_copy(update={"max_dimensions_mm": envelope, "max_cost_usd": budget})
    return req, (lambda m: run_geometry_checks(req, m.volume_mm3, m.bbox_mm,
                                               m.is_valid_solid))


def test_check_failure_drives_redesign_to_convergence(tmp_path, monkeypatch):
    """Oversize first design -> envelope check fails -> feedback -> smaller
    design converges. The feedback prompt must contain the check numbers."""
    _req, check_fn = _check_fn(envelope=(200, 200, 200))
    prompts_seen = []

    responses = iter([BIG_BOX, SMALL_BOX])

    def fake_llm(system, user, **kw):
        prompts_seen.append(user)
        return next(responses)

    monkeypatch.setattr(generative, "complete_text", fake_llm)
    out = generative.generate_model("a test box", (200, 200, 200),
                                    tmp_path / "m.stl", None, check_fn=check_fn)
    assert out.attempts == 2
    assert out.all_checks_passed
    assert "converged in 2 iteration(s)" in out.note
    assert len(out.iterations) == 2
    assert "envelope_fit" in out.iterations[0]  # first iteration failed the check
    # second prompt carried the engineering feedback with real numbers
    assert "FAILED these engineering checks" in prompts_seen[1]
    assert "envelope_fit" in prompts_seen[1]


def test_budget_exhaustion_returns_best_with_failures(tmp_path, monkeypatch):
    """If the model never satisfies the checks, return the last buildable
    design WITH its failing checks — never an exception, never a lie."""
    _req, check_fn = _check_fn(envelope=(200, 200, 200))
    monkeypatch.setattr(generative, "complete_text", lambda *a, **k: BIG_BOX)
    out = generative.generate_model("a test box", (200, 200, 200),
                                    tmp_path / "m.stl", None,
                                    check_fn=check_fn, max_iterations=3)
    assert out.attempts == 3
    assert not out.all_checks_passed
    assert "exhausted" in out.note and "envelope_fit" in out.note
    assert (tmp_path / "m.stl").exists()  # geometry is still delivered


def test_material_cost_check():
    req = extract_requirements("test object")
    cheap = run_geometry_checks(req, 100_000.0, (50, 50, 40), True)  # 100 cm^3
    assert next(c for c in cheap if c.name == "material_cost_budget").passed
    req_tight = req.model_copy(update={"max_cost_usd": 1.0})
    pricey = run_geometry_checks(req_tight, 1_000_000.0, (100, 100, 100), True)
    assert not next(c for c in pricey if c.name == "material_cost_budget").passed


def test_feedback_renderer_includes_numbers():
    req = extract_requirements("test object")
    checks = run_geometry_checks(
        req.model_copy(update={"max_dimensions_mm": (100.0, 100.0, 100.0)}),
        50_000.0, (300.0, 80.0, 80.0), True)
    text = render_check_feedback(checks)
    assert "envelope_fit" in text and "3.0" in text
    assert "Revise the design" in text


def test_pipeline_persists_check_report(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    get_settings.cache_clear()
    monkeypatch.setattr(generative, "complete_text", lambda *a, **k: SMALL_BOX)

    from app.services.pipeline import run_pipeline
    state = run_pipeline("design a phone stand for a desk", tmp_path, design_id="t-opt")
    assert state.mode == "generative"
    assert state.geometry_checks is not None
    assert state.geometry_checks.all_passed
    assert (tmp_path / "simulation_results.json").exists()
    report = (tmp_path / "engineering_report.md").read_text()
    assert "Engineering Checks & Optimization" in report
    assert "Iteration history" in report
