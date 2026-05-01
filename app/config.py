from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Nequi Chat API"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "sqlite:///./data/messages.db"
    api_key: str = "nequi-secret-key-change-in-production"
    rate_limit_per_minute: int = 60
    cors_origins: List[str] = ["http://localhost:4200", "http://localhost:8080", "http://localhost:80", "http://localhost"]

    model_config = {"env_file": ".env"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
