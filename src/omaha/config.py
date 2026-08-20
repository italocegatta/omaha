"""Application settings, loaded from environment and `.env`."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ProfileKey = Literal["italo", "ana"]


class _ProfileBoundary(Protocol):
    """Small profile boundary needed by the offline resolver."""

    name: str
    is_family_sentinel: bool


class MyProfitConfigurationError(ValueError):
    """Stable, secret-free failure from the MyProfit configuration boundary."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.code = reason
        super().__init__(reason)

    def __repr__(self) -> str:
        return f"MyProfitConfigurationError(reason={self.reason!r})"


@dataclass(frozen=True, slots=True)
class MyProfitProfileConfig:
    """Resolved connector input for one real profile.

    Values remain usable by the future connector, while this representation
    never renders credential or destination material in diagnostics.
    """

    profile: ProfileKey
    email: str
    password: SecretStr
    destination: str

    @property
    def profile_key(self) -> ProfileKey:
        """Return canonical profile key without exposing configuration values."""
        return self.profile

    def __repr__(self) -> str:
        return (
            "MyProfitProfileConfig("
            f"profile={self.profile!r}, email=<redacted>, "
            "password=<redacted>, destination=<redacted>)"
        )


_PROFILE_ALIASES: dict[ProfileKey, frozenset[str]] = {
    "italo": frozenset({"italo"}),
    "ana": frozenset({"ana", "ana livia"}),
}

# Values reserved for documentation and local examples. They must never be
# accepted as a live connector configuration.
_FALSE_MYPROFIT_VALUES = frozenset(
    {
        "italo@example.invalid",
        "ana@example.invalid",
        "replace-with-italo-password",
        "replace-with-ana-password",
        "https://myprofit.invalid/italo",
        "https://myprofit.invalid/ana",
    }
)


def _normalise_profile_name(name: object) -> str:
    return " ".join(str(name).split()).casefold()


def _profile_key(profile: _ProfileBoundary) -> ProfileKey:
    if profile.is_family_sentinel:
        raise MyProfitConfigurationError("household_read_only")

    name = _normalise_profile_name(profile.name)
    matches = [key for key, aliases in _PROFILE_ALIASES.items() if name in aliases]
    if len(matches) > 1:
        raise MyProfitConfigurationError("ambiguous_profile")
    if not matches:
        raise MyProfitConfigurationError("unknown_profile")
    return matches[0]


def _is_false_myprofit_value(value: str) -> bool:
    normalised = value.strip().casefold()
    return (
        normalised in _FALSE_MYPROFIT_VALUES
        or normalised.endswith("@example.invalid")
        or normalised.startswith("https://myprofit.invalid/")
        or normalised.startswith("replace-with-")
    )


def _resolve_values(
    profile_key: ProfileKey,
    email: str | None,
    password: SecretStr | None,
    destination: str | None,
) -> MyProfitProfileConfig:
    raw_password = (
        password.get_secret_value()
        if isinstance(password, SecretStr)
        else password
        if isinstance(password, str)
        else None
    )
    values = (email, raw_password, destination)
    if any(value is None or not value.strip() for value in values):
        raise MyProfitConfigurationError("incomplete_configuration")
    assert email is not None
    assert raw_password is not None
    assert destination is not None
    if any(_is_false_myprofit_value(value) for value in (email, raw_password, destination)):
        raise MyProfitConfigurationError("placeholder_configuration")
    return MyProfitProfileConfig(
        profile=profile_key,
        email=email.strip(),
        password=SecretStr(raw_password),
        destination=destination.strip(),
    )


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

    # MyProfit credentials remain environment-backed and profile-specific.
    # They are optional at startup; the resolver fails closed until one
    # complete, non-placeholder profile mapping is supplied.
    MYPROFIT_ITALO_EMAIL: str | None = Field(default=None, repr=False)
    MYPROFIT_ITALO_PASSWORD: SecretStr | None = Field(default=None, repr=False)
    MYPROFIT_ITALO_DESTINATION: str | None = Field(default=None, repr=False)
    MYPROFIT_ANA_EMAIL: str | None = Field(default=None, repr=False)
    MYPROFIT_ANA_PASSWORD: SecretStr | None = Field(default=None, repr=False)
    MYPROFIT_ANA_DESTINATION: str | None = Field(default=None, repr=False)
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

    def __repr__(self) -> str:
        """Keep settings diagnostics free of credential and routing values."""
        return (
            "Settings(SECRET_KEY=<redacted>, DATABASE_URL=<redacted>, "
            "MYPROFIT_ITALO_EMAIL=<redacted>, "
            "MYPROFIT_ITALO_PASSWORD=<redacted>, "
            "MYPROFIT_ITALO_DESTINATION=<redacted>, "
            "MYPROFIT_ANA_EMAIL=<redacted>, "
            "MYPROFIT_ANA_PASSWORD=<redacted>, "
            "MYPROFIT_ANA_DESTINATION=<redacted>)"
        )

    __str__ = __repr__


def resolve_myprofit_profile_config(
    profile: _ProfileBoundary,
    config: Settings | None = None,
) -> MyProfitProfileConfig:
    """Resolve MyProfit values for active real profile, never Família."""
    profile_key = _profile_key(profile)
    source = config if config is not None else settings
    if profile_key == "italo":
        return _resolve_values(
            profile_key,
            source.MYPROFIT_ITALO_EMAIL,
            source.MYPROFIT_ITALO_PASSWORD,
            source.MYPROFIT_ITALO_DESTINATION,
        )
    return _resolve_values(
        profile_key,
        source.MYPROFIT_ANA_EMAIL,
        source.MYPROFIT_ANA_PASSWORD,
        source.MYPROFIT_ANA_DESTINATION,
    )


# Short alias for connector callers that already have a profile resolver name.
resolve_myprofit_config = resolve_myprofit_profile_config


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

__all__ = [
    "Field",
    "MyProfitConfigurationError",
    "MyProfitProfileConfig",
    "Settings",
    "resolve_myprofit_config",
    "resolve_myprofit_profile_config",
    "settings",
]
