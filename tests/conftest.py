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
    assert result.returncode == 0, (
        f"alembic upgrade head failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


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
    # Default to non-prod so the (T02) https_only flip stays False
    # and the Starlette TestClient can still authenticate over plain
    # HTTP without the secure-cookie check rejecting the cookie.
    os.environ.setdefault("OMAHA_ENV", "development")

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


# ---------------------------------------------------------------------------
# Pytest marker convention
# ---------------------------------------------------------------------------
# Two markers partition the suite: ``unit`` (pure functions, no DB no HTTP)
# and ``integration`` (boots the FastAPI app, hits a SQLite DB, uses
# TestClient, or reads the live ``app.css`` / templates).  The rule is
# location-based so we don't have to touch every existing test file.
#
# * tests/e2e/*.py                       → no marker (Playwright, run via
#                                          ``task test-e2e``)
# * tests/audit_integration/*            → @pytest.mark.integration
# * explicit integration prefix list     → @pytest.mark.integration
# * everything else in tests/*.py        → @pytest.mark.unit
#
# The explicit integration prefix list (see ``_INTEGRATION_PREFIXES`` below)
# is the single source of truth: any new ``tests/test_*.py`` that hits DB
# or TestClient MUST be added there, or it silently gets the ``unit``
# marker and pollutes the unit subset.
#
# A new file in ``tests/*.py`` that matches neither set triggers a
# ``UnknownTestPath`` warning so future drift is loud.


class UnknownTestPath(UserWarning):
    """Raised when a ``tests/*.py`` file matches neither the integration
    prefix list nor the e2e carve-out.  This is a soft warning, not a
    hard error: the file is still tagged ``unit`` so the test runs, but
    the next agent will see the warning and decide whether the prefix
    list needs updating.
    """


_INTEGRATION_PREFIXES = (
    "tests/test_assets_delete.py",
    "tests/test_assets_e2e.py",
    "tests/test_assets_model.py",
    "tests/test_assets_post.py",
    "tests/test_assets_routes.py",
    "tests/test_assets_patch_legacy.py",
    "tests/test_assets_trade_flags.py",
    "tests/test_auth.py",
    "tests/test_backup.py",
    "tests/test_classes_delete.py",
    "tests/test_classes_e2e.py",
    "tests/test_classes_model.py",
    "tests/test_classes_patch.py",
    "tests/test_classes_post.py",
    "tests/test_classes_routes.py",
    "tests/test_csv_import.py",
    "tests/test_db_reset_both_profiles.py",
    "tests/test_e2e.py",
    "tests/test_healthz.py",
    "tests/test_import_commit.py",
    "tests/test_import_get_preview.py",
    "tests/test_import_preview.py",
    "tests/test_imports_routes.py",
    "tests/test_pages_routes.py",
    "tests/test_positions_model.py",
    "tests/test_quote_cache.py",
    "tests/test_quote_routes.py",
    "tests/test_quote_service.py",
    "tests/test_real_csv_flow.py",
    "tests/test_rebalance_builders.py",
    "tests/test_rebalance_glue.py",
    "tests/test_rebalance_route.py",
    "tests/test_rebalance_schemas.py",
    "tests/test_market_prices_adapter.py",
    "tests/test_seed.py",
    "tests/test_seed_from_csv.py",
)


# Unit allow-list: files that are pure functions, no DB no HTTP no Playwright.
# These predate the explicit integration prefix list and would otherwise
# trip the ``UnknownTestPath`` warning. Adding them here silences the
# warning for the legitimate unit set.
_UNIT_FILES = frozenset(
    {
        "tests/scripts/test_reset_both_profiles.py",
        "tests/test_audit_color_resolver.py",
        "tests/test_audit_css_parser.py",
        "tests/test_audit_report.py",
        "tests/test_asset_target.py",
        "tests/test_csv_import.py",
        "tests/test_dockerfile.py",
        "tests/test_e2e_port_uniqueness.py",
        "tests/test_logging.py",
        "tests/test_tokens.py",
        "tests/test_yfinance_provider.py",
    }
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Apply the location-based marker rule documented above.

    Items that already carry an explicit ``unit`` or ``integration``
    marker (via ``pytestmark = pytest.mark.X`` at module top) are
    skipped — the file author wins over the location rule. This lets
    tests that genuinely depend on production files opt out of the
    unit subset without renaming or moving files.

    Files in ``tests/e2e/`` are left un-marker'd (Playwright tests
    are filtered separately by path). Files in
    ``tests/audit_integration/`` and any path matching
    ``_INTEGRATION_PREFIXES`` are tagged ``integration``. Everything
    else in ``tests/*.py`` is tagged ``unit`` — and if it does not
    match any of the prefixes above, a ``UnknownTestPath`` warning
    is emitted so the operator can update the prefix list.
    """
    warned_paths: set[str] = set()
    for item in items:
        existing = {m.name for m in item.iter_markers()}
        if "unit" in existing or "integration" in existing:
            continue
        path = str(item.fspath)
        if "/tests/e2e/" in path:
            continue
        if "/tests/bdd/" in path:
            item.add_marker(pytest.mark.bdd)
            continue
        if "/tests/audit_integration/" in path:
            item.add_marker(pytest.mark.integration)
            continue
        if any(prefix in path for prefix in _INTEGRATION_PREFIXES):
            item.add_marker(pytest.mark.integration)
            continue
        if path.endswith("/tests/conftest.py"):
            continue
        if any(path.endswith(p) for p in _UNIT_FILES):
            item.add_marker(pytest.mark.unit)
            continue
        item.add_marker(pytest.mark.unit)
        if path not in warned_paths:
            warned_paths.add(path)
            import warnings

            warnings.warn(
                f"{path} matches no integration prefix and is not in tests/e2e/. "
                f"Tagged as unit. If this file hits DB / TestClient, "
                f"add its prefix to _INTEGRATION_PREFIXES in tests/conftest.py.",
                UnknownTestPath,
                stacklevel=2,
            )
