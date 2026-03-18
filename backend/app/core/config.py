from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Backoffice AI"
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/rag_system"
    request_timeout_seconds: int = 45
    url_ingest_allowed_domains: list[str] = []
    url_ingest_max_redirects: int = 5
    embedding_provider: Literal["mock", "openai"] = "mock"
    generation_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    generation_model: str = "gpt-5-mini"
    embedding_dimensions: int = 1536
    default_chunk_strategy: Literal["fixed", "overlap"] = "overlap"
    default_chunk_size: int = 512
    default_overlap_tokens: int = 64
    default_top_k: int = 5
    retrieval_candidate_limit: int = 25
    retrieval_score_threshold: float = 0.2
    context_character_limit: int = 6000
    worker_poll_seconds: int = 5
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_origin_regex: str = r"^https?://([a-zA-Z0-9.-]+|\d{1,3}(\.\d{1,3}){3}):3000$"
    run_migrations_on_startup: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
