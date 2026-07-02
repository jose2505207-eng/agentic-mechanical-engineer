# Agents

"Agent" means two things in this repo. Keep them straight:

1. **Pipeline agents** (`backend/app/agents/`, `backend/app/llm/`) — the
   stations of the assembly line. Today: deterministic functions. Tomorrow:
   LLM-backed nodes. Same contracts either way.
2. **Development agents** (`.claude/agents/`) — role instructions for AI
   coding assistants working on this repo (architect, QA, CAD owner, …).

This page covers #1. For #2, read the files in `.claude/agents/` — each is
self-describing.

## Pipeline agent contracts

| Agent | Input → Output | Today | Upgrade path |
|---|---|---|---|
| Requirements | `str` → `Requirements` | **LLM-wired:** `llm/agents.py::extract_requirements` — schema-validated, deterministic fallback (`agents/requirements.py`) | richer prompts, multi-turn clarification |
| Architecture | `Requirements` → `ArchitectureSpec` | **LLM-wired:** `llm/agents.py::propose_architecture` — proposal must pass `llm/gates.py` physics feasibility gates or falls back to `agents/architecture.py` | wider template/material space |
| CAD params | `Requirements, ArchitectureSpec` → `CADParams` | direct mapping (`agents/cad_params.py`) | LLM selects template + parameters within schema bounds |
| CAD | `CADParams` → STL/STEP + volume | CadQuery template — **stays engineer-authored forever** | more templates, not freehand AI geometry |
| Checks | `SimulationInput` → `SimulationResults` | analytical formulas — **stays deterministic** | add PyBullet, then FEA; formulas remain as sanity anchor |
| Risk | reqs+arch+sim → `RiskReport` | threshold rules | LLM adds narrative; rules keep severity authority |
| BOM | arch+cad → `BOM` | curated table + gated Nexar enrichment (`bom/sourcing.py`, needs `ALLOW_EXTERNAL_PART_SEARCH=true` **and** NEXAR credentials; anything less keeps curated prices and says so in the disclaimer) | supplier alternatives, stock checks |
| Report | full state → Markdown | template renderer | LLM prose sections around machine-generated tables |

## The replacement rule

An AI implementation may replace a deterministic one **only if**:

1. It produces the exact same schema (validated, not trusted).
2. It falls back to the deterministic version on any failure — see
   `llm/agents.py` for the canonical pattern.
3. The golden-path tests still pass with the provider mocked *and* with
   `MODEL_PROVIDER=deterministic`.

Note the two "stays" rows above: geometry generation and physics checks are
deliberately *not* on the AI upgrade path. AI chooses parameters; verified
code computes consequences.

## LLM provider abstraction

`llm/provider.py::complete_json(system, user, schema)` is the only LLM call
site pattern allowed. Provider = `MODEL_PROVIDER` env var (anthropic /
openai / openrouter / ollama / vllm / local / deterministic). Adding a
provider = adding a base URL or one branch in that file. Nothing else in the
app knows which model is running.
