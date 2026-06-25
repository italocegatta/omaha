"""Idempotent database seed for the two household accounts.

The seed creates two users — ``Italo`` and ``Ana`` — both with the
shared family password (from ``settings.ADMIN_PASSWORD``), each with
one profile of the same name. It is safe to call more than once: if
any user already exists, the function still re-syncs ``password_hash``
from ``settings.ADMIN_PASSWORD`` so a rotation in the environment
propagates without manual DB surgery.

Typical entry points:

* ``uv run python -m omaha.seed`` — runs :func:`seed` against the
  configured ``DATABASE_URL`` and prints a one-line status message.
* ``alembic upgrade head && python -m omaha.seed`` — fresh database
  bootstrap.
* The T02 unit test calls :func:`seed` against a temporary SQLite file.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from omaha.auth import hash_password
from omaha.config import settings
from omaha.db import SessionLocal
from omaha.models import Profile, User

DEFAULT_USERS: tuple[tuple[str, int], ...] = (
    ("Italo", 0),
    ("Ana", 1),
)


def _seed_with_session(db: Session) -> int:
    """Idempotently create the two users + their default profiles.

    If users already exist, re-sync ``password_hash`` from
    ``settings.ADMIN_PASSWORD`` so an environment-level password change
    takes effect on the next seed run without dropping the DB.

    Returns the number of users that existed *before* the call, which is
    a convenient signal for callers (``0`` = we just seeded, ``1+`` =
    already populated).
    """
    existing = db.query(User).count()
    if existing > 0:
        if settings.ADMIN_PASSWORD:
            expected_hash = hash_password(settings.ADMIN_PASSWORD)
            stale = db.query(User).filter(User.password_hash != expected_hash).all()
            for user in stale:
                user.password_hash = expected_hash
            if stale:
                db.commit()
        return existing

    if not settings.ADMIN_PASSWORD:
        raise RuntimeError(
            "ADMIN_PASSWORD is not set; cannot seed. Configure it in .env "
            "or export it in the environment."
        )

    password_hash = hash_password(settings.ADMIN_PASSWORD)

    for username, order in DEFAULT_USERS:
        user = User(username=username, password_hash=password_hash)
        db.add(user)
        db.flush()  # populate user.id before the profile row
        db.add(Profile(user_id=user.id, name=username, display_order=order))

    db.commit()
    return 0


def seed() -> int:
    """Idempotent seed entry point.

    Opens a short-lived session, runs :func:`_seed_with_session`, and
    prints a one-line status message. Returns the prior user count
    (``0`` when we just created the seed data).
    """
    db = SessionLocal()
    try:
        prior = _seed_with_session(db)
    finally:
        db.close()

    if prior == 0:
        print(
            f"seeded {len(DEFAULT_USERS)} users with the shared password: "
            f"{[u for u, _ in DEFAULT_USERS]}"
        )
    else:
        print(f"seed skipped: {prior} user(s) already present")
    return prior


if __name__ == "__main__":  # pragma: no cover - manual entry point
    seed()
