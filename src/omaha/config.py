"""Application settings, loaded from environment and `.env`."""

from __future__ import annotations

import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Omaha application.

    Values are read first from environment variables and then from a local
    `.env` file (which is gitignored). Tests typically inject overrides via
    environment variables using `monkeypatch.setenv` before importing this
    module, or rely on test-mode detection that skips the SECRET_KEY check.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./data/portfolio.db"
    ADMIN_PASSWORD: str | None = None


def _is_test_mode() -> bool:
    """Return True when the config module is being imported under pytest.

    Detection is deliberately conservative: if `pytest` is already in
    `sys.modules` we are being collected/executed by pytest, and the
    test code itself is responsible for setting the right env vars or
    `.env` file before instantiating settings.
    """
    return "pytest" in sys.modules


def _build_settings() -> Settings:
    settings = Settings()
    if not settings.SECRET_KEY and not _is_test_mode():
        raise RuntimeError(
            "SECRET_KEY is not set. Copy `.env.example` to `.env` and set a "
            "50+ char random value, or export SECRET_KEY in the environment."
        )
    return settings


settings = _build_settings()

__all__ = ["Settings", "settings", "Field"]
