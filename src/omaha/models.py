"""ORM models for the Omaha family-portfolio app.

Defines the user-account, profile, and asset-class tables. Later slices
(S03-S05) extend this file with portfolio, asset, and movement tables.
All model classes inherit from :class:`omaha.db.Base` so a single
``Base.metadata`` is populated for Alembic autogenerate to work
correctly.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
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
    asset_classes: Mapped[list[AssetClass]] = relationship(
        "AssetClass",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="AssetClass.display_order",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Profile(id={self.id!r}, name={self.name!r}, user_id={self.user_id!r})"


class AssetClass(Base):
    """A named asset-class bucket scoped to a profile (e.g. 'Renda Fixa 60%').

    Each profile owns zero or more :class:`AssetClass` rows. The slice
    S02 CRUD editor enforces that the ``target_pct`` values across a
    profile's classes sum to exactly 100; the database itself does not
    enforce that invariant — the editor owns the "sum to 100" check
    on every save, and the API rejects invalid submissions.

    The ``(profile_id, name)`` unique constraint prevents a profile
    from having two classes with the same display name. ``display_order``
    is a stable ordering hint used by the editor and downstream
    reports; the relationship is ``order_by="AssetClass.display_order"``
    so iteration in Python matches the user's saved order.

    On profile deletion, the FK ``ON DELETE CASCADE`` removes all
    child classes; the ORM relationship also declares
    ``cascade="all, delete-orphan"`` so in-process ``session.delete``
    behaves the same.
    """

    __tablename__ = "asset_classes"
    __table_args__ = (UniqueConstraint("profile_id", "name", name="uq_asset_class_profile_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    target_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    profile: Mapped[Profile] = relationship("Profile", back_populates="asset_classes")

    def __repr__(self) -> str:
        return (
            f"AssetClass(id={self.id!r}, profile_id={self.profile_id!r}, "
            f"name={self.name!r}, target_pct={self.target_pct!r})"
        )


__all__ = ["User", "Profile", "AssetClass"]
