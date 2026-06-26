"""Delete all Asset rows, keep classes intact."""

from __future__ import annotations

from omaha.db import SessionLocal
from omaha.models import Asset, Position


def clear_assets() -> int:
    db = SessionLocal()
    try:
        # Delete positions first — SQLite FK cascade requires
        # `PRAGMA foreign_keys=ON` per-connection, which is off by
        # default in our engine config. Explicit delete avoids orphan
        # positions surviving after Asset rows are wiped.
        n_pos = db.query(Position).delete()
        n_assets = db.query(Asset).delete()
        db.commit()
        print(f"Deleted {n_pos} position(s) and {n_assets} asset(s)")
        return n_assets
    finally:
        db.close()


if __name__ == "__main__":
    clear_assets()
