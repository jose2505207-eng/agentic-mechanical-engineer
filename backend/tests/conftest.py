"""Shared fixtures. The pipeline runs once per session into a tmp dir; all
golden-path tests assert against that single run (fast, deterministic)."""

import pytest

from app.services.pipeline import run_pipeline

DEMO_PROMPT = "Design a mobile robot that can inspect manufacturing equipment for 8 hours."


@pytest.fixture(scope="session")
def demo_output_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("outputs")
    run_pipeline(DEMO_PROMPT, out, design_id="test-demo")
    return out


@pytest.fixture(scope="session")
def demo_state(tmp_path_factory):
    out = tmp_path_factory.mktemp("state-run")
    return run_pipeline(DEMO_PROMPT, out, design_id="test-state")
