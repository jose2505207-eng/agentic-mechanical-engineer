# Architecture

## System diagram

```mermaid
flowchart TD
    U[User prompt] --> RQ[agents/requirements.py<br/>Requirements]
    RQ --> AR[agents/architecture.py<br/>ArchitectureSpec]
    AR --> CP[agents/cad_params.py<br/>CADParams — bound-checked]
    CP --> CAD[cad/chassis.py<br/>CadQuery template → STL/STEP]
    CAD -->|solid volume × density| SIM[simulation/checks.py<br/>SimulationResults]
    AR --> SIM
    SIM --> RISK[simulation/risk.py<br/>RiskReport]
    AR --> BOM[bom/generator.py<br/>BOM + bom.csv]
    RISK --> REP[reports/markdown.py<br/>engineering_report.md]
    BOM --> REP
    SIM --> REP
    REP --> MAN[storage/artifacts.py<br/>artifact_manifest.json]

    subgraph orchestration
        PIPE[services/pipeline.py — run_pipeline]
    end
    subgraph interfaces
        CLI[scripts/run_demo.py]
        API[api/routes.py + main.py<br/>FastAPI]
    end
    CLI --> PIPE
    API --> PIPE

    subgraph future AI layer
        LLM[llm/provider.py + llm/agents.py<br/>LLM stations w/ deterministic fallback]
    end
    LLM -. replaces stages 1–3 behind same contracts .-> RQ
```

## Modules

| Module | Job | Depends on |
|---|---|---|
| `app/schemas/` | All data contracts (Pydantic). The constitution of the repo. | nothing |
| `app/agents/` | Deterministic pipeline stations (requirements, architecture, cad params) | schemas |
| `app/cad/` | CadQuery template `mobile_robot_base_v1` + placeholder STL fallback | schemas |
| `app/simulation/` | Engineering checks + rule-based risk report | schemas |
| `app/bom/` | Curated BOM generation + CSV writer | schemas |
| `app/reports/` | Markdown report renderer | schemas |
| `app/storage/` | Artifact store (local FS now; swap point for S3/Supabase later) | schemas |
| `app/services/` | `run_pipeline()` — the only place that knows the stage order | everything above |
| `app/api/` + `main.py` | FastAPI wrapper around the pipeline | services |
| `app/llm/` | Provider-agnostic LLM client + LLM stations with fallback | schemas, config |
| `app/config.py` | Env-driven settings (see `env-space`) | nothing |

## Dependency rules (enforced by review, keep them true)

1. `schemas` imports nothing from the app. Everyone imports schemas.
2. Stations never import each other — only `services/pipeline.py` composes them.
3. Only `storage/` touches the filesystem layout; only `config.py` reads env.
4. `llm/` may import deterministic agents (for fallback); never the reverse.

Rule 2 is what makes stations independently replaceable — by better code or
by AI agents.
