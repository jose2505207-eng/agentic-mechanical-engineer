"""Shared fixtures. The pipeline runs once per session into a tmp dir; all
golden-path tests assert against that single run (fast, deterministic).

Tests are ALWAYS offline: the developer's local .env may select a live LLM
provider or open the sourcing gate, so we override both before any settings
object is built. Individual tests re-set these via monkeypatch as needed.
"""

import os

import pytest

os.environ["MODEL_PROVIDER"] = "deterministic"
os.environ["ALLOW_EXTERNAL_PART_SEARCH"] = "false"

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.services.pipeline import run_pipeline  # noqa: E402

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
