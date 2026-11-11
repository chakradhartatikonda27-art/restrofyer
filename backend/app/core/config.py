import os
from pydantic_settings import BaseSettings
from typing import List


def _resolve_database_url() -> str:
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        if env_url.startswith("postgres://"):
            return env_url.replace("postgres://", "postgresql://", 1)
        return env_url
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/restaurant_saas.db"
    return "sqlite:///./restaurant_saas.db"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Restaurant CRM / ERP Multi-Tenant SaaS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "super-secret-production-quality-jwt-signing-key-for-saas-platform-2026",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = _resolve_database_url()

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    # Storage
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "/tmp/storage" if os.getenv("VERCEL") else "./storage")

    class Config:
        case_sensitive = True


settings = Settings()
