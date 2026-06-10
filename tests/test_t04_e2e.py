"""T04: end-to-end integration test for the foundation + auth slice.

This is the integration-closure proof for S01: it drives the full
operator-facing flow with a single :class:`TestClient` and asserts
that the response chain (login → profile pick → dashboard → logout)
binds the session cookie correctly and renders the production
template copy.

The test is intentionally a single happy-path narrative — every step
re-uses the cookie state the previous step wrote — because the
existing T03 suite already covers each step in isolation
(wrong password, missing profile, etc.). This file proves the steps
compose into the demo the slice plan advertises.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clean_asset_classes() -> None:
    """Wipe the ``asset_classes`` table so the dashboard renders the empty state.

    The T04 flow asserts the empty-state copy, which only renders
    when the active profile has zero classes. Without this fixture
    the T03 snapshot tests would leave rows behind and T04 would
    see the populated summary instead.
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_full_login_profile_dashboard_logout_flow(client: TestClient) -> None:
    """The demo end-to-end: login → pick Italo → see dashboard → logout.

    Steps:

    1. ``GET /login`` renders the form (200, text/html).
    2. ``POST /login`` with the seed credentials sets the
       ``omaha_session`` cookie and 303s to ``/profiles``.
    3. ``GET /profiles`` renders both seeded profiles.
    4. ``POST /profiles/1/select`` (Italo) 303s to ``/``.
    5. ``GET /`` renders the dashboard with "Bem-vindo, Italo" in
       the body — the slice demo's payoff line.
    6. ``POST /logout`` clears the session and 303s to ``/login``.
    7. A follow-up ``GET /`` bounces to ``/login`` because the
       session is empty.
    """
    # 1. Login form is reachable without a session.
    login_form = client.get("/login")
    assert login_form.status_code == 200
    assert "text/html" in login_form.headers["content-type"]
    # The form posts back to /login and asks for the shared password.
    assert 'action="/login"' in login_form.text

    # 2. Valid credentials → 303 to /profiles + the session cookie.
    login_response = client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/profiles"
    assert "omaha_session" in login_response.cookies
    cookie_value = login_response.cookies["omaha_session"]
    # Starlette signs the cookie — even on an empty session the value is
    # non-empty. We assert non-emptiness here as a sanity check that the
    # middleware actually wrote a cookie.
    assert cookie_value, "omaha_session cookie should be non-empty after login"

    # 3. Profile picker is reachable and lists both seed profiles.
    profiles_page = client.get("/profiles")
    assert profiles_page.status_code == 200
    assert "Italo" in profiles_page.text
    assert "Ana Livia" in profiles_page.text

    # 4. Selecting Italo (profile id 1) 303s to the dashboard.
    select_response = client.post("/profiles/1/select", follow_redirects=False)
    assert select_response.status_code == 303
    assert select_response.headers["location"] == "/"

    # 5. The dashboard renders the production copy. The T04 plan's
    #    payoff line is "Bem-vindo, Italo" — its presence proves the
    #    base.html / dashboard.html wiring reached the response body.
    dashboard = client.get("/", follow_redirects=False)
    assert dashboard.status_code == 200
    assert "text/html" in dashboard.headers["content-type"]
    assert "Bem-vindo, Italo" in dashboard.text
    # The empty-state copy is also rendered on this slice's dashboard
    # so an operator who reaches the page knows where to look next.
    assert "Sem classes ainda" in dashboard.text

    # 6. Logout clears the session and 303s back to the login form.
    logout_response = client.post("/logout", follow_redirects=False)
    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/login"

    # 7. The follow-up GET / is unauthenticated and bounces to /login.
    after_logout = client.get("/", follow_redirects=False)
    assert after_logout.status_code == 303
    assert after_logout.headers["location"] == "/login"


def test_healthz_is_reachable_without_session(client: TestClient) -> None:
    """`/healthz` returns the documented JSON without auth or DB access.

    The T03 suite already covers the JSON payload shape; this test
    pins the *unauthenticated* path because `/healthz` is the
    orchestrator's liveness probe and must work for an empty cookie
    jar (i.e. before the user has logged in). S06 extended the
    payload with ``db`` and ``version`` so the endpoint can drive a
    Dockerfile HEALTHCHECK + an orchestrator readiness probe.
    """
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["service"] == "omaha"
    assert body["version"] == "0.1.0"
