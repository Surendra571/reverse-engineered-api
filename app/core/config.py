"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Union


class Settings(BaseSettings):
    PROJECT_NAME: str = "Mutual Fund Discovery & Intelligence API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Upstream Groww Configuration
    UPSTREAM_BASE_URL: str = "https://groww.in"
    UPSTREAM_TIMEOUT_CONNECT: float = 5.0
    UPSTREAM_TIMEOUT_READ: float = 10.0
    UPSTREAM_TIMEOUT_WRITE: float = 5.0
    UPSTREAM_TIMEOUT_POOL: float = 5.0
    UPSTREAM_MAX_RETRIES: int = 2
    UPSTREAM_BACKOFF_FACTOR: float = 0.5
    UPSTREAM_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # In-memory Cache Configuration (TTL in seconds)
    CACHE_ENABLED: bool = True
    CACHE_SEARCH_TTL: int = 900       # 15 minutes
    CACHE_EXPLORE_TTL: int = 1800     # 30 minutes
    CACHE_DETAIL_TTL: int = 7200      # 2 hours
    CACHE_CATEGORIES_TTL: int = 86400 # 24 hours
    CACHE_MAX_ITEMS: int = 2048

    # Rate limiting / Client limits
    DEFAULT_PAGE_SIZE: int = 15
    MAX_PAGE_SIZE: int = 50

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Union[str, bool]) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "debug")
        return False

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
