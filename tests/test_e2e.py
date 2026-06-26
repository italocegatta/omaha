"""T04: end-to-end integration test for the foundation + auth slice.

This is the integration-closure proof for S01: it drives the full
operator-facing flow with a single :class:`TestClient` and asserts
that the response chain (login → dashboard → logout) binds the
session cookie correctly and renders the production template copy.

The direct-landing change collapses the auth bootstrap: the user
goes straight from POST /login to GET / (no intermediate /profiles
picker). The test is intentionally a single happy-path narrative —
every step re-uses the cookie state the previous step wrote —
because the existing T03 suite already covers each step in isolation
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


def test_full_login_dashboard_logout_flow(client: TestClient) -> None:
    """The demo end-to-end: login → see dashboard → logout.

    Steps:

    1. ``GET /login`` renders the form (200, text/html).
    2. ``POST /login`` with the seed credentials sets the
       ``omaha_session`` cookie AND binds ``active_profile_id`` to
       the logged-in user's first profile. The response is 303 to
       ``/`` (no intermediate /profiles picker).
    3. ``GET /`` renders the dashboard directly. The
       ``data-testid="profile-switcher"`` chip is present and the
       active profile is marked ``selected``.
    4. ``POST /logout`` clears the session and 303s to ``/login``.
    5. A follow-up ``GET /`` bounces to ``/login`` because the
       session is empty.
    """
    # 1. Login form is reachable without a session.
    login_form = client.get("/login")
    assert login_form.status_code == 200
    assert "text/html" in login_form.headers["content-type"]
    # The form posts back to /login and asks for the shared password.
    assert 'action="/login"' in login_form.text

    # 2. Valid credentials → 303 to / + the session cookie.
    login_response = client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/"
    assert "omaha_session" in login_response.cookies
    cookie_value = login_response.cookies["omaha_session"]
    # Starlette signs the cookie — even on an empty session the value is
    # non-empty. We assert non-emptiness here as a sanity check that the
    # middleware actually wrote a cookie.
    assert cookie_value, "omaha_session cookie should be non-empty after login"

    # 3. The dashboard renders directly. The header chip is present
    #    and the active profile is marked selected.
    dashboard = client.get("/", follow_redirects=False)
    assert dashboard.status_code == 200
    assert "text/html" in dashboard.headers["content-type"]
    assert 'data-testid="profile-switcher"' in dashboard.text
    # The selected option in the chip carries the profile name (no ✓ glyph).
    assert ">Italo</option>" in dashboard.text
    # And that option carries the selected attribute.
    assert 'value="1" selected>Italo<' in dashboard.text
    # The onboarding empty-state copy is also rendered on this
    # slice's dashboard so an operator who reaches the page knows
    # where to look next. After dashboard-action-sidebar the empty
    # state is a 3-step onboarding card; the heading "Vamos comecar"
    # is the new payoff line.
    assert "Vamos comecar" in dashboard.text
    # direct-landing-with-header-profile-switcher: the h1 "Bem-vindo"
    # payoff is gone (the chip identifies the portfolio instead).
    assert "Bem-vindo" not in dashboard.text

    # 4. Logout clears the session and 303s back to the login form.
    logout_response = client.post("/logout", follow_redirects=False)
    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/login"

    # 5. The follow-up GET / is unauthenticated and bounces to /login.
    after_logout = client.get("/", follow_redirects=False)
    assert after_logout.status_code == 303
    assert after_logout.headers["location"] == "/login"
