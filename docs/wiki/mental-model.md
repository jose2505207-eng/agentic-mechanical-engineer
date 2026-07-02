# Mental Model

## The one-liner

**This system is an assembly line that transforms vague intent into
engineering artifacts.** Each station on the line takes a typed object,
does one job, and hands a typed object to the next station.

```
"design me a robot…"                                  (vague intent)
   │
   ▼  Requirements station     — what does the customer actually need?
Requirements (JSON)
   │
   ▼  Architecture station     — what machine satisfies those needs?
ArchitectureSpec (JSON)
   │
   ▼  CAD-params station       — what exact dimensions realize that machine?
CADParams (JSON, bound-checked)
   │
   ▼  CAD station              — build the geometry
robot_chassis.stl / .step
   │
   ▼  Checks station           — does the physics work out?
SimulationResults (JSON, formulas included)
   │
   ▼  Risk station             — what could go wrong?
RiskReport (JSON)
   │
   ▼  BOM station              — what parts, what cost?
bom.csv
   │
   ▼  Report station           — explain it all to a human
engineering_report.md
```

## Three ideas that make it work

**1. Contracts, not vibes.** Every arrow above is a Pydantic schema
(`backend/app/schemas/models.py`). A station can be a dumb rule, a curated
table, or a frontier LLM — the rest of the line doesn't know or care, because
the contract is enforced at the boundary. This is why the deterministic MVP
and the future AI version are the *same codebase*.

**2. The LLM never touches geometry.** When AI stations come online, they
produce *parameters* (validated, bounded), and engineer-written templates
produce geometry. An LLM can propose a 900 mm chassis; the schema will reject
it before the CAD kernel ever runs. Constrain the model where it's weak, use
it where it's strong.

**3. Honesty is load-bearing.** Every calculation carries its formula and
assumptions in the output itself. Every report states its limitations. A
wrong number you can audit is recoverable; a confident black box is not.

## What this is NOT

- Not FEA. `simulation_results.json` is whiteboard physics, clearly labeled.
- Not a text-to-CAD toy. Geometry is the *middle* of the pipeline, not the
  product. The product is the engineering decisions around it.
- Not autonomous engineering. A human engineer reviews everything before
  anything gets built.

## The upgrade path (why the code is shaped like this)

`EngineeringReportState` is the shared state object that flows through
`run_pipeline()`. It is deliberately shaped like a LangGraph state: when we
swap the sequential function for a graph (Sprint 8+), the nodes are the same
stations, the state is the same object, and the tests still pass. Determinism
isn't the destination — it's the safety net we keep forever.
