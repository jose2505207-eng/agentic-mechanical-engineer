"""Design API.

POST /api/v1/designs runs the pipeline synchronously (it takes well under a
second for the deterministic path). When LLM agents make runs slow, switch
to a background task + status field; the schema already returns design_id
so clients are ready for that.
"""

import json
import logging
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import ArtifactManifest
from app.services.pipeline import run_pipeline
from app.storage.artifacts import load_manifest
from app.utils.events import StatusFileSink, set_sink

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


class DesignRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=2000)


class DesignResponse(BaseModel):
    design_id: str
    manifest: ArtifactManifest


def _design_dir(design_id: str) -> Path:
    # design_id is always server-generated (uuid hex); reject anything else
    # so a crafted id can never traverse paths.
    if not design_id.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="invalid design id")
    return get_settings().storage_dir / "designs" / design_id


def _get_manifest_or_404(design_id: str) -> ArtifactManifest:
    manifest = load_manifest(_design_dir(design_id))
    if manifest is None:
        raise HTTPException(status_code=404, detail=f"design {design_id} not found")
    return manifest


@router.post("/designs", response_model=DesignResponse)
def create_design(body: DesignRequest) -> DesignResponse:
    design_id = f"design-{uuid.uuid4().hex[:12]}"
    state = run_pipeline(body.prompt, _design_dir(design_id), design_id=design_id)
    assert state.manifest is not None
    return DesignResponse(design_id=design_id, manifest=state.manifest)


class AsyncDesignResponse(BaseModel):
    design_id: str
    status_url: str


@router.post("/designs/async", response_model=AsyncDesignResponse)
def create_design_async(body: DesignRequest) -> AsyncDesignResponse:
    """Start a pipeline run in the background; poll the status URL for the
    live event feed (stages + generative-loop iterations)."""
    design_id = f"design-{uuid.uuid4().hex[:12]}"
    out_dir = _design_dir(design_id)
    sink = StatusFileSink(out_dir / "status.json")

    def worker() -> None:
        set_sink(sink)  # thread-local via contextvars
        try:
            run_pipeline(body.prompt, out_dir, design_id=design_id)
            sink.finish("complete")
        except Exception as exc:  # surfaced to the client, never swallowed
            logger.exception("background pipeline failed for %s", design_id)
            sink.finish("failed", error=str(exc))

    threading.Thread(target=worker, daemon=True, name=f"pipeline-{design_id}").start()
    return AsyncDesignResponse(
        design_id=design_id, status_url=f"/api/v1/designs/{design_id}/status")


@router.get("/designs/{design_id}/status")
def get_status(design_id: str) -> dict:
    path = _design_dir(design_id) / "status.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"no status for {design_id}")
    return json.loads(path.read_text())


@router.get("/designs/{design_id}", response_model=ArtifactManifest)
def get_design(design_id: str) -> ArtifactManifest:
    return _get_manifest_or_404(design_id)


@router.get("/designs/{design_id}/artifacts")
def list_artifacts(design_id: str) -> list[dict]:
    manifest = _get_manifest_or_404(design_id)
    return [a.model_dump() for a in manifest.artifacts]


@router.get("/designs/{design_id}/report", response_class=PlainTextResponse)
def get_report(design_id: str) -> str:
    _get_manifest_or_404(design_id)
    path = _design_dir(design_id) / "engineering_report.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="report not found")
    return path.read_text()


@router.get("/designs/{design_id}/artifacts/{name}")
def get_artifact_file(design_id: str, name: str) -> FileResponse:
    """Serve one artifact's content. Only names listed in the manifest are
    reachable — no free-form paths."""
    manifest = _get_manifest_or_404(design_id)
    ref = next((a for a in manifest.artifacts if a.name == name), None)
    if ref is None:
        raise HTTPException(status_code=404, detail=f"artifact {name} not in manifest")
    path = _design_dir(design_id) / Path(ref.name).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact file missing")
    return FileResponse(path, filename=path.name)


@router.get("/designs/{design_id}/model")
def get_model(design_id: str) -> FileResponse:
    """Serve the design's STL, whatever the pipeline mode named it."""
    manifest = _get_manifest_or_404(design_id)
    stl = next((a for a in manifest.artifacts if a.kind == "stl"), None)
    if stl is None:
        raise HTTPException(status_code=404, detail="no STL artifact for this design")
    path = _design_dir(design_id) / Path(stl.name).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="model file missing")
    return FileResponse(path, media_type="model/stl", filename=path.name)
