# Agentic Mechanical Engineer — Wiki

You typed one sentence. You got back a requirements document, a system
architecture, a 3D model, engineering checks, a risk report, a bill of
materials, and an engineering report. That's the project.

## What this is

An AI mechanical engineering agent. Input: a natural-language product request
("Design a mobile robot that can inspect manufacturing equipment for 8
hours"). Output: a structured, honest, concept-level engineering package in
`outputs/`.

The current pipeline is **deterministic** — every stage is a typed Python
function you can read, test, and trust. The AI layer (`backend/app/llm/`)
replaces stages one at a time behind the *same contracts*, with the
deterministic code as permanent fallback. That's the core strategy: **build
the working spine first, upgrade the vertebrae later.**

## Run it (2 commands)

```bash
make install   # venv + deps (CadQuery is big; get coffee)
make demo      # prompt -> full package in outputs/
```

Then read `outputs/engineering_report.md` and open `outputs/robot_chassis.stl`
in any STL viewer.

## What the golden path currently does

1. Parses the prompt into `Requirements` (runtime, payload, environment…),
   recording every assumption it makes.
2. Sizes a system architecture: skid-steer drivetrain, LiFePO4 battery sized
   from a power budget, motors with torque headroom.
3. Maps that to bound-checked CAD parameters.
4. Builds a parametric chassis in CadQuery, exports STL + STEP.
5. Runs six engineering checks (runtime, torque, payload, tip-over, bending,
   envelope) with the formulas printed in the output.
6. Turns failures and known hazards into a risk report.
7. Prices a curated BOM.
8. Writes the report, and a manifest of everything it produced.

## Where to go next

| You want to… | Read |
|---|---|
| Understand the big idea | [mental-model.md](mental-model.md) |
| See the module layout | [architecture.md](architecture.md) |
| Trace prompt → report step by step | [golden-path.md](golden-path.md) |
| Find a file | [code-map.md](code-map.md) |
| Understand the data contracts | [schemas.md](schemas.md) |
| Add a CAD template | [cad-system.md](cad-system.md) |
| Audit the engineering math | [simulation-system.md](simulation-system.md) |
| Set up your machine | [setup.md](setup.md) |
| Know why we chose X | [decisions.md](decisions.md) |
| See what's coming | [roadmap.md](roadmap.md) |
| Fix something broken | [troubleshooting.md](troubleshooting.md) |

## Honesty contract

This tool is an engineering **assistant**, not a licensed professional
engineer. Every output says so. The checks are first-order sizing math, not
FEA. Assumptions and limitations are printed in every report, always.
