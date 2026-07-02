---
name: wiki-updater
description: Update the Karpathy-style wiki whenever architecture, schemas, APIs, agents, or workflows change.
---

# Wiki Updater

The wiki must explain the project like a brilliant engineer teaching a
future contributor: mental model first, concrete examples, real commands,
zero corporate fog. Reader: smart stranger, 2 AM, production question.

## Procedure
1. `make wiki` — regenerates code-map.md, schemas.md, api.md and appends to
   docs/sprint_logs/wiki_updates.md.
2. Then update the HAND-WRITTEN pages affected by the change:
   - formulas/thresholds changed -> simulation-system.md
   - CAD template added/changed -> cad-system.md
   - stage added/reordered -> mental-model.md, architecture.md, golden-path.md
   - decision made/reversed -> decisions.md (append ADR; never delete old ones)
   - commands changed -> setup.md + README.md
   - scope changed -> roadmap.md
3. `.venv/bin/python scripts/update_wiki.py --check` must pass before done.

## Style checklist per page
- Opens with what/why in plain language, not a definition.
- Shows the data flow or a runnable command within the first screen.
- Every claim checkable against code; file paths are real.
- Limitations stated plainly. If something is a placeholder, the wiki says so.
