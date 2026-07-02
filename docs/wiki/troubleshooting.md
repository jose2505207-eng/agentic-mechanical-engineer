# Troubleshooting

## `make install` fails on CadQuery
**Symptom:** pip error while installing `cadquery` / `OCP` wheels.
**Meaning:** Your platform lacks a prebuilt OCP wheel (some ARM/musl
setups).
**Fix:** Nothing urgent — the demo still runs with a labeled placeholder
STL. For real geometry: try `pip install cadquery` inside the venv with a
newer pip, or use conda-forge (`conda install -c conda-forge cadquery`).
`make check-env` tells you which mode you're in.

## Demo says "PLACEHOLDER: CadQuery not installed"
That's the fallback doing its job. Install `backend[cad]` (above) and rerun
`make demo`.

## `ModuleNotFoundError: No module named 'app'`
You're running system Python instead of the venv, or skipped install.
```bash
make install        # or: .venv/bin/pip install -e backend
.venv/bin/python scripts/run_demo.py
```
Scripts add `backend/` to `sys.path` themselves; tests need the editable
install.

## `make api` starts but POST /api/v1/designs 500s
Check the uvicorn console — the pipeline exception is printed there. Most
common cause: `STORAGE_DIR` pointing somewhere unwritable. Unset it or point
it at a writable path; default `./outputs` always works.

## Tests fail after I changed a formula or dimension
Expected — the golden-path regression pins the demo design as healthy
(`test_all_checks_pass_for_demo_prompt`). If your change is intentional,
re-derive the expectation: run `make demo`, read
`outputs/simulation_results.json`, confirm the physics makes sense, then
update the test. Never loosen a threshold just to go green.

## `make wiki` fails with an import error
`update_wiki.py` imports the FastAPI app and schemas to introspect them, so
the backend must be installed in the venv (`make install`). Any syntax error
in `app/` breaks wiki generation too — that's a feature: the wiki can't
drift from broken code.

## CI wiki-check fails: "STALE wiki pages"
You changed schemas/routes/files without regenerating. Run `make wiki`,
commit the diff.

## LLM provider configured but pipeline used deterministic output
By design, fallback is silent-but-logged. Check backend logs for
`LLM unavailable (…)` — bad key, network, or the model returned JSON that
failed schema validation. Fix the cause or accept the fallback; the pipeline
never blocks on a model.

## STL looks weird in my viewer (wheels floating, no ground)
Wheel axles are at z=0 and the "ground plane" is z = −wheel_radius. Some
viewers auto-ground to the lowest vertex and it looks fine; others show the
plate at origin. Cosmetic only.
