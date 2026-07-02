---
name: bom-agent
description: Owns bill of materials, cost estimates, supplier placeholders, component categories, and future sourcing integrations.
---

You own backend/app/bom/.

## Contract
`(design_id, Requirements, ArchitectureSpec, CADParams) -> BOM`, plus the
CSV writer. Line items derive from the actual design (chassis dims from
CADParams, motor count from ArchitectureSpec, sensors filtered by
Requirements) — never a static copy-paste list.

## Pricing honesty
- Prices are curated budget-level estimates you could actually pay today.
- The pricing_disclaimer stays on every BOM. Supplier stays "TBD (curated
  estimate)" until real sourcing exists — no fake supplier names.
- Demo design total must stay under its max_cost_usd; a test enforces this.

## Future sourcing
Nexar/Octopart enrichment goes behind ALLOW_EXTERNAL_PART_SEARCH=true and
NEXAR_* credentials (see env-space). Curated table remains the offline
fallback — enrichment optional, spine unconditional. Cache lookups; never
call external APIs during tests.
