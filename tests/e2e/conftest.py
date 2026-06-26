"""Browser-based E2E fixtures for the Omaha app.

Drives a real chromium against a real uvicorn server bound to
127.0.0.1:<TEST_PORT>, backed by a separate SQLite file
(data/test_e2e.db) so the user's manual-testing DB
(data/portfolio.db) is never touched.

Chromium resolution
-------------------
The ``_browser`` fixture launches a single chromium process for
the suite. It does NOT hard-code a single path — it searches in
order:

1. ``$E2E_CHROMIUM_PATH`` (explicit override)
2. ``~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome``
   (binaries installed by ``playwright install chromium``)
3. ``/usr/bin/chromium-browser`` (system chromium, legacy hosts)

If none of these exist the fixture raises an actionable
RuntimeError pointing the operator at the install command. This
keeps the suite runnable on hosts that have either the bundled
Playwright browser or a system chromium, without committing to
one or the other in source.

Server lifecycle
----------------
- The session-scoped ``live_url`` fixture deletes any leftover
  test DB, starts a uvicorn subprocess with overrides for
  ``DATABASE_URL``, ``ADMIN_PASSWORD``, and ``SECRET_KEY``, and
  waits for the port to accept connections. The subprocess's
  startup hook runs ``alembic upgrade head`` + idempotent
  ``seed()`` against the test DB on its own, so the schema and
  the ``family`` / ``Italo`` / ``Ana Livia`` seed data are
  present before the first test hits the server.
- The function-scoped ``clean_italo`` fixture wipes
  ``Italo``'s classes (and the cascading assets) via raw sqlite3
  so each test starts from a known-empty class list.

Browser lifecycle
-----------------
- A fresh chromium context per test (isolated cookies, isolated
  storage). The browser process itself is reused across tests in
  the same module for speed.
"""

from __future__ import annotations

import os
import socket
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

from tests.e2e.test_import_user_journey import SELECTORS as IMPORT_SELECTORS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DB_PATH = REPO_ROOT / "data" / "test_e2e.db"
TEST_PORT = 8765
TEST_ADMIN_PASSWORD = "test-password"
TEST_SECRET_KEY = "test-secret-e2e-do-not-use-in-prod"
TEST_BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

# Separate server fixture for the expired-preview test: a 1-second
# PREVIEW_TTL lets the test wait for real expiration instead of
# backdating the DB. We isolate it on its own port/DB so the global
# 1s TTL does not break the longer import-modal journeys.
#
# Port 8767 (not 8765/8766): 8765 is the main e2e suite; 8766 is
# the bdd suite. Sharing a port with another session-scoped uvicorn
# causes the second uvicorn's bind to fail silently and the test
# ends up talking to whichever uvicorn was bound first (with the
# wrong DB and the default TTL), see
# openspec/changes/investigate-expired-preview-flake.
TEST_DB_PATH_SHORT_TTL = REPO_ROOT / "data" / "test_e2e_short_ttl.db"
TEST_PORT_SHORT_TTL = 8767
TEST_BASE_URL_SHORT_TTL = f"http://127.0.0.1:{TEST_PORT_SHORT_TTL}"


def _seed_assets_with_positions_via_import(
    page,
    live_url: str,
    class_assignments: list[tuple[str, str]],
    positions: dict[str, tuple[float, float]] | None = None,
) -> None:
    """Drive the dashboard import modal with a small inline CSV.

    Builds a 1-line-header + N-data-rows CSV in /tmp, uploads via
    dashboard import modal (existing flow), auto-matches everything
    (no unmatched names), commits. End state: N assets with 1
    position each, assigned to the requested classes.

    Replaces _seed_one_position_for_asset and _seed_positions,
    which violated the project's "assets come from import, never
    from seed" rule (AGENTS.md).
    """
    csv_path = Path("/tmp") / f"omaha-test-{uuid.uuid4().hex[:8]}.csv"
    with csv_path.open("w") as f:
        f.write('"Posicao consolidada","Cliente: TEST"\n')
        # broker-csv-import-totals: include ``Total investido`` /
        # ``Total atual`` columns so the parsed positions carry the
        # broker-published totals. Without these, the dashboard's
        # portfolio header (gated on current_value > 0) hides and
        # downstream e2e selectors that wait on it timeout. We use
        # ``R$`` prefix + BR-milhar to exercise the parser's
        # number-format path the same way the real broker CSV does.
        f.write(
            "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,"
            "Total investido,Total atual,Minha Categoria\n"
        )
        for class_name, asset_name in class_assignments:
            qty, price = (positions or {}).get(asset_name, (100.0, 100.0))
            total_invested = qty * 100.00
            total_current = qty * price

            # Use BR-milhar formatting for prices > 1000 so the
            # parser exercises the dot-as-thousands path.
            def _fmt(value: float) -> str:
                # Renders 12345.67 → "12.345,67"; small values stay
                # as "100,00".
                s = f"{value:,.2f}"
                return s.replace(",", "X").replace(".", ",").replace("X", ".")

            f.write(
                f"{asset_name},{asset_name},{qty:.2f},100.00,{price:.2f},"
                f'"R$ {_fmt(total_invested)}","R$ {_fmt(total_current)}",{class_name}\n'
            )

    # Drive the modal — reuse the flow from test_import_user_journey.py
    page.click(IMPORT_SELECTORS["dashboard_import_btn"])
    page.wait_for_selector('[data-testid="import-modal-overlay"]', state="visible", timeout=5000)
    page.wait_for_timeout(300)  # Alpine modal mounts
    page.set_input_files(IMPORT_SELECTORS["import_file_input"], str(csv_path))
    page.wait_for_timeout(300)  # Alpine @change fires
    page.click(IMPORT_SELECTORS["import_upload_btn"], force=True)
    page.wait_for_selector(IMPORT_SELECTORS["import_commit_btn"], timeout=10000)
    # No unmatched — direct commit
    page.click(IMPORT_SELECTORS["import_commit_btn"], force=True)
    page.wait_for_timeout(300)
    error_text = ""
    try:
        error_el = page.locator(IMPORT_SELECTORS["import_commit_error"])
        if error_el.count() and error_el.is_visible():
            error_text = error_el.inner_text()
    except Exception:
        pass
    if error_text:
        raise RuntimeError(f"import commit failed: {error_text}")
    page.wait_for_selector('[data-testid="import-modal-overlay"]', state="hidden", timeout=10000)
    csv_path.unlink(missing_ok=True)  # cleanup


def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    """Block until ``host:port`` accepts a TCP connection or raise."""
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return
            except OSError as exc:
                last_err = exc
                time.sleep(0.1)
    raise RuntimeError(
        f"server on {host}:{port} did not become ready in {timeout}s (last error: {last_err})"
    )


@pytest.fixture(scope="session")
def live_url() -> str:
    """Start a real uvicorn process for the e2e suite; yield the base URL."""
    # Reset test DB so alembic starts from a clean slate.
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{TEST_DB_PATH}",
        "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
        "SECRET_KEY": TEST_SECRET_KEY,
        # Empty string means "not set" to the app's check
        # (``os.environ.get(...) != "1"``), so the startup hook
        # runs alembic + seed against the test DB.
        "OMAHA_SKIP_STARTUP": "",
    }

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "omaha.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(TEST_PORT),
            "--log-level",
            "warning",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_port("127.0.0.1", TEST_PORT, timeout=30.0)
    except Exception:
        proc.terminate()
        try:
            out = proc.stdout.read(timeout=2) if proc.stdout else b""
        except Exception:
            out = b"<unreadable>"
        raise RuntimeError(
            f"uvicorn did not start. output:\n{out.decode(errors='replace')}"
        ) from None

    yield TEST_BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _start_uvicorn(db_path: Path, port: int, extra_env: dict[str, str]) -> subprocess.Popen:
    """Start a uvicorn subprocess for e2e with the given DB and env."""
    if db_path.exists():
        db_path.unlink()

    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
        "SECRET_KEY": TEST_SECRET_KEY,
        "OMAHA_SKIP_STARTUP": "",
        **extra_env,
    }

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "omaha.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_port("127.0.0.1", port, timeout=30.0)
    except Exception:
        proc.terminate()
        try:
            out = proc.stdout.read(timeout=2) if proc.stdout else b""  # type: ignore[attr-defined]
        except Exception:
            out = b"<unreadable>"
        raise RuntimeError(
            f"uvicorn did not start. output:\n{out.decode(errors='replace')}"
        ) from None

    return proc


@pytest.fixture(scope="session")
def live_url_short_ttl() -> str:
    """Start a uvicorn process with a 1-second preview TTL."""
    proc = _start_uvicorn(
        TEST_DB_PATH_SHORT_TTL,
        TEST_PORT_SHORT_TTL,
        extra_env={"PREVIEW_TTL_SECONDS": "1"},
    )
    yield TEST_BASE_URL_SHORT_TTL

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _wipe_classes_for(profile_name: str) -> None:
    """Delete every AssetClass (and cascading Asset) for ``profile_name``.

    The assets table has ``ON DELETE CASCADE`` on its FK to
    asset_classes (see 0003_assets), but SQLite does NOT enforce
    FK constraints unless ``PRAGMA foreign_keys = ON`` is set on
    the connection — and SQLAlchemy does not enable it by default.
    A bare ``DELETE FROM asset_classes`` would leave orphan assets
    behind, and the next test would see them because the editor
    renders every asset in the table (not just the ones whose
    class still exists). Wipe both tables explicitly. (L005 — the
    S04 T04 happy-path test surfaced this latent bug. S03's
    tests passed because each one re-creates its own assets and
    the residue is never visible from inside a single test.)
    """
    if not TEST_DB_PATH.exists():
        return
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        row = conn.execute("SELECT id FROM profiles WHERE name = ?", (profile_name,)).fetchone()
        if row is None:
            return
        pid = row[0]
        # Wipe positions first — SQLite without PRAGMA foreign_keys=ON
        # does not cascade, and orphan position rows collide with the
        # UNIQUE (asset_id, broker_ticker) constraint in later tests.
        conn.execute(
            "DELETE FROM positions WHERE asset_id IN "
            "(SELECT a.id FROM assets a "
            " JOIN asset_classes ac ON a.asset_class_id = ac.id "
            " WHERE ac.profile_id = ?)",
            (pid,),
        )
        conn.execute(
            "DELETE FROM assets WHERE asset_class_id IN "
            "(SELECT id FROM asset_classes WHERE profile_id = ?)",
            (pid,),
        )
        conn.execute("DELETE FROM asset_classes WHERE profile_id = ?", (pid,))
        # Wipe import previews for this profile too — the S04 test
        # backdates them via direct SQL and a previous test's
        # preview could pollute the next one's session.
        conn.execute("DELETE FROM import_previews WHERE profile_id = ?", (pid,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def clean_italo() -> None:
    """Wipe ``Italo``'s classes (and their assets) before each test."""
    _wipe_classes_for("Italo")
    yield
    # No teardown — the next test's autouse invocation re-cleans.


def _wipe_classes_for_in_db(db_path: Path, profile_name: str) -> None:
    """Variant of ``_wipe_classes_for`` that targets an arbitrary DB file."""
    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT id FROM profiles WHERE name = ?", (profile_name,)).fetchone()
        if row is None:
            return
        pid = row[0]
        conn.execute(
            "DELETE FROM positions WHERE asset_id IN "
            "(SELECT a.id FROM assets a "
            " JOIN asset_classes ac ON a.asset_class_id = ac.id "
            " WHERE ac.profile_id = ?)",
            (pid,),
        )
        conn.execute(
            "DELETE FROM assets WHERE asset_class_id IN "
            "(SELECT id FROM asset_classes WHERE profile_id = ?)",
            (pid,),
        )
        conn.execute("DELETE FROM asset_classes WHERE profile_id = ?", (pid,))
        conn.execute("DELETE FROM import_previews WHERE profile_id = ?", (pid,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def clean_italo_short_ttl() -> None:
    """Wipe ``Italo``'s classes in the short-TTL test DB before each test."""
    _wipe_classes_for_in_db(TEST_DB_PATH_SHORT_TTL, "Italo")
    yield


def _resolve_chromium() -> str:
    """Find a usable chromium binary on this host.

    Search order:
        1. ``$E2E_CHROMIUM_PATH`` if set and the file exists
        2. ``~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome``
           (the binary installed by ``playwright install chromium``)
        3. ``/usr/bin/chromium-browser`` (legacy system chromium)

    Returns the first match as a string path. Raises RuntimeError
    with an actionable message if nothing is found.
    """
    candidates: list[Path] = []
    env = os.environ.get("E2E_CHROMIUM_PATH")
    if env:
        candidates.append(Path(env))

    cache = Path.home() / ".cache" / "ms-playwright"
    if cache.exists():
        # Sort newest first so we pick the latest installed revision
        # when multiple are present.
        candidates.extend(sorted(cache.glob("chromium-*/chrome-linux*/chrome"), reverse=True))
        candidates.extend(
            sorted(cache.glob("chromium-*/chrome-linux*/headless_shell"), reverse=True)
        )

    candidates.append(Path("/usr/bin/chromium-browser"))

    for cand in candidates:
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)

    raise RuntimeError(
        "chromium binary not found. Tried: "
        + ", ".join(str(c) for c in candidates if not str(c).startswith("~"))
        + ". Run `uv run playwright install chromium --with-deps` "
        "or set E2E_CHROMIUM_PATH=/path/to/chrome."
    )


@pytest.fixture(scope="function")
def _browser():
    """Per-function chromium browser process to avoid asyncio loop pollution.

    The session-scoped version is faster, but when the BDD subset (or any
    pytest-asyncio/anyio tests) runs in the same process they leave an
    asyncio event loop on the main thread. Playwright's sync API refuses
    to run inside an existing loop, so we isolate each browser instance.
    """
    from playwright.sync_api import sync_playwright

    executable = _resolve_chromium()
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                executable_path=executable,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to launch chromium at {executable}: {exc}. "
                "If this looks like 'shared library not found', run "
                "`uv run playwright install chromium --with-deps` to install "
                "system dependencies (libnss3, libxkbcommon0, libgbm1, etc.)."
            ) from exc
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture()
def browser_context(_browser):
    """Fresh chromium context per test (isolated cookies, isolated storage)."""
    context = _browser.new_context()
    try:
        yield context
    finally:
        context.close()


@pytest.fixture()
def page(browser_context):
    """Fresh page bound to an isolated browser context."""
    page = browser_context.new_page()
    try:
        yield page
    finally:
        page.close()
