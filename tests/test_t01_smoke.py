"""Smoke test for T01: the package is importable and settings load."""

from __future__ import annotations

from omaha.config import settings


def test_settings_database_url_is_set() -> None:
    """`settings.DATABASE_URL` must always resolve to a non-empty string."""
    assert settings.DATABASE_URL, "DATABASE_URL must be set"
    assert isinstance(settings.DATABASE_URL, str)
