"""Positions belong to assets.

Revision ID: 0004_positions
Revises: 0003_assets
Create Date: 2026-06-07

Adds the ``positions`` table that the S04 CSV importer writes and the
S05 dashboard reads. Each row is one (asset, broker_ticker) holding
the broker reported, with the quantity, average cost, and current
price captured at import time.

``asset_id`` is the FK to the S03 ``assets`` table; ``ON DELETE
CASCADE`` mirrors the asset → asset_class CASCADE (0003) and the
class → profile CASCADE (0002), so deleting an asset removes its
positions, and deleting a profile removes every class, asset, and
position underneath it in a single transaction.

The ``(asset_id, broker_ticker)`` unique constraint makes a re-import
of the same ticker for the same asset an idempotent upsert (not a
duplicate row) — the S04 confirm handler relies on this for safe
re-runs. ``broker_ticker`` is stored verbatim from the CSV row, so
the importer does not need a separate ticker-mapping table to keep
the import idempotent.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_positions"
down_revision = "0003_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False),
        sa.Column("avg_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("current_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("broker_ticker", sa.String(length=32), nullable=False),
        sa.Column(
            "imported_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
            ondelete="CASCADE",
            name="fk_position_asset_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_id", "broker_ticker", name="uq_position_asset_ticker"),
    )
    op.create_index("ix_positions_asset_id", "positions", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_positions_asset_id", table_name="positions")
    op.drop_table("positions")
