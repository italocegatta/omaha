"""Integration tests for the R06 ``db-mutation-safety`` reactive layer.

Exercises the destructive routes end-to-end via the FastAPI
:class:`TestClient` against the per-test SQLite database. The
test DB is set up by ``tests/conftest.py::_omaha_test_env``;
each test wipes ``assets`` / ``asset_classes`` / ``db_snapshots``
/ ``db_mutations`` first so the audit + snapshot assertions
are deterministic.

The reactive layer is the *recovery* path for accidental
wipes, not a code-level gate. The cases below verify that
every destructive op:

1. Captures a pre-mutation snapshot to ``data/snapshots/``.
2. Writes a :class:`DbMutation` audit row after the commit
   with the route, actor, profile, before/after counts, and
   snapshot path.
3. Back-fills ``db_snapshots.mutation_id`` on the snapshot
   row so the admin ``/admin/snapshots`` listing can attach
   the mutation to the snapshot.

No code-level gate (``confirm`` flag, threshold, type-to-confirm)
is tested here — PRD §4.11 is the process contract, not a
code contract. The reactive layer's job is RECOVERY, not
prevention.

Cases
-----

1. ``test_snapshot_replace_writes_audit_and_snapshot`` — the
   happy path for ``POST /classes``: 303 redirect + 1 audit
   row + 1 snapshot file + ``db_snapshots.mutation_id`` is
   back-filled.
2. ``test_snapshot_file_is_valid_sqlite_with_pre_mutation_state``
   — the snapshot file is a valid SQLite file containing the
   pre-mutation class rows.
3. ``test_class_delete_form_writes_audit_and_snapshot`` —
   ``POST /classes/{id}/delete`` happy path.
4. ``test_class_delete_api_writes_audit_and_snapshot`` —
   ``DELETE /api/classes/{id}`` happy path.
5. ``test_asset_delete_form_writes_audit_and_snapshot`` —
   ``POST /assets/{id}/delete`` happy path.
6. ``test_asset_delete_api_writes_audit_and_snapshot`` —
   ``DELETE /api/assets/{id}`` happy path.
7. ``test_import_commit_writes_audit_and_snapshot`` —
   ``POST /api/import/commit`` happy path.
8. ``test_audit_count_equals_one_per_destructive_op`` —
   3 destructive ops → 3 audit rows + 3 snapshot files.
"""

from __future__ import annotations

import contextlib
import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_state() -> None:
    """Wipe DB rows + snapshot dir before each test."""
    from omaha.db import SessionLocal
    from omaha.models import (
        Asset,
        AssetClass,
        DbMutation,
        DbSnapshot,
        Position,
    )

    db = SessionLocal()
    try:
        db.query(Position).delete()
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.query(DbSnapshot).delete()
        db.query(DbMutation).delete()
        db.commit()
    finally:
        db.close()

    import os

    dest = Path(os.environ.get("SNAPSHOT_DEST_DIR", "data/snapshots"))
    if dest.exists():
        for f in dest.glob("portfolio-*.db"):
            with contextlib.suppress(OSError):
                f.unlink()

    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    profile_name = {1: "Italo", 2: "Ana"}.get(profile_id, "Italo")
    client.post(
        "/login",
        data={"username": profile_name, "password": "test-password"},
        follow_redirects=False,
    )


def _seed_classes(profile_id: int, rows: list[tuple[str, str]]) -> list[int]:
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        ids: list[int] = []
        for idx, (name, pct) in enumerate(rows):
            cls = AssetClass(
                profile_id=profile_id,
                name=name,
                target_pct=Decimal(pct),
                display_order=idx,
            )
            db.add(cls)
            db.flush()
            ids.append(cls.id)
        db.commit()
        return ids
    finally:
        db.close()


def _seed_assets(class_id: int, names: list[str]) -> list[int]:
    from omaha.db import SessionLocal
    from omaha.models import Asset

    db = SessionLocal()
    try:
        ids: list[int] = []
        for idx, name in enumerate(names):
            db.add(
                Asset(
                    asset_class_id=class_id,
                    name=name,
                    target_pct=Decimal("0"),
                    display_order=idx,
                )
            )
            db.flush()
            ids.append(idx + 1)  # placeholder; not used as IDs
        db.commit()
    finally:
        db.close()
    return ids


# ---------------------------------------------------------------------------
# Snapshot-replace: POST /classes
# ---------------------------------------------------------------------------


def test_snapshot_replace_writes_audit_and_snapshot(client: TestClient) -> None:
    """POST /classes happy path: 303, audit row, snapshot file, back-fill."""
    from omaha.db import SessionLocal
    from omaha.models import DbMutation, DbSnapshot

    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[(f"C{i}", "16.66") for i in range(6)],
    )
    r = client.post(
        "/classes",
        data={"name[]": ["A", "B", "C"], "target_pct[]": ["30", "30", "30"]},
        follow_redirects=False,
    )
    assert r.status_code == 303

    db = SessionLocal()
    try:
        mutations = db.query(DbMutation).all()
        assert len(mutations) == 1
        m = mutations[0]
        assert m.route == "POST /classes"
        assert m.profile_id is not None
        assert m.snapshot_path is not None
        snap = db.query(DbSnapshot).filter_by(path=m.snapshot_path).one()
        assert snap.mutation_id == m.id
    finally:
        db.close()


def test_snapshot_file_is_valid_sqlite_with_pre_mutation_state(
    client: TestClient,
) -> None:
    """The snapshot file is a valid SQLite DB containing the pre-mutation state."""
    import os

    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[(f"C{i}", "16.66") for i in range(6)],
    )
    client.post(
        "/classes",
        data={"name[]": ["A", "B", "C"], "target_pct[]": ["30", "30", "30"]},
        follow_redirects=False,
    )

    snap_dir = Path(os.environ.get("SNAPSHOT_DEST_DIR", "data/snapshots"))
    snaps = list(snap_dir.glob("portfolio-*.db"))
    assert len(snaps) == 1
    with sqlite3.connect(str(snaps[0])) as conn:
        count = conn.execute("SELECT COUNT(*) FROM asset_classes").fetchone()[0]
    assert count == 6  # pre-mutation state preserved


# ---------------------------------------------------------------------------
# Class deletes
# ---------------------------------------------------------------------------


def test_class_delete_form_writes_audit_and_snapshot(client: TestClient) -> None:
    """POST /classes/{id}/delete happy path: 303 + audit + snapshot."""
    from omaha.db import SessionLocal
    from omaha.models import DbMutation

    _login_and_select(client, profile_id=1)
    cls_id = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])[0]
    r = client.post(f"/classes/{cls_id}/delete", follow_redirects=False)
    assert r.status_code == 303

    db = SessionLocal()
    try:
        mutations = db.query(DbMutation).all()
        assert len(mutations) == 1
        assert mutations[0].route == "POST /classes/{id}/delete"
        assert mutations[0].snapshot_path is not None
    finally:
        db.close()


def test_class_delete_api_writes_audit_and_snapshot(client: TestClient) -> None:
    """DELETE /api/classes/{id} happy path: 204 + audit + snapshot."""
    from omaha.db import SessionLocal
    from omaha.models import DbMutation

    _login_and_select(client, profile_id=1)
    cls_id = _seed_classes(profile_id=1, rows=[("Renda Fixa", "100")])[0]
    r = client.delete(f"/api/classes/{cls_id}")
    assert r.status_code == 204

    db = SessionLocal()
    try:
        mutations = db.query(DbMutation).all()
        assert len(mutations) == 1
        assert mutations[0].route == "DELETE /api/classes/{id}"
        assert mutations[0].snapshot_path is not None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Asset deletes
# ---------------------------------------------------------------------------


def test_asset_delete_form_writes_audit_and_snapshot(client: TestClient) -> None:
    """POST /assets/{id}/delete happy path: 303 + audit + snapshot."""
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass, DbMutation

    _login_and_select(client, profile_id=1)
    db = SessionLocal()
    try:
        cls = AssetClass(profile_id=1, name="RF", target_pct=Decimal("100"), display_order=0)
        db.add(cls)
        db.flush()
        asset = Asset(
            asset_class_id=cls.id,
            name="Tesouro Selic",
            target_pct=Decimal("0"),
            display_order=0,
        )
        db.add(asset)
        db.commit()
        asset_id = asset.id
    finally:
        db.close()

    r = client.post(f"/assets/{asset_id}/delete", follow_redirects=False)
    assert r.status_code == 303

    db = SessionLocal()
    try:
        mutations = db.query(DbMutation).all()
        assert len(mutations) == 1
        assert mutations[0].route == "POST /assets/{id}/delete"
        assert mutations[0].snapshot_path is not None
    finally:
        db.close()


def test_asset_delete_api_writes_audit_and_snapshot(client: TestClient) -> None:
    """DELETE /api/assets/{id} happy path: 204 + audit + snapshot."""
    from omaha.db import SessionLocal
    from omaha.models import Asset, AssetClass, DbMutation

    _login_and_select(client, profile_id=1)
    db = SessionLocal()
    try:
        cls = AssetClass(profile_id=1, name="RF", target_pct=Decimal("100"), display_order=0)
        db.add(cls)
        db.flush()
        asset = Asset(
            asset_class_id=cls.id,
            name="Tesouro Selic",
            target_pct=Decimal("0"),
            display_order=0,
        )
        db.add(asset)
        db.commit()
        asset_id = asset.id
    finally:
        db.close()

    r = client.delete(f"/api/assets/{asset_id}")
    assert r.status_code == 204

    db = SessionLocal()
    try:
        mutations = db.query(DbMutation).all()
        assert len(mutations) == 1
        assert mutations[0].route == "DELETE /api/assets/{id}"
        assert mutations[0].snapshot_path is not None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Import commit
# ---------------------------------------------------------------------------


def test_import_commit_writes_audit_and_snapshot(client: TestClient) -> None:
    """POST /api/import/commit happy path: 200 + audit + snapshot."""
    from omaha.db import SessionLocal
    from omaha.models import DbMutation

    _login_and_select(client, profile_id=1)
    csv = b"ticker,qty,avg,cur\nPETR4,10,30,32\nVALE3,20,40,42\n"
    r = client.post("/api/import/preview", files={"file": ("b.csv", csv, "text/csv")})
    assert r.status_code == 200
    preview_id = r.json()["preview_id"]

    r = client.post(
        "/api/import/commit",
        json={"preview_id": preview_id, "assignments": []},
    )
    assert r.status_code == 200

    db = SessionLocal()
    try:
        mutations = db.query(DbMutation).all()
        assert len(mutations) == 1
        assert mutations[0].route == "POST /api/import/commit"
        assert mutations[0].snapshot_path is not None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Multi-op: every destructive op leaves one audit + one snapshot
# ---------------------------------------------------------------------------


def test_audit_count_equals_one_per_destructive_op(client: TestClient) -> None:
    """3 destructive ops → 3 audit rows + 3 snapshot files."""
    from omaha.db import SessionLocal
    from omaha.models import Asset, DbMutation, DbSnapshot

    _login_and_select(client, profile_id=1)
    # Two classes + two assets. Delete the class that has NO
    # assets (no FK cascade), then delete an asset in the other
    # class, then snapshot-replace. All three are independent
    # destructive ops that should each write an audit row.
    cls_empty_id, cls_with_asset_id = _seed_classes(
        profile_id=1,
        rows=[("Renda Fixa", "50"), ("Renda Variável", "50")],
    )
    db = SessionLocal()
    try:
        asset = Asset(
            asset_class_id=cls_with_asset_id,
            name="Tesouro Selic",
            target_pct=Decimal("0"),
            display_order=0,
        )
        db.add(asset)
        db.commit()
        asset_id = asset.id
    finally:
        db.close()

    # 3 independent destructive ops.
    client.delete(f"/api/classes/{cls_empty_id}")
    client.delete(f"/api/assets/{asset_id}")
    client.post(
        "/classes",
        data={"name[]": ["A"], "target_pct[]": ["100"]},
        follow_redirects=False,
    )

    db = SessionLocal()
    try:
        assert db.query(DbMutation).count() == 3
        assert db.query(DbSnapshot).count() == 3
    finally:
        db.close()
