"""Offline-testable Playwright boundary for MyProfit position CSV downloads."""

from __future__ import annotations

import re
import shutil
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from cloakbrowser import launch_persistent_context as _launch_persistent_context
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from omaha.config import (
    MyProfitConfigurationError,
    MyProfitProfileConfig,
    Settings,
    resolve_myprofit_profile_config,
)
from omaha.myprofit.telemetry import current_recorder, stage_span

LOGIN_URL = "https://myprofitweb.com/Login.aspx"
STOCK_DETAIL_URL = "https://myprofitweb.com/App/StockDetail.aspx"

_TWO_FACTOR_PATTERN = re.compile(r"^(Mais tarde|Later)$", re.IGNORECASE)
_LOGIN_EMAIL_SELECTORS = (
    "#email",
    'input[type="email"]',
    'input[autocomplete="username"]',
    'input[name*="email" i]',
    'input[name*="user" i]',
)
_LOGIN_PASSWORD_SELECTORS = (
    "#password",
    'input[type="password"]',
    'input[autocomplete="current-password"]',
)
_LOGIN_SUBMIT_SELECTORS = (
    "#buttonLogin",
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Entrar")',
    'button:has-text("Login")',
    'button:has-text("Sign in")',
)
_Launcher = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class MyProfitCsvDownload:
    """In-memory connector result with no persistence or parser coupling."""

    filename: str
    content: bytes


@dataclass(frozen=True, slots=True)
class MyProfitConnectorTimeouts:
    """Per-stage Playwright timeouts in milliseconds."""

    navigation_ms: int = 45_000
    login_settle_ms: int = 5_000
    two_factor_probe_ms: int = 30_000
    export_button_ms: int = 30_000
    csv_option_ms: int = 10_000
    download_ms: int = 45_000

    def __post_init__(self) -> None:
        values = (
            self.navigation_ms,
            self.login_settle_ms,
            self.two_factor_probe_ms,
            self.export_button_ms,
            self.csv_option_ms,
            self.download_ms,
        )
        if any(value <= 0 for value in values):
            raise ValueError("connector timeouts must be positive")


class MyProfitConnectorError(RuntimeError):
    """Stable stage/code error that never includes browser or secret details."""

    def __init__(self, stage: str, code: str) -> None:
        self.stage = stage
        self.code = code
        super().__init__(f"myprofit connector error: {stage}/{code}")

    def __repr__(self) -> str:
        return f"MyProfitConnectorError(stage={self.stage!r}, code={self.code!r})"


class MyProfitConnector(Protocol):
    """Narrow profile-to-CSV connector contract."""

    def download_positions_csv(self, profile: Any) -> MyProfitCsvDownload:
        """Download current positions for one real active profile."""
        ...


class PlaywrightMyProfitConnector:
    """Download MyProfit positions through an injected browser launcher."""

    def __init__(
        self,
        *,
        config: Settings | None = None,
        launcher: _Launcher = _launch_persistent_context,
        timeouts: MyProfitConnectorTimeouts | None = None,
    ) -> None:
        self._config = config
        self._launcher = launcher
        self._timeouts = timeouts or MyProfitConnectorTimeouts()

    def download_positions_csv(self, profile: Any) -> MyProfitCsvDownload:
        """Resolve a guarded profile, then return downloaded CSV bytes."""
        recorder = current_recorder()
        job_id = recorder.job_id if recorder is not None and recorder.job_id is not None else ""
        with stage_span(job_id, domain="connector", stage="credentials"):
            if getattr(profile, "is_family_sentinel", False):
                raise MyProfitConnectorError("credentials", "household_read_only")

        try:
            with stage_span(job_id, domain="connector", stage="credentials"):
                credentials = resolve_myprofit_profile_config(profile, self._config)
        except MyProfitConfigurationError as error:
            raise MyProfitConnectorError("credentials", error.reason) from None

        root = Path(tempfile.mkdtemp(prefix="omaha-myprofit-"))
        profile_dir = root / "browser-profile"
        download_dir = root / "downloads"
        context: Any | None = None
        operation_error: MyProfitConnectorError | None = None
        try:
            with stage_span(job_id, domain="browser", stage="browser"):
                try:
                    context = self._launcher(
                        str(profile_dir),
                        headless=True,
                        accept_downloads=True,
                    )
                except PlaywrightTimeoutError:
                    raise MyProfitConnectorError("browser", "timeout") from None
                except PlaywrightError:
                    raise MyProfitConnectorError("browser", "launch_failed") from None
                except Exception:
                    raise MyProfitConnectorError("browser", "launch_failed") from None

            with stage_span(job_id, domain="browser", stage="browser"):
                try:
                    page = context.pages[0] if context.pages else context.new_page()
                except Exception:
                    raise MyProfitConnectorError("browser", "page_failed") from None

            result = self._download_from_page(page, credentials, download_dir)
            return result
        except MyProfitConnectorError as error:
            operation_error = error
            raise
        finally:
            cleanup_error: MyProfitConnectorError | None = None
            cleanup_started = time.perf_counter()
            if context is not None:
                try:
                    context.close()
                except Exception:
                    cleanup_error = MyProfitConnectorError("cleanup", "browser_close_failed")
            try:
                shutil.rmtree(root)
            except Exception:
                cleanup_error = MyProfitConnectorError("cleanup", "temporary_files_failed")
            if current_recorder() is not None:
                recorder = current_recorder()
                assert recorder is not None
                recorder.stage(
                    domain="browser",
                    status="failed" if cleanup_error is not None else "succeeded",
                    stage="cleanup",
                    code=cleanup_error.code if cleanup_error is not None else "success",
                    duration_ms=(time.perf_counter() - cleanup_started) * 1000,
                )
            if cleanup_error is not None and operation_error is None:
                raise cleanup_error

    def _download_from_page(
        self,
        page: Any,
        credentials: MyProfitProfileConfig,
        download_dir: Path,
    ) -> MyProfitCsvDownload:
        recorder = current_recorder()
        job_id = recorder.job_id if recorder is not None and recorder.job_id is not None else ""
        try:
            with stage_span(job_id, domain="browser", stage="navigation"):
                page.goto(
                    LOGIN_URL, wait_until="domcontentloaded", timeout=self._timeouts.navigation_ms
                )
            with stage_span(job_id, domain="connector", stage="login"):
                email = _first_visible(page, _LOGIN_EMAIL_SELECTORS, self._timeouts.navigation_ms)
                password = _first_visible(
                    page, _LOGIN_PASSWORD_SELECTORS, self._timeouts.navigation_ms
                )
                submit = _first_visible(page, _LOGIN_SUBMIT_SELECTORS, self._timeouts.navigation_ms)
                if email is None or password is None or submit is None:
                    raise MyProfitConnectorError("login", "controls_not_found")
                email.fill(credentials.email, timeout=self._timeouts.navigation_ms)
                password.fill(
                    credentials.password.get_secret_value(),
                    timeout=self._timeouts.navigation_ms,
                )
                submit.click(timeout=self._timeouts.navigation_ms)
                page.wait_for_timeout(self._timeouts.login_settle_ms)
        except PlaywrightTimeoutError:
            raise MyProfitConnectorError("login", "timeout") from None
        except PlaywrightError:
            raise MyProfitConnectorError("login", "browser_failed") from None
        except Exception:
            raise MyProfitConnectorError("login", "failed") from None

        try:
            with stage_span(job_id, domain="connector", stage="two_factor"):
                defer_control = self._find_two_factor_defer(page)
                if defer_control is not None:
                    defer_control.click(timeout=self._timeouts.two_factor_probe_ms)
                if email.is_visible(timeout=self._timeouts.two_factor_probe_ms) or (
                    password.is_visible(timeout=self._timeouts.two_factor_probe_ms)
                ):
                    raise MyProfitConnectorError("two_factor", "authentication_unconfirmed")
        except MyProfitConnectorError:
            raise
        except PlaywrightTimeoutError:
            raise MyProfitConnectorError("two_factor", "timeout") from None
        except PlaywrightError:
            raise MyProfitConnectorError("two_factor", "browser_failed") from None
        except Exception:
            raise MyProfitConnectorError("two_factor", "failed") from None

        try:
            with stage_span(job_id, domain="browser", stage="navigation"):
                page.goto(
                    STOCK_DETAIL_URL,
                    wait_until="domcontentloaded",
                    timeout=self._timeouts.navigation_ms,
                )
        except PlaywrightTimeoutError:
            raise MyProfitConnectorError("navigation", "timeout") from None
        except PlaywrightError:
            raise MyProfitConnectorError("navigation", "browser_failed") from None
        except Exception:
            raise MyProfitConnectorError("navigation", "failed") from None

        export_button = page.locator('button[aria-label="Export"]').first
        try:
            with stage_span(job_id, domain="connector", stage="export"):
                export_button.wait_for(state="visible", timeout=self._timeouts.export_button_ms)
                export_button.click(timeout=self._timeouts.export_button_ms)
        except PlaywrightTimeoutError:
            raise MyProfitConnectorError("export", "timeout") from None
        except PlaywrightError:
            raise MyProfitConnectorError("export", "browser_failed") from None
        except Exception:
            raise MyProfitConnectorError("export", "failed") from None

        csv_option = page.get_by_text("CSV", exact=True).last
        try:
            with stage_span(job_id, domain="connector", stage="export"):
                csv_option.wait_for(state="visible", timeout=self._timeouts.csv_option_ms)
        except PlaywrightTimeoutError:
            raise MyProfitConnectorError("export", "timeout") from None
        except PlaywrightError:
            raise MyProfitConnectorError("export", "browser_failed") from None
        except Exception:
            raise MyProfitConnectorError("export", "failed") from None

        try:
            with stage_span(job_id, domain="connector", stage="download"):
                download_dir.mkdir(parents=True, exist_ok=True)
                with page.expect_download(timeout=self._timeouts.download_ms) as download_info:
                    csv_option.click(timeout=self._timeouts.csv_option_ms)
        except PlaywrightTimeoutError:
            raise MyProfitConnectorError("download", "timeout") from None
        except PlaywrightError:
            raise MyProfitConnectorError("download", "browser_failed") from None
        except Exception:
            raise MyProfitConnectorError("download", "failed") from None

        try:
            with stage_span(job_id, domain="connector", stage="download"):
                download = download_info.value
                filename = Path(download.suggested_filename).name or "export.csv"
                destination = download_dir / filename
                download.save_as(str(destination))
                content = destination.read_bytes()
                if not content:
                    raise MyProfitConnectorError("download", "empty_file")
                return MyProfitCsvDownload(filename=filename, content=content)
        except MyProfitConnectorError:
            raise
        except (OSError, ValueError):
            raise MyProfitConnectorError("download", "file_failed") from None
        except Exception:
            raise MyProfitConnectorError("download", "failed") from None

    def _find_two_factor_defer(self, page: Any) -> Any | None:
        candidates = (
            page.get_by_role("button", name=_TWO_FACTOR_PATTERN),
            page.locator("button").filter(has_text=_TWO_FACTOR_PATTERN),
            page.locator('[role="button"]').filter(has_text=_TWO_FACTOR_PATTERN),
            page.get_by_text("Mais tarde", exact=True),
            page.get_by_text("Later", exact=True),
        )
        deadline = time.monotonic() + self._timeouts.two_factor_probe_ms / 1000
        while True:
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            for candidate in candidates:
                for index in range(candidate.count() - 1, -1, -1):
                    control = candidate.nth(index)
                    try:
                        if control.is_visible(timeout=min(200, max(1, remaining_ms))):
                            return control
                    except PlaywrightTimeoutError:
                        continue
            if remaining_ms <= 0:
                return None
            page.wait_for_timeout(min(200, remaining_ms))


def _first_visible(page: Any, selectors: tuple[str, ...], timeout_ms: int) -> Any | None:
    locator = page.locator(", ".join(selectors))
    deadline = time.monotonic() + timeout_ms / 1000
    while True:
        remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
        for index in range(locator.count()):
            candidate = locator.nth(index)
            try:
                if candidate.is_visible(timeout=min(200, max(1, remaining_ms))):
                    return candidate
            except PlaywrightTimeoutError:
                continue
        if remaining_ms <= 0:
            return None
        page.wait_for_timeout(min(200, remaining_ms))


__all__ = [
    "LOGIN_URL",
    "STOCK_DETAIL_URL",
    "MyProfitConnector",
    "MyProfitConnectorError",
    "MyProfitConnectorTimeouts",
    "MyProfitCsvDownload",
    "PlaywrightMyProfitConnector",
]
