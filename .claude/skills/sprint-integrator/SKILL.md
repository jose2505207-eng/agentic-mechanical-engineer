---
name: sprint-integrator
description: Merge outputs from specialized agents, resolve conflicts, update tests, and update the wiki.
---

# Sprint Integrator

## When to use
End of every sprint, or after parallel workstreams touch overlapping files.

## Integration protocol (in order, no skipping)
1. Reconcile contracts first: if two workstreams changed schemas/models.py
   differently, resolve THERE before touching call sites — the schema is
   the constitution.
2. `make test` — fix failures at the source, don't paper over.
3. `make demo` — golden path must produce all 9 artifacts; read the
   summary line and skim the report for nonsense.
4. `make wiki` and hand-update affected wiki pages (see wiki-updater skill).
5. Append a sprint entry to docs/sprint_logs/ (one file per sprint):
   what shipped, what's still placeholder, decisions made, follow-ups.
6. Update README if any command or capability changed.
7. Produce the commit-ready summary: files changed, what works now, what is
   still placeholder (labeled), what the next sprint should pick up.

## Conflict rules
- Prefer the version that keeps stations decoupled and the golden path green.
- A feature that breaks the demo does not merge, however shiny.
- When in doubt, the principal-architect agent arbitrates; record the call
  in decisions.md.
