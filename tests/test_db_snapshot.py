"""Unit tests for :mod:`scripts.snapshot_db`.

R06 — ``db-mutation-safety`` requires that the platform-managed
snapshot helper correctly copies a live SQLite DB and enforces
FIFO retention. The helper is pure stdlib (no DB session
required), so the file lives in the unit bucket and is fast
enough to run alongside the other unit tests.

Cases
-----

1. ``test_snapshot_live_db_writes_file_to_dest_dir`` — the
   helper writes a file under ``dest_dir`` with the
   ``portfolio-<UTC>.db`` naming scheme and the copied DB is
   a valid SQLite file with the source's tables preserved.
2. ``test_snapshot_live_db_returns_absolute_path`` — the
   returned path is absolute (operator can use it without
   resolving relative to cwd).
3. ``test_snapshot_live_db_raises_when_source_missing`` —
   a missing source DB is surfaced as ``FileNotFoundError``,
   not a generic ``sqlite3.Error``.
4. ``test_prune_snapshots_no_op_when_under_retention`` — fewer
   than ``retention + 1`` files is a no-op; nothing deleted.
5. ``test_prune_snapshots_deletes_oldest_beyond_retention`` —
   60 files with retention 50 → 10 oldest are removed; the 50
   newest survive.
6. ``test_prune_snapshots_ignores_non_matching_files`` —
   ``foo.db`` (not the platform's naming) is never touched.
7. ``test_prune_snapshots_no_op_when_dest_dir_missing`` —
   a missing ``dest_dir`` is a no-op (not an error).
8. ``test_roundtrip_snapshot_then_restore`` — ``shutil.copy2``
   over a snapshot file produces a DB identical to the source
   (the destructive route's recovery path).
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from scripts.snapshot_db import prune_snapshots, snapshot_live_db


def _make_source_db(tmp_path: Path, *, tables: tuple[str, ...] = ("foo",)) -> Path:
    """Create a SQLite file with ``tables`` under ``tmp_path``.

    Returns the path to the source file. The source is
    populated with one row per table so the test can assert
    that the snapshot preserved the data.
    """
    src = tmp_path / "src.db"
    with sqlite3.connect(str(src)) as conn:
        for t in tables:
            conn.execute(f"CREATE TABLE {t} (id INTEGER PRIMARY KEY, x TEXT)")
            conn.execute(f"INSERT INTO {t} VALUES (1, 'hello-{t}')")
    return src


def test_snapshot_live_db_writes_file_to_dest_dir(tmp_path: Path) -> None:
    """The helper writes a file under ``dest_dir`` and the copy is a valid SQLite file."""
    src = _make_source_db(tmp_path)
    dest_dir = tmp_path / "snap"

    out = snapshot_live_db(src, dest_dir)

    assert out.exists()
    assert out.parent == dest_dir.resolve()
    # Filename follows the platform naming scheme.
    assert out.name.startswith("portfolio-")
    assert out.name.endswith(".db")
    # The copy is a valid SQLite DB with the source's tables.
    with sqlite3.connect(str(out)) as conn:
        rows = list(conn.execute("SELECT * FROM foo"))
    assert rows == [(1, "hello-foo")]


def test_snapshot_live_db_returns_absolute_path(tmp_path: Path) -> None:
    """The returned path is absolute so the caller can use it without resolving."""
    src = _make_source_db(tmp_path)
    dest_dir = tmp_path / "snap"
    out = snapshot_live_db(src, dest_dir)
    assert out.is_absolute()


def test_snapshot_live_db_raises_when_source_missing(tmp_path: Path) -> None:
    """A missing source DB is surfaced as ``FileNotFoundError``."""
    with pytest.raises(FileNotFoundError):
        snapshot_live_db(tmp_path / "does-not-exist.db", tmp_path / "snap")


def test_prune_snapshots_no_op_when_under_retention(tmp_path: Path) -> None:
    """Fewer than ``retention + 1`` files is a no-op."""
    dest_dir = tmp_path / "snap"
    dest_dir.mkdir()
    for i in range(3):
        (dest_dir / f"portfolio-2026-01-0{i + 1}T00-00-00Z.db").write_bytes(b"x")
    assert prune_snapshots(dest_dir, retention=10) == 0
    # All three files still present.
    assert len(list(dest_dir.glob("portfolio-*.db"))) == 3


def test_prune_snapshots_deletes_oldest_beyond_retention(tmp_path: Path) -> None:
    """60 files with retention 50 → 10 oldest are removed; the 50 newest survive."""
    dest_dir = tmp_path / "snap"
    dest_dir.mkdir()
    # Generate 60 timestamped files in lexicographic order.
    for i in range(60):
        day = f"{i + 1:02d}"
        (dest_dir / f"portfolio-2026-02-{day}T00-00-00Z.db").write_bytes(b"x")

    deleted = prune_snapshots(dest_dir, retention=50)
    assert deleted == 10
    # 50 files remain — the newest (days 11..60) survive.
    remaining = sorted(p.name for p in dest_dir.glob("portfolio-*.db"))
    assert len(remaining) == 50
    assert remaining[0] == "portfolio-2026-02-11T00-00-00Z.db"
    assert remaining[-1] == "portfolio-2026-02-60T00-00-00Z.db"  # lexicographic


def test_prune_snapshots_ignores_non_matching_files(tmp_path: Path) -> None:
    """Files not matching ``portfolio-*.db`` are never touched."""
    dest_dir = tmp_path / "snap"
    dest_dir.mkdir()
    for i in range(60):
        (dest_dir / f"portfolio-2026-03-{i + 1:02d}T00-00-00Z.db").write_bytes(b"x")
    # Operator's manual copy + a pre-existing test fixture.
    (dest_dir / "manual-backup.db").write_bytes(b"manual")
    (dest_dir / "fixture.txt").write_text("hi")

    deleted = prune_snapshots(dest_dir, retention=10)
    assert deleted == 50
    # Manual copy and fixture survive untouched.
    assert (dest_dir / "manual-backup.db").exists()
    assert (dest_dir / "fixture.txt").exists()
    # 10 platform snapshots remain (the newest 10).
    assert len(list(dest_dir.glob("portfolio-*.db"))) == 10


def test_prune_snapshots_no_op_when_dest_dir_missing(tmp_path: Path) -> None:
    """A missing ``dest_dir`` is a no-op (the first destructive op creates it)."""
    assert prune_snapshots(tmp_path / "never-created", retention=50) == 0


def test_roundtrip_snapshot_then_restore(tmp_path: Path) -> None:
    """``shutil.copy2`` over a snapshot file produces a DB identical to the source.

    Mirrors the destructive route's recovery path:
    ``snapshot_live_db`` → ``shutil.copy2(snapshot, live_db)``.
    """
    src = _make_source_db(tmp_path, tables=("a", "b", "c"))
    dest_dir = tmp_path / "snap"

    snap = snapshot_live_db(src, dest_dir)
    restored = tmp_path / "restored.db"
    shutil.copy2(snap, restored)

    with sqlite3.connect(str(restored)) as conn:
        for t in ("a", "b", "c"):
            rows = list(conn.execute(f"SELECT * FROM {t}"))
            assert rows == [(1, f"hello-{t}")]
