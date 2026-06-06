"""ORM models for the Omaha family-portfolio app.

Defines the user-account and profile tables. Later slices (S02-S05) extend
this file with portfolio, asset, and movement tables. All model classes
inherit from :class:`omaha.db.Base` so a single ``Base.metadata`` is
populated for Alembic autogenerate to work correctly.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omaha.db import Base

if TYPE_CHECKING:
    pass


class User(Base):
    """A family-account holder with one shared password.

    The login flow (S01) authenticates against this table. The shared
    family password is hashed with bcrypt (see ``omaha.auth``).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    profiles: Mapped[list[Profile]] = relationship(
        "Profile",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Profile.display_order",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"User(id={self.id!r}, username={self.username!r})"


class Profile(Base):
    """A named family member (e.g. 'Italo', 'Ana Livia') tied to a User.

    After login the user picks a profile, and every portfolio record
    (added in later slices) is scoped to a profile. The
    ``(user_id, name)`` unique constraint prevents duplicate names under
    the same account.
    """

    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_profile_user_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="profiles")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Profile(id={self.id!r}, name={self.name!r}, user_id={self.user_id!r})"


__all__ = ["User", "Profile"]
