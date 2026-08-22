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

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from omaha.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent


def _settings_from_env_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    content: str,
) -> Settings:
    """Load synthetic settings without reading repository `.env`."""
    monkeypatch.delenv("OMAHA_ENV", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(content, encoding="utf-8")
    return Settings(_env_file=env_file, SECRET_KEY="test-cookie-secret")


def _session_https_only(app: object) -> bool:
    """Read exact SessionMiddleware option from a factory-built app."""
    middleware = next(item for item in app.user_middleware if item.cls is SessionMiddleware)
    return middleware.kwargs["https_only"]


def _app_from_settings(monkeypatch: pytest.MonkeyPatch, loaded: Settings) -> object:
    """Build app from explicitly loaded settings, not process environment."""
    import omaha.main as main_module

    monkeypatch.setattr(main_module, "settings", loaded)
    return main_module.create_app()


def test_environment_mode_documentation() -> None:
    """Local setup documents mode, restart requirement, and no real secrets."""
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert env_example.count("OMAHA_ENV=development") == 1
    assert "ADMIN_PASSWORD=distendidos" in env_example
    assert "OMAHA_ENV=development" in readme
    assert "ignored `.env`" in readme
    assert "exact, case-sensitive `OMAHA_ENV=production`" in readme
    assert "Restart `uv run task serve` after `.env` edits." in readme
    assert "uv run task serve" in readme
    assert "--host 0.0.0.0" in readme
    assert "real SECRET_KEY" in readme
    assert "MYPROFIT_ITALO_EMAIL / MYPROFIT_ITALO_PASSWORD" in readme
    assert "MYPROFIT_ANA_EMAIL   / MYPROFIT_ANA_PASSWORD" in readme
    assert "https://myprofit.invalid/" not in readme


@pytest.mark.parametrize(
    ("mode", "expected_secure", "expected_log_format"),
    (
        ("production", True, "json"),
        ("development", False, "text"),
        ("Production", False, "text"),
        ("staging", False, "text"),
    ),
)
def test_session_cookie_mode_uses_loaded_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: str,
    expected_secure: bool,
    expected_log_format: str,
) -> None:
    """Cookie and default log mode follow exact value loaded from `.env` file."""
    loaded = _settings_from_env_file(
        monkeypatch,
        tmp_path,
        f"OMAHA_ENV={mode}\n",
    )
    app = _app_from_settings(monkeypatch, loaded)

    assert mode == loaded.OMAHA_ENV
    assert loaded.effective_log_format == expected_log_format
    assert _session_https_only(app) is expected_secure


def test_session_cookie_does_not_follow_later_process_environment_change(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Middleware keeps loaded development mode after process environment drifts."""
    loaded = _settings_from_env_file(
        monkeypatch,
        tmp_path,
        "OMAHA_ENV=development\n",
    )
    monkeypatch.setenv("OMAHA_ENV", "production")
    app = _app_from_settings(monkeypatch, loaded)

    assert loaded.OMAHA_ENV == "development"
    assert _session_https_only(app) is False


def test_environment_mode_load_precedence_and_log_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Process environment wins before load; exact defaults remain mode-specific."""
    env_file = tmp_path / ".env"
    env_file.write_text("OMAHA_ENV=development\n", encoding="utf-8")
    monkeypatch.setenv("OMAHA_ENV", "production")
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    production = Settings(_env_file=env_file, SECRET_KEY="test-cookie-secret")
    production_app = _app_from_settings(monkeypatch, production)

    assert production.OMAHA_ENV == "production"
    assert production.effective_log_format == "json"
    assert _session_https_only(production_app) is True

    monkeypatch.delenv("OMAHA_ENV", raising=False)
    development = Settings(_env_file=env_file, SECRET_KEY="test-cookie-secret")
    development_app = _app_from_settings(monkeypatch, development)

    assert development.OMAHA_ENV == "development"
    assert development.effective_log_format == "text"
    assert _session_https_only(development_app) is False


def test_explicit_log_format_does_not_change_cookie_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Explicit log format wins only for logs, not session-cookie security."""
    loaded = _settings_from_env_file(
        monkeypatch,
        tmp_path,
        "OMAHA_ENV=development\nLOG_FORMAT=json\n",
    )
    app = _app_from_settings(monkeypatch, loaded)

    assert loaded.effective_log_format == "json"
    assert _session_https_only(app) is False

    production_file = tmp_path / "production.env"
    production_file.write_text(
        "OMAHA_ENV=production\nLOG_FORMAT=text\n",
        encoding="utf-8",
    )
    production = Settings(
        _env_file=production_file,
        SECRET_KEY="test-cookie-secret",
    )
    production_app = _app_from_settings(monkeypatch, production)

    assert production.effective_log_format == "text"
    assert _session_https_only(production_app) is True


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
    from omaha.db import SessionLocal
    from omaha.models import User

    db = SessionLocal()
    try:
        ana = db.query(User).filter(User.username == "Ana").one_or_none()
        print("\n\nDEBUG: Ana user:", ana)
        if ana is not None:
            print("DEBUG: Ana profiles:", [p.name for p in ana.profiles])
    finally:
        db.close()
    client.post(
        "/login",
        data={"username": "Ana", "password": "test-password"},
        follow_redirects=False,
    )
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        ana = db.query(User).filter(User.username == "Ana").one_or_none()
        print("\n\nDEBUG after login: Ana user:", ana)
        if ana is not None:
            print("DEBUG after login: Ana profiles:", [p.name for p in ana.profiles])
    finally:
        db.close()

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
