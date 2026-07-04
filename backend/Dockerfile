# Backend image: FastAPI + CadQuery (OCCT) + PyBullet, fully baked so the
# pipeline runs offline in deterministic mode with zero env vars.
# Build context = repo root (see docker-compose.yml).
FROM python:3.12-slim

# build-essential: PyBullet compiles from source.
# libgl1 & friends: OCCT/CadQuery runtime libraries (headless).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgl1 libglu1-mesa libxrender1 libxext6 libsm6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Heavy third-party deps in their own layer so source edits don't trigger a
# ~10 min PyBullet recompile + CadQuery redownload.
RUN pip install --no-cache-dir \
    "fastapi>=0.110" "uvicorn>=0.29" "pydantic>=2.6" "pydantic-settings>=2.2" \
    "numpy>=1.26" "httpx>=0.27" "cadquery>=2.4" "pybullet>=3.2" "trimesh>=4.0"

COPY backend /app/backend
COPY scripts /app/scripts
RUN pip install --no-cache-dir --no-deps /app/backend

ENV STORAGE_DIR=/data/outputs
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
