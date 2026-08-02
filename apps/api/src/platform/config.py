from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "development"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://scrum:scrum@localhost:5432/scrum_tool"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    cors_origins: list[str] = ["http://localhost:3000"]
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    microsoft_oauth_client_id: str | None = None
    microsoft_oauth_client_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
