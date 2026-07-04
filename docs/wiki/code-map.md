# Code Map

What lives where, and why. Human notes go above/below the auto-generated block.

<!-- AUTO-GENERATED:START -->
## File map (auto-generated — do not hand-edit inside markers)

| File | What it does |
|---|---|
| `.claude/agents/backend-agent.md` |  |
| `.claude/agents/bom-agent.md` |  |
| `.claude/agents/cad-agent.md` |  |
| `.claude/agents/devops-agent.md` |  |
| `.claude/agents/frontend-agent.md` |  |
| `.claude/agents/mechanical-architecture-agent.md` |  |
| `.claude/agents/principal-architect.md` |  |
| `.claude/agents/qa-agent.md` |  |
| `.claude/agents/requirements-agent.md` |  |
| `.claude/agents/security-agent.md` |  |
| `.claude/agents/simulation-agent.md` |  |
| `.claude/agents/wiki-agent.md` |  |
| `.claude/settings.local.json` |  |
| `.claude/skills/cad-reviewer/SKILL.md` |  |
| `.claude/skills/engineering-sanity-checker/SKILL.md` |  |
| `.claude/skills/env-steward/SKILL.md` |  |
| `.claude/skills/golden-path-tester/SKILL.md` |  |
| `.claude/skills/repo-cartographer/SKILL.md` |  |
| `.claude/skills/sprint-integrator/SKILL.md` |  |
| `.claude/skills/wiki-updater/SKILL.md` |  |
| `.env.example` |  |
| `.github/workflows/wiki-check.yml` |  |
| `Makefile` |  |
| `README.md` |  |
| `backend/README.md` |  |
| `backend/app/__init__.py` | Agentic Mechanical Engineer backend package. |
| `backend/app/agents/__init__.py` | Pipeline agents. |
| `backend/app/agents/architecture.py` | Deterministic system architecture generation. |
| `backend/app/agents/cad_params.py` | Map architecture spec -> validated CAD parameters. |
| `backend/app/agents/requirements.py` | Deterministic requirements extraction. |
| `backend/app/api/__init__.py` | FastAPI route modules. |
| `backend/app/api/routes.py` | Design API. |
| `backend/app/bom/__init__.py` | Bill of materials generation from curated component data. |
| `backend/app/bom/generator.py` | BOM generation. |
| `backend/app/bom/sourcing.py` | External part sourcing enrichment (Nexar/Octopart), gated and honest. |
| `backend/app/cad/__init__.py` | Parametric CAD generation (CadQuery templates + honest fallback). |
| `backend/app/cad/chassis.py` | Mobile robot base template (mobile_robot_base_v1). |
| `backend/app/cad/generative.py` | Generative CAD with sim-feedback optimization. |
| `backend/app/cad/runner.py` | Subprocess entry point for sandboxed CAD script execution. |
| `backend/app/cad/sandbox.py` | Sandboxed execution of model-generated CadQuery scripts. |
| `backend/app/cad/stl_fallback.py` | Pure-Python binary STL writer for a rectangular box. |
| `backend/app/config.py` | Runtime configuration loaded from environment variables. |
| `backend/app/llm/__init__.py` | Model-provider abstraction for the AI agent layer. |
| `backend/app/llm/agents.py` | LLM-backed pipeline agents with deterministic fallback. |
| `backend/app/llm/gates.py` | Feasibility gates for LLM-proposed architectures. |
| `backend/app/llm/provider.py` | Provider-agnostic LLM client. |
| `backend/app/llm/telemetry.py` | Per-run LLM call telemetry — the data behind the provenance panel. |
| `backend/app/main.py` | FastAPI application entrypoint. |
| `backend/app/reports/__init__.py` | Engineering report generation (Markdown first; PDF later). |
| `backend/app/reports/generic_markdown.py` | Report renderer for generative-mode designs (arbitrary objects). |
| `backend/app/reports/markdown.py` | Markdown engineering report generator. |
| `backend/app/schemas/__init__.py` | Public schema exports. Import from `app.schemas`, not `app.schemas.models`. |
| `backend/app/schemas/models.py` | Core Pydantic schemas — the data contracts of the whole pipeline. |
| `backend/app/services/__init__.py` | Service layer: pipeline orchestration and design registry. |
| `backend/app/services/pipeline.py` | The golden path: prompt -> full engineering artifact package. |
| `backend/app/simulation/__init__.py` | Deterministic engineering checks. Not FEA. Not certified analysis. |
| `backend/app/simulation/checks.py` | Deterministic engineering check suite. |
| `backend/app/simulation/geometry_checks.py` | Deterministic checks for generatively-built geometry. |
| `backend/app/simulation/physics.py` | Headless physics testing of generated geometry (PyBullet). |
| `backend/app/simulation/risk.py` | Rule-based risk report generation. |
| `backend/app/storage/__init__.py` | Artifact storage (local filesystem MVP). |
| `backend/app/storage/artifacts.py` | Local filesystem artifact store. |
| `backend/app/utils/events.py` | Pipeline progress events, streamed to a per-run sink. |
| `backend/pyproject.toml` |  |
| `backend/tests/conftest.py` | Shared fixtures. The pipeline runs once per session into a tmp dir; all |
| `backend/tests/test_api.py` | API tests using FastAPI's TestClient against a temp storage dir. |
| `backend/tests/test_architecture_gates.py` | Sprint 8: LLM architecture proposals must pass deterministic feasibility |
| `backend/tests/test_async_and_provenance.py` | Async pipeline runs, live status feed, provenance ledger, artifact serving. |
| `backend/tests/test_generative_cad.py` | Generative CAD: sandbox safety, real execution, retry loop, pipeline mode. |
| `backend/tests/test_golden_path.py` | Golden-path regression tests: the demo must produce every artifact, |
| `backend/tests/test_llm_fallback.py` | AI agent layer tests with mocked model responses. |
| `backend/tests/test_optimization_loop.py` | Sim-feedback optimization loop: checks drive redesign iterations. |
| `backend/tests/test_physics_sim.py` | Physics simulation: known-answer stability tests + URDF export. |
| `backend/tests/test_provider_routing.py` | Provider routing: fireworks entry, per-provider key requirement, and the |
| `backend/tests/test_schemas.py` | Schema contract tests: validation works, bad values are rejected. |
| `backend/tests/test_scope_and_budget.py` | Honesty rules for out-of-scope prompts and budget overruns. |
| `backend/tests/test_sourcing_gate.py` | ALLOW_EXTERNAL_PART_SEARCH gate contract: |
| `context/README.md` |  |
| `context/hackathon-report/01-system-overview.md` |  |
| `context/hackathon-report/02-agent-pipeline.md` |  |
| `context/hackathon-report/03-tech-stack.md` |  |
| `context/hackathon-report/04-team-responsibilities.md` |  |
| `context/hackathon-report/05-mvp-scope.md` |  |
| `context/hackathon-report/06-technical-risks.md` |  |
| `context/hackathon-report/07-validation-plan.md` |  |
| `context/hackathon-report/08-deliverables.md` |  |
| `context/master-baseline/01-project-overview.md` |  |
| `context/master-baseline/02-users-and-workflows.md` |  |
| `context/master-baseline/03-capabilities.md` |  |
| `context/master-baseline/04-cad-and-components.md` |  |
| `context/master-baseline/05-materials.md` |  |
| `context/master-baseline/06-simulation-and-failure.md` |  |
| `context/master-baseline/07-manufacturing-intelligence.md` |  |
| `context/master-baseline/08-optimization-bom-digital-twin.md` |  |
| `context/master-baseline/09-multi-agent-system.md` |  |
| `context/master-baseline/10-tech-stack.md` |  |
| `context/master-baseline/11-positioning-and-market.md` |  |
| `context/master-baseline/12-limitations.md` |  |
| `context/master-baseline/13-hackathon-mvp.md` |  |
| `context/master-baseline/14-vision.md` |  |
| `docker-compose.yml` |  |
| `docs/api/README.md` |  |
| `docs/architecture/README.md` |  |
| `docs/decisions/README.md` |  |
| `docs/wiki/agents.md` |  |
| `docs/wiki/api.md` |  |
| `docs/wiki/architecture.md` |  |
| `docs/wiki/bom-system.md` |  |
| `docs/wiki/cad-system.md` |  |
| `docs/wiki/code-map.md` |  |
| `docs/wiki/decisions.md` |  |
| `docs/wiki/golden-path.md` |  |
| `docs/wiki/index.md` |  |
| `docs/wiki/mental-model.md` |  |
| `docs/wiki/roadmap.md` |  |
| `docs/wiki/schemas.md` |  |
| `docs/wiki/setup.md` |  |
| `docs/wiki/simulation-system.md` |  |
| `docs/wiki/troubleshooting.md` |  |
| `env-space` |  |
| `examples/architecture.json` |  |
| `examples/cad_params.json` |  |
| `examples/requirements.json` |  |
| `frontend/.next/app-build-manifest.json` |  |
| `frontend/.next/build-manifest.json` |  |
| `frontend/.next/cache/next-devtools-config.json` |  |
| `frontend/.next/package.json` |  |
| `frontend/.next/prerender-manifest.json` |  |
| `frontend/.next/react-loadable-manifest.json` |  |
| `frontend/.next/routes-manifest.json` |  |
| `frontend/.next/server/app-paths-manifest.json` |  |
| `frontend/.next/server/middleware-manifest.json` |  |
| `frontend/.next/server/next-font-manifest.json` |  |
| `frontend/.next/server/pages-manifest.json` |  |
| `frontend/.next/server/server-reference-manifest.json` |  |
| `frontend/.next/static/css/app/layout.css` |  |
| `frontend/.next/static/webpack/633457081244afec._.hot-update.json` |  |
| `frontend/.next/types/package.json` |  |
| `frontend/README.md` |  |
| `frontend/app/globals.css` |  |
| `frontend/app/layout.jsx` |  |
| `frontend/app/page.jsx` |  |
| `frontend/components/StlViewer.jsx` |  |
| `frontend/next.config.mjs` |  |
| `frontend/package.json` |  |
| `scripts/check_env.py` | Environment sanity check: reports which env vars are set (never their |
| `scripts/repo_map.py` | Print a map of the repository: tree of tracked-worthy files with the first |
| `scripts/run_demo.py` | Golden path demo: canned prompt -> full engineering package in outputs/. |
| `scripts/update_wiki.py` | Automatic wiki updater. |
<!-- AUTO-GENERATED:END -->
