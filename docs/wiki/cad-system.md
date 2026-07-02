# CAD System

Two modes since ADR-009:

1. **Template mode** — the proven wheeled-robot vertical (below).
2. **Generative mode** — for arbitrary objects, the LLM writes a parametric
   CadQuery script; `cad/sandbox.py` AST-validates it (import whitelist, no
   dangerous builtins, no dunder access) and executes it in an isolated
   subprocess with a timeout; `cad/generative.py` feeds failures back to the
   model for up to 3 attempts. Output: `model.stl`, `model.step`, plus
   `cad_script.py` — the editable parametric source. Fillet/chamfer/shell/
   loft/sweep are banned in generated code (dominant OCCT failure mode).
   Pipeline dispatch: `services/pipeline.py::select_mode` — robot-class
   prompts go to template; everything else generative; generative failure
   falls back to template; no LLM provider = always template.

## How template mode works

CAD generation is **template-based parametric modeling**, not AI freehand
geometry. The flow:

```
CADParams (schema-validated) → cad/chassis.py template → STL + STEP + solid volume
```

The one template today is `mobile_robot_base_v1` in
`backend/app/cad/chassis.py`:

- rectangular plate, rounded corners (`chassis_length/width/thickness_mm`)
- 4 corner mounting holes (`mounting_hole_diameter_mm`, 15 mm inset)
- battery bay + electronics bay: walled open boxes on the deck (3 mm walls)
- sensor mast: cylinder at front-center (`mast_height/diameter_mm`)
- 4 wheel placeholder cylinders centered on the track line at
  (±wheelbase/2, ±track/2)

Coordinates: chassis plate bottom at z=0, XY centered. Wheel axles at z=0,
so the "ground" is at z = −wheel_radius.

Two outputs matter downstream:

1. **STL/STEP files** — the deliverable.
2. **`chassis_volume_mm3`** — actual solid volume of the *structure* (wheels
   excluded), which × material density = chassis mass for the simulation
   stage. This is why the mass numbers aren't hand-waved (risk R2).

## The safety layers (why bad geometry can't happen)

1. `CADParams` schema has hard bounds on every dimension (`ge=`/`le=`).
   An LLM or a buggy mapping proposing a 5-meter chassis fails validation
   before any geometry code runs.
2. `MAX_CAD_COMPLEXITY` (env) caps job size as a second guardrail.
3. If CadQuery isn't installed, `cad/stl_fallback.py` writes a plain box STL
   whose header literally says `PLACEHOLDER BOX STL - not real geometry`,
   and the manifest + report carry the note. The pipeline degrades honestly,
   never silently.

## Adding a new template (the recipe)

1. **Schema first.** Add a `CADParams`-style model (or extend `CADParams`)
   with hard bounds on every new dimension. Bounds are the contract with the
   future AI layer — set them to what the template can *actually* build.
2. Write the builder in `backend/app/cad/<name>.py`:
   `def generate_<name>(params, stl_path, step_path) -> CADResult`.
   Return the real structure volume.
3. Give it a `template` id string (e.g. `sensor_mast_v2`) and route on it in
   the pipeline.
4. Test: parameter sweep across the full bound range must render and export
   a non-empty STL without exceptions (see `test_golden_path.py::test_stl_is_valid_and_nonempty`
   for the STL validity pattern).
5. `make wiki` and describe the template here.

## Debugging CAD locally

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
from app.agents.requirements import extract_requirements
from app.agents.architecture import generate_architecture
from app.agents.cad_params import generate_cad_params
from app.cad.chassis import generate_chassis
from pathlib import Path
req = extract_requirements('Design an inspection robot for 8 hours')
arch = generate_architecture(req)
p = generate_cad_params(req, arch)
r = generate_chassis(p, Path('/tmp/test.stl'))
print(r.chassis_volume_mm3, r.note)"
```

View STLs with any viewer (f3d, PrusaSlicer, https://viewstl.com).
