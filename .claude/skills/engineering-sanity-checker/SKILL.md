---
name: engineering-sanity-checker
description: Check formulas, assumptions, units, and engineering limitations. Never pretend placeholder calculations are real FEA.
---

# Engineering Sanity Checker

## When to use
Any change to backend/app/simulation/, architecture sizing constants, or
material properties.

## Procedure
1. **Units audit.** Trace every formula end to end: mm vs m conversions
   (the classic bug: mm³ -> m³ is 1e-9; mm -> m in stress terms), Wh vs J,
   deg vs rad at every trig call. Recompute one check by hand with a
   calculator and compare to `outputs/simulation_results.json`.
2. **Formula-string honesty.** The `formula` field in each CheckResult must
   describe what the code computes. Diverged = bug.
3. **Assumptions audit.** Every constant (Crr, η, load factors, lumped
   heights) is either justified in a comment + wiki, or flagged. No magic
   numbers without provenance.
4. **Limits audit.** The limitations list must still truthfully cover what
   the checks do NOT model (dynamics, fatigue, thermal, FEA). If a new
   check narrows a limitation, update the list; if a change adds unmodeled
   territory, extend it.
5. **Known-answer test.** Construct a config that must fail (e.g. top-heavy
   mast, tiny battery) and confirm the corresponding check fails. Passing
   everything on garbage input means the checks are decorative.
6. **Sanity ranges.** Mass 5–50 kg class, runtime not 100x requirement,
   SF not < 1 on a passing design. Absurd magnitudes = unit bug until
   proven otherwise.

## The prime directive
Never let placeholder or first-order math masquerade as FEA or certified
analysis — in code comments, wiki, report text, or PR descriptions.
