# Decisions (ADR summaries)

Short-form architecture decision records. Newest last. If you reverse one,
don't delete it — add a superseding entry.

## ADR-001: Deterministic spine before AI layer
**Decision:** Build the entire pipeline as deterministic, tested Python
first; add LLM stations later behind identical contracts with mandatory
fallback.
**Why:** A demo that always works beats a smarter demo that sometimes works.
Deterministic code doubles as ground truth for evaluating AI replacements.
**Consequence:** Some "agents" are regexes and lookup tables today. That's
fine; they're honest about it.

## ADR-002: LLM never generates geometry
**Decision:** AI selects and parameterizes engineer-authored CadQuery
templates. Schema bounds reject bad parameters before the kernel runs.
**Why:** LLM freehand geometry is unreliable and unverifiable; parameter
spaces are boundable and testable. (Carried over from the hackathon report —
"the core reliability decision of the project.")

## ADR-003: Pydantic schemas as the module boundary
**Decision:** Every stage boundary is a Pydantic model in `app/schemas/`;
stations may not import each other, only `services/pipeline.py` composes.
**Why:** Replaceability (rule → LLM), testability, and the future LangGraph
migration all fall out of typed contracts for free.

## ADR-004: Local filesystem storage first
**Decision:** Artifacts go to `STORAGE_DIR` via one small `ArtifactStore`
class; no DB in the MVP.
**Why:** Zero setup for the demo. The store is the single swap point for
S3/Supabase later.

## ADR-005: Provider-agnostic LLM client, config-selected
**Decision:** One `complete_json()` entry point; provider from
`MODEL_PROVIDER` env. Anthropic native API + OpenAI-compatible endpoints
(openai/openrouter/ollama/vllm) cover every target incl. AMD/ROCm-hosted
vLLM.
**Why:** Requirement: switch Anthropic/OpenAI/OpenRouter/local without
rewriting the app. Also: model output is *validated*, never trusted.

## ADR-006: Checks re-derive rather than reuse sizing math
**Decision:** `simulation/checks.py` recomputes power/mass from CAD-derived
values instead of importing `architecture.py`'s estimates.
**Why:** A verification stage that shares code with the design stage
verifies nothing.

## ADR-007: Honesty as an output requirement
**Decision:** Every simulation output carries formulas + assumptions +
limitations; every report opens with the not-certified banner; placeholders
label themselves (even inside the STL header).
**Why:** This tool's value is trustworthy engineering judgment. Fake
precision would poison exactly that.

## ADR-009: Generative CAD — the model writes code, a sandbox runs it
**Decision:** Partially supersedes ADR-002. For arbitrary (non-robot-class)
objects, the LLM writes a parametric CadQuery *script*; we AST-validate it
(import whitelist, no dangerous builtins, no dunder access), execute it in
an isolated subprocess (`python -I`, timeout, temp cwd), measure the result
(volume, bbox, kernel validity), and feed failures back for up to 3
attempts. Template mode remains the fallback and the only path when no LLM
is configured. Fillet/chamfer/shell/loft/sweep are banned in generated code
— observed to be the dominant OCCT failure mode.
**Why:** "Anything as a 3D model" cannot come from a template library; code
generation is the only mechanism where the model's output is fully
inspectable, parametric (users can edit dimensions and re-run), and
gate-able. ADR-002's spirit survives: the model still never emits raw
geometry — it emits *reviewable source* that a validated toolchain turns
into geometry.
**Consequence:** We now execute model-written code. The sandbox treats model
output as untrusted (see security-agent checklist); the threat model is a
misbehaving model, not a hostile local user.

## ADR-008: Markdown reports before PDF, wiki before docs-site
**Decision:** Ship Markdown everywhere first.
**Why:** Diffable, testable, readable in the repo. PDF is a rendering
concern, deferred to V1.
