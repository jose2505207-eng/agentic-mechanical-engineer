# BOM System

## Today: curated, honest, offline

`backend/app/bom/generator.py` holds a curated parts list for the mobile
inspection robot class — real component categories with realistic
budget-level prices (SBC $80, 2D lidar $99, thermal camera $199, LiFePO4
512 Wh pack $189, …). Dynamic bits:

- chassis plate line item takes its dimensions from `CADParams`
- motor/wheel quantities and specs from `ArchitectureSpec`
- sensor line items filtered by `Requirements.sensors_required`

Outputs: `bom.json` (typed `BOM` model) and `bom.csv` (spreadsheet-friendly,
with a TOTAL row). Every BOM carries `pricing_disclaimer` — these are
planning estimates, not quotes. Supplier column says `TBD (curated
estimate)` because pretending we have supplier relationships would be lying.

## Future: live sourcing enrichment

The plan (see roadmap):

1. `ALLOW_EXTERNAL_PART_SEARCH=true` gate — the app never calls external
   APIs unless explicitly enabled (cost + privacy control).
2. Nexar/Octopart API (`NEXAR_CLIENT_ID`/`SECRET` in env-space) to resolve
   each curated category to live parts: real MPNs, real prices,
   real stock, 2–3 alternatives per line.
3. Cache results locally; the curated table remains the offline fallback —
   same pattern as the LLM layer: **enrichment optional, spine unconditional.**

## Adding parts to the curated table

Edit the `rows` list in `generate_bom()`. Keep the discipline:

- part_number: `CAT-NAME-NNN` convention, stable once published
- price: something you could actually buy it for today, not aspirational
- notes: why it's there / mounting context, if not obvious
- if the part is conditional, filter on requirements like the sensor items do

Then run `make test` — BOM row-count and budget-compliance tests will tell
you if you broke the demo design's budget.
