#!/usr/bin/env python3
"""Environment sanity check: reports which env vars are set (never their
values), which features that unlocks, and whether the CAD kernel is present.

Usage: make check-env
"""

import importlib.util
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (var, feature unlocked)
OPTIONAL_VARS = [
    ("MODEL_PROVIDER", "AI agent layer backend selection"),
    ("MODEL_NAME", "specific model choice"),
    ("ANTHROPIC_API_KEY", "Anthropic/Fable LLM agents"),
    ("OPENAI_API_KEY", "OpenAI LLM agents"),
    ("OPENROUTER_API_KEY", "OpenRouter LLM agents"),
    ("DATABASE_URL", "Postgres persistence"),
    ("SUPABASE_URL", "Supabase storage/auth"),
    ("STORAGE_DIR", "custom artifact directory"),
    ("NEXAR_CLIENT_ID", "live BOM part sourcing"),
    ("SENTRY_DSN", "error tracking"),
]


def main() -> int:
    print("Agentic Mechanical Engineer — environment check\n")
    print("The deterministic MVP needs NO env vars. Everything below is optional.\n")

    env_file = REPO_ROOT / ".env"
    print(f".env file: {'present' if env_file.exists() else 'absent (fine for MVP)'}")

    cad_ok = importlib.util.find_spec("cadquery") is not None
    print(f"CadQuery:  {'installed — real CAD geometry' if cad_ok else 'MISSING — demo will use labeled placeholder STL (pip install -e backend[cad])'}")

    print("\nOptional variables:")
    for var, feature in OPTIONAL_VARS:
        status = "SET" if os.environ.get(var) else "unset"
        print(f"  {var:26s} {status:6s} -> {feature}")

    provider = os.environ.get("MODEL_PROVIDER", "deterministic")
    print(f"\nActive model provider: {provider}")
    if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: MODEL_PROVIDER=anthropic but ANTHROPIC_API_KEY is unset — "
              "pipeline will fall back to deterministic agents.")
    print("\nSee `env-space` at the repo root for full documentation of every variable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
