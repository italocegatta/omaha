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

────────────────────────────────────────────────────────────────────────
PROD-DB ISOLATION CONTRACT — DO NOT REMOVE OR REORDER
────────────────────────────────────────────────────────────────────────
The block immediately below sets ``DATABASE_URL`` and friends to a
session-scoped tmp file AND force-imports ``omaha.db`` BEFORE pytest
discovers any test module. This is mandatory because tests like
``tests/test_rebalance_engine_glue.py`` and
``tests/test_import_get_preview.py`` do
``from omaha.db import SessionLocal`` inside autouse fixtures
(``_wipe_tables`` / ``_clean_data``). If omaha.db was first imported
with the prod default ``sqlite:///./data/portfolio.db`` (see
``src/omaha/config.py``), SessionLocal would bind to the prod DB and
the fixtures would wipe + re-seed the prod portfolio on every test
run — the exact corruption observed 2026-07-07 (RF+RV+Selic+
ETF BOVA11 × R$ 6k+R$ 4k).

The defense-in-depth safety guard inside each ``_wipe_tables`` /
``_clean_data`` raises ``RuntimeError`` if SessionLocal ends up bound
to prod, so a future regression that breaks this contract fails LOUD
instead of silently corrupting the household's portfolio DB.

Tests that need full FastAPI client access (``client`` fixture) still
hit the same session-scoped tmp DB via ``_omaha_test_env``. Tests that
use ``SessionLocal`` directly use the same DB because the import was
already bound by this module-load block.
────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

# CRITICAL ORDERING: env setup + omaha.db import must happen BEFORE any
# `import pytest` and BEFORE pytest discovers test modules. Keep this
# block at the very top of the file.
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Per-session safe DB — created via tempfile.mkdtemp so it survives the
# full pytest session even when tests use tmp_path fixtures internally.
_SAFE_DB_DIR = Path(tempfile.mkdtemp(prefix="omaha-conftest-safe-"))
_SAFE_DB_FILE = _SAFE_DB_DIR / "portfolio.db"
_SAFE_SNAPSHOT_DIR = _SAFE_DB_DIR / "snapshots"
_SAFE_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DATABASE_URL", f"sqlite:///{_SAFE_DB_FILE}")
os.environ.setdefault("SNAPSHOT_SOURCE", str(_SAFE_DB_FILE))
os.environ.setdefault("SNAPSHOT_DEST_DIR", str(_SAFE_SNAPSHOT_DIR))
os.environ.setdefault("SECRET_KEY", "test-secret-do-not-use")
os.environ.setdefault("ADMIN_PASSWORD", "test-password")
os.environ.setdefault("OMAHA_SKIP_STARTUP", "1")
os.environ.setdefault("OMAHA_ENV", "development")

# Force-import omaha.config + omaha.db NOW so SessionLocal is bound to
# the safe DB. Any subsequent `from omaha.db import SessionLocal` in
# test modules resolves to this same instance.
import omaha.config  # noqa: F401, E402 — populates ``settings``
import omaha.db  # noqa: F401, E402 — populates engine + SessionLocal

# Run alembic migrations against the safe DB so schema exists when tests
# query. Idempotent — safe to run even if the DB is empty.
_REPO_ROOT_FOR_ALEMBIC = Path(__file__).resolve().parent.parent
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    cwd=str(_REPO_ROOT_FOR_ALEMBIC),
    env={**os.environ},
    check=True,
    capture_output=True,
    text=True,
)

# NOW we can import pytest + fastapi. Anything below this line runs
# AFTER SessionLocal is bound to the safe DB.
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_SECRET_KEY = "test-secret-do-not-use"
TEST_ADMIN_PASSWORD = "test-password"


# Seed users + profiles in the safe DB so tests that query for
# "Italo" / "Ana" / "Família" find them. Idempotent — no-op if users
# already present (e.g. when `_omaha_test_env` fixture runs again).
import omaha.seed  # noqa: E402

omaha.seed.seed()


def _verify_session_local_is_safe() -> None:
    """Defense-in-depth check called by every autouse wipe/clean fixture.

    If SessionLocal is somehow bound to ``data/portfolio.db`` at test
    time, raise hard instead of silently corrupting prod. The conftest
    module-load block above guarantees this never happens in a normal
    pytest run; this guard exists to make regressions LOUD.
    """
    from omaha.db import SessionLocal

    probe = SessionLocal()
    try:
        bind = probe.get_bind()
        url = str(bind.url) if bind is not None else ""
        if "data/portfolio.db" in url or url.endswith("/data/portfolio.db"):
            raise RuntimeError(
                f"PROD-DB ISOLATION BROKEN: SessionLocal is bound to "
                f"prod DB ({url!r}). Conftest env isolation failed — "
                f"refusing to run any test that would wipe/seed prod. "
                f"See conftest.py module-load block."
            )
    finally:
        probe.close()


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


@pytest.fixture(scope="session", autouse=True)
def _omaha_test_env(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """Prepare a one-time test database for the session.

    **DEPRECATED 2026-07-07:** the env setup + omaha.db import +
    alembic upgrade + seed now happen at MODULE LOAD above (so
    ``SessionLocal`` is bound to a safe DB BEFORE pytest discovers
    any test module). This fixture is kept for backward compat with
    ``client`` fixture callers that request ``_omaha_test_env`` —
    it re-runs seed (idempotent no-op if users exist) and returns
    the safe DB path for tests that need it.

    **autouse=True:** guarantees ``_omaha_test_env`` runs at
    session start so the seed runs even if no test requests it.
    """
    db_file = Path(os.environ["DATABASE_URL"].replace("sqlite:///", ""))
    return {"db_path": str(db_file), "db_url": os.environ["DATABASE_URL"]}


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
    "tests/test_household_aggregate.py",
    "tests/test_family_aggregate.py",
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
    "tests/test_rebalance_engine_glue.py",
    "tests/test_rebalance_glue.py",
    "tests/test_rebalance_page.py",
    "tests/test_rebalance_route.py",
    "tests/test_rebalance_schemas.py",
    "tests/test_market_prices_adapter.py",
    "tests/test_seed.py",
    "tests/test_seed_from_csv.py",
    "tests/test_snapshot_to_csv.py",
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
        "tests/test_rebalance_constants.py",
        "tests/test_rebalance_engine_regression.py",
        "tests/test_rebalance_policy.py",
        "tests/test_rebalance_postprocessing.py",
        "tests/test_rebalance_solver.py",
        "tests/test_rebalance_validation.py",
        "tests/test_dark_mode_tokens.py",
        "tests/test_typography_tokens.py",
        "tests/test_yfinance_provider.py",
        "tests/test_quote_provider_selector.py",
        "tests/test_quote_provider_stub.py",
        "tests/test_seed_from_csv_loaders.py",
        "tests/test_seed_from_csv_validation.py",
        "tests/test_iconography_tokens.py",
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
