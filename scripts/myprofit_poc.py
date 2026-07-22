"""Owner-gated MyProfit PoC: Playwright login, modal handling, CSV capture.

Each external step pauses for owner verification before proceeding.
Credentials are never logged, printed, or stored in artifacts.
"""

from __future__ import annotations

import sys
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from omaha.config import Settings
from omaha.csv_import import RawPosition, parse_positions

# ---------------------------------------------------------------------------
# Selectors — observed from MyProfit markup; centralised for easy update.
# ---------------------------------------------------------------------------
MYPROFIT_URL = "https://myprofitweb.com"
LOGIN_URL = f"{MYPROFIT_URL}/Login.aspx"
SELECTOR_EMAIL = "#email"
SELECTOR_PASSWORD = "#password"
SELECTOR_LOGIN_BTN = "#buttonLogin"
SELECTOR_2FA_MODAL_TEXT = "text=+ Segurança pra você!"
SELECTOR_2FA_DISMISS = "button.bootbox-cancel:has-text('Mais tarde')"
SELECTOR_EXPORT_BTN = 'button[aria-label="Export"]'
SELECTOR_CSV_ITEM = 'a.dropdown-item[data-type="csv"]'
STOCK_DETAIL_URL = f"{MYPROFIT_URL}/App/StockDetail.aspx"


class MyProfitPocError(RuntimeError):
    """Safe, user-facing failure without credential or CSV contents."""


@dataclass(frozen=True)
class MyProfitCredentials:
    email: str
    password: str


@dataclass(frozen=True)
class LoginCheckpoint:
    """Result of a login step that requires owner verification."""

    step: str
    message: str
    url: str
    modal_seen: bool = False


# --- Credential helpers ---------------------------------------------------


def load_credentials(settings: Settings | None = None) -> MyProfitCredentials:
    """Load required credentials without exposing their values."""
    source = settings or Settings()
    email = (source.MYPROFIT_EMAIL or "").strip()
    password = source.MYPROFIT_PASSWORD or ""
    if not email or not password:
        raise MyProfitPocError(
            "Configure MYPROFIT_EMAIL and MYPROFIT_PASSWORD in .env before "
            "running the MyProfit PoC."
        )
    return MyProfitCredentials(email=email, password=password)


# --- CSV validation -------------------------------------------------------


def validate_csv_bytes(csv_bytes: bytes) -> tuple[RawPosition, ...]:
    """Decode and parse downloaded bytes, rejecting unusable files."""
    if not csv_bytes:
        raise MyProfitPocError("MyProfit export is empty.")
    try:
        text = csv_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise MyProfitPocError("MyProfit export is not valid UTF-8.") from None

    positions = tuple(parse_positions(text))
    if not positions:
        raise MyProfitPocError("MyProfit export contains no recognized positions.")
    return positions


def validate_csv_file(path: Path) -> tuple[RawPosition, ...]:
    """Validate an already-captured file without writing to Omaha storage."""
    try:
        csv_bytes = path.read_bytes()
    except OSError:
        raise MyProfitPocError("MyProfit export could not be read.") from None
    return validate_csv_bytes(csv_bytes)


# --- Download capture (temp-only, no persistence) -------------------------


def save_and_validate_download(
    download_bytes: bytes,
    *,
    work_dir: Path | None = None,
) -> tuple[RawPosition, bytes]:
    """Save download to temp dir, validate, clean up. Returns (positions, raw_bytes)."""
    if not download_bytes:
        raise MyProfitPocError("Download is empty — no file captured.")

    target_dir = work_dir or Path(tempfile.mkdtemp(prefix="omaha_myprofit_"))
    tmp_file = target_dir / "myprofit_export.csv"
    try:
        tmp_file.write_bytes(download_bytes)
        positions = validate_csv_file(tmp_file)
    finally:
        with suppress(OSError):
            tmp_file.unlink(missing_ok=True)
    return positions, download_bytes


# --- Playwright login flow with owner gates --------------------------------


def _login_step_fill_and_submit(
    page: object,
    credentials: MyProfitCredentials,
) -> LoginCheckpoint:
    """Navigate to login page, fill credentials, click submit.

    ``page`` must be a Playwright Page instance.  Separated from the
    browser lifecycle so tests can inject a mock/stub.
    """
    page.goto(LOGIN_URL)  # type: ignore[union-attr]
    page.wait_for_selector(SELECTOR_EMAIL)  # type: ignore[union-attr]

    page.fill(SELECTOR_EMAIL, credentials.email)  # type: ignore[union-attr]
    page.fill(SELECTOR_PASSWORD, credentials.password)  # type: ignore[union-attr]
    page.click(SELECTOR_LOGIN_BTN)  # type: ignore[union-attr]
    page.wait_for_load_state("domcontentloaded")  # type: ignore[union-attr]

    return LoginCheckpoint(
        step="credentials_submitted",
        message=(
            "Credentials submitted. Verify in the browser that the login page "
            "received the correct e-mail and password."
        ),
        url=page.url,  # type: ignore[union-attr]
    )


def _login_step_verify_redirect(page: object) -> LoginCheckpoint:
    """Wait for authenticated redirect and handle optional 2FA modal.

    ``page`` must be a Playwright Page instance.
    """
    page.wait_for_url("**/App/**", timeout=30_000)  # type: ignore[union-attr]
    assert "/App/" in page.url, f"Expected /App/ in URL, got: {page.url}"  # type: ignore[union-attr]  # nosec B101

    # Optional 2FA setup modal — short timeout, not an error if absent.
    modal_seen = False
    modal = page.query_selector(SELECTOR_2FA_MODAL_TEXT)  # type: ignore[union-attr]
    if modal:
        page.click(SELECTOR_2FA_DISMISS, timeout=5_000)  # type: ignore[union-attr]
        page.wait_for_load_state("domcontentloaded")  # type: ignore[union-attr]
        modal_seen = True

    return LoginCheckpoint(
        step="authenticated",
        message=(
            "Login succeeded. Verify the browser shows the MyProfit dashboard. "
            + ("2FA modal was dismissed." if modal_seen else "No 2FA modal appeared.")
        ),
        url=page.url,  # type: ignore[union-attr]
        modal_seen=modal_seen,
    )


def run_login_flow(
    credentials: MyProfitCredentials,
    *,
    headless: bool = False,
) -> list[LoginCheckpoint]:
    """Execute the full Playwright login flow (no export).

    Returns the list of checkpoints. Caller is responsible for presenting
    gates to the owner between steps if desired.  This function runs the
    full flow in one call — suitable for the interactive CLI where the
    script itself manages the gates.

    Raises ``MyProfitPocError`` on any Playwright failure.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise MyProfitPocError(
            "playwright is not installed. Run: uv run task install-e2e"
        ) from None

    checkpoints: list[LoginCheckpoint] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(MYPROFIT_URL)
            page.wait_for_load_state("domcontentloaded")

            # Step 1: fill and submit
            cp1 = _login_step_fill_and_submit(page, credentials)
            checkpoints.append(cp1)

            # Step 2: verify redirect + optional modal
            cp2 = _login_step_verify_redirect(page)
            checkpoints.append(cp2)

        except Exception:
            browser.close()
            raise
        finally:
            with suppress(Exception):
                browser.close()

    return checkpoints


# --- CLI entry point -------------------------------------------------------


def _prompt_owner(step_name: str) -> bool:
    """Prompt owner on stderr; return True to continue, False to abort."""
    print(
        f"\n[OWNER GATE] step={step_name}\n"
        "Verify the browser state, then press Enter to continue "
        "(or type 'q' to abort): ",
        end="",
        file=sys.stderr,
        flush=True,
    )
    answer = input().strip().lower()
    return answer not in ("q", "quit", "exit")


def main() -> int:
    """CLI entry point: launch headful Playwright, pause at owner gates."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MyProfit PoC: headful Playwright login with owner gates.",
    )
    parser.parse_args()

    print("MyProfit PoC — Playwright login (headful)", file=sys.stderr)

    credentials = load_credentials()
    print(f"Credentials loaded for: {credentials.email[:3]}***", file=sys.stderr)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise MyProfitPocError(
            "playwright is not installed. Run: uv run task install-e2e"
        ) from None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            page.goto(MYPROFIT_URL)
            page.wait_for_load_state("domcontentloaded")

            # --- Gate 1: credentials submitted ---
            cp1 = _login_step_fill_and_submit(page, credentials)
            print(f"\n✓ {cp1.message}", file=sys.stderr)
            print(f"  URL: {cp1.url}", file=sys.stderr)
            if not _prompt_owner(cp1.step):
                print("Aborted by owner.", file=sys.stderr)
                return 1

            # --- Gate 2: authenticated ---
            cp2 = _login_step_verify_redirect(page)
            print(f"\n✓ {cp2.message}", file=sys.stderr)
            print(f"  URL: {cp2.url}", file=sys.stderr)
            if not _prompt_owner(cp2.step):
                print("Aborted by owner.", file=sys.stderr)
                return 1

            print(
                "\nLogin flow complete. Browser remains open for manual inspection.",
                file=sys.stderr,
            )
            input("Press Enter to close the browser...")
        finally:
            with suppress(Exception):
                browser.close()

    return 0


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())
