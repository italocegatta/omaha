"""Bump ``positions.qty / avg_price / current_price`` to ``Numeric(18, 8)``.

Revision ID: 0015_bump_position_precision
Revises: 0014_add_quote_cache_and_quote_kind
Create Date: 2026-06-24

The CSV-driven seed (``data/seed/{profile}_positions.csv``) writes
``avg_price = total_investido / qty`` and ``current_price = total_atual
/ qty`` so ``qty × unit_price == total`` exactly (the dashboard's
``portfolio.current_value`` then matches the broker's claimed footer
total). With ``Numeric(18, 4)`` precision the seed loses up to ~R$ 0.20
of accuracy across 40 tradeable rows because each unit price is
truncated to 4 decimals on insert; ``Numeric(18, 8)`` preserves 8
decimals and the cumulative error drops below R$ 0.0001.

Existing rows are simply re-cast: 4-decimal values still fit in an
8-decimal column, no data loss, no rebuild needed.

Downgrade reverses the type change; values written at >4dp after this
migration will be rounded on the way back down.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0015_bump_position_precision"
down_revision = "0014_add_quote_cache_and_quote_kind"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("positions") as batch_op:
        batch_op.alter_column(
            "qty",
            existing_type=sa.Numeric(18, 4),
            type_=sa.Numeric(18, 8),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "avg_price",
            existing_type=sa.Numeric(18, 4),
            type_=sa.Numeric(18, 8),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "current_price",
            existing_type=sa.Numeric(18, 4),
            type_=sa.Numeric(18, 8),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("positions") as batch_op:
        batch_op.alter_column(
            "qty",
            existing_type=sa.Numeric(18, 8),
            type_=sa.Numeric(18, 4),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "avg_price",
            existing_type=sa.Numeric(18, 8),
            type_=sa.Numeric(18, 4),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "current_price",
            existing_type=sa.Numeric(18, 8),
            type_=sa.Numeric(18, 4),
            existing_nullable=False,
        )