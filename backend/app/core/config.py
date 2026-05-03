from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Real-Time Face Detection API"
    environment: str = "dev"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/facedb"
    max_frame_bytes: int = 2_000_000
    cors_origins: str = "http://localhost:5173"
    max_ws_fps: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
