"""ORM models for the Omaha family-portfolio app.

Defines the user-account, profile, and asset-class tables. Later slices
(S03-S05) extend this file with portfolio, asset, and movement tables.
All model classes inherit from :class:`omaha.db.Base` so a single
``Base.metadata`` is populated for Alembic autogenerate to work
correctly.
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import sql as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omaha.db import Base

if TYPE_CHECKING:
    pass


class QuoteKind(enum.StrEnum):
    """Policy for fetching live quotes per asset class.

    * ``auto`` — the QuoteService refreshes quotes for positions in
      this class via the configured :class:`QuoteProvider`
      (yfinance). Used for tradeable instruments: BR stocks/FIIs,
      US stocks/ETFs, crypto, FX.
    * ``manual`` — reserved for a future change that lets the user
      type a price per position via the UI. For v1 behaves the same
      as ``none`` (use broker price).
    * ``none`` — the QuoteService skips positions in this class.
      ``Position.current_price`` (from the broker CSV import) is the
      authoritative price. Default for existing rows on migration.
    """

    AUTO = "auto"
    MANUAL = "manual"
    NONE = "none"


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
    # F07 — Família-as-profile sentinel. When ``True`` this Profile
    # row represents the cross-User family aggregate (peer of the real
    # profiles in the profile-switcher) instead of a per-User portfolio.
    # The row is owned by a no-password ``User("family")`` so it
    # cannot authenticate; ``get_active_profile`` short-circuits to
    # ``None`` when this flag is set because the sentinel does not own
    # any ``AssetClass`` rows (mutations on Família are nonsensical —
    # the family aggregate is read-only by F01/F06 contract). The
    # default ``False`` keeps the column backward compatible with rows
    # from before the migration; existing Italo RF2 fixture rows (F01)
    # backfill to ``False`` and stay filterable as ordinary profiles
    # until a future R-slice drops them.
    is_family_sentinel: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )
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
        return (
            f"Profile(id={self.id!r}, name={self.name!r}, "
            f"user_id={self.user_id!r}, is_family_sentinel={self.is_family_sentinel!r})"
        )


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

    ``quote_kind`` controls whether the QuoteService fetches live
    prices for positions under this class. See :class:`QuoteKind`.
    Defaults to ``none`` so existing rows on migration opt out of
    live fetching until the user explicitly flips the toggle.

    On profile deletion, the FK ``ON DELETE CASCADE`` removes all
    child classes; the ORM relationship also declares
    ``cascade="all, delete-orphan"`` so in-process ``session.delete``
    behaves the same.
    """

    __tablename__ = "asset_classes"
    __table_args__ = (
        UniqueConstraint("profile_id", "name", name="uq_asset_class_profile_name"),
        CheckConstraint(
            "quote_kind IN ('auto', 'manual', 'none')",
            name="ck_asset_class_quote_kind",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    target_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quote_kind: Mapped[str] = mapped_column(
        String(8), nullable=False, default=QuoteKind.NONE.value, server_default=QuoteKind.NONE.value
    )
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
            f"name={self.name!r}, target_pct={self.target_pct!r}, "
            f"quote_kind={self.quote_kind!r})"
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

    Fase 1 of the rebalance plan (``.planning/REBALANCE_PLAN.md``,
    Gap A) adds three per-asset trade-control attributes that the
    Fase 2+ CVXPY solver reads as hard locks: ``buy_enabled`` and
    ``sell_enabled`` gate whether the solver may issue buy/sell
    orders for the asset; ``currency_code`` keys the quote source.
    Defaults are opt-out (``True/True/BRL``) per owner decision
    2026-06-26 — the dashboard's inline toggle lets the operator
    flip individual assets to ``False`` when maturity-locked
    (RDB/CDB/Tesouro Selic) instruments should not be sold. The
    ``currency_code`` allowlist is enforced by the
    ``ck_asset_currency_code`` CHECK constraint added in the
    ``0016_asset_trade_flags`` migration.
    """

    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("asset_class_id", "name", name="uq_asset_asset_class_name"),
        CheckConstraint(
            "currency_code IN ('BRL', 'USD')",
            name="ck_asset_currency_code",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_class_id: Mapped[int] = mapped_column(
        ForeignKey("asset_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # Per-asset target percentage. The sum of ``target_pct`` across
    # the assets in one class must equal 100; the invariant is
    # enforced by :func:`omaha.validators.validate_target_pct_sum`
    # on the PATCH route (S01) and the Alpine inline editor (S01).
    # The DB column itself only enforces ``NOT NULL`` — the DB
    # can't run a per-class sum check, and SQLite rejects
    # ``ALTER TABLE ... ADD CONSTRAINT`` anyway. Mirrors
    # :attr:`AssetClass.target_pct` shape so the validator can mix
    # class-level and asset-level percentages without precision
    # mismatches. Existing rows backfill to 0 via the
    # ``server_default="0"`` in the 0006 migration.
    target_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # ``buy_enabled`` / ``sell_enabled`` / ``currency_code`` —
    # per-asset trade-control attributes consumed by the Fase 2+
    # CVXPY rebalance solver. Defaults are opt-out
    # (``True / True / 'BRL'``) per owner decision 2026-06-26.
    # Existing rows backfill to these defaults via the
    # ``server_default`` in the ``0016_asset_trade_flags``
    # migration; the CHECK on ``currency_code`` is the
    # ``ck_asset_currency_code`` constraint added in the same
    # migration.
    buy_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa.true()
    )
    sell_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa.true()
    )
    currency_code: Mapped[str] = mapped_column(
        String(8), nullable=False, default="BRL", server_default="BRL"
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
    ``Numeric(18, 8)`` precision — enough headroom for Brazilian
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
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    # ``total_invested`` / ``total_current`` carry the broker-published
    # per-row totals (the CSV columns ``Total investido`` / ``Total
    # atual``). Nullable, no default — ``NULL`` signals "the source
    # file did not publish this column" and the dashboard calc treats
    # the row as a zero contribution. Numeric(18, 4) is enough for BRL
    # cents; do NOT recompute ``qty * price`` here, that path is the
    # exact drift source the user is removing. See change
    # ``broker-csv-import-totals``.
    total_invested: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    total_current: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
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


class Quote(Base):
    """A cached market quote for one symbol (ticker / FX / crypto).

    Populated by the :class:`~omaha.quotes.service.QuoteService` background
    loop and read by the ``/api/quotes`` routes. The cache is DB-backed
    so a uvicorn reload (dev) or container restart (prod) does not clear
    it; freshness is computed at read time from ``fetched_at`` and
    :attr:`~omaha.config.Settings.QUOTE_TTL_SECONDS`.

    ``symbol`` is the canonical key the consumer reads by — the
    yfinance-mapped form (``PETR4.SA``, ``BTC-USD``, ``BRL=X``) is what
    callers send; the cache does not store the un-mapped BR ticker.
    ``price`` carries enough precision for Brazilian broker positions
    and FX rates (matches :class:`Position.current_price` shape);
    ``currency`` lets the consumer distinguish BRL vs USD vs
    crypto-quote currencies for the future multi-currency rebalance.

    The table is intentionally not FK-linked to :class:`Asset` or
    :class:`Position`: a quote is keyed by raw symbol, and the same
    yfinance ticker can back multiple broker positions across
    profiles (e.g. ``IVVB11.SA`` in both Italo's and Ana's portfolio).
    """

    __tablename__ = "quotes"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"Quote(symbol={self.symbol!r}, price={self.price!r}, "
            f"currency={self.currency!r}, fetched_at={self.fetched_at!r})"
        )


__all__ = [
    "User",
    "Profile",
    "AssetClass",
    "Asset",
    "Position",
    "ImportPreview",
    "Quote",
    "QuoteKind",
]
