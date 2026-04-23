from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "labapp-api"
    app_env: str = "development"
    api_prefix: str = "/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    temp_upload_dir: Path = Path("storage/tmp")
    local_data_dir: Path = Path("storage/app")
    postgres_dsn: str = Field(default="postgresql+psycopg://labapp:labapp@localhost:5432/labapp")
    redis_url: str | None = Field(default=None)
    stripe_payment_url: str | None = Field(default=None)
    paypal_payment_url: str | None = Field(default=None)
    telegram_stars_url: str | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.temp_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.local_data_dir.mkdir(parents=True, exist_ok=True)
    return settings
