"""T03: end-to-end auth flow against the FastAPI app.

Each test exercises a single step of the documented flow:

1. ``test_healthz_returns_ok`` — ``/healthz`` returns a 200 JSON
   payload with ``status="ok"`` and ``service="omaha"`` without
   touching the database or session.
2. ``test_index_unauthenticated_redirects_to_login`` — a bare
   ``GET /`` against an empty session gets a 303 pointing at
   ``/login``.
3. ``test_login_wrong_password_rerenders_form`` — ``POST /login``
   with the right username but a bad password re-renders the form
   with a 200 status and a non-empty error message; the session is
   not bound to a user.
4. ``test_login_correct_password_redirects_to_profiles`` — a
   successful login sets the ``omaha_session`` cookie, leaves the
   ``active_profile_id`` slot empty, and 303s to ``/profiles``.
5. ``test_select_profile_redirects_to_dashboard`` — once logged in,
   ``POST /profiles/1/select`` writes ``active_profile_id`` to the
   session and 303s to ``/``.
6. ``test_index_with_active_profile_renders_dashboard`` — with an
   active profile in the session, ``GET /`` renders the dashboard
   template and the active profile's name appears in the body.
7. ``test_logout_clears_session`` — ``POST /logout`` clears the
   session and 303s to ``/login``; a follow-up ``GET /`` then bounces
   back to ``/login`` because the session no longer has a user id.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz_returns_ok(client: TestClient) -> None:
    """`/healthz` returns 200 JSON with the documented payload."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok", "service": "omaha"}


def test_index_unauthenticated_redirects_to_login(client: TestClient) -> None:
    """`GET /` with no session cookie bounces to /login."""
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_wrong_password_rerenders_form(client: TestClient) -> None:
    """A bad password re-renders the form (200) and does not log the user in."""
    response = client.post(
        "/login",
        data={"username": "family", "password": "WRONG"},
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


def test_login_correct_password_redirects_to_profiles(client: TestClient) -> None:
    """A good password sets the cookie and 303s to /profiles."""
    response = client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/profiles"
    # The session cookie is set on the client. Subsequent requests on
    # the same client will carry it.
    assert "omaha_session" in response.cookies

    # And the follow-up ``GET /profiles`` is now authenticated.
    profiles_page = client.get("/profiles", follow_redirects=False)
    assert profiles_page.status_code == 200
    assert "Italo" in profiles_page.text
    assert "Ana Livia" in profiles_page.text


def test_select_profile_redirects_to_dashboard(client: TestClient) -> None:
    """After login, picking profile 1 binds the session and 303s to '/'."""
    # Log in first.
    client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )

    response = client.post("/profiles/1/select", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_index_with_active_profile_renders_dashboard(client: TestClient) -> None:
    """With an active profile, GET / renders the dashboard for that profile."""
    # Log in and select a profile.
    client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )
    client.post("/profiles/2/select", follow_redirects=False)  # Ana Livia (display_order=1)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Profile name is rendered into a dedicated element so the test
    # does not depend on the surrounding copy.
    assert "profile-name" in response.text
    assert "Ana Livia" in response.text


def test_logout_clears_session(client: TestClient) -> None:
    """`POST /logout` clears the session and 303s to /login."""
    # Establish a logged-in session first.
    client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )
    # Sanity check: a protected page is reachable.
    pre_logout = client.get("/", follow_redirects=False)
    # No active profile yet, so / -> /profiles.
    assert pre_logout.status_code == 303
    assert pre_logout.headers["location"] == "/profiles"

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    # The session cookie is cleared in the response, so the follow-up
    # `GET /` is unauthenticated and bounces back to /login.
    post_logout = client.get("/", follow_redirects=False)
    assert post_logout.status_code == 303
    assert post_logout.headers["location"] == "/login"
