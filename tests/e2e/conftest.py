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
import socket
import sqlite3
import subprocess
import sys
import time
import uuid
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError

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
TRACE_DIR_ENV_VAR = "OMAHA_E2E_TRACE_DIR"

_BROWSER_CONTEXTS: dict[int, list[Any]] = {}
_GOTO_INTERRUPT_RE = re.compile(
    r'Navigation to "(?P<target>[^"]+)" is interrupted by another navigation to "(?P<other>[^"]+)"'
)


class _HarnessPage:
    """Thin Page proxy with retry-on-same-URL navigation guard.

    Some Omaha test workflows click a UI action that triggers
    ``window.location.reload()`` and then immediately call
    ``page.goto()`` to the same dashboard URL. Under slower harness
    paths (notably trace/debug runs), Playwright can surface this as
    a same-URL navigation interruption even though the in-flight
    reload already heads to the requested page. Treat that narrow
    case as wait-for-completion instead of hard failure.
    """

    def __init__(self, page: Any):
        self._page = page

    def __getattr__(self, name: str) -> Any:
        return getattr(self._page, name)

    def goto(self, url: str, *args: Any, **kwargs: Any):
        try:
            return self._page.goto(url, *args, **kwargs)
        except PlaywrightError as exc:
            match = _GOTO_INTERRUPT_RE.search(str(exc))
            if match is None or match.group("target") != url or match.group("other") != url:
                raise
            timeout = int(kwargs.get("timeout", 30_000))
            wait_until = kwargs.get("wait_until", "load")
            _log_harness(f"same-URL goto interrupted by in-flight reload; waiting instead: {url}")
            self._page.wait_for_url(url, wait_until=wait_until, timeout=timeout)
            return None


def _log_harness(message: str) -> None:
    print(f"[omaha-test-harness] {message}", file=sys.stderr, flush=True)


def _remember_call_report(item: pytest.Item, report: pytest.TestReport) -> None:
    if report.when == "call":
        item._omaha_call_report = report


def _trace_artifact_path(base_dir: Path, nodeid: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", nodeid).strip("_") or "trace"
    return base_dir / f"{slug}.zip"


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def _uvicorn_log_file(label: str):
    log_dir = REPO_ROOT / "tmp" / "uvicorn-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-") or "uvicorn"
    return NamedTemporaryFile(prefix=f"{slug}-", suffix=".log", dir=log_dir, delete=False)


def _read_log_tail(log_path: Path, max_bytes: int = 4000) -> str:
    if not log_path.exists():
        return "<missing log file>"
    data = log_path.read_bytes()
    return data[-max_bytes:].decode(errors="replace")


def _shutdown_uvicorn(
    proc: subprocess.Popen[bytes],
    *,
    label: str,
    host: str,
    port: int,
    log_handle: Any | None = None,
    log_path: Path | None = None,
) -> None:
    proc.terminate()
    with suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=3)

    if proc.poll() is None:
        _log_harness(f"{label}: terminate timeout on {host}:{port}; sending kill()")
        proc.kill()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _log_harness(f"{label}: process still alive after kill() on {host}:{port}")

    if not _port_is_free(host, port):
        _log_harness(f"{label}: port {port} still bound after teardown")

    if log_handle is not None:
        log_handle.close()
    if log_path is not None and proc.returncode not in (0, -15):
        _log_harness(f"{label}: uvicorn log tail\n{_read_log_tail(log_path)}")


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


def _set_asset_target_pcts_via_db(
    assignments: dict[str, float],
    db_path: Path | None = None,
) -> None:
    """Patch ``Asset.target_pct`` directly via sqlite so the
    CVXPY rebalance engine sees a valid portfolio (assets' target_pct
    must sum to 100 within each class).

    Used by e2e tests that need the rebalance plan to render but
    don't have a CSV import path that already encodes target_pct.
    Direct DB write — bypasses the asset/position seed invariant
    (PRD §4.3) because this is test-only setup.
    """
    if db_path is None:
        db_path = Path(__file__).resolve().parent.parent.parent / "data" / "test_e2e.db"
    conn = sqlite3.connect(db_path)
    try:
        for asset_name, target_pct in assignments.items():
            conn.execute(
                "UPDATE assets SET target_pct = ? WHERE name = ?",
                (target_pct, asset_name),
            )
        conn.commit()
    finally:
        conn.close()


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

    log_handle = _uvicorn_log_file("e2e-live-url")
    log_path = Path(log_handle.name)
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
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_port("127.0.0.1", TEST_PORT, timeout=30.0)
    except Exception:
        proc.terminate()
        log_handle.close()
        raise RuntimeError(f"uvicorn did not start. output:\n{_read_log_tail(log_path)}") from None

    yield TEST_BASE_URL

    _shutdown_uvicorn(
        proc,
        label="e2e live_url",
        host="127.0.0.1",
        port=TEST_PORT,
        log_handle=log_handle,
        log_path=log_path,
    )


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

    log_handle = _uvicorn_log_file(f"e2e-port-{port}")
    log_path = Path(log_handle.name)
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
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_port("127.0.0.1", port, timeout=30.0)
    except Exception:
        proc.terminate()
        log_handle.close()
        raise RuntimeError(f"uvicorn did not start. output:\n{_read_log_tail(log_path)}") from None

    proc._omaha_log_handle = log_handle
    proc._omaha_log_path = log_path
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

    _shutdown_uvicorn(
        proc,
        label="e2e live_url_short_ttl",
        host="127.0.0.1",
        port=TEST_PORT_SHORT_TTL,
        log_handle=getattr(proc, "_omaha_log_handle", None),
        log_path=getattr(proc, "_omaha_log_path", None),
    )


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
        conn.execute("PRAGMA busy_timeout = 3000")
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
        conn.execute("PRAGMA busy_timeout = 3000")
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
    page = _HarnessPage(raw_page)
    try:
        yield page
    finally:
        raw_page.close()
