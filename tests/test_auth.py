"""T03: end-to-end auth flow against the FastAPI app.

Each test exercises a single step of the documented flow:

1. ``test_index_unauthenticated_redirects_to_login`` — a bare
   ``GET /`` against an empty session gets a 303 pointing at
   ``/login``.
2. ``test_login_wrong_password_rerenders_form`` — ``POST /login``
   with the right username but a bad password re-renders the form
   with a 200 status and a non-empty error message; the session is
   not bound to a user.
3. ``test_login_correct_password_redirects_to_dashboard`` — a
   successful login sets the ``omaha_session`` cookie, binds
   ``active_profile_id`` to the logged-in user's first profile, and
   303s to ``/``. There is no intermediate profile picker — the
   user lands directly on their own dashboard.
4. ``test_select_profile_redirects_to_dashboard`` — ``POST
   /profiles/{id}/select`` writes ``active_profile_id`` to the
   session and 303s to ``/``. Cross-profile switching is now
   allowed; the route accepts any existing profile id.
5. ``test_index_with_active_profile_renders_dashboard`` — with an
   active profile in the session, ``GET /`` renders the dashboard
   template and the active profile's name appears in the body.
6. ``test_logout_clears_session`` — ``POST /logout`` clears the
   session and 303s to ``/login``; a follow-up ``GET /`` then bounces
   back to ``/login`` because the session no longer has a user id.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_index_unauthenticated_redirects_to_login(client: TestClient) -> None:
    """`GET /` with no session cookie bounces to /login."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_wrong_password_rerenders_form(client: TestClient) -> None:
    """A bad password re-renders the form (200) and does not log the user in."""
    response = client.post(
        "/login",
        data={"username": "Italo", "password": "WRONG"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # The error message is rendered into a dedicated element with
    # ``data-testid="login-error"`` so this test does not couple to
    # the production copy that T04 will introduce.
    assert "login-error" in response.text
    assert "Usuário ou senha inválidos" in response.text

    # Session must not have a user id after a failed login — the
    # follow-up `GET /` should still bounce to /login.
    follow_up = client.get("/", follow_redirects=False)
    assert follow_up.status_code == 303
    assert follow_up.headers["location"] == "/login"


def test_login_correct_password_redirects_to_dashboard(client: TestClient) -> None:
    """A good password sets the cookie, binds the landing profile, and 303s to /."""
    response = client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    # The session cookie is set on the client. Subsequent requests on
    # the same client will carry it.
    assert "omaha_session" in response.cookies

    # And the follow-up ``GET /`` is now authenticated — the dashboard
    # renders without any intermediate /profiles step.
    dashboard = client.get("/", follow_redirects=False)
    assert dashboard.status_code == 200
    assert "Italo" in dashboard.text


def test_select_profile_redirects_to_dashboard(client: TestClient) -> None:
    """After login, picking profile 2 (cross-profile) still binds and 303s to '/'.

    Cross-profile switching is now allowed: the route's per-user
    ownership check was removed. We pick profile 2 (Ana) while
    logged in as Italo and verify the session binds to it.
    """
    # Log in first.
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )

    response = client.post("/profiles/2/select", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_index_with_active_profile_renders_dashboard(client: TestClient) -> None:
    """With an active profile, GET / renders the dashboard for that profile.

    Login auto-binds the landing profile, so the follow-up GET /
    renders Ana's dashboard without an explicit /profiles step.
    The profile name surfaces in the sidebar wordmark (the new
    header chip also shows it but the testid stays stable).
    """
    client.post(
        "/login",
        data={"username": "Ana", "password": "test-password"},
        follow_redirects=False,
    )

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # The h1 "profile-name" element was removed by
    # direct-landing-with-header-profile-switcher; the profile name
    # is now rendered in the sidebar wordmark and the header chip.
    assert "profile-name" not in response.text
    # Header chip is present.
    assert 'data-testid="profile-switcher"' in response.text
    assert "Ana" in response.text


def test_logout_clears_session(client: TestClient) -> None:
    """`POST /logout` clears the session and 303s to /login."""
    # Establish a logged-in session first.
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    # Sanity check: a protected page is reachable.
    pre_logout = client.get("/", follow_redirects=False)
    # Login auto-bound the landing profile, so / renders 200 directly.
    assert pre_logout.status_code == 200

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    # The session cookie is cleared in the response, so the follow-up
    # `GET /` is unauthenticated and bounces back to /login.
    post_logout = client.get("/", follow_redirects=False)
    assert post_logout.status_code == 303
    assert post_logout.headers["location"] == "/login"


def test_stale_active_profile_redirects_to_login(client: TestClient) -> None:
    """A stale ``active_profile_id`` (nonexistent row) clears and redirects to /login.

    Log in as Italo (auto-binds profile 1), then delete that profile
    so the session's ``active_profile_id`` points at a row that no
    longer exists. ``GET /`` must clear the stale key and redirect
    to ``/login`` (NOT ``/profiles`` — the picker is gone).

    Teardown re-creates the Italo profile with the SAME id it had
    before so downstream tests that assume profile_id=1 (the seeded
    value) continue to work — the DB is session-scoped and shared
    across modules. Using a new autoincrement id would silently
    break later tests that hard-code profile_id=1 in seeds/POSTs.
    """
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )

    from sqlalchemy import text

    from omaha.db import SessionLocal
    from omaha.models import Profile, User

    db = SessionLocal()
    try:
        italo = db.query(User).filter(User.username == "Italo").first()
        assert italo is not None
        profile = db.query(Profile).filter(Profile.user_id == italo.id).first()
        assert profile is not None
        old_profile_id = profile.id
        db.delete(profile)
        db.commit()
    finally:
        db.close()

    # The session still has active_profile_id pointing at a row
    # that no longer exists. GET / must clear + redirect to /login.
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    # Re-create the Italo profile with the SAME id so downstream
    # tests that hard-code profile_id=1 in seed data + POSTs
    # continue to find the right profile. SQLite allows explicit
    # id reuse after a delete (the rowid is freed).
    db = SessionLocal()
    try:
        db.execute(
            text(
                "INSERT INTO profiles (id, user_id, name, display_order, created_at) "
                "VALUES (:id, :uid, 'Italo', 0, :ts)"
            ),
            {
                "id": old_profile_id,
                "uid": italo.id,
                "ts": "2026-01-01 00:00:00",
            },
        )
        db.commit()
    finally:
        db.close()
