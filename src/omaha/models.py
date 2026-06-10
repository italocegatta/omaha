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
    assets: Mapped[list[Asset]] = relationship(
        "Asset",
        back_populates="asset_class",
        cascade="all, delete-orphan",
        order_by="Asset.display_order",
    )

    def __repr__(self) -> str:
        return (
            f"AssetClass(id={self.id!r}, profile_id={self.profile_id!r}, "
            f"name={self.name!r}, target_pct={self.target_pct!r})"
        )


class Asset(Base):
    """A specific financial instrument belonging to an asset class.

    Each :class:`AssetClass` owns zero or more :class:`Asset` rows
    (e.g. "Renda Fixa" might own "Tesouro Selic 2029", "Tesouro IPCA
    2035"). The S03 CRUD editor lets the user add, edit, and remove
    assets inside the active profile's classes; the S04 CSV importer
    uses the same table as the import target; the S05 dashboard
    groups assets under their class for the distribution view.

    The ``(asset_class_id, name)`` unique constraint prevents two
    assets in the same class from sharing a name. ``display_order``
    is a stable ordering hint used by the editor and the dashboard
    distribution view; the relationship is
    ``order_by="Asset.display_order"`` so iteration in Python
    matches the user's saved order.

    On asset-class deletion, the FK ``ON DELETE CASCADE`` removes all
    child assets; the ORM relationship also declares
    ``cascade="all, delete-orphan"`` so in-process
    ``session.delete`` behaves the same. Combined with the S02
    profile → class cascade, deleting a profile removes every class
    and every asset underneath it in a single operation.
    """

    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("asset_class_id", "name", name="uq_asset_asset_class_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_class_id: Mapped[int] = mapped_column(
        ForeignKey("asset_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    asset_class: Mapped[AssetClass] = relationship("AssetClass", back_populates="assets")
    positions: Mapped[list[Position]] = relationship(
        "Position",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="Position.id",
    )

    def __repr__(self) -> str:
        return f"Asset(id={self.id!r}, asset_class_id={self.asset_class_id!r}, name={self.name!r})"


class Position(Base):
    """A broker-side holding of a specific :class:`Asset` for a profile.

    Positions are the data the S04 CSV importer writes and the S05
    dashboard reads. Each row is one (asset, broker_ticker) pair with
    the quantity, average cost, and current price the broker reported
    for that position. The ``(asset_id, broker_ticker)`` unique
    constraint makes a re-import of the same broker ticker for the
    same asset an idempotent upsert, not a duplicate row.

    ``broker_ticker`` is the symbol the broker used (e.g. ``PETR4``,
    ``IVVB11``, ``TESOURO_SELIC_2029``). It is stored verbatim from
    the CSV row that produced it; the importer normalizes the asset
    name *separately* for matching, so two CSVs from different
    brokers can write to the same ``(asset_id, broker_ticker)`` row
    as long as the tickers match. ``qty``, ``avg_price``, and
    ``current_price`` are :class:`~decimal.Decimal` columns with
    ``Numeric(18, 4)`` precision — enough headroom for Brazilian
    broker positions and FX-aware totals without losing cents.

    On asset deletion, the FK ``ON DELETE CASCADE`` removes all
    child positions; the ORM relationship also declares
    ``cascade="all, delete-orphan"`` so in-process
    ``session.delete`` behaves the same. Combined with the S03
    asset → class CASCADE and the S02 class → profile CASCADE,
    deleting a profile removes every class, every asset, and every
    position underneath it in a single operation.
    """

    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("asset_id", "broker_ticker", name="uq_position_asset_ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    broker_ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    asset: Mapped[Asset] = relationship("Asset", back_populates="positions")

    def __repr__(self) -> str:
        return (
            f"Position(id={self.id!r}, asset_id={self.asset_id!r}, "
            f"broker_ticker={self.broker_ticker!r})"
        )


class ImportPreview(Base):
    """A short-lived server-side snapshot of a parsed broker CSV.

    The S04 importer parses the upload once, then persists the parsed
    :class:`~omaha.csv_import.RawPosition` list (as JSON) so the
    review screen can re-render after a navigation without forcing
    the user to re-upload. The preview is deleted when the user
    confirms (or when the 1h expiration window passes — the route
    re-detects expiry on each access). The 1h window is the floor
    for "reasonable review time"; a confirmation that arrives after
    the window renders the "Expirado" state instead of silently
    re-using stale data.

    ``raw_json`` is the JSON-serialized list of RawPosition dicts
    (the parser is pure, so re-serializing the dataclass-as-dict
    list is enough; the S04 confirm handler re-hydrates it). Storing
    the parsed rows in the DB instead of in the session means the
    preview survives a server restart and is large-file-tolerant
    (the session cookie is 4 KB, the preview can be 1 MB).

    On profile deletion, the FK ``ON DELETE CASCADE`` removes the
    preview; combined with the S02 profile → class CASCADE and the
    S03 class → asset CASCADE, deleting a profile removes every
    preview underneath it in a single operation.
    """

    __tablename__ = "import_previews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_json: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"ImportPreview(id={self.id!r}, profile_id={self.profile_id!r}, "
            f"created_at={self.created_at!r})"
        )


__all__ = ["User", "Profile", "AssetClass", "Asset", "Position", "ImportPreview"]
