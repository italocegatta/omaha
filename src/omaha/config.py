"""Application settings, loaded from environment and `.env`."""

from __future__ import annotations

import sys
from typing import Literal

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
    # NOTE: this default points at the LIVE prod DB
    # (`./data/portfolio.db`). It is ONLY safe to rely on when running
    # the dev server (`uv run task serve` / `uv run uvicorn …`) — i.e.
    # when no test harness is involved. **The pytest suite MUST
    # override this via ``tests/conftest.py`` module-load before any
    # test module imports ``omaha.db.SessionLocal``**; if a test
    # triggers a code path that imports this module first (without
    # conftest having set the env), SessionLocal will bind to prod and
    # any ``_wipe_tables`` / ``_seed_class`` helper will corrupt the
    # household's portfolio DB. See PRD §4.12 + the module-load
    # isolation contract in ``tests/conftest.py``.
    DATABASE_URL: str = "sqlite:///./data/portfolio.db"
    ADMIN_PASSWORD: str | None = None

    # S06: production-readiness knobs. All four are read at import
    # time (Settings is instantiated eagerly) and feed both the
    # logging config (LOG_LEVEL / LOG_FORMAT) and the secure-cookie
    # flip in main.py (OMAHA_ENV).
    LOG_LEVEL: str = "INFO"
    # ``None`` means "derive from OMAHA_ENV" via ``effective_log_format``.
    # Set to ``"json"`` or ``"text"`` to force one specific format
    # regardless of environment.
    LOG_FORMAT: str | None = None
    OMAHA_ENV: str = "development"
    APP_VERSION: str = "0.1.0"

    # S04: preview expiration window. E2E tests set this to 1 second so
    # the expired-preview test can wait for real expiration instead of
    # backdating the database. Default 1h keeps production behavior.
    PREVIEW_TTL_SECONDS: int = 3600

    # Quote cache: TTL for the cached quote (seconds). Default 900 (15 min).
    QUOTE_TTL_SECONDS: int = 900
    # Background refresh interval in seconds. Default 900 (15 min).
    QUOTE_REFRESH_INTERVAL_SECONDS: int = 900
    # Circuit breaker cooldown after consecutive full-batch failures.
    QUOTE_REFRESH_CIRCUIT_COOLDOWN_SECONDS: int = 300
    # Number of consecutive full-batch failures before opening the circuit.
    QUOTE_REFRESH_CIRCUIT_THRESHOLD: int = 3

    # R03: provider selector source. ``"yfinance"`` (default) keeps the
    # historical production wiring; ``"stub"`` resolves to the in-memory
    # :class:`omaha.quotes.provider.StubProvider` for offline scenarios.
    # Unknown values fail at pydantic-settings validation time, so a
    # misconfigured deploy fails loudly at startup.
    QUOTE_PROVIDER: Literal["yfinance", "stub"] = "yfinance"

    @property
    def effective_log_format(self) -> str:
        """Resolve the log format the runtime should actually use.

        Precedence: an explicit ``LOG_FORMAT`` (``"json"`` or ``"text"``)
        wins; otherwise the format follows ``OMAHA_ENV`` — ``"json"``
        in production, ``"text"`` everywhere else. The smart default
        keeps local dev logs readable without forcing operators to
        set an env var.
        """
        if self.LOG_FORMAT in ("json", "text"):
            return self.LOG_FORMAT
        return "json" if self.OMAHA_ENV == "production" else "text"


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
