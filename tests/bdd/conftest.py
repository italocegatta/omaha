"""BDD e2e fixtures for the Omaha app.

Drives a real chromium against a real uvicorn server bound to
127.0.0.1:8766 (one port off from the legacy ``tests/e2e/``
suite's 8765 so the two suites can run in parallel). Backed by
a separate SQLite file ``data/test_bdd.db`` so the legacy
``data/test_e2e.db`` is never touched by this suite.

Browser lifecycle is identical to ``tests/e2e/conftest.py`` — we
import the ``page`` / ``browser_context`` / ``_browser`` fixtures
directly from there. BDD-specific harness glue adds stronger
uvicorn teardown and a 3s SQLite ``busy_timeout`` during profile
wipes so late-suite lock contention is observable instead of
failing immediately.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys

import pytest

from tests.e2e.conftest import (  # noqa: F401  (re-exported to step_defs)
    REPO_ROOT as _E2E_REPO_ROOT,
)
from tests.e2e.conftest import (
    _browser,  # noqa: F401  (transitive: page → browser_context → _browser)
    _remember_call_report,
    _read_log_tail,
    _shutdown_uvicorn,
    _uvicorn_log_file,
    _wait_for_port,
    browser_context,  # noqa: F401
    page,  # noqa: F401
)

BDD_DB_PATH = _E2E_REPO_ROOT / "data" / "test_bdd.db"
BDD_PORT = 8766
TEST_ADMIN_PASSWORD = "test-password"
TEST_SECRET_KEY = "test-secret-bdd-do-not-use-in-prod"
TEST_BASE_URL = f"http://127.0.0.1:{BDD_PORT}"

# The seed creates exactly two profiles (see src/omaha/seed.py
# DEFAULT_USERS — usernames ``Italo`` and ``Ana`` are used as
# both user name and profile name). The autouse
# ``clean_seeded_profiles`` fixture wipes both before each
# scenario so parametrized tests that pick either profile start
# from an empty baseline. Note: a previous revision of this
# fixture listed ``"Ana Livia"`` here, which never matched the
# actual seeded profile name and silently left Ana's classes in
# place across tests — that's the bug this comment is here to
# prevent from coming back.
BDD_SEEDED_PROFILES = ("Italo", "Ana")


def _wait_for_bdd_port(
    host: str = "127.0.0.1", port: int = BDD_PORT, timeout: float = 30.0
) -> None:
    """Block until the BDD uvicorn is listening on ``host:port``.

    Wraps :func:`tests.e2e.conftest._wait_for_port` with a longer
    default timeout — the BDD suite runs after the legacy e2e
    suite and the port may still be in TIME_WAIT briefly.
    """
    _wait_for_port(host, port, timeout=timeout)


def _wipe_profile(profile_name: str) -> None:
    """Wipe classes + assets + import_previews for ``profile_name``.

    Mirrors :func:`tests.e2e.conftest._wipe_classes_for` — SQLite
    does not enforce FK constraints without ``PRAGMA
    foreign_keys = ON``, so we wipe ``positions`` /
    ``assets`` / ``asset_classes`` / ``import_previews`` in that
    order to avoid orphan rows in the next test.
    """
    if not BDD_DB_PATH.exists():
        return
    conn = sqlite3.connect(BDD_DB_PATH)
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


@pytest.fixture(scope="session")
def live_url() -> str:
    """Start a real uvicorn for the BDD suite on port 8766."""
    if BDD_DB_PATH.exists():
        BDD_DB_PATH.unlink()

    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{BDD_DB_PATH}",
        "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
        "SECRET_KEY": TEST_SECRET_KEY,
        "OMAHA_SKIP_STARTUP": "",
    }

    log_handle = _uvicorn_log_file("bdd-live-url")
    log_path = _E2E_REPO_ROOT / "tmp" / "uvicorn-logs" / os.path.basename(log_handle.name)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "omaha.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BDD_PORT),
            "--log-level",
            "warning",
        ],
        cwd=_E2E_REPO_ROOT,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )

    try:
        _wait_for_bdd_port()
    except Exception:
        proc.terminate()
        log_handle.close()
        raise RuntimeError(
            f"BDD uvicorn did not start on {TEST_BASE_URL}. output:\n{_read_log_tail(log_path)}"
        ) from None

    yield TEST_BASE_URL

    _shutdown_uvicorn(
        proc,
        label="bdd live_url",
        host="127.0.0.1",
        port=BDD_PORT,
        log_handle=log_handle,
        log_path=log_path,
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    _remember_call_report(item, outcome.get_result())


@pytest.fixture(autouse=True)
def clean_seeded_profiles() -> None:
    """Wipe BOTH seeded profiles before each BDD scenario.

    Replaces the legacy ``clean_italo`` autouse (which only wipes
    ``Italo``). The BDD suite is parametrized over ``Italo`` and
    ``Ana`` so each scenario needs a known-empty baseline for
    BOTH profiles regardless of the parametrization pick.
    """
    for profile in BDD_SEEDED_PROFILES:
        _wipe_profile(profile)
    yield


# ─────────────────────────────────────────────────────────────────────
# Re-export step definitions as conftest fixtures.
# pytest-bdd discovers step fixtures in the test module + conftest.py
# in the test's directory tree. Importing the step_defs modules
# re-binds the step_function_marker fixtures into this conftest's
# namespace so the discovery walker can find them.
# ─────────────────────────────────────────────────────────────────────

# Re-export every step function as a fixture in this conftest. The
# pytest-bdd @given/@when/@then decorators register a
# step_function_marker in the *calling module's* namespace; the
# fixtures only become discoverable from a test when they live in
# the test's own module or in a conftest.py reachable from the
# test. Importing the step_defs submodules rebinds the same name
# here so pytest-bdd can find the markers.
from tests.bdd.step_defs.asset_steps import *  # noqa: E402, F401, F403
from tests.bdd.step_defs.class_steps import *  # noqa: E402, F401, F403
from tests.bdd.step_defs.common_steps import *  # noqa: E402, F401, F403
from tests.bdd.step_defs.dashboard_steps import *  # noqa: E402, F401, F403
from tests.bdd.step_defs.import_steps import *  # noqa: E402, F401, F403
from tests.bdd.step_defs.target_steps import *  # noqa: E402, F401, F403
