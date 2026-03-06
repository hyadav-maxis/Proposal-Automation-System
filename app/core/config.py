"""
Core configuration — reads all settings from environment variables.

Usage:
    from app.core.config import settings
    print(settings.DB_HOST)
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (one level up from app/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# Explicitly load .env file
load_dotenv(dotenv_path=ENV_PATH, override=True)


class Settings(BaseSettings):
    """Application settings loaded from .env / environment."""

    # ── Database ──────────────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "proposal_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # ── API ───────────────────────────────────────────────────────────────────
    API_PORT: int = 8000
    API_TITLE: str = "Proposal Automation API"
    API_VERSION: str = "1.0.0"

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Paths ─────────────────────────────────────────────────────────────────
    LOGO_PATH: str = "static/company_logo.png"

    # ── SMTP ──────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Proposal System"
    SMTP_REPLY_TO: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()


# Convenience alias used throughout the app
settings = get_settings()
