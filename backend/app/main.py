"""FastAPI application entrypoint.

Run: make api    (uvicorn app.main:app --app-dir backend --reload)
Docs: http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI

from app import __version__
from app.api.routes import router
from app.config import get_settings

# Make pipeline decisions (LLM used / gated / fallback) visible in server
# logs — silent failures are banned, and that includes silent fallbacks.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Agentic Mechanical Engineer",
    version=__version__,
    description="Natural-language request -> engineering artifact package. "
                "Concept-level output; not certified engineering.",
)
app.include_router(router)


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "model_provider": settings.model_provider,
        "storage_dir": str(settings.storage_dir),
    }
