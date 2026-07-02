# Simulation System

**Read this first:** nothing here is FEA. These are the first-order sizing
calculations an engineer does before opening an FEA tool — implemented in
`backend/app/simulation/checks.py`, with every formula and assumption echoed
into the output JSON so results are auditable, not oracular.

## The six checks

### 1. Battery runtime
```
avg_draw_W = m·g·(Crr + sin(grade_avg))·v_avg / η  +  P_electronics + P_idle
runtime_hr = capacity_Wh × usable_fraction / avg_draw_W
PASS if runtime_hr ≥ required runtime
```
Constants: Crr = 0.015 (rubber on hard floor), η = 0.70 (motor+gearbox+driver,
conservative), v_avg = 0.8 × max speed, grade_avg = 1°, electronics = 30 W.

### 2. Motor torque margin (worst case)
```
F_tractive = m·g·sin(θ_ramp) + m·a + m·g·Crr·cos(θ_ramp)     [θ=8°, a=0.3 m/s²]
T_per_wheel = F_tractive × r_wheel / n_wheels
margin = T_rated / T_per_wheel        PASS if ≥ 1.5
```
Assumes equal load sharing — optimistic on split-μ surfaces; the 1.5 floor
absorbs that.

### 3. Payload margin
Structure is sized for 2× required payload by convention; the bending check
below verifies the convention holds. PASS if ≥ 1.5.

### 4. Static tip-over
Lumped-mass CoG: chassis & motors at axle height, battery/electronics on
deck, mast mass at 70% of mast height, payload at deck + 60 mm.
```
tip_angle = atan(support_half_width / CoG_height)
PASS if min(lateral, longitudinal) ≥ 2.5 × max_ramp
```
Static only — braking/cornering dynamics are not modeled (listed limitation).

### 5. Chassis bending
Plate treated as a simply-supported beam across the wheelbase, payload as a
centered point load at 2× load factor:
```
σ = 3·F·L / (2·w·t²)      SF = σ_yield / σ       PASS if SF ≥ 3
```
Conservative for distributed loads; non-conservative for concentrated edge
loads — which is exactly why R-000 tells you to run FEA before building.

### 6. Dimensional envelope
Bounding box (chassis ∪ wheels ∪ mast) must fit `max_dimensions_mm`.
`length_bb = max(chassis_len, wheelbase + wheel_dia)`,
`width_bb = max(chassis_w, track + wheel_w)` (wheels centered on track line),
`height = wheel_r + plate_t + mast_h`.

## Mass model

```
total = (chassis[CAD volume × ρ] + motors + wheels + battery + 2.7 kg fixed) × 1.10
```
The 1.10 covers fasteners/wiring/brackets; 2.7 kg = electronics 1.2 +
sensors/mast hardware 1.5. Chassis mass comes from the **actual CAD solid
volume**, not a guess — that's the R2 mitigation.

## Independence rule

`architecture.py` sizes the battery with a similar power model using an
*a-priori* mass guess (20 kg). `checks.py` re-derives power from the
*computed* mass. Deliberate near-duplication: the check stage independently
verifies the sizing stage instead of confirming it tautologically. Don't
"refactor" them into one function.

## Limitations (also printed in every output)

- No FEA, no dynamics, no vibration/impact/fatigue, no thermal analysis.
- CoG from lumped estimates; battery model ignores temperature and aging.
- All results require review by a qualified engineer before fabrication.

## Changing formulas

Formulas live in code; this page documents them. If you touch one, update
both, and update the pinned expectations in
`backend/tests/test_golden_path.py`. The `formula` string inside each
`CheckResult` must match what the code actually computes — that string is
the audit trail.
