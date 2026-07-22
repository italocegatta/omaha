"""Offline contract tests for the owner-gated MyProfit PoC."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from omaha.config import Settings
from scripts.myprofit_poc import (
    LOGIN_URL,
    MYPROFIT_URL,
    SELECTOR_CSV_ITEM,
    SELECTOR_EMAIL,
    SELECTOR_EXPORT_BTN,
    SELECTOR_LOGIN_BTN,
    SELECTOR_PASSWORD,
    STOCK_DETAIL_URL,
    LoginCheckpoint,
    MyProfitCredentials,
    MyProfitPocError,
    _login_step_fill_and_submit,
    _login_step_verify_redirect,
    load_credentials,
    run_login_flow,
    save_and_validate_download,
    validate_csv_bytes,
    validate_csv_file,
)

pytestmark = pytest.mark.unit

# ── Credential tests ──────────────────────────────────────────────────────


def test_missing_credentials_fail_without_exposing_values() -> None:
    secret = "super-secret-value"
    with pytest.raises(MyProfitPocError, match="MYPROFIT_EMAIL") as error:
        load_credentials(Settings(MYPROFIT_EMAIL=None, MYPROFIT_PASSWORD=secret))

    assert secret not in str(error.value)


def test_credentials_are_loaded_without_normalizing_password() -> None:
    credentials = load_credentials(
        Settings(MYPROFIT_EMAIL="  operator@example.test ", MYPROFIT_PASSWORD=" p@ss ")
    )

    assert credentials == MyProfitCredentials("operator@example.test", " p@ss ")


# ── CSV validation tests ──────────────────────────────────────────────────


def test_csv_bytes_use_existing_parser() -> None:
    csv_bytes = b"Ticker,Name,Qty,Avg Price,Current Price\nAAPL,AAPL,1,2,3\n"

    positions = validate_csv_bytes(csv_bytes)

    assert len(positions) == 1
    assert positions[0].broker_ticker == "AAPL"


def test_empty_invalid_and_unrecognized_csv_fail() -> None:
    with pytest.raises(MyProfitPocError, match="empty"):
        validate_csv_bytes(b"")
    with pytest.raises(MyProfitPocError, match="UTF-8"):
        validate_csv_bytes(b"\xff")
    with pytest.raises(MyProfitPocError, match="recognized positions"):
        validate_csv_bytes(b"not,a,position\n")


def test_csv_file_reads_only_supplied_path(tmp_path: Path) -> None:
    path = tmp_path / "positions.csv"
    path.write_bytes(b"Ticker,Name,Qty,Avg Price,Current Price\nAAPL,AAPL,1,2,3\n")

    positions = validate_csv_file(path)

    assert len(positions) == 1
    assert path.exists()


# ── Download save+validate tests ──────────────────────────────────────────


def test_save_and_validate_download_writes_validates_and_removes(
    tmp_path: Path,
) -> None:
    csv_bytes = b"Ticker,Name,Qty,Avg Price,Current Price\nPETR4,PETR4,100,25,30\n"

    positions, raw = save_and_validate_download(csv_bytes, work_dir=tmp_path)

    assert len(positions) == 1
    assert positions[0].broker_ticker == "PETR4"
    assert raw == csv_bytes
    # Temp file should be cleaned up.
    remaining = list(tmp_path.iterdir())
    assert not any(f.name == "myprofit_export.csv" for f in remaining)


def test_save_and_validate_download_empty_raises(tmp_path: Path) -> None:
    with pytest.raises(MyProfitPocError, match="empty"):
        save_and_validate_download(b"", work_dir=tmp_path)


def test_save_and_validate_download_uses_default_temp_dir() -> None:
    csv_bytes = b"Ticker,Name,Qty,Avg Price,Current Price\nAAPL,AAPL,1,2,3\n"

    # Should not raise — uses system temp dir.
    positions, raw = save_and_validate_download(csv_bytes)
    assert len(positions) == 1
    assert raw == csv_bytes


# ── Selector constant tests ──────────────────────────────────────────────


def test_selectors_match_expected_myprofit_markup() -> None:
    """Smoke-check that selectors are non-empty and have expected shapes."""
    assert SELECTOR_EMAIL == "#email"
    assert SELECTOR_PASSWORD == "#password"
    assert SELECTOR_LOGIN_BTN == "#buttonLogin"
    assert SELECTOR_EXPORT_BTN == 'button[aria-label="Export"]'
    assert SELECTOR_CSV_ITEM == 'a.dropdown-item[data-type="csv"]'
    assert MYPROFIT_URL == "https://myprofitweb.com"
    assert f"{MYPROFIT_URL}/Login.aspx" == LOGIN_URL
    assert f"{MYPROFIT_URL}/App/StockDetail.aspx" == STOCK_DETAIL_URL


# ── LoginCheckpoint dataclass tests ───────────────────────────────────────


def test_login_checkpoint_fields() -> None:
    cp = LoginCheckpoint(
        step="test_step",
        message="test message",
        url="https://example.com/App/",
        modal_seen=True,
    )
    assert cp.step == "test_step"
    assert cp.message == "test message"
    assert cp.url == "https://example.com/App/"
    assert cp.modal_seen is True


def test_login_checkpoint_modal_seen_defaults_false() -> None:
    cp = LoginCheckpoint(step="s", message="m", url="u")
    assert cp.modal_seen is False


# ── Playwright step tests (mocked page, no network) ──────────────────────


def _make_mock_page(url: str = "https://myprofitweb.com/App/Dashboard") -> MagicMock:
    """Build a mock Playwright Page that records calls."""
    page = MagicMock()
    page.url = url
    page.wait_for_load_state = MagicMock()
    page.goto = MagicMock()
    page.fill = MagicMock()
    page.click = MagicMock()
    page.wait_for_selector = MagicMock()
    page.wait_for_url = MagicMock()
    page.query_selector = MagicMock(return_value=None)  # no modal by default
    return page


def test_login_step_fill_and_submit_calls_correct_selectors() -> None:
    page = _make_mock_page()
    creds = MyProfitCredentials(email="user@test.com", password="s3cret")

    checkpoint = _login_step_fill_and_submit(page, creds)

    page.goto.assert_called_once_with(LOGIN_URL)
    page.fill.assert_any_call(SELECTOR_EMAIL, "user@test.com")
    page.fill.assert_any_call(SELECTOR_PASSWORD, "s3cret")
    page.click.assert_called_once_with(SELECTOR_LOGIN_BTN)
    assert checkpoint.step == "credentials_submitted"
    assert "user@test.com" not in checkpoint.message
    assert "s3cret" not in checkpoint.message


def test_login_step_verify_redirect_checks_url_and_modal_absent() -> None:
    page = _make_mock_page(url="https://myprofitweb.com/App/Dashboard")

    checkpoint = _login_step_verify_redirect(page)

    assert checkpoint.step == "authenticated"
    assert checkpoint.modal_seen is False
    page.query_selector.assert_called_once()
    page.click.assert_not_called()  # no modal to dismiss


def test_login_step_verify_redirect_dismisses_modal_when_present() -> None:
    page = _make_mock_page(url="https://myprofitweb.com/App/Dashboard")
    mock_modal = MagicMock()
    page.query_selector = MagicMock(return_value=mock_modal)

    checkpoint = _login_step_verify_redirect(page)

    assert checkpoint.step == "authenticated"
    assert checkpoint.modal_seen is True
    page.click.assert_called_once()  # clicked "Mais tarde"


def test_login_step_verify_redirect_wrong_url_raises() -> None:
    page = _make_mock_page(url="https://myprofitweb.com/Login.aspx")

    with pytest.raises(AssertionError, match="Expected /App/"):
        _login_step_verify_redirect(page)


# ── run_login_flow tests (mocked Playwright, no network) ─────────────────


def test_run_login_flow_returns_two_checkpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    """Full flow returns credentials_submitted + authenticated checkpoints."""
    mock_page = _make_mock_page(url="https://myprofitweb.com/App/Dashboard")
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_sync = MagicMock()
    mock_sync.__enter__ = MagicMock(return_value=mock_pw)
    mock_sync.__exit__ = MagicMock(return_value=False)

    monkeypatch.setattr(
        "playwright.sync_api.sync_playwright",
        MagicMock(return_value=mock_sync),
    )

    creds = MyProfitCredentials(email="a@b.com", password="pw")
    checkpoints = run_login_flow(creds, headless=True)

    assert len(checkpoints) == 2
    assert checkpoints[0].step == "credentials_submitted"
    assert checkpoints[1].step == "authenticated"
    mock_browser.close.assert_called()


def test_run_login_flow_cleans_up_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Browser is closed even when login step raises."""
    mock_page = _make_mock_page()
    mock_page.fill.side_effect = RuntimeError("selector not found")
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page

    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_sync = MagicMock()
    mock_sync.__enter__ = MagicMock(return_value=mock_pw)
    mock_sync.__exit__ = MagicMock(return_value=False)

    monkeypatch.setattr(
        "playwright.sync_api.sync_playwright",
        MagicMock(return_value=mock_sync),
    )

    creds = MyProfitCredentials(email="a@b.com", password="pw")
    with pytest.raises(RuntimeError, match="selector not found"):
        run_login_flow(creds, headless=True)

    mock_browser.close.assert_called()


def test_run_login_flow_does_not_access_real_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify no real Playwright is instantiated — all calls go through mocks."""
    real_sync_playwright_called = False

    def _guard(*args, **kwargs):
        nonlocal real_sync_playwright_called
        real_sync_playwright_called = True
        raise AssertionError("Real sync_playwright must not be called in offline tests")

    monkeypatch.setattr("playwright.sync_api.sync_playwright", _guard)

    creds = MyProfitCredentials(email="a@b.com", password="pw")
    with pytest.raises(AssertionError, match="must not be called"):
        run_login_flow(creds)

    assert real_sync_playwright_called
