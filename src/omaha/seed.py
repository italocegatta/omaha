"""Idempotent database seed for the two household accounts.

The seed creates two password-authenticated users — ``Italo`` and
``Ana`` — both with the shared family password (from
``settings.ADMIN_PASSWORD``), each with **one canonical profile** of
the same name. A third password-less user ``family`` owns the
``Família`` sentinel profile (``is_family_sentinel=True``) which the
profile-switcher renders as a peer of ``Italo`` / ``Ana`` (F07).

The F01 ``Italo RF2`` fixture profile (a synthetic second profile on
``Italo``'s User) was retired in F07 — the F01 multi-profile
intra-User invariant is dead (Italo and Ana are separate ``User``
rows in the canonical seed, so the household toggle aggregating
``Italo.profiles`` never crossed users). F06 superseded the toggle
semantics with cross-User full-join; F07 promotes Família from a
querystring toggle to a sentinel profile row. Any leftover
``Italo RF2`` row from a pre-F07 database is removed during
:func:`_ensure_family_sentinel` so the canonical ``db-reset`` state
is exactly two real profiles + one sentinel.

It is safe to call more than once: if any user already exists, the
function still re-syncs ``password_hash`` from
``settings.ADMIN_PASSWORD`` so a rotation in the environment propagates
without manual DB surgery.

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

# F07 — Família sentinel profile (sentinel option in the
# profile-switcher). Owned by a password-less ``User("family")`` so
# the sentinel can never authenticate; the profile itself carries
# ``is_family_sentinel=True`` so the application layer can
# short-circuit :func:`omaha.auth.get_active_profile` to ``None``
# (sentinel has no AssetClass rows — mutations are nonsensical on
# the family aggregate, the F01 read-only contract applies).
FAMILY_SENTINEL_USER = "family"
FAMILY_SENTINEL_PROFILE_NAME = "Família"
FAMILY_SENTINEL_DISPLAY_ORDER = 2

# F07 D3 — the F01 ``Italo RF2`` fixture profile is retired. Legacy
# rows left in pre-F07 databases are removed by
# :func:`_ensure_family_sentinel` so ``db-reset`` produces exactly
# two real profiles + one sentinel.
LEGACY_HOUSEHOLD_FIXTURE_PROFILE_NAMES: tuple[str, ...] = ("Italo RF2",)


def _seed_with_session(db: Session) -> int:
    """Idempotently create the two users + their default profiles.

    If users already exist, re-sync ``password_hash`` from
    ``settings.ADMIN_PASSWORD`` so an environment-level password change
    takes effect on the next seed run without dropping the DB. Also
    ensures the Família sentinel row exists (F07) and removes the
    F01 ``Italo RF2`` fixture profile from legacy databases so the
    canonical seed shape is preserved.

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
        _ensure_family_sentinel(db)
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
    _ensure_family_sentinel(db)
    return 0


def _ensure_family_sentinel(db: Session) -> None:
    """Ensure the F07 Família sentinel Profile row exists.

    Idempotent — creates the password-less ``User("family")`` and
    the matching ``Profile("Família", is_family_sentinel=True)`` only
    if missing. Runs inside the same transaction so the sentinel can
    never split-brain against the user creation above. Also removes
    the F01 ``Italo RF2`` fixture profile from legacy databases so
    the canonical post-F07 shape (``2 real profiles + 1 sentinel``)
    is restored on next ``db-reset``.

    The sentinel's ``User`` has an empty ``password_hash`` — it
    cannot authenticate because :func:`omaha.auth.verify_password`
    rejects the empty string on either side of the comparison (no
    plaintext will hash to ``""`` and the empty hash cannot be
    parsed by ``bcrypt.checkpw``). The session-based auth path
    therefore can never bind to ``family`` — the row exists solely
    as the canonical owner of the Família Profile.
    """
    family_user = db.query(User).filter(User.username == FAMILY_SENTINEL_USER).one_or_none()
    if family_user is None:
        family_user = User(
            username=FAMILY_SENTINEL_USER,
            password_hash="",  # sentinel: no password; cannot log in
        )
        db.add(family_user)
        db.flush()

    sentinel_profile = (
        db.query(Profile)
        .filter(
            Profile.user_id == family_user.id,
            Profile.name == FAMILY_SENTINEL_PROFILE_NAME,
        )
        .one_or_none()
    )
    if sentinel_profile is None:
        db.add(
            Profile(
                user_id=family_user.id,
                name=FAMILY_SENTINEL_PROFILE_NAME,
                display_order=FAMILY_SENTINEL_DISPLAY_ORDER,
                is_family_sentinel=True,
            )
        )

    # F07 D3 — drop the F01 ``Italo RF2`` fixture profile so the
    # canonical post-F07 shape is restored on legacy databases.
    # No-op if the row never existed (fresh install).
    for legacy_name in LEGACY_HOUSEHOLD_FIXTURE_PROFILE_NAMES:
        for legacy_profile in db.query(Profile).filter(Profile.name == legacy_name).all():
            db.delete(legacy_profile)

    db.commit()


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
            f"seeded {len(DEFAULT_USERS)} users + family sentinel "
            f"with the shared password: "
            f"{[u for u, _ in DEFAULT_USERS]}"
        )
    else:
        print(f"seed skipped: {prior} user(s) already present")
    return prior


if __name__ == "__main__":  # pragma: no cover - manual entry point
    seed()
