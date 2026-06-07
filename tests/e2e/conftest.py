"""Browser-based E2E fixtures for the Omaha app.

Drives a real chromium against a real uvicorn server bound to
127.0.0.1:<TEST_PORT>, backed by a separate SQLite file
(data/test_e2e.db) so the user's manual-testing DB
(data/portfolio.db) is never touched.

Why the system chromium, not the bundled one: Playwright's bundled
browsers do not have a build for ``ubuntu26.04-x64`` (the host is
on Ubuntu Resolute Raccoon). The host has chromium 149 at
``/usr/bin/chromium-browser`` which speaks the same CDP protocol and
is launched via ``executable_path=...``.

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
        )

    yield TEST_BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _wipe_classes_for(profile_name: str) -> None:
    """Delete every AssetClass (and cascading Asset) for ``profile_name``."""
    if not TEST_DB_PATH.exists():
        return
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        row = conn.execute(
            "SELECT id FROM profiles WHERE name = ?", (profile_name,)
        ).fetchone()
        if row is None:
            return
        pid = row[0]
        # assets table has a FK to asset_classes with ON DELETE
        # CASCADE (see 0003_assets), so this single delete
        # wipes both tables for the test profile.
        conn.execute("DELETE FROM asset_classes WHERE profile_id = ?", (pid,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def clean_italo() -> None:
    """Wipe ``Italo``'s classes (and their assets) before each test."""
    _wipe_classes_for("Italo")
    yield
    # No teardown — the next test's autouse invocation re-cleans.


@pytest.fixture(scope="session")
def _browser():
    """Single chromium browser process for the suite (faster than per-test)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium-browser",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
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
