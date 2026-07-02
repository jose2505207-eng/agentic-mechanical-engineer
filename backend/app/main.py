"""FastAPI application entrypoint.

Run: make api    (uvicorn app.main:app --app-dir backend --reload)
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI

from app import __version__
from app.api.routes import router
from app.config import get_settings

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
