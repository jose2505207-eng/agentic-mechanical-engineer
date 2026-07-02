---
name: cad-reviewer
description: Review CAD code for parameter sanity, export reliability, and mechanical plausibility.
---

# CAD Reviewer

## Review checklist for any change under backend/app/cad/ or to CADParams

**Parameter sanity**
- Every dimension has schema bounds (ge/le) matching what the template can
  actually build. No unbounded floats.
- Derived geometry stays valid across the FULL bound range: corner radius <
  half of min(length,width)? bays fit on the plate? holes don't intersect
  fillets? Run a corner-case sweep (all-min, all-max, mixed).

**Export reliability**
- STL export succeeds and is watertight; triangle count > 0; file size sane
  vs MAX_CAD_COMPLEXITY.
- STEP export failure is tolerated (best-effort) but logged in the
  CADResult note, never silently dropped.
- Fallback path (no CadQuery) still produces a labeled placeholder.

**Mechanical plausibility**
- Wheel placeholders at (±wheelbase/2, ±track/2), centered on the track
  line — bounding width = track + wheel_width (the envelope check depends
  on this convention).
- Volume returned = structure only (no wheels); mass downstream depends on it.
- Bays sized for the components the BOM actually lists; mast won't obviously
  tip the CoG past the stability check.

**Verdict format:** APPROVE / REQUEST CHANGES with the specific parameter
combination that breaks, if any.
