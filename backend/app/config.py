"""Runtime configuration loaded from environment variables.

Every variable documented in `env-space` at the repo root. The deterministic
MVP requires none of them; sane defaults keep the golden path fully offline.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    model_provider: str = "deterministic"
    model_name: str = ""
    storage_dir: Path = Path("./outputs")
    max_cad_complexity: int = 100_000
    cad_max_iterations: int = 5
    allow_external_part_search: bool = False

    # LLM providers (AI agent layer only)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    fireworks_api_key: str = ""
    # Base URL for self-hosted OpenAI-compatible inference (vllm/local
    # providers) — point at the AMD Developer Cloud instance when provisioned.
    vllm_base_url: str = "http://localhost:8001/v1"

    # External part sourcing (used only when allow_external_part_search=True)
    nexar_client_id: str = ""
    nexar_client_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
