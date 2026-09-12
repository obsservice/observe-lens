from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AUTH_", extra="ignore")

    database_url: str = (
        "postgresql+asyncpg://observelens:observelens@localhost:5433/observelens_auth"
    )
    jwt_secret: SecretStr = Field(
        default=SecretStr("local-development-secret-change-before-production"), min_length=32
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=14, ge=1, le=365)
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: SecretStr = SecretStr("observelens")
    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_tenant_name: str = "default"
    bootstrap_tenant_display_name: str = "Default"


@lru_cache
def get_settings() -> Settings:
    return Settings()
