"""End-to-end test for class CRUD with reactive validation (S03).

The class editor lives at ``GET /classes`` (a dedicated template) and
POSTs to the same URL. The form sends parallel arrays via
``name[]`` and ``target_pct[]`` (matching the FastAPI form aliases
declared in ``omaha.routes.classes``). The snapshot model (D016)
means no ``class_id[]`` and no ``deleted_ids`` — the route does a
delete-all-then-insert on every save.

These tests use the same seed password as the rest of the suite
(``"test-password"`` — the value the conftest installs via
``ADMIN_PASSWORD``). The T02 conftest's ``_clean_asset_classes``
autouse fixture keeps the ``asset_classes`` table empty between tests
in this file's module too (cross-module, autouse).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from omaha.models import AssetClass, Profile


@pytest.fixture(autouse=True)
def _clean_asset_classes() -> None:
    """Wipe the ``asset_classes`` table before each S03 e2e test.

    Mirrors the T02 fixture in test_classes_routes.py — the
    session-scoped DB persists between tests in this module too,
    so we clean up to keep the ``len(classes) == N`` assertions
    honest.
    """
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


TEST_PASSWORD = "test-password"


def _login_and_select_profile(client: TestClient, profile_name: str = "Italo") -> Profile:
    """Log in as ``Italo`` and select the named profile (defaults to Italo)."""
    client.post("/login", data={"username": "Italo", "password": TEST_PASSWORD})
    # Use a fresh session to read the profile (mirrors T02's
    # helper pattern: open a new SessionLocal so we see committed
    # state, not in-flight transaction state).
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.name == profile_name).first()
    finally:
        db.close()
    client.post(f"/profiles/{profile.id}/select")
    return profile


def _classes_for_profile(profile_id: int) -> list[AssetClass]:
    """Return the asset classes for ``profile_id`` ordered by display_order."""
    from omaha.db import SessionLocal

    db: Session = SessionLocal()
    try:
        return (
            db.query(AssetClass)
            .filter(AssetClass.profile_id == profile_id)
            .order_by(AssetClass.display_order)
            .all()
        )
    finally:
        db.close()


class TestClassesE2E:
    """Full end-to-end tests for the class editor."""

    def test_create_three_classes_sum_100(self, client: TestClient):
        """Add 3 classes summing to 100: save succeeds, dashboard shows the summary."""
        profile = _login_and_select_profile(client)

        resp = client.post(
            "/classes",
            data={
                "name[]": ["Renda Fixa", "Acoes", "Reserva"],
                "target_pct[]": ["60.00", "30.00", "10.00"],
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # After save, redirect goes to the dashboard, which shows
        # the saved classes as a summary.
        assert 'data-testid="class-summary"' in resp.text
        assert 'data-testid="class-summary-row"' in resp.text
        assert "Renda Fixa" in resp.text
        assert "Acoes" in resp.text
        assert "Reserva" in resp.text

        # Verify DB state
        classes = _classes_for_profile(profile.id)
        assert len(classes) == 3
        assert classes[0].name == "Renda Fixa"
        assert classes[1].name == "Acoes"
        assert classes[2].name == "Reserva"
        assert abs(float(classes[0].target_pct) - 60.0) < 0.01
        assert abs(float(classes[1].target_pct) - 30.0) < 0.01
        assert abs(float(classes[2].target_pct) - 10.0) < 0.01

    def test_save_succeeds_even_with_non_100_sum(self, client: TestClient):
        """Adding less than 100% succeeds — allocation is informational, not blocking.

        The snapshot ``POST /classes`` form no longer validates the
        sum-to-100 invariant. Classes at any valid percentage are
        created; the user builds the portfolio incrementally.
        """
        profile = _login_and_select_profile(client)

        resp = client.post(
            "/classes",
            data={
                "name[]": ["Renda Fixa", "Acoes"],
                "target_pct[]": ["60.00", "30.00"],
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # The dashboard shows the saved classes (redirected to /).
        assert 'data-testid="class-summary"' in resp.text
        assert "Renda Fixa" in resp.text
        assert "Acoes" in resp.text

        # Verify the classes were committed (both rows exist)
        count = len(_classes_for_profile(profile.id))
        assert count == 2

    def test_edit_class_via_snapshot_resubmit(self, client: TestClient):
        """Snapshot edit: re-submit with a new name; old row is gone, new row is the only one.

        With the partial-update model, a second POST could change
        the name of an existing row while preserving its id. The
        snapshot model drops identity — the old row is wiped, the
        new row is inserted. The user sees the same effect (their
        class is "renamed") but the underlying id is new.
        """
        profile = _login_and_select_profile(client)

        # Create a class first.
        resp = client.post(
            "/classes",
            data={
                "name[]": ["OldName"],
                "target_pct[]": ["100.00"],
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        created = _classes_for_profile(profile.id)
        assert len(created) == 1

        # Re-submit with the new name. The old id must not survive.
        resp = client.post(
            "/classes",
            data={
                "name[]": ["NewName"],
                "target_pct[]": ["100.00"],
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        updated = _classes_for_profile(profile.id)
        assert len(updated) == 1
        assert updated[0].name == "NewName"
        # Note: the new row's id can collide with ``old_id`` if
        # SQLite's autoincrement counter happens to reuse the
        # slot — we cannot rely on id inequality to prove the
        # snapshot fired. The on-disk row count and name are
        # enough.

    def test_dashboard_shows_seeded_classes(self, client: TestClient):
        """S02: GET / shows seeded classes in the dashboard (not empty).

        The old standalone editor started empty (D014). S02
        replaced it with the dashboard, which always renders
        existing classes as collapsible sections. Seeded classes
        must appear by name.
        """
        from decimal import Decimal

        from omaha.db import SessionLocal

        profile = _login_and_select_profile(client)

        db = SessionLocal()
        try:
            for idx, (name, pct) in enumerate(
                [("Legacy1", "40"), ("Legacy2", "40"), ("Legacy3", "20")]
            ):
                db.add(
                    AssetClass(
                        profile_id=profile.id,
                        name=name,
                        target_pct=Decimal(pct),
                        display_order=idx,
                    )
                )
            db.commit()
        finally:
            db.close()
        assert len(_classes_for_profile(profile.id)) == 3

        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.text
        # The dashboard now shows all classes as sections.
        assert "Legacy1" in body
        assert "Legacy2" in body
        assert "Legacy3" in body
