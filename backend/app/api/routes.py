"""Design API.

POST /api/v1/designs runs the pipeline synchronously (it takes well under a
second for the deterministic path). When LLM agents make runs slow, switch
to a background task + status field; the schema already returns design_id
so clients are ready for that.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import ArtifactManifest
from app.services.pipeline import run_pipeline
from app.storage.artifacts import load_manifest

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


@router.get("/designs/{design_id}/model")
def get_model(design_id: str) -> FileResponse:
    _get_manifest_or_404(design_id)
    path = _design_dir(design_id) / "robot_chassis.stl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="model not found")
    return FileResponse(path, media_type="model/stl", filename="robot_chassis.stl")
