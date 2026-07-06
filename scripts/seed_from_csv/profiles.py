"""Profile resolution for the CSV-driven seed.

Maps the CLI ``--profile`` value to the ``(User.username,
Profile.name)`` pair the seed targets. The Família sentinel lives
in ``seed.py`` (not the CSV path) and is not seeded via this
triplet — Família has no class/asset/position rows.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from omaha.models import Profile, User

PROFILES = ("italo", "ana")

PROFILE_OWNER_TO_NAME: dict[str, tuple[str, str]] = {
    "italo": ("Italo", "Italo"),
    "ana": ("Ana", "Ana"),
}


def get_profile_id(db: Session, profile: str) -> int:
    user_username, profile_name = PROFILE_OWNER_TO_NAME[profile]
    user = db.query(User).filter(User.username == user_username).one()
    prof = db.query(Profile).filter(Profile.user_id == user.id, Profile.name == profile_name).one()
    return prof.id
