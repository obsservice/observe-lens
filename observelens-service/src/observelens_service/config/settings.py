from functools import lru_cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OBSERVELENS_SERVICE_",
        extra="ignore",
    )

    database_url: str
    agent_base_url: HttpUrl
    catalog_base_url: HttpUrl | None = None
    catalog_timeout_seconds: float = 10.0
    agent_timeout_seconds: float = 30.0
    environment: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    # BaseSettings resolves required values from the environment and `.env` at runtime.
    return Settings()  # type: ignore[call-arg]
