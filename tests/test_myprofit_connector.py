"""Offline fake-browser coverage for the MyProfit connector."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from omaha.config import Settings
from omaha.myprofit.connector import (
    _LOGIN_EMAIL_SELECTORS,
    _LOGIN_PASSWORD_SELECTORS,
    _LOGIN_SUBMIT_SELECTORS,
    LOGIN_URL,
    STOCK_DETAIL_URL,
    MyProfitConnectorError,
    MyProfitConnectorTimeouts,
    PlaywrightMyProfitConnector,
)

pytestmark = pytest.mark.unit


class FakeDownload:
    suggested_filename = "../positions.csv"

    def __init__(self, content: bytes = b"header\nrow\n") -> None:
        self.content = content

    def save_as(self, path: str) -> None:
        Path(path).write_bytes(self.content)


class FakeDownloadCapture:
    def __init__(self, download: FakeDownload) -> None:
        self.value = download

    def __enter__(self) -> FakeDownloadCapture:
        return self

    def __exit__(self, *_: object) -> None:
        return None


class FakeLocatorGroup:
    def __init__(self, locators: list[FakeLocator]) -> None:
        self.locators = locators

    def count(self) -> int:
        return len(self.locators)

    def nth(self, index: int) -> FakeLocator:
        return self.locators[index]

    @property
    def first(self) -> FakeLocator:
        return self.locators[0]

    @property
    def last(self) -> FakeLocator:
        return self.locators[-1]


class FakeLocator:
    def __init__(
        self,
        page: FakePage,
        name: str,
        *,
        visible: bool = False,
        timeout: bool = False,
        interaction_timeout: bool = False,
    ) -> None:
        self.page = page
        self.name = name
        self.visible = visible
        self.timeout = timeout
        self.interaction_timeout = interaction_timeout

    def wait_for(self, *, state: str, timeout: int) -> None:
        self.page.calls.append(("wait_for", self.name, state, timeout))
        if self.timeout or not self.visible:
            raise PlaywrightTimeoutError("fake timeout")

    def fill(self, value: str, *, timeout: int) -> None:
        self.page.calls.append(("fill", self.name, value, timeout))
        if self.interaction_timeout:
            raise PlaywrightTimeoutError("fake fill timeout")

    def click(self, *, timeout: int) -> None:
        self.page.calls.append(("click", self.name, timeout))
        if self.interaction_timeout:
            raise PlaywrightTimeoutError("fake click timeout")
        if self.name.startswith("submit"):
            self.page.authenticated = self.page.login_succeeds

    def is_visible(self, *, timeout: int) -> bool:
        self.page.calls.append(("is_visible", self.name, timeout))
        if self.name.startswith(("email", "password")):
            return self.visible and not self.page.authenticated
        return self.visible

    def count(self) -> int:
        return 1

    def nth(self, index: int) -> FakeLocator:
        if index != 0:
            raise IndexError(index)
        return self

    @property
    def first(self) -> FakeLocator:
        return self

    @property
    def last(self) -> FakeLocator:
        return self

    def filter(self, *, has_text: object) -> FakeLocator:
        return self


class FakePage:
    def __init__(
        self,
        *,
        prompt: str | None = None,
        login_succeeds: bool = True,
        login_timeout: bool = False,
        interaction_timeout: str | None = None,
        content: bytes = b"header\nrow\n",
        login_variant: str = "standard",
        two_factor_variant: str | None = None,
        duplicate_export: bool = False,
        duplicate_csv: bool = False,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.prompt = prompt
        self.login_succeeds = login_succeeds
        self.authenticated = False
        self.content = content
        self.login_timeout = login_timeout
        self.interaction_timeout = interaction_timeout
        self.login_variant = login_variant
        self.two_factor_variant = two_factor_variant or ("role" if prompt else None)
        self.duplicate_export = duplicate_export
        self.duplicate_csv = duplicate_csv

    def _login_locators(self, selectors: str) -> FakeLocatorGroup:
        if selectors == ", ".join(_LOGIN_EMAIL_SELECTORS):
            kind = "email"
        elif selectors == ", ".join(_LOGIN_PASSWORD_SELECTORS):
            kind = "password"
        elif selectors == ", ".join(_LOGIN_SUBMIT_SELECTORS):
            kind = "submit"
        else:
            raise AssertionError(f"unexpected login selector fallback: {selectors}")
        if self.login_variant == "fallback":
            return FakeLocatorGroup(
                [
                    FakeLocator(
                        self,
                        f"{kind}:primary",
                        visible=False,
                        interaction_timeout=self.interaction_timeout == kind,
                    ),
                    FakeLocator(
                        self,
                        f"{kind}:fallback",
                        visible=True,
                        interaction_timeout=self.interaction_timeout == kind,
                    ),
                ]
            )
        return FakeLocatorGroup(
            [
                FakeLocator(
                    self,
                    kind,
                    visible=True,
                    interaction_timeout=self.interaction_timeout == kind,
                )
            ]
        )

    def goto(self, url: str, *, wait_until: str, timeout: int) -> None:
        self.calls.append(("goto", url, wait_until, timeout))
        if self.login_timeout and url == LOGIN_URL:
            raise PlaywrightTimeoutError("fake login timeout")

    def locator(self, selector: str) -> FakeLocator:
        self.calls.append(("locator", selector))
        if selector in {
            ", ".join(_LOGIN_EMAIL_SELECTORS),
            ", ".join(_LOGIN_PASSWORD_SELECTORS),
            ", ".join(_LOGIN_SUBMIT_SELECTORS),
        }:
            return self._login_locators(selector)  # type: ignore[return-value]
        if selector == "button":
            return FakeLocator(
                self,
                "prompt:button-filter",
                visible=self.two_factor_variant == "button",
                interaction_timeout=self.interaction_timeout == "defer",
            )
        if selector == '[role="button"]':
            return FakeLocator(
                self,
                "prompt:role-button-filter",
                visible=self.two_factor_variant == "role-button",
                interaction_timeout=self.interaction_timeout == "defer",
            )
        values = {
            "#email": FakeLocator(
                self, "email", visible=True, interaction_timeout=self.interaction_timeout == "email"
            ),
            "#password": FakeLocator(
                self,
                "password",
                visible=True,
                interaction_timeout=self.interaction_timeout == "password",
            ),
            "#buttonLogin": FakeLocator(
                self,
                "submit",
                visible=True,
                interaction_timeout=self.interaction_timeout == "submit",
            ),
            'button[aria-label="Export"]': FakeLocator(
                self,
                "export",
                visible=True,
                interaction_timeout=self.interaction_timeout == "export",
            ),
        }
        if selector == 'button[aria-label="Export"]' and self.duplicate_export:
            return FakeLocatorGroup(  # type: ignore[return-value]
                [
                    FakeLocator(
                        self,
                        "export:first",
                        visible=True,
                        interaction_timeout=self.interaction_timeout == "export",
                    ),
                    FakeLocator(self, "export:second", visible=True),
                ]
            )
        return values.get(selector, FakeLocator(self, selector, visible=False))

    def wait_for_timeout(self, milliseconds: int) -> None:
        self.calls.append(("wait_for_timeout", milliseconds))

    def get_by_role(self, role: str, *, name: object) -> FakeLocator:
        self.calls.append(("get_by_role", role, str(name)))
        return FakeLocator(
            self,
            f"prompt:{self.prompt}",
            visible=self.two_factor_variant == "role",
            interaction_timeout=self.interaction_timeout == "defer",
        )

    def get_by_text(self, text: str, *, exact: bool) -> FakeLocator:
        self.calls.append(("get_by_text", text, exact))
        if text == "CSV":
            if self.duplicate_csv:
                return FakeLocatorGroup(  # type: ignore[return-value]
                    [
                        FakeLocator(self, "csv:first", visible=True),
                        FakeLocator(
                            self,
                            "csv:last",
                            visible=True,
                            interaction_timeout=self.interaction_timeout == "csv",
                        ),
                    ]
                )
            return FakeLocator(
                self,
                "csv",
                visible=True,
                interaction_timeout=self.interaction_timeout == "csv",
            )
        return FakeLocator(
            self,
            f"prompt:{text}",
            visible=self.two_factor_variant == text.lower(),
            interaction_timeout=self.interaction_timeout == "defer",
        )

    def expect_download(self, *, timeout: int) -> FakeDownloadCapture:
        self.calls.append(("expect_download", timeout))
        return FakeDownloadCapture(FakeDownload(self.content))


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self.pages = [page]
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        MYPROFIT_ITALO_EMAIL="italo.connector@fixture.test",
        MYPROFIT_ITALO_PASSWORD="connector-password-marker",
        MYPROFIT_ANA_EMAIL="ana.connector@fixture.test",
        MYPROFIT_ANA_PASSWORD="ana-password-marker",
    )


def _profile(name: str = "Italo", *, family: bool = False) -> SimpleNamespace:
    return SimpleNamespace(name=name, is_family_sentinel=family)


def _connector(
    page: FakePage,
    launcher_calls: list[tuple[str, dict[str, object]]],
    contexts: list[FakeContext] | None = None,
) -> PlaywrightMyProfitConnector:
    context = FakeContext(page)
    if contexts is not None:
        contexts.append(context)

    def launcher(path: str, **kwargs: object) -> FakeContext:
        launcher_calls.append((path, kwargs))
        return context

    return PlaywrightMyProfitConnector(
        config=_settings(),
        launcher=launcher,
        timeouts=MyProfitConnectorTimeouts(
            navigation_ms=10,
            login_settle_ms=1,
            two_factor_probe_ms=10,
            export_button_ms=10,
            csv_option_ms=10,
            download_ms=10,
        ),
    )


def test_download_flow() -> None:
    page = FakePage()
    launches: list[tuple[str, dict[str, object]]] = []

    result = _connector(page, launches).download_positions_csv(_profile())

    assert result.filename == "positions.csv"
    assert result.content == b"header\nrow\n"
    assert launches[0][1] == {"headless": True, "accept_downloads": True}
    assert [call for call in page.calls if call[0] == "goto"] == [
        ("goto", LOGIN_URL, "domcontentloaded", 10),
        ("goto", STOCK_DETAIL_URL, "domcontentloaded", 10),
    ]
    assert ("fill", "email", "italo.connector@fixture.test", 10) in page.calls
    assert ("fill", "password", "connector-password-marker", 10) in page.calls
    assert ("click", "submit", 10) in page.calls
    assert ("click", "export", 10) in page.calls
    assert ("get_by_text", "CSV", True) in page.calls
    assert ("click", "csv", 10) in page.calls
    assert not Path(launches[0][0]).exists()


def test_download_flow_emits_bounded_stage_telemetry(caplog: pytest.LogCaptureFixture) -> None:
    from omaha.myprofit.telemetry import telemetry_context

    page = FakePage()
    launches: list[tuple[str, dict[str, object]]] = []
    logger = logging.getLogger("omaha")
    logger.setLevel(logging.INFO)
    with telemetry_context("12345678-1234-4234-8234-123456789012"):
        _connector(page, launches).download_positions_csv(_profile())

    messages = [record.getMessage() for record in caplog.records if record.name == "omaha"]
    assert messages
    assert {"navigation", "login", "two_factor", "export", "download", "cleanup"} <= {
        dict(token.split("=", 1) for token in message.split()[1:])["stage"] for message in messages
    }
    assert all("connector-password-marker" not in message for message in messages)


@pytest.mark.parametrize("prompt", ["Mais tarde", "Later"])
def test_two_factor_defer(prompt: str) -> None:
    page = FakePage(prompt=prompt)
    launches: list[tuple[str, dict[str, object]]] = []

    _connector(page, launches).download_positions_csv(_profile())

    assert ("click", f"prompt:{prompt}", 10) in page.calls
    assert any(call[:2] == ("goto", STOCK_DETAIL_URL) for call in page.calls)


def test_missing_two_factor_prompt_continues_after_authentication() -> None:
    page = FakePage(prompt=None)
    launches: list[tuple[str, dict[str, object]]] = []

    _connector(page, launches).download_positions_csv(_profile())

    assert not any(call[0] == "click" and "prompt" in str(call) for call in page.calls)
    assert any(call[:2] == ("goto", STOCK_DETAIL_URL) for call in page.calls)


def test_login_fallback_selectors_find_alternate_dom_controls() -> None:
    page = FakePage(login_variant="fallback")
    launches: list[tuple[str, dict[str, object]]] = []

    _connector(page, launches).download_positions_csv(_profile())

    assert any(
        call[:3] == ("fill", "email:fallback", "italo.connector@fixture.test")
        for call in page.calls
    )
    assert any(
        call[:3] == ("fill", "password:fallback", "connector-password-marker")
        for call in page.calls
    )
    assert ("click", "submit:fallback", 10) in page.calls
    assert not any("primary" in str(call) and call[0] in {"fill", "click"} for call in page.calls)


def test_two_factor_fallback_finds_button_filter_control() -> None:
    page = FakePage(prompt="Mais tarde", two_factor_variant="button")
    launches: list[tuple[str, dict[str, object]]] = []

    _connector(page, launches).download_positions_csv(_profile())

    assert ("click", "prompt:button-filter", 10) in page.calls
    assert any(call[:2] == ("goto", STOCK_DETAIL_URL) for call in page.calls)


def test_duplicate_export_and_csv_controls_use_first_and_last() -> None:
    page = FakePage(duplicate_export=True, duplicate_csv=True)
    launches: list[tuple[str, dict[str, object]]] = []

    _connector(page, launches).download_positions_csv(_profile())

    assert ("click", "export:first", 10) in page.calls
    assert ("click", "csv:last", 10) in page.calls
    assert ("click", "export:second", 10) not in page.calls
    assert not any(call[0] == "click" and call[1] == "csv:first" for call in page.calls)


def test_unconfirmed_authentication_fails_before_export() -> None:
    page = FakePage(login_succeeds=False)
    launches: list[tuple[str, dict[str, object]]] = []

    with pytest.raises(MyProfitConnectorError) as caught:
        _connector(page, launches).download_positions_csv(_profile())

    assert (caught.value.stage, caught.value.code) == ("two_factor", "authentication_unconfirmed")
    assert not any(call[0] == "goto" and call[1] == STOCK_DETAIL_URL for call in page.calls)
    assert not any(call[0] == "click" and call[1] == "export" for call in page.calls)
    assert not Path(launches[0][0]).exists()


def test_family_rejected_before_launcher(monkeypatch: pytest.MonkeyPatch) -> None:
    launches: list[tuple[str, dict[str, object]]] = []

    def unexpected_resolution(*_: object, **__: object) -> None:
        raise AssertionError("family must not resolve credentials")

    monkeypatch.setattr(
        "omaha.myprofit.connector.resolve_myprofit_profile_config", unexpected_resolution
    )

    with pytest.raises(MyProfitConnectorError) as caught:
        PlaywrightMyProfitConnector(
            launcher=lambda *_args, **_kwargs: launches.append(())
        ).download_positions_csv(_profile("Família", family=True))

    assert (caught.value.stage, caught.value.code) == ("credentials", "household_read_only")
    assert launches == []


def test_missing_credentials_never_launches() -> None:
    launches: list[tuple[str, dict[str, object]]] = []
    connector = PlaywrightMyProfitConnector(
        config=Settings(_env_file=None),
        launcher=lambda path, **kwargs: launches.append((path, kwargs)),
    )

    with pytest.raises(MyProfitConnectorError) as caught:
        connector.download_positions_csv(_profile())

    assert (caught.value.stage, caught.value.code) == ("credentials", "incomplete_configuration")
    assert launches == []


def test_timeout_cleanup_and_error_are_sanitized() -> None:
    page = FakePage(login_timeout=True)
    launches: list[tuple[str, dict[str, object]]] = []

    with pytest.raises(MyProfitConnectorError) as caught:
        _connector(page, launches).download_positions_csv(_profile())

    assert (caught.value.stage, caught.value.code) == ("login", "timeout")
    assert "connector-password-marker" not in str(caught.value)
    assert "fixture.test" not in repr(caught.value)
    assert not Path(launches[0][0]).exists()


@pytest.mark.parametrize(
    ("interaction", "stage"),
    [
        ("email", "login"),
        ("password", "login"),
        ("submit", "login"),
        ("defer", "two_factor"),
        ("export", "export"),
        ("csv", "download"),
    ],
)
def test_each_playwright_interaction_uses_stage_timeout_and_cleans_up(
    interaction: str,
    stage: str,
) -> None:
    page = FakePage(
        prompt="Mais tarde" if interaction == "defer" else None, interaction_timeout=interaction
    )
    launches: list[tuple[str, dict[str, object]]] = []
    contexts: list[FakeContext] = []

    with pytest.raises(MyProfitConnectorError) as caught:
        _connector(page, launches, contexts).download_positions_csv(_profile())

    assert (caught.value.stage, caught.value.code) == (stage, "timeout")
    if interaction in {"email", "password", "submit", "defer", "export"}:
        expected_timeout = 10
    else:
        expected_timeout = 10
    interaction_call = next(
        call
        for call in page.calls
        if call[0] in {"fill", "click"}
        and call[1]
        in {
            "email",
            "password",
            "submit",
            "prompt:Mais tarde",
            "export",
            "csv",
        }
        and ((interaction == "defer" and call[1] == "prompt:Mais tarde") or call[1] == interaction)
    )
    assert interaction_call[-1] == expected_timeout
    assert contexts[0].closed
    assert not Path(launches[0][0]).exists()


def test_connector_timeout_configuration_is_immutable() -> None:
    timeouts = MyProfitConnectorTimeouts()

    with pytest.raises(AttributeError):
        timeouts.navigation_ms = 1  # type: ignore[misc]


@pytest.mark.parametrize(
    "field",
    [
        "navigation_ms",
        "login_settle_ms",
        "two_factor_probe_ms",
        "export_button_ms",
        "csv_option_ms",
        "download_ms",
    ],
)
@pytest.mark.parametrize("value", [0, -1])
def test_non_positive_timeout_is_rejected_before_browser_use(field: str, value: int) -> None:
    timeout_values = {
        "navigation_ms": 10,
        "login_settle_ms": 10,
        "two_factor_probe_ms": 10,
        "export_button_ms": 10,
        "csv_option_ms": 10,
        "download_ms": 10,
    }
    timeout_values[field] = value
    launches: list[tuple[str, dict[str, object]]] = []

    with pytest.raises(ValueError, match="must be positive"):
        PlaywrightMyProfitConnector(
            config=_settings(),
            launcher=lambda path, **kwargs: launches.append((path, kwargs)),
            timeouts=MyProfitConnectorTimeouts(**timeout_values),
        )

    assert launches == []
