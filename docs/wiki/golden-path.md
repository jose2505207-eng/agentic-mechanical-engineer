# The Golden Path

The single flow the whole repo exists to serve. Run it:

```bash
make demo
```

which executes `scripts/run_demo.py`, which calls
`run_pipeline(prompt, outputs/)` in `backend/app/services/pipeline.py`.

## Step by step

**0. Prompt.** `"Design a mobile robot that can inspect manufacturing
equipment for 8 hours."`

**1. Requirements** (`agents/requirements.py`) — regexes pull `8 hours` →
`runtime_hr=8.0`; "manufacturing" → `environment=indoor_industrial`;
"inspect" → thermal camera + lidar in the sensor list. Everything the prompt
*didn't* say (payload, budget, envelope) becomes a default **plus a logged
assumption with a rationale and confidence**. Unanswerable things go to
`unknowns`. → `outputs/requirements.json`

**2. Architecture** (`agents/architecture.py`) — a power budget
(`P = m·g·(Crr + sin θ)·v/η + electronics`) sizes the battery:
~44 W average × 8 h ÷ 0.9 usable × 1.2 margin ≈ 470 Wh → snaps to a real
512 Wh LiFePO4 pack. Motors picked with headroom (verified later,
independently). → `outputs/architecture.json`

**3. CAD parameters** (`agents/cad_params.py`) — architecture → concrete
dimensions, validated against hard bounds in the `CADParams` schema. A crazy
value dies *here*, not in the CAD kernel. → `outputs/cad_params.json`

**4. CAD** (`cad/chassis.py`) — the `mobile_robot_base_v1` CadQuery template:
plate + corner holes + battery/electronics bays + sensor mast + wheel
placeholders. Exports STL and STEP, and returns the **actual solid volume**,
which × material density = chassis mass. No CadQuery installed? A labeled
placeholder box STL keeps the line moving. → `outputs/robot_chassis.stl`

**5. Checks** (`simulation/checks.py`) — six first-order checks: battery
runtime, motor torque margin (worst case: 8° ramp + 0.3 m/s² accel), payload
margin, static tip-over angles from a lumped-mass CoG, chassis bending SF
(beam approximation), dimensional envelope. Each check carries its formula
and assumptions *in the JSON*. → `outputs/simulation_results.json`

**6. Risk** (`simulation/risk.py`) — deterministic rules: every failed check
becomes a high-severity item; thin margins, industrial hazards, thermal,
lithium handling, and the standing "this is not FEA" item R-000.
→ `outputs/risk_report.json`

**7. BOM** (`bom/generator.py`) — curated parts with realistic budget prices,
filtered by required sensors. Demo total ≈ $774, under the $1500 budget.
→ `outputs/bom.csv`

**8. Report** (`reports/markdown.py`) — all of the above rendered for humans,
with assumptions and limitations mandatory, never optional.
→ `outputs/engineering_report.md`

**9. Manifest** (`storage/artifacts.py`) — every artifact, its path, kind,
and description. The API serves designs from this. →
`outputs/artifact_manifest.json`

## Verifying the path

```bash
make test          # 21 tests, includes full golden-path regression
make check-env     # what's configured, what's not
```

The regression test (`test_golden_path.py::test_all_checks_pass_for_demo_prompt`)
pins the demo design as *healthy*: if a future change makes the reference
robot fail its own physics, CI screams.
