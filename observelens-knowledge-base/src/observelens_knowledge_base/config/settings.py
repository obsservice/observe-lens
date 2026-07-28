from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OBS_KNOWLEDGE_BASE_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "ObserveLens Knowledge Base"
    environment: str = "local"
    database_url: str = (
        "postgresql+asyncpg://observelens:observelens@localhost:5432/observelens_knowledge"
    )
    cors_origins: str = "*"
    storage_path: Path = Field(default=Path(".data/knowledge-files"))
    max_file_size_mb: int = 100
    parser_version: str = "mvp-text-parser-v1"
    embedding_model: str = "local-keyword-embedding"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
