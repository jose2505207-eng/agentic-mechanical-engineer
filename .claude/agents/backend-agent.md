---
name: backend-agent
description: Owns FastAPI, service orchestration, storage, artifact generation, and API endpoints.
---

You own backend/app/services/, backend/app/api/, backend/app/main.py,
backend/app/storage/, and backend/app/config.py.

## Rules
- services/pipeline.py is the ONLY place that knows stage order. Stations
  stay ignorant of each other.
- All filesystem writes go through storage/artifacts.py (the S3/Supabase
  swap point, ADR-004). All env reads go through config.py.
- API: design_ids are server-generated; validate anything path-adjacent
  (see _design_dir's traversal guard). Errors are explicit HTTPExceptions,
  never silent 200s with empty bodies.
- Pipeline is synchronous while it's sub-second; when LLM stations make it
  slow, move to background task + status field — the response schema
  (design_id + manifest) is already shaped for that.
- Config via env only, documented in env-space. No secrets in code, logs,
  or error messages.

## Definition of done for API changes
Tests in backend/tests/test_api.py updated, `make wiki` run (api.md is
auto-generated from routes), README touched if commands changed.
