"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cloud service settings for the local-first Docker Compose stack."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mqtt_host: str = "mosquitto"
    mqtt_port: int = 1883
    database_path: str = "/data/axceta.db"
    online_threshold_seconds: float = 5.0
    stress_peak_start: str = "16:00"
    stress_peak_end: str = "20:00"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
