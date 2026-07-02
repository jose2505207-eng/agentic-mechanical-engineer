---
name: repo-cartographer
description: Map the repository, explain what each important file does, and keep docs/wiki/code-map.md current.
---

# Repo Cartographer

## When to use
After adding/moving/deleting files, or when someone asks "where does X live".

## Procedure
1. Run `.venv/bin/python scripts/repo_map.py` — tree + first docstring line
   per Python module.
2. Run `make wiki` — regenerates the AUTO-GENERATED block of
   docs/wiki/code-map.md from that map.
3. If a module has no docstring or a useless one, FIX THE DOCSTRING (first
   line = one honest sentence about the module's job). The map is generated
   from docstrings; improving the map means improving the source.
4. Add hand-written orientation notes OUTSIDE the markers in code-map.md for
   anything the generated table can't express (e.g. "start reading at
   services/pipeline.py").
5. Verify idempotence: `.venv/bin/python scripts/update_wiki.py --check`
   must pass afterward.

## Rules
- Never hand-edit between AUTO-GENERATED markers.
- outputs/, .venv/, caches, and sprint_logs/ stay excluded (see SKIP_DIRS
  in scripts/repo_map.py).
