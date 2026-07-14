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
  waits for the port to accept connections. Teardown now uses
  ``terminate()`` → wait → ``kill()`` fallback and logs if the
  port stays bound after shutdown. The subprocess's startup hook
  runs ``alembic upgrade head`` + idempotent ``seed()`` against
  the test DB on its own, so the schema and the ``family`` /
  ``Italo`` / ``Ana`` seed data are present before first test
  hits the server.
- The function-scoped ``clean_italo`` fixture wipes
  ``Italo``'s classes (and the cascading assets) via raw sqlite3
  so each test starts from a known-empty class list.

Browser lifecycle
-----------------
- A fresh chromium context per test (isolated cookies, isolated
  storage). ``OMAHA_E2E_TRACE_DIR=/path`` enables best-effort
  Playwright traces on failure for harness debugging.
- The shared ``page`` fixture wraps same-URL ``goto()`` calls so
  trace/debug replays wait for an in-flight dashboard reload
  instead of failing on Playwright's self-interrupt navigation
  error.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pytest

from tests.support.browser import (
    HarnessPage,
    launch_chromium,
)
from tests.support.browser import (
    log_harness as _log_harness,
)

# Re-export for backward compat — test files import from this module
from tests.support.browser import read_log_tail as _read_log_tail  # noqa: E402, F401
from tests.support.browser import (
    resolve_chromium as _resolve_chromium,
)
from tests.support.browser import shutdown_uvicorn as _shutdown_uvicorn  # noqa: E402, F401
from tests.support.browser import uvicorn_log_file as _uvicorn_log_file  # noqa: E402, F401
from tests.support.browser import wait_for_port as _wait_for_port  # noqa: E402, F401
from tests.support.constants import (
    REPO_ROOT,
    TEST_ADMIN_PASSWORD,
    TEST_SECRET_KEY,
)
from tests.support.db import (
    set_asset_target_pcts_via_db as _set_asset_target_pcts_via_db,  # noqa: F401  (re-exported)
)
from tests.support.db import wipe_profile_in_sqlite
from tests.support.hooks import remember_call_report as _remember_call_report
from tests.support.import_flow import (
    seed_assets_with_positions_via_import as _seed_assets_with_positions_via_import,  # noqa: F401
)
from tests.support.server import run_test_server

TEST_DB_PATH = REPO_ROOT / "data" / "test_e2e.db"
TEST_PORT = 8765
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
TRACE_DIR_ENV_VAR = "OMAHA_E2E_TRACE_DIR"

_BROWSER_CONTEXTS: dict[int, list[Any]] = {}


def _trace_artifact_path(base_dir: Path, nodeid: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", nodeid).strip("_") or "trace"
    return base_dir / f"{slug}.zip"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    _remember_call_report(item, outcome.get_result())


@pytest.fixture(scope="session")
def live_url() -> str:
    """Start a real uvicorn process for the e2e suite; yield the base URL."""
    # Reset test DB so alembic starts from a clean slate.
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    with run_test_server(
        TEST_DB_PATH,
        TEST_PORT,
        label="e2e-live-url",
        secret_key=TEST_SECRET_KEY,
        admin_password=TEST_ADMIN_PASSWORD,
    ) as url:
        yield url


@pytest.fixture(scope="session")
def live_url_short_ttl() -> str:
    """Start a uvicorn process with a 1-second preview TTL."""
    if TEST_DB_PATH_SHORT_TTL.exists():
        TEST_DB_PATH_SHORT_TTL.unlink()

    with run_test_server(
        TEST_DB_PATH_SHORT_TTL,
        TEST_PORT_SHORT_TTL,
        label="e2e-port-8767",
        secret_key=TEST_SECRET_KEY,
        admin_password=TEST_ADMIN_PASSWORD,
        extra_env={"PREVIEW_TTL_SECONDS": "1"},
    ) as url:
        yield url


@pytest.fixture(autouse=True)
def clean_italo() -> None:
    """Wipe ``Italo``'s classes (and their assets) before each test."""
    wipe_profile_in_sqlite(TEST_DB_PATH, "Italo")
    yield
    # No teardown — the next test's autouse invocation re-cleans.


@pytest.fixture(autouse=True)
def clean_italo_short_ttl() -> None:
    """Wipe ``Italo``'s classes in the short-TTL test DB before each test."""
    wipe_profile_in_sqlite(TEST_DB_PATH_SHORT_TTL, "Italo")
    yield


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
        browser = launch_chromium(p, executable)
        browser_key = id(browser)
        _BROWSER_CONTEXTS[browser_key] = []
        try:
            yield browser
        finally:
            try:
                browser.close()
            except Exception as exc:
                _log_harness(f"browser.close() failed: {exc}")
                for context in list(_BROWSER_CONTEXTS.get(browser_key, [])):
                    try:
                        context.close()
                    except Exception as context_exc:
                        _log_harness(f"browser context fallback close failed: {context_exc}")
            finally:
                _BROWSER_CONTEXTS.pop(browser_key, None)


@pytest.fixture()
def browser_context(_browser, request: pytest.FixtureRequest):
    """Fresh chromium context per test (isolated cookies, isolated storage)."""
    trace_dir_raw = os.environ.get(TRACE_DIR_ENV_VAR)
    trace_dir = Path(trace_dir_raw) if trace_dir_raw else None
    context = _browser.new_context()
    browser_key = id(_browser)
    _BROWSER_CONTEXTS.setdefault(browser_key, []).append(context)
    tracing_enabled = False
    if trace_dir is not None:
        trace_dir.mkdir(parents=True, exist_ok=True)
        try:
            context.tracing.start(screenshots=True, snapshots=True)
            tracing_enabled = True
        except Exception as exc:
            _log_harness(f"trace start failed for {request.node.nodeid}: {exc}")
    try:
        yield context
    finally:
        report = getattr(request.node, "_omaha_call_report", None)
        failed = bool(report and report.failed)
        if tracing_enabled and trace_dir is not None:
            trace_path = _trace_artifact_path(trace_dir, request.node.nodeid)
            try:
                if failed:
                    context.tracing.stop(path=str(trace_path))
                    _log_harness(f"trace kept for failing test: {trace_path}")
                else:
                    context.tracing.stop()
            except Exception as exc:
                _log_harness(f"trace stop failed for {request.node.nodeid}: {exc}")
        if not _browser.is_connected():
            _log_harness(f"browser disconnected before context teardown: {request.node.nodeid}")
        try:
            context.close()
        except Exception as exc:
            _log_harness(f"browser context close failed for {request.node.nodeid}: {exc}")
        finally:
            contexts = _BROWSER_CONTEXTS.get(browser_key, [])
            if context in contexts:
                contexts.remove(context)


@pytest.fixture()
def page(browser_context):
    """Fresh page bound to an isolated browser context."""
    raw_page = browser_context.new_page()
    page = HarnessPage(raw_page)
    try:
        yield page
    finally:
        raw_page.close()
