"""Delete all Asset rows, keep classes intact."""

from __future__ import annotations

from omaha.db import SessionLocal
from omaha.models import Asset


def clear_assets() -> int:
    db = SessionLocal()
    try:
        n = db.query(Asset).delete()
        db.commit()
        return n
    finally:
        db.close()


if __name__ == "__main__":
    n = clear_assets()
    print(f"Deleted {n} asset(s)")
