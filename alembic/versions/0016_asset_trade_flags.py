"""Add per-asset trade-control columns and currency CHECK.

Revision ID: 0016_asset_trade_flags
Revises: 1c73065cff10
Create Date: 2026-06-26

asset-trade-flags: Fase 1 do rebalance plano. Three new columns on
``assets`` so the Fase 2+ CVXPY solver can lock buys/sells and pick
the right quote source per asset.

Schema
------

* ``buy_enabled BOOLEAN NOT NULL DEFAULT 1`` — solver hard lock;
  ``False`` means the solver cannot issue buy orders for this asset.
* ``sell_enabled BOOLEAN NOT NULL DEFAULT 1`` — solver hard lock;
  ``False`` means the solver cannot drain the asset below target.
* ``currency_code VARCHAR(8) NOT NULL DEFAULT 'BRL'`` — the
  quote currency for the asset. CHECK restricts the value to
  ``{'BRL', 'USD'}`` via ``ck_asset_currency_code``.

Defaults favor opt-out over opt-in (owner decision 2026-06-26):
every existing row reads ``True/True/BRL`` after upgrade, so the
first rebalance can run without an explicit 96-asset opt-in
ceremony. The dashboard's inline toggle lets the operator flip
individual assets when a maturity-locked (RDB/CDB/Tesouro Selic)
should never be sold.

Why the CHECK constraint, not a SQLAlchemy ``Enum``
---------------------------------------------------

Same reasoning as ``ck_asset_class_quote_kind`` (0014 migration):
a bare ``String(8)`` column with a DB CHECK keeps the Python
representation (the implicit string) and the SQL CHECK in sync
without locking the column to a SQLAlchemy enum type (which would
require an Alembic migration to ``ALTER TYPE`` every time a value
is added, and would force every raw ``INSERT`` to cast). Adding
a new currency is a one-line CHECK rewrite in a follow-up
migration.

Downgrade
---------

Drops the CHECK constraint then the three columns in reverse
order. The dashboard renders the asset list unchanged; the
Fase 2+ CVXPY solver won't read these columns. The inline
toggle UI is also dropped by the matching template changes in
the same change, so there is no dead UI after downgrade.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0016_asset_trade_flags"
down_revision = "1c73065cff10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the three trade-control columns and the currency CHECK."""
    with op.batch_alter_table("assets") as batch_op:
        batch_op.add_column(
            sa.Column(
                "buy_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "sell_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "currency_code",
                sa.String(length=8),
                nullable=False,
                server_default="BRL",
            )
        )
        batch_op.create_check_constraint(
            "ck_asset_currency_code",
            "currency_code IN ('BRL', 'USD')",
        )


def downgrade() -> None:
    """Drop the CHECK + the three columns in reverse order."""
    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_constraint("ck_asset_currency_code", type_="check")
        batch_op.drop_column("currency_code")
        batch_op.drop_column("sell_enabled")
        batch_op.drop_column("buy_enabled")
