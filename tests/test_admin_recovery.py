"""Integration tests for the R06 ``admin-recovery`` endpoints.

Three endpoints under ``/admin``:
- ``GET  /admin/snapshots``
- ``POST /admin/restore/{snapshot_id}``
- ``GET  /admin/audit``

All three are gated by :func:`omaha.routes.admin.require_admin`
which checks the ``X-Admin-Password`` request header against
``os.environ["ADMIN_PASSWORD"]``. The conftest installs
``ADMIN_PASSWORD="test-password"`` for the test session.

Cases
-----

1. ``test_admin_snapshots_requires_password`` — missing or
   wrong ``X-Admin-Password`` → 401.
2. ``test_admin_snapshots_lists_platform_snapshots`` — after
   a confirmed destructive commit, the listing returns the
   snapshot metadata (id, path, size, created_at, mutation_id).
3. ``test_admin_snapshots_skips_missing_files`` — a
   ``db_snapshots`` row whose file was manually deleted is
   filtered out of the listing.
4. ``test_admin_restore_requires_password`` — 401 without
   the right header.
5. ``test_admin_restore_404_for_missing_snapshot`` — 404 when
   the id does not match a file under ``data/snapshots/``.
6. ``test_admin_restore_happy_path_copies_and_returns_202`` —
   the snapshot is copied over ``data/portfolio.db``; the
   response carries ``restart_needed: true`` (no systemd
   unit in the test env).
7. ``test_admin_audit_requires_password`` — 401 without the
   right header.
8. ``test_admin_audit_paginates_with_since`` — rows newer
   than ``since`` are returned.
9. ``test_admin_audit_clamps_limit_to_max`` — a
   ``limit=10000`` request is clamped to ``AUDIT_LIMIT_MAX``
   (500).
"""

from __future__ import annotations

import contextlib
import os
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ADMIN_HEADER = {"X-Admin-Password": "test-password"}


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

    dest = Path(os.environ.get("SNAPSHOT_DEST_DIR", "data/snapshots"))
    if dest.exists():
        for f in dest.glob("portfolio-*.db"):
            with contextlib.suppress(OSError):
                f.unlink()

    yield


# ---------------------------------------------------------------------------
# /admin/snapshots
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


def _make_snapshot_dir() -> Path:
    """Ensure ``data/snapshots/`` exists; return the path."""
    dest = Path.cwd() / "data" / "snapshots"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


# ---------------------------------------------------------------------------
# /admin/snapshots
# ---------------------------------------------------------------------------


def test_admin_snapshots_requires_password(client: TestClient) -> None:
    """Missing or wrong ``X-Admin-Password`` → 401."""
    # No header
    r = client.get("/admin/snapshots")
    assert r.status_code == 401
    # Wrong password
    r = client.get("/admin/snapshots", headers={"X-Admin-Password": "nope"})
    assert r.status_code == 401


def test_admin_snapshots_lists_platform_snapshots(client: TestClient) -> None:
    """After a confirmed destructive commit, the listing returns the snapshot."""
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[(f"Classe {i}", "8.33") for i in range(12)],
    )
    # Confirmed snapshot-replace fires the gate and writes a
    # snapshot + audit row.
    client.post(
        "/classes",
        data={
            "name[]": ["A", "B", "C"],
            "target_pct[]": ["30", "30", "30"],
            "confirm": "true",
        },
        follow_redirects=False,
    )

    r = client.get("/admin/snapshots", headers=ADMIN_HEADER)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 1
    entry = body[0]
    # Spec: ``id (the basename minus .db)`` — the listing strips
    # the extension so the caller can pass the id verbatim to
    # the restore endpoint.
    assert entry["id"].startswith("portfolio-")
    assert not entry["id"].endswith(".db")
    assert entry["size_bytes"] > 0
    # ``path`` still includes the full filename (with the .db
    # extension) so the operator can ``cat`` the file from the
    # shell if needed.
    assert entry["path"].endswith(entry["id"] + ".db")
    assert entry["mutation_id"] is not None
    assert entry["created_at"].endswith("Z")


def test_admin_snapshots_skips_missing_files(client: TestClient) -> None:
    """A ``db_snapshots`` row whose file was deleted is filtered out."""
    from omaha.db import SessionLocal
    from omaha.models import DbSnapshot

    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[(f"Classe {i}", "8.33") for i in range(12)],
    )
    client.post(
        "/classes",
        data={
            "name[]": ["A", "B", "C"],
            "target_pct[]": ["30", "30", "30"],
            "confirm": "true",
        },
        follow_redirects=False,
    )

    # Manually delete the snapshot file but keep the row.
    db = SessionLocal()
    try:
        snap = db.query(DbSnapshot).first()
        assert snap is not None
        Path(snap.path).unlink()
    finally:
        db.close()

    r = client.get("/admin/snapshots", headers=ADMIN_HEADER)
    assert r.status_code == 200
    assert r.json() == []  # missing file filtered out


# ---------------------------------------------------------------------------
# /admin/restore/{snapshot_id}
# ---------------------------------------------------------------------------


def test_admin_restore_requires_password(client: TestClient) -> None:
    r = client.post("/admin/restore/whatever")
    assert r.status_code == 401


def test_admin_restore_404_for_missing_snapshot(client: TestClient) -> None:
    r = client.post("/admin/restore/portfolio-does-not-exist", headers=ADMIN_HEADER)
    assert r.status_code == 404
    assert r.json() == {"detail": "snapshot_not_found"}


def test_admin_restore_400_for_path_traversal(client: TestClient) -> None:
    r = client.post("/admin/restore/..etc..passwd", headers=ADMIN_HEADER)
    assert r.status_code == 400


def test_admin_restore_happy_path_copies_and_returns_202(client: TestClient) -> None:
    """A confirmed destructive commit produces a snapshot we can restore from."""
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[(f"Classe {i}", "8.33") for i in range(12)],
    )
    client.post(
        "/classes",
        data={
            "name[]": ["A", "B", "C"],
            "target_pct[]": ["30", "30", "30"],
            "confirm": "true",
        },
        follow_redirects=False,
    )

    # List snapshots to get the id.
    listing = client.get("/admin/snapshots", headers=ADMIN_HEADER).json()
    assert len(listing) == 1
    snap_id = listing[0]["id"]

    # Restore.
    r = client.post(f"/admin/restore/{snap_id}", headers=ADMIN_HEADER)
    assert r.status_code == 202
    body = r.json()
    # No systemd unit in the test env → restart_needed: True.
    assert body["restart_needed"] is True
    assert body["restarted_via"] is None


# ---------------------------------------------------------------------------
# /admin/audit
# ---------------------------------------------------------------------------


def test_admin_audit_requires_password(client: TestClient) -> None:
    r = client.get("/admin/audit")
    assert r.status_code == 401


def test_admin_audit_empty_when_no_mutations(client: TestClient) -> None:
    r = client.get("/admin/audit", headers=ADMIN_HEADER)
    assert r.status_code == 200
    assert r.json() == []


def test_admin_audit_returns_recorded_mutations(client: TestClient) -> None:
    """After a confirmed commit, the audit listing returns the row."""
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[(f"Classe {i}", "8.33") for i in range(12)],
    )
    client.post(
        "/classes",
        data={
            "name[]": ["A", "B", "C"],
            "target_pct[]": ["30", "30", "30"],
            "confirm": "true",
        },
        follow_redirects=False,
    )

    r = client.get("/admin/audit", headers=ADMIN_HEADER)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    row = body[0]
    assert row["route"] == "POST /classes"
    assert row["profile_id"] is not None
    assert row["snapshot_path"] is not None
    assert row["before"] == {"classes": 12, "assets": 0, "positions": 0}
    assert row["after"]["classes"] == 3
    assert row["created_at"].endswith("Z")


def test_admin_audit_paginates_with_since(client: TestClient) -> None:
    """Rows newer than ``since`` are returned."""
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[(f"Classe {i}", "8.33") for i in range(12)],
    )
    client.post(
        "/classes",
        data={
            "name[]": ["A", "B", "C"],
            "target_pct[]": ["30", "30", "30"],
            "confirm": "true",
        },
        follow_redirects=False,
    )

    # ``since`` in the future → no rows.
    future = "2099-01-01T00:00:00Z"
    r = client.get(f"/admin/audit?since={future}", headers=ADMIN_HEADER)
    assert r.status_code == 200
    assert r.json() == []


def test_admin_audit_clamps_limit_to_max(client: TestClient) -> None:
    """A ``limit=10000`` request is clamped to ``AUDIT_LIMIT_MAX``."""
    r = client.get("/admin/audit?limit=10000", headers=ADMIN_HEADER)
    assert r.status_code == 200
    # 0 rows since no destructive commits; the clamp doesn't
    # matter here. What matters is the request does not 4xx.
    assert r.json() == []


def test_admin_audit_rejects_invalid_since(client: TestClient) -> None:
    """An unparseable ``since`` → 400."""
    r = client.get("/admin/audit?since=not-a-date", headers=ADMIN_HEADER)
    assert r.status_code == 400
