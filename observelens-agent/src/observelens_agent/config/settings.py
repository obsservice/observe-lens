from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OBSERVELENS_AGENT_",
        extra="ignore",
    )

    cors_allowed_origins: str = "http://localhost:3080,http://127.0.0.1:3080"
    environment: str = "development"
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # BaseSettings resolves required values from the environment and `.env` at runtime.
    return Settings()
