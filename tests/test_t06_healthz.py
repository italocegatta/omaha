"""T06: ``/healthz`` with DB readiness probe.

The /healthz endpoint is the contract for the Dockerfile HEALTHCHECK
and the prod nginx healthcheck. It runs ``SELECT 1`` against the DB
and returns:

- 200 + the full JSON payload on success (process is alive AND the
  DB is reachable).
- 503 + a structured failure payload when the engine raises (process
  is alive but the DB is the failing component; the orchestrator
  should NOT restart the container).

The endpoint is intentionally auth-free: orchestrators and load
balancers hit it with no session cookie.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

# ``omaha.db.get_db`` and ``omaha.main.app`` are imported *inside* the
# test bodies. The session-scoped ``_omaha_test_env`` fixture in
# ``tests/conftest.py`` clears every ``omaha.*`` entry from
# ``sys.modules`` and re-imports them so the in-process engine points
# at the per-session SQLite file. Module-level imports here would
# capture the pre-fixture (stale) callable, and the override would
# miss the live ``get_db`` referenced by ``omaha.auth.DbSession``.


def test_healthz_returns_200_when_db_reachable(client: TestClient) -> None:
    """A real DB on a healthy app returns 200 with the full JSON payload."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["service"] == "omaha"
    assert body["version"] == "0.1.0"


def test_healthz_returns_503_with_db_down_when_engine_raises(
    client: TestClient,
) -> None:
    """A session whose ``.execute()`` raises returns 503 + structured failure.

    The reason field surfaces the exception class name (not the
    traceback) so the orchestrator can route on it without parsing
    free-form text.
    """
    # Late imports so the override key matches the live ``get_db``
    # bound by the session-scoped ``_omaha_test_env`` fixture.
    from omaha.db import get_db
    from omaha.main import app

    def _failing_get_db() -> Any:
        session = MagicMock()
        session.execute.side_effect = OperationalError(
            "SELECT 1", {}, Exception("connection lost")
        )
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _failing_get_db
    try:
        response = client.get("/healthz")
    finally:
        # Pop the override so it does not leak into the next test.
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] == "down"
    assert body["reason"] == "OperationalError"
    assert body["service"] == "omaha"
    assert body["version"] == "0.1.0"


def test_healthz_json_shape_matches_contract_on_200(client: TestClient) -> None:
    """The 200 response has exactly ``status, db, service, version`` — nothing else.

    No auth fields leak (no ``user_id``, no ``active_profile_id``);
    no DB row data leaks (no count, no path). The contract is the
    four documented keys in that order.
    """
    response = client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert list(body.keys()) == ["status", "db", "service", "version"]
    # Defensive: no auth / DB internals bleed into the response.
    assert "user_id" not in body
    assert "active_profile_id" not in body
    assert "tables" not in body
    assert "url" not in body


def test_healthz_does_not_require_auth(client: TestClient) -> None:
    """A bare GET /healthz with no cookies returns 200, not a 303 to /login.

    The orchestrator + the Dockerfile HEALTHCHECK both hit the
    endpoint without a session cookie; auth would break the probe.
    """
    # Late import so the ``app`` matches the one wired by the
    # session-scoped ``_omaha_test_env`` fixture.
    from omaha.main import app

    # Make a *fresh* client (no cookies shared from earlier tests in
    # the session) and hit /healthz without ever logging in.
    with TestClient(app) as fresh_client:
        response = fresh_client.get("/healthz", follow_redirects=False)

    assert response.status_code == 200
    # No redirect to /login (the auth requirement is exactly what we
    # are testing against).
    assert response.headers.get("location", "") == ""
    assert "/login" not in response.text
