"""End-to-end test for class CRUD with reactive validation (S03).

The class editor lives at ``GET /classes`` (a dedicated template) and
POSTs to the same URL. The form sends parallel arrays via
``class_id[]``, ``name[]``, ``target_pct[]`` (matching the FastAPI form
aliases declared in ``omaha.routes.classes``) and a comma-separated
``deleted_ids`` field for rows the Alpine editor removed client-side.

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

    Mirrors the T02 fixture in test_t02_classes_routes.py — the
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
    """Log in as ``family`` and select the named profile (defaults to Italo)."""
    client.post("/login", data={"username": "family", "password": TEST_PASSWORD})
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
        """Add 3 classes summing to 100: save succeeds, classes visible in editor."""
        profile = _login_and_select_profile(client)

        # Create 3 classes
        resp = client.post(
            "/classes",
            data={
                "name[]": ["Renda Fixa", "Acoes", "Reserva"],
                "target_pct[]": ["60.00", "30.00", "10.00"],
                "class_id[]": ["", "", ""],
                "deleted_ids": "",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert 'data-testid="class-editor"' in resp.text

        # Verify DB state
        classes = _classes_for_profile(profile.id)
        assert len(classes) == 3
        assert classes[0].name == "Renda Fixa"
        assert classes[1].name == "Acoes"
        assert classes[2].name == "Reserva"
        assert abs(float(classes[0].target_pct) - 60.0) < 0.01
        assert abs(float(classes[1].target_pct) - 30.0) < 0.01
        assert abs(float(classes[2].target_pct) - 10.0) < 0.01

    def test_save_blocked_when_sum_not_100(self, client: TestClient):
        """Adding less than 100% is rejected with error message."""
        profile = _login_and_select_profile(client)

        resp = client.post(
            "/classes",
            data={
                "name[]": ["Renda Fixa", "Acoes"],
                "target_pct[]": ["60.00", "30.00"],
                "class_id[]": ["", ""],
                "deleted_ids": "",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # The form re-renders with the editor + a Falta/Sobra message.
        assert 'data-testid="class-editor"' in resp.text
        assert "falta" in resp.text.lower() or "faltam" in resp.text.lower()

        # Verify nothing was committed
        count = len(_classes_for_profile(profile.id))
        assert count == 0

    def test_edit_class_name(self, client: TestClient):
        """Editing an existing class name is saved correctly."""
        profile = _login_and_select_profile(client)

        # Create a class first (via API to mirror the real flow)
        resp = client.post(
            "/classes",
            data={
                "name[]": ["OldName"],
                "target_pct[]": ["100.00"],
                "class_id[]": [""],
                "deleted_ids": "",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        created = _classes_for_profile(profile.id)
        assert len(created) == 1
        cid = created[0].id

        # Edit it
        resp = client.post(
            "/classes",
            data={
                "name[]": ["NewName"],
                "target_pct[]": ["100.00"],
                "class_id[]": [str(cid)],
                "deleted_ids": "",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        updated = _classes_for_profile(profile.id)
        assert len(updated) == 1
        assert updated[0].name == "NewName"
        assert updated[0].id == cid

    def test_delete_class_and_add_new(self, client: TestClient):
        """Delete a class and add a replacement, sum still 100."""
        profile = _login_and_select_profile(client)

        # Create 2 classes summing to 100
        resp = client.post(
            "/classes",
            data={
                "name[]": ["Fix", "Var"],
                "target_pct[]": ["60.00", "40.00"],
                "class_id[]": ["", ""],
                "deleted_ids": "",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        created = _classes_for_profile(profile.id)
        assert len(created) == 2
        ac1, ac2 = created

        # Delete Fix, keep Var at 40, add Reserva at 60
        resp = client.post(
            "/classes",
            data={
                "name[]": ["Var", "Reserva"],
                "target_pct[]": ["40.00", "60.00"],
                "class_id[]": [str(ac2.id), ""],
                "deleted_ids": str(ac1.id),
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        # Verify: ac1 deleted, ac2 (Var) still exists, Reserva added
        remaining = _classes_for_profile(profile.id)
        assert len(remaining) == 2
        names = [c.name for c in remaining]
        assert "Reserva" in names
        assert "Var" in names
        assert "Fix" not in names

    def test_class_editor_has_data_testid_hooks(self, client: TestClient):
        """Class editor renders with expected data-testid hooks."""
        _login_and_select_profile(client)

        resp = client.get("/classes")
        assert resp.status_code == 200
        assert 'data-testid="class-editor"' in resp.text
        assert 'data-testid="class-editor-total"' in resp.text
        assert 'data-testid="class-editor-add"' in resp.text
        assert 'data-testid="class-editor-save"' in resp.text
