"""Shared test fixtures for the Omaha test suite.

The ``client`` fixture builds a TestClient pointed at a real FastAPI
app (the same ``omaha.main.app`` used by the production server) but
backed by a per-test SQLite database in ``tmp_path``. Alembic
migrations and the idempotent seed run once per pytest *session* so
the seven T03 auth tests share one prepared database and only the
client (and therefore the session cookies) is per-test.

The startup migration that ``omaha.main`` runs on ``on_event("startup")``
is suppressed via the ``OMAHA_SKIP_STARTUP=1`` env var; the fixture
already populated the database, and a second migration+seed pass would
just slow the tests down.

Each test that needs a clean cookie jar gets a fresh :class:`TestClient`
instance — the cookies live on the client, not the server, so a logout
in one test does not leak into the next.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_SECRET_KEY = "test-secret-do-not-use"
TEST_ADMIN_PASSWORD = "test-password"


def _run_alembic_upgrade(db_url: str) -> None:
    """Run ``alembic upgrade head`` against ``db_url`` in a subprocess.

    The subprocess is necessary because the migration environment
    (``alembic/env.py``) reads ``DATABASE_URL`` from the process
    environment, and SQLAlchemy's engine inside the parent process is
    bound at import time.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
            "SECRET_KEY": TEST_SECRET_KEY,
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert (
        result.returncode == 0
    ), f"alembic upgrade head failed: stdout={result.stdout!r} stderr={result.stderr!r}"


@pytest.fixture(scope="session")
def _omaha_test_env(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """Prepare a one-time test database for the session.

    Runs alembic + seed against a session-scoped SQLite file under
    ``tmp_path_factory``, then imports :mod:`omaha` with the right
    env vars so the in-process engine points at the same file. The
    startup event on ``omaha.main.app`` is suppressed so the same
    migration does not run a second time when the TestClient is
    created.
    """
    db_dir = tmp_path_factory.mktemp("omaha-test-db")
    db_file = db_dir / "portfolio.db"
    db_url = f"sqlite:///{db_file}"

    _run_alembic_upgrade(db_url)

    # Inject env vars *before* importing omaha — settings is built at
    # import time and the test-mode guard only suppresses the
    # SECRET_KEY check (it doesn't read env vars lazily).
    os.environ["DATABASE_URL"] = db_url
    os.environ["ADMIN_PASSWORD"] = TEST_ADMIN_PASSWORD
    os.environ["SECRET_KEY"] = TEST_SECRET_KEY
    os.environ["OMAHA_SKIP_STARTUP"] = "1"

    # Drop any cached omaha modules so the import below re-runs the
    # config + engine + session-factory wiring against the new env.
    for mod_name in list(sys.modules):
        if mod_name == "omaha" or mod_name.startswith("omaha."):
            del sys.modules[mod_name]

    import omaha.config  # noqa: F401 — populates ``settings``
    import omaha.db  # noqa: F401 — populates engine + SessionLocal
    import omaha.main  # noqa: F401 — populates ``app``
    import omaha.models  # noqa: F401 — registers tables on Base
    import omaha.seed  # noqa: F401 — registers seed module

    omaha.seed.seed()

    return {"db_path": str(db_file), "db_url": db_url}


@pytest.fixture()
def client(_omaha_test_env: dict[str, str]) -> TestClient:
    """Yield a per-test :class:`TestClient` with a clean cookie jar.

    Uses :class:`fastapi.testclient.TestClient` as a context manager so
    the underlying ASGI app is properly shut down between tests.
    """
    from omaha.main import app

    with TestClient(app) as test_client:
        yield test_client
