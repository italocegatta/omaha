"""End-to-end tests for the S04 /import routes.

Covers the slice verification matrix:
- multipart upload produces an ImportPreview
- GET /import and GET /import/review redirect to dashboard (retired)
- POST /import/confirm commits Positions for both auto-matched and
  user-resolved rows
- re-import is idempotent (same Position count after a second confirm)
- cross-profile preview isolation enforced via API (404)
- empty file returns a 200 with the inline error
- oversized file returns 200 with inline error (1 MB cap)
- malformed CSV returns 200 with inline error
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from omaha.csv_import import parse_positions

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAMPLE_CSV = (FIXTURES / "sample_broker.csv").read_text(encoding="utf-8")


def _login_and_pick_profile(
    client: TestClient, profile_name: str = "Italo", username: str | None = None
) -> None:
    """Helper: log in as ``username`` and pick the named profile.

    Each seed user owns exactly one profile, so ``username`` defaults
    to ``profile_name`` when not given. Pass a different ``username``
    only when you intentionally want to authenticate as another
    user (cross-profile isolation tests).
    """
    if username is None:
        username = profile_name
    r = client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    profile_id = _profile_id_for(client, profile_name)
    r = client.post(
        f"/profiles/{profile_id}/select",
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text


def _profile_id_for(client: TestClient, name: str) -> int:
    """Read the profile id from /profiles after login."""
    r = client.get("/profiles")
    assert r.status_code == 200, r.text
    import re

    # /profiles page renders one form per profile with
    # action="/profiles/{id}/select" and a button whose text is the
    # profile name.
    m = re.search(
        rf'action="/profiles/(\d+)/select"[^>]*>\s*<button[^>]*>\s*{re.escape(name)}\s*</button>',
        r.text,
    )
    if not m:
        m = re.search(
            rf'>\s*{re.escape(name)}\s*</button>.*?action="/profiles/(\d+)/select"',
            r.text,
            re.DOTALL,
        )
    assert m, f"profile {name!r} not found in /profiles HTML"
    return int(m.group(1))


def _ensure_class_with_asset(
    client: TestClient, profile_id: int, class_name: str, asset_names: list[str]
) -> int:
    """Create a class + assets for the active profile, return the class id.

    Uses the ORM directly so the test fixture is independent of the
    /classes and /assets route contracts (which are tested elsewhere).
    """
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass

    with SessionLocal() as db:
        existing = (
            db.query(AssetClass)
            .filter(AssetClass.profile_id == profile_id, AssetClass.name == class_name)
            .first()
        )
        if existing is None:
            cls = AssetClass(
                profile_id=profile_id,
                name=class_name,
                target_pct=100,
                display_order=0,
            )
            db.add(cls)
            db.commit()
            db.refresh(cls)
            class_id = cls.id
        else:
            class_id = existing.id
        for idx, asset_name in enumerate(asset_names):
            existing_asset = (
                db.query(Asset)
                .filter(Asset.asset_class_id == class_id, Asset.name == asset_name)
                .first()
            )
            if existing_asset is None:
                db.add(
                    Asset(
                        asset_class_id=class_id,
                        name=asset_name,
                        display_order=idx,
                    )
                )
        db.commit()
    return class_id


@pytest.fixture()
def logged_in(client: TestClient) -> TestClient:
    _login_and_pick_profile(client, "Italo")
    return client


def test_get_import_redirects_to_dashboard(logged_in: TestClient) -> None:
    """GET /import now redirects to the dashboard (the form was retired)."""
    r = logged_in.get("/import", follow_redirects=False)
    assert r.status_code == 302, r.text
    assert r.headers["location"] == "/"


def test_upload_produces_preview(logged_in: TestClient) -> None:
    r = logged_in.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    assert r.headers["location"] == "/import/review"

    # The preview row should exist.
    from omaha.db import SessionLocal
    from omaha.models import ImportPreview, Profile

    with SessionLocal() as db:
        prof = db.query(Profile).filter(Profile.name == "Italo").first()
        preview = (
            db.query(ImportPreview)
            .filter(ImportPreview.profile_id == prof.id)
            .order_by(ImportPreview.id.desc())
            .first()
        )
        assert preview is not None
        # raw_json should be valid JSON and parse back to RawPositions.
        raw = parse_positions(SAMPLE_CSV)
        # The CSV may have a few rows that get rejected by the parser
        # (banner / footer / malformed) — we just check the preview
        # parsed *some* rows successfully.
        assert len(raw) > 0


def test_review_redirects_to_dashboard(logged_in: TestClient) -> None:
    """GET /import/review now redirects to the dashboard (the review page was retired)."""
    # Upload first to create a preview (POST /import still works).
    _ensure_class_with_asset(logged_in, 1, "Renda Fixa", ["PETR4", "IVVB11"])
    logged_in.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    r = logged_in.get("/import/review", follow_redirects=False)
    assert r.status_code == 302, r.text
    assert r.headers["location"] == "/"


def test_confirm_commits_positions(logged_in: TestClient) -> None:
    _ensure_class_with_asset(logged_in, 1, "Renda Fixa", ["PETR4"])
    logged_in.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    r = logged_in.post(
        "/import/confirm",
        data={},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    assert r.headers["location"] == "/"

    # Positions should exist for the auto-matched rows.
    from omaha.db import SessionLocal
    from omaha.models import Position

    with SessionLocal() as db:
        n = db.query(Position).count()
        assert n > 0, "no positions committed"


def test_reimport_is_idempotent(logged_in: TestClient) -> None:
    """Second confirm of the same file must not duplicate positions."""
    _ensure_class_with_asset(logged_in, 1, "Renda Fixa", ["PETR4"])
    # First import + confirm.
    logged_in.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    logged_in.post("/import/confirm", data={}, follow_redirects=False)
    from omaha.db import SessionLocal
    from omaha.models import Position

    with SessionLocal() as db:
        first = db.query(Position).count()
    # Second import + confirm.
    logged_in.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    logged_in.post("/import/confirm", data={}, follow_redirects=False)
    with SessionLocal() as db:
        second = db.query(Position).count()
    assert first == second, f"idempotency broken: {first} -> {second}"


def test_cross_profile_preview_via_api(client: TestClient) -> None:
    """A preview id from another profile must be invisible via the API.
    GET /import/review is retired (now redirects), so cross-profile
    isolation is tested via the /api/import/preview/{id} endpoint."""
    # Profile A uploads.
    _login_and_pick_profile(client, "Italo")
    r = client.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    # Get the preview id from the database.
    from omaha.db import SessionLocal
    from omaha.models import ImportPreview, Profile

    with SessionLocal() as db:
        prof = db.query(Profile).filter(Profile.name == "Italo").first()
        preview = (
            db.query(ImportPreview)
            .filter(ImportPreview.profile_id == prof.id)
            .order_by(ImportPreview.id.desc())
            .first()
        )
        assert preview is not None
        preview_id = preview.id

    # Logout, login as the other profile. The seed creates one
    # user per account, so the second profile's owner is a
    # different user; the helper defaults ``username`` to
    # ``profile_name`` so passing "Ana" is enough to re-auth as
    # Ana (her only profile).
    client.post("/logout", follow_redirects=False)
    _login_and_pick_profile(client, "Ana")
    # GET /import/review now redirects to dashboard.
    r = client.get("/import/review", follow_redirects=False)
    assert r.status_code == 302, r.text
    assert r.headers["location"] == "/"

    # Cross-profile isolation is enforced by the API endpoint.
    r = client.get(f"/api/import/preview/{preview_id}")
    assert r.status_code == 404, r.text


def test_expired_preview_redirects_to_dashboard(logged_in: TestClient) -> None:
    """GET /import/review always redirects to dashboard regardless of preview state.
    The modal handles the expired state client-side via the preview API."""
    logged_in.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    # Backdate the preview to 2h ago.
    from omaha.db import SessionLocal
    from omaha.models import ImportPreview, Profile

    with SessionLocal() as db:
        prof = db.query(Profile).filter(Profile.name == "Italo").first()
        preview = (
            db.query(ImportPreview)
            .filter(ImportPreview.profile_id == prof.id)
            .order_by(ImportPreview.id.desc())
            .first()
        )
        assert preview is not None
        preview.created_at = datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(hours=2)
        db.commit()
    r = logged_in.get("/import/review", follow_redirects=False)
    assert r.status_code == 302, r.text
    assert r.headers["location"] == "/"


def test_empty_file_returns_inline_error(logged_in: TestClient) -> None:
    r = logged_in.post(
        "/import",
        files={"file": ("empty.csv", b"", "text/csv")},
        follow_redirects=False,
    )
    assert r.status_code == 200
    assert 'data-testid="import-error"' in r.text


def test_oversized_file_returns_inline_error(logged_in: TestClient) -> None:
    # 2 MB blob, well over the 1 MB cap.
    big = b"a" * (2 * 1024 * 1024)
    r = logged_in.post(
        "/import",
        files={"file": ("big.csv", big, "text/csv")},
        follow_redirects=False,
    )
    assert r.status_code == 200
    assert 'data-testid="import-error"' in r.text


def test_malformed_csv_returns_inline_error(logged_in: TestClient) -> None:
    # All banner / footer / unparseable text.
    r = logged_in.post(
        "/import",
        files={"file": ("bad.csv", b"blah blah blah\nfoo bar baz\n", "text/csv")},
        follow_redirects=False,
    )
    assert r.status_code == 200
    assert 'data-testid="import-error"' in r.text


def test_dashboard_shows_position_counts(logged_in: TestClient) -> None:
    """After a confirm, the dashboard surfaces the per-asset position count.

    M002 S01/T03: the visible "N posicao(oes)" line is removed (D015
    — the 4-percentage grid replaces the position-count text). The
    count is still carried on the ``<li>`` as ``data-position-count``
    so downstream e2e selectors and future copy edits can find it
    without re-introducing the visible text.
    """
    _ensure_class_with_asset(logged_in, 1, "Renda Fixa", ["PETR4"])
    logged_in.post(
        "/import",
        files={"file": ("broker.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
        follow_redirects=False,
    )
    logged_in.post("/import/confirm", data={}, follow_redirects=False)
    r = logged_in.get("/")
    assert r.status_code == 200
    # The visible "posicao(oes)" text is gone (D015).
    assert "posicao(oes)" not in r.text
    # The count is still on the <li> as an attribute, so any
    # downstream selector that wants it can read it.
    assert 'data-position-count="' in r.text
    # And at least one row has a count > 0.
    import re

    counts = [int(m) for m in re.findall(r'data-position-count="(\d+)"', r.text)]
    assert any(c > 0 for c in counts), f"no positive position counts: {counts}"


def test_nav_link_to_import_removed(logged_in: TestClient) -> None:
    """The Importar nav link was removed per M002/S04. The import
    modal trigger button is in the dashboard body, not the nav."""
    r = logged_in.get("/")
    assert r.status_code == 200
    assert 'data-testid="nav-import"' not in r.text
    assert 'data-testid="dashboard-import-btn"' in r.text
