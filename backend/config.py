"""
LifeOS Configuration — Centralized Settings Management
========================================================
All environment-specific and operational settings in one place.
Supports .env file override via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # --- App Settings ---
    PROJECT_NAME: str = "LifeOS"
    ENVIRONMENT: str = "development"  # development | production
    LOG_LEVEL: str = "DEBUG"
    VERSION: str = "2.0.0"

    # --- Database ---
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/lifeos"
    REDIS_URL: str = "redis://redis:6379/0"
    MONGO_URL: str = "mongodb://mongodb:27017"

    # --- JWT & Auth ---
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # --- AI / LLM ---
    # Model Memory Requirements (approximate):
    # - phi3:mini (3.8B): ~2.3GB RAM - Best for 4GB systems
    # - gemma2:2b (2B): ~1.6GB RAM - Best for 3GB systems
    # - mistral:7b (7B): ~4.5GB RAM - Requires 8GB+ systems
    OPENAI_API_KEY: str = "ollama"
    OPENAI_BASE_URL: str = "http://127.0.0.1:11434/v1"
    AI_MODEL: str = "phi3:mini"

    # --- Security ---
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:3001,http://localhost:3002"
    RATE_LIMIT_PER_MIN: int = 60

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # --- Mail ---
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 465
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@lifeos.ai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parses CORS_ORIGINS into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()
