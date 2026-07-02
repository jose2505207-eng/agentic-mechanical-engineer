"""Local filesystem artifact store.

Layout:
  {STORAGE_DIR}/                      <- demo writes here directly (flat)
  {STORAGE_DIR}/designs/{design_id}/  <- API-created designs

Every write goes through this module so a future S3/Supabase backend only
has to reimplement this file.
"""

import json
from pathlib import Path

from pydantic import BaseModel

from app.schemas import ArtifactManifest, ArtifactRef


class ArtifactStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._refs: list[ArtifactRef] = []

    def path(self, name: str) -> Path:
        return self.base_dir / name

    def write_json(self, name: str, model: BaseModel, description: str = "") -> Path:
        p = self.path(name)
        p.write_text(model.model_dump_json(indent=2))
        self._track(name, "json", description)
        return p

    def write_text(self, name: str, content: str, kind: str, description: str = "") -> Path:
        p = self.path(name)
        p.write_text(content)
        self._track(name, kind, description)
        return p

    def track_file(self, name: str, kind: str, description: str = "") -> None:
        """Register an artifact written directly by another module (e.g. CAD)."""
        if not self.path(name).exists():
            raise FileNotFoundError(f"cannot track missing artifact: {self.path(name)}")
        self._track(name, kind, description)

    def _track(self, name: str, kind: str, description: str) -> None:
        self._refs = [r for r in self._refs if r.name != name]
        self._refs.append(
            ArtifactRef(name=name, path=str(self.path(name)), kind=kind, description=description)
        )

    def write_manifest(self, design_id: str, prompt: str, notes: list[str]) -> ArtifactManifest:
        manifest = ArtifactManifest(
            design_id=design_id, prompt=prompt, artifacts=list(self._refs), notes=notes
        )
        p = self.path("artifact_manifest.json")
        p.write_text(manifest.model_dump_json(indent=2))
        return manifest


def load_manifest(base_dir: Path) -> ArtifactManifest | None:
    p = base_dir / "artifact_manifest.json"
    if not p.exists():
        return None
    return ArtifactManifest.model_validate(json.loads(p.read_text()))
