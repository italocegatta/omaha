"""Offline F57 coverage for profile-scoped MyProfit configuration."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from omaha.config import (
    MyProfitConfigurationError,
    MyProfitProfileConfig,
    Settings,
    resolve_myprofit_profile_config,
)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent
MYPROFIT_FIELDS = {
    "MYPROFIT_ITALO_EMAIL",
    "MYPROFIT_ITALO_PASSWORD",
    "MYPROFIT_ITALO_DESTINATION",
    "MYPROFIT_ANA_EMAIL",
    "MYPROFIT_ANA_PASSWORD",
    "MYPROFIT_ANA_DESTINATION",
}


def _profile(name: str, *, family: bool = False) -> SimpleNamespace:
    return SimpleNamespace(name=name, is_family_sentinel=family)


def _settings(**overrides: str | None) -> Settings:
    values: dict[str, str | None] = {
        "MYPROFIT_ITALO_EMAIL": "italo.synthetic@fixture.test",
        "MYPROFIT_ITALO_PASSWORD": "italo-password-fixture",
        "MYPROFIT_ITALO_DESTINATION": "https://fixture.test/myprofit/italo",
        "MYPROFIT_ANA_EMAIL": "ana.synthetic@fixture.test",
        "MYPROFIT_ANA_PASSWORD": "ana-password-fixture",
        "MYPROFIT_ANA_DESTINATION": "https://fixture.test/myprofit/ana",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_settings_model_fields_and_environment_are_profile_specific(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for field in MYPROFIT_FIELDS:
        monkeypatch.delenv(field, raising=False)
    monkeypatch.setenv("MYPROFIT_ITALO_EMAIL", "italo.env@fixture.test")
    monkeypatch.setenv("MYPROFIT_ITALO_PASSWORD", "italo-env-password")
    monkeypatch.setenv("MYPROFIT_ITALO_DESTINATION", "https://fixture.test/env/italo")
    monkeypatch.setenv("MYPROFIT_ANA_EMAIL", "ana.env@fixture.test")
    monkeypatch.setenv("MYPROFIT_ANA_PASSWORD", "ana-env-password")
    monkeypatch.setenv("MYPROFIT_ANA_DESTINATION", "https://fixture.test/env/ana")

    config = Settings(_env_file=None)

    assert set(Settings.model_fields) >= MYPROFIT_FIELDS
    assert config.MYPROFIT_ITALO_EMAIL == "italo.env@fixture.test"
    assert config.MYPROFIT_ANA_EMAIL == "ana.env@fixture.test"
    assert SecretStr("italo-env-password") == config.MYPROFIT_ITALO_PASSWORD
    assert SecretStr("ana-env-password") == config.MYPROFIT_ANA_PASSWORD
    assert config.MYPROFIT_ITALO_DESTINATION != config.MYPROFIT_ANA_DESTINATION


def test_italo_uses_italo_values_without_fallback() -> None:
    config = _settings(
        MYPROFIT_ANA_EMAIL="ana-only@fixture.test",
        MYPROFIT_ANA_PASSWORD="ana-only-password",
        MYPROFIT_ANA_DESTINATION="https://fixture.test/ana-only",
    )

    resolved = resolve_myprofit_profile_config(_profile("Italo"), config)

    assert isinstance(resolved, MyProfitProfileConfig)
    assert resolved.profile_key == "italo"
    assert resolved.email == "italo.synthetic@fixture.test"
    assert resolved.password.get_secret_value() == "italo-password-fixture"
    assert resolved.destination == "https://fixture.test/myprofit/italo"


def test_ana_alias_uses_only_ana_values() -> None:
    config = _settings(
        MYPROFIT_ITALO_EMAIL="italo-only@fixture.test",
        MYPROFIT_ITALO_PASSWORD="italo-only-password",
        MYPROFIT_ITALO_DESTINATION="https://fixture.test/italo-only",
    )

    resolved = resolve_myprofit_profile_config(_profile("Ana Livia"), config)

    assert resolved.profile_key == "ana"
    assert resolved.email == "ana.synthetic@fixture.test"
    assert resolved.password.get_secret_value() == "ana-password-fixture"
    assert resolved.destination == "https://fixture.test/myprofit/ana"


def test_incomplete_profile_fails_closed_without_fallback() -> None:
    config = _settings(
        MYPROFIT_ITALO_EMAIL="italo-only@fixture.test",
        MYPROFIT_ITALO_PASSWORD=None,
        MYPROFIT_ITALO_DESTINATION=None,
    )

    with pytest.raises(MyProfitConfigurationError) as caught:
        resolve_myprofit_profile_config(_profile("Italo"), config)

    assert caught.value.reason == "incomplete_configuration"
    assert "ana.synthetic" not in str(caught.value)


def test_family_rejected_before_lookup() -> None:
    calls = 0
    config = _settings(
        MYPROFIT_ITALO_EMAIL="family-marker@fixture.test",
        MYPROFIT_ITALO_PASSWORD="family-password-marker",
        MYPROFIT_ITALO_DESTINATION="https://fixture.test/family-marker",
    )

    with pytest.raises(MyProfitConfigurationError) as caught:
        resolve_myprofit_profile_config(_profile("Família", family=True), config)

    assert caught.value.reason == "household_read_only"
    assert calls == 0
    assert "family-marker" not in str(caught.value)


def test_unknown_profile_rejected() -> None:
    with pytest.raises(MyProfitConfigurationError) as caught:
        resolve_myprofit_profile_config(_profile("Outro"), _settings())

    assert caught.value.reason == "unknown_profile"


def test_secret_sanitization(caplog: pytest.LogCaptureFixture) -> None:
    email = "italo.private-marker@fixture.test"
    password = "italo-password-private-marker"
    destination = "https://fixture.test/private-destination-marker"
    config = _settings(
        MYPROFIT_ITALO_EMAIL=email,
        MYPROFIT_ITALO_PASSWORD=password,
        MYPROFIT_ITALO_DESTINATION=destination,
    )
    resolved = resolve_myprofit_profile_config(_profile("Italo"), config)

    with caplog.at_level(logging.INFO):
        logging.getLogger("f57-test").info("resolved=%r settings=%r", resolved, config)

    diagnostics = " ".join((repr(config), str(config), repr(resolved), caplog.text))
    assert email not in diagnostics
    assert password not in diagnostics
    assert destination not in diagnostics
    assert "<redacted>" in diagnostics


def test_env_example_placeholders_are_false() -> None:
    env_path = REPO_ROOT / ".env.example"
    entries = {
        line.split("=", 1)[0]: line.split("=", 1)[1]
        for line in env_path.read_text().splitlines()
        if line and not line.startswith("#") and "=" in line
    }

    assert set(entries) >= MYPROFIT_FIELDS
    assert len({entries[field] for field in MYPROFIT_FIELDS}) == 6
    assert entries["MYPROFIT_ITALO_EMAIL"].endswith("@example.invalid")
    assert entries["MYPROFIT_ANA_EMAIL"].endswith("@example.invalid")
    assert all(
        "example.invalid" in entries[field]
        or "myprofit.invalid" in entries[field]
        or "replace-with-" in entries[field]
        for field in MYPROFIT_FIELDS
    )

    config = Settings(_env_file=None, **entries)
    with pytest.raises(MyProfitConfigurationError) as caught:
        resolve_myprofit_profile_config(_profile("Italo"), config)
    assert caught.value.reason == "placeholder_configuration"


def test_docs_do_not_contain_secrets() -> None:
    readme = (REPO_ROOT / "README.md").read_text()

    for field in MYPROFIT_FIELDS:
        assert field in readme
    assert ".env" in readme
    assert "Família" in readme
    for marker in (
        "italo.private-marker",
        "italo-password-private-marker",
        "private-destination-marker",
    ):
        assert marker not in readme
