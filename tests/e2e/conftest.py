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
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DB_PATH = REPO_ROOT / "data" / "test_e2e.db"
TEST_PORT = 8765
TEST_ADMIN_PASSWORD = "test-password"
TEST_SECRET_KEY = "test-secret-e2e-do-not-use-in-prod"
TEST_BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


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


@pytest.fixture(scope="session")
def _browser():
    """Single chromium browser process for the suite (faster than per-test)."""
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
