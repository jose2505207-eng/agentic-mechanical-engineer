"""Generative CAD: sandbox safety, real execution, retry loop, pipeline mode.

The sandbox tests execute REAL CadQuery in the isolated subprocess (no
network, no LLM). The generative-flow tests mock the model with known
scripts so the loop logic is tested deterministically and offline.
"""

import pytest

from app.cad import generative
from app.cad.sandbox import CADScriptError, run_script, validate_script
from app.config import get_settings
from app.services.pipeline import run_pipeline, select_mode

GOOD_SCRIPT = """
import cadquery as cq
length, width, height, wall = 80.0, 40.0, 30.0, 2.4
result = (cq.Workplane("XY").box(length, width, height)
          .faces(">Z").shell(-wall))
"""

BROKEN_SCRIPT = "import cadquery as cq\nresult = cq.Workplane('XY').box(0, 0, 0)\n"


# ---- sandbox: static safety validation ----

@pytest.mark.parametrize("bad,why", [
    ("import os\nresult = None", "os import"),
    ("from subprocess import run\nresult = None", "subprocess import"),
    ("data = open('/etc/passwd').read()\nresult = None", "open()"),
    ("x = eval('1+1')\nresult = None", "eval"),
    ("x = ().__class__.__bases__\nresult = None", "dunder escape"),
    ("import cadquery as cq\nresult = getattr(cq, 'W')", "getattr"),
])
def test_validator_rejects_dangerous_code(bad, why):
    assert validate_script(bad), f"validator must reject: {why}"


def test_validator_accepts_good_script():
    assert validate_script(GOOD_SCRIPT) == []


# ---- sandbox: real isolated execution ----

def test_run_script_builds_real_geometry(tmp_path):
    res = run_script(GOOD_SCRIPT, tmp_path / "out.stl", tmp_path / "out.step")
    assert res.volume_mm3 > 0
    assert res.is_valid_solid
    assert abs(res.bbox_mm[0] - 80.0) < 1.0
    assert (tmp_path / "out.stl").stat().st_size > 84


def test_run_script_degenerate_geometry_raises(tmp_path):
    with pytest.raises(CADScriptError):
        run_script(BROKEN_SCRIPT, tmp_path / "out.stl", None)


def test_run_script_with_relative_output_path(tmp_path, monkeypatch):
    """Regression: subprocess cwd is a tempdir; a relative output path must
    still land in the caller's working directory, not vanish with the tempdir."""
    monkeypatch.chdir(tmp_path)
    from pathlib import Path
    res = run_script(GOOD_SCRIPT, Path("rel/out.stl"), None)
    assert (tmp_path / "rel" / "out.stl").exists()
    assert res.volume_mm3 > 0


# ---- generative loop with mocked model ----

def test_generate_model_retries_then_succeeds(tmp_path, monkeypatch):
    responses = iter(["import os\nresult = None",   # rejected by validator
                      f"```python\n{GOOD_SCRIPT}\n```"])  # then good, fenced
    monkeypatch.setattr(generative, "complete_text", lambda *a, **k: next(responses))
    out = generative.generate_model("a hollow box", (200, 200, 200),
                                    tmp_path / "m.stl", None)
    assert out.attempts == 2
    assert out.metrics.volume_mm3 > 0


def test_generate_model_exhausts_attempts(tmp_path, monkeypatch):
    monkeypatch.setattr(generative, "complete_text",
                        lambda *a, **k: "import os\nresult = None")
    with pytest.raises(CADScriptError):
        generative.generate_model("anything", (100, 100, 100), tmp_path / "m.stl", None)


# ---- mode selection & pipeline dispatch ----

def test_mode_is_template_when_deterministic(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "deterministic")
    get_settings.cache_clear()
    assert select_mode("create a drone") == "template"
    get_settings.cache_clear()


def test_mode_selection_with_provider(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    get_settings.cache_clear()
    assert select_mode("create a drone that carries 2kg") == "generative"
    assert select_mode("design a phone stand for a desk") == "generative"
    assert select_mode("Design a mobile robot that can inspect equipment") == "template"
    get_settings.cache_clear()


def test_generative_pipeline_end_to_end(tmp_path, monkeypatch):
    """Full generic-mode run with mocked code generation: artifacts, metrics,
    risks, report, manifest — all real except the model call."""
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    get_settings.cache_clear()
    monkeypatch.setattr(generative, "complete_text", lambda *a, **k: GOOD_SCRIPT)

    state = run_pipeline("design a phone stand for a desk", tmp_path, design_id="t-gen")
    assert state.mode == "generative"
    assert state.geometry is not None and state.geometry.volume_mm3 > 0
    for name in ("requirements.json", "cad_script.py", "model.stl",
                 "geometry_metrics.json", "risk_report.json",
                 "engineering_report.md", "artifact_manifest.json"):
        assert (tmp_path / name).exists(), f"missing {name}"
    report = (tmp_path / "engineering_report.md").read_text()
    assert "AI-generated concept geometry" in report
    assert "Limitations" in report
    assert any("GENERATIVE" in n for n in state.manifest.notes)
    get_settings.cache_clear()


def test_generative_failure_falls_back_to_template(tmp_path, monkeypatch):
    """If the model can't produce working CAD, the pipeline must still finish
    with the template vertical rather than dying."""
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    get_settings.cache_clear()
    monkeypatch.setattr(generative, "complete_text",
                        lambda *a, **k: "import os\nresult = None")
    # requirements/architecture LLM calls also fail fast -> deterministic
    from app.llm import provider as llm_provider

    def no_llm(*a, **k):
        raise llm_provider.LLMUnavailable("mocked outage")
    monkeypatch.setattr(llm_provider, "_chat_once", no_llm)

    state = run_pipeline("create a drone that carries 2kg", tmp_path, design_id="t-fb")
    assert state.mode == "template"
    assert (tmp_path / "robot_chassis.stl").exists()
    assert any(i.id == "R-001" for i in state.risk_report.items), \
        "scope risk must still fire on the fallback"
    get_settings.cache_clear()
