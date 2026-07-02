#!/usr/bin/env python3
"""Print a map of the repository: tree of tracked-worthy files with the first
docstring line of each Python module. Used by update_wiki.py and handy on
its own: .venv/bin/python scripts/repo_map.py
"""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".venv", "__pycache__", ".git", ".pytest_cache", ".ruff_cache",
             "node_modules", "outputs", ".egg-info", "sprint_logs"}


def first_docstring_line(path: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(path.read_text()))
        return doc.strip().splitlines()[0] if doc else ""
    except (SyntaxError, UnicodeDecodeError):
        return ""


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in p.parts):
            continue
        if p.name == "package-lock.json":
            continue
        if p.is_file() and p.suffix in {
            ".py", ".toml", ".md", ".yml", ".yaml", ".jsx", ".mjs", ".json", ".css"
        } or p.name in ("Makefile", "env-space", ".env.example"):
            yield p


def build_map() -> list[tuple[str, str]]:
    """Return [(relative_path, one-line description)]."""
    entries = []
    for p in iter_files(REPO_ROOT):
        rel = p.relative_to(REPO_ROOT)
        desc = first_docstring_line(p) if p.suffix == ".py" else ""
        entries.append((str(rel), desc))
    return entries


def main() -> int:
    for rel, desc in build_map():
        print(f"{rel:60s} {desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
