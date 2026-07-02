#!/usr/bin/env python3
"""Automatic wiki updater.

Regenerates the AUTO-GENERATED sections of:
  docs/wiki/code-map.md   (from the repo tree + module docstrings)
  docs/wiki/schemas.md    (introspected from Pydantic models)
  docs/wiki/api.md        (introspected from FastAPI routes)

Rules:
- Content between <!-- AUTO-GENERATED:START --> and <!-- AUTO-GENERATED:END -->
  is machine-owned and replaced on every run.
- Everything outside the markers is human-owned and NEVER touched.
- If a page doesn't exist, it is created with a human-editable preamble.
- Every run appends a timestamped entry to docs/sprint_logs/wiki_updates.md.

Usage: make wiki    |    check mode (CI): update_wiki.py --check
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from repo_map import build_map  # noqa: E402

WIKI = REPO_ROOT / "docs" / "wiki"
START = "<!-- AUTO-GENERATED:START -->"
END = "<!-- AUTO-GENERATED:END -->"


def splice(path: Path, generated: str, preamble: str) -> bool:
    """Insert/replace the auto-generated block. Returns True if file changed."""
    block = f"{START}\n{generated.rstrip()}\n{END}\n"
    if path.exists():
        text = path.read_text()
        if START in text and END in text:
            before = text[: text.index(START)]
            after = text[text.index(END) + len(END):].lstrip("\n")
            new = before + block + ("\n" + after if after else "")
        else:
            new = text.rstrip() + "\n\n" + block
    else:
        new = preamble.rstrip() + "\n\n" + block
    changed = not path.exists() or path.read_text() != new
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new)
    return changed


def gen_code_map() -> str:
    lines = ["## File map (auto-generated — do not hand-edit inside markers)\n",
             "| File | What it does |", "|---|---|"]
    for rel, desc in build_map():
        lines.append(f"| `{rel}` | {desc} |")
    return "\n".join(lines)


def gen_schemas() -> str:
    from pydantic import BaseModel

    import app.schemas as schemas_pkg

    lines = ["## Schema reference (auto-generated from `app/schemas/models.py`)\n"]
    for name in schemas_pkg.__all__:
        obj = getattr(schemas_pkg, name)
        if not (isinstance(obj, type) and issubclass(obj, BaseModel)):
            continue
        doc = (obj.__doc__ or "").strip().splitlines()
        lines.append(f"### {name}\n")
        if doc:
            lines.append(doc[0] + "\n")
        lines.append("| Field | Type | Notes |")
        lines.append("|---|---|---|")
        for fname, finfo in obj.model_fields.items():
            ftype = str(finfo.annotation).replace("typing.", "")
            note = finfo.description or ""
            lines.append(f"| `{fname}` | `{ftype}` | {note} |")
        lines.append("")
    return "\n".join(lines)


def gen_api() -> str:
    from fastapi.routing import APIRoute

    from app.main import app

    lines = ["## Endpoint reference (auto-generated from FastAPI routes)\n",
             "| Method | Path | Summary |", "|---|---|---|"]
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ",".join(sorted(route.methods - {"HEAD", "OPTIONS"}))
            doc = (route.endpoint.__doc__ or "").strip().splitlines()
            summary = doc[0] if doc else route.name
            lines.append(f"| {methods} | `{route.path}` | {summary} |")
    return "\n".join(lines)


def main() -> int:
    check_mode = "--check" in sys.argv
    targets = [
        (WIKI / "code-map.md", gen_code_map,
         "# Code Map\n\nWhat lives where, and why. Human notes go above/below "
         "the auto-generated block."),
        (WIKI / "schemas.md", gen_schemas,
         "# Schemas\n\nThe typed contracts every pipeline stage speaks. "
         "See docs/wiki/mental-model.md for how data flows through them."),
        (WIKI / "api.md", gen_api,
         "# API\n\nBackend endpoints. Run `make api` and open "
         "http://localhost:8000/docs for the interactive version."),
    ]

    # Pre-create missing pages so the code map sees the final file tree even
    # on the very first run (keeps the script idempotent).
    if not check_mode:
        for path, _gen, preamble in targets:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(preamble.rstrip() + f"\n\n{START}\n{END}\n")

    changed = [str(p.relative_to(REPO_ROOT)) for p, gen, pre in targets if splice(p, gen(), pre)]

    if check_mode:
        if changed:
            print(f"STALE wiki pages (run `make wiki`): {', '.join(changed)}")
            return 1
        print("Wiki is up to date.")
        return 0

    log = REPO_ROOT / "docs" / "sprint_logs" / "wiki_updates.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"- {stamp} — regenerated: {', '.join(changed) if changed else 'no changes needed'}\n"
    if not log.exists():
        log.write_text("# Wiki Update Log\n\n")
    log.write_text(log.read_text() + entry)

    print(f"Wiki updated. Changed: {', '.join(changed) if changed else 'nothing (already current)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
