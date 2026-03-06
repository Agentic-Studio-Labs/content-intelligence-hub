from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "CIH_"}

    # Server
    port: int = 8420

    # Paths
    data_dir: Path = Path.home() / "Library" / "Application Support" / "ContentIntelligenceHub"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.7

    # Search
    search_limit: int = 10
    hybrid_alpha: float = 0.5

    # Watched folders
    watched_folders: list[str] = []

    @property
    def db_path(self) -> Path:
        return self.data_dir / "content.db"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
