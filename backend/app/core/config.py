from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RAG Visual Optimizer"
    environment: Literal["local", "test", "staging", "production"] = "local"
    api_prefix: str = "/api"
    debug: bool = False

    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://postgres:postgres@postgres:5432/rag_visual_optimizer"
    )
    redis_url: RedisDsn = Field(default="redis://redis:6379/0")

    jwt_secret_key: str = Field(min_length=32, default="change-me-in-production-at-least-32-chars")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    cors_origins: list[AnyHttpUrl | str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "rag-documents"
    minio_secure: bool = False

    max_upload_mb: int = 50
    rate_limit_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
