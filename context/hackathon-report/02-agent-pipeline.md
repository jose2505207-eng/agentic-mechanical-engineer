# Architecture — Agent Pipeline

The system is organized as a **LangGraph state machine**. Each node is a specialized agent with a defined input/output contract; state is a shared typed object (Pydantic) passed through the graph.

## [1] Requirements Agent
- **Input:** raw user prompt
- **Output:** structured requirements JSON
- **Fields:** `payload_kg`, `runtime_hr`, `max_dimensions_mm`, `environment`, `max_cost_usd`, `locomotion_type`, `sensors_required`
- **Method:** LLM extraction with JSON schema enforcement + validation rules (e.g., payload > 0, runtime physically plausible)

## [2] Architecture Agent
- **Input:** requirements JSON
- **Output:** system architecture spec (drivetrain type, wheel count, chassis topology, sensor placement, battery class, motor class)
- **Method:** LLM reasoning constrained by a rules layer defined by the mechatronics engineer (feasibility gates before CAD)

## [3] CAD Agent
- **Input:** architecture spec
- **Output:** parametric 3D geometry
- **Method:** architecture parameters mapped to CadQuery templates (Python-native parametric CAD). Templates for MVP: chassis plate, wheel/motor mounts, sensor mast, battery tray, enclosure.
- **Export:** STL (print), STEP (interop)
- **NOTE:** The LLM does NOT freehand geometry. It selects and parameterizes engineer-validated templates. This is the core reliability decision of the project.

## [4] Simulation Agent
- **Input:** STL/STEP assembly + mass properties
- **Output:** simulation results
- **Method:** geometry → URDF (links, joints, inertia from CAD mass properties) → PyBullet headless simulation
- **Checks (MVP):** static stability (tip-over angle), payload load case, drivetrain torque vs. required tractive force, basic collision/clearance

## [5] Failure Prediction Agent
- **Input:** requirements + architecture + simulation results
- **Output:** risk report with per-item severity
- **Method:** deterministic engineering rules (NOT LLM-guessed):
  - Safety factor thresholds per material (yield-based)
  - Motor stall torque margin vs. worst-case load
  - Battery runtime: `capacity_Wh / avg_draw_W` vs. required runtime
  - Thermal flag for enclosed electronics
  - 3D-printability: overhang angle, min wall thickness
- Rules are authored and validated by the mechatronics engineer.

## [6] BOM Agent
- **Input:** architecture spec + failure constraints
- **Output:** bill of materials with quantities, unit cost estimates, and vendor-class suggestions (motors, battery, fasteners, bearings, sensors, controller)
- **Method:** component database (curated CSV/Postgres table for MVP) + LLM for alternatives text

## [7] Report Agent
- **Input:** full pipeline state
- **Output:** engineering report (Markdown/PDF): assumptions, design decisions, simulation summary, risks, BOM, next steps
