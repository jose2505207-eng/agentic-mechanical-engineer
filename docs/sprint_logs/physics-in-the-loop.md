# Sprint Log — Physics simulation in the optimization loop

Date: 2026-07-02.

## What shipped
- `simulation/physics.py`: headless PyBullet testing of every generative
  build — drop test (20 mm, 3 s settle) + push test (30% of weight lateral
  at the true CoM, 0.5 s + 2 s settle). Results -> `physics_settles_upright`
  and `physics_push_stability` CheckResults that feed the sim-feedback
  loop, so the AI redesigns geometry that falls over. PyBullet absent ->
  checks skipped with a note, never faked.
- URDF export (`model.urdf`, bounding-box inertia stated in-file) so every
  design loads directly in Gazebo / Webots (urdf2webots) / PyBullet for
  continued testing — the bridge to full robot simulators.
- Deps: backend[sim] extra (pybullet compiles from source ~10 min; trimesh
  for CoM/bounds). make install tolerates failure.

## Physics bug caught by known-answer testing
PyBullet assumes CoM at the mesh origin; bottom-origin parts were
unrealistically stable (the mandatory tall-stick-must-topple test failed).
Fixed by passing trimesh's center_mass as baseInertialFramePosition and
pushing through the live CoM each step. This is exactly why the test
discipline exists — a decorative sim would have shipped.

## Verified live (design-808bf5192220)
"design a tall desk lamp, 400mm tall, that will not tip over easily" ->
5 iterations, footprint shrank 375->356->328 mm chasing envelope_fit;
physics PASSED (settled 0 deg, survived push) — the anti-tip requirement is
sim-verified; envelope_fit never converged and was reported honestly as a
HIGH risk (NOT converged note in the UI).

## Observed issue -> roadmap
LLM requirements extraction produced an envelope (~350 mm) inconsistent
with the prompt's stated 400 mm height, making convergence impossible.
Fix queued: deterministic consistency guard between prompt dimensions and
extracted envelope.

## Tests: 59 passing (5 new physics known-answer + URDF tests).
