"""add position totals

Revision ID: 1c73065cff10
Revises: 0015_bump_position_precision
Create Date: 2026-06-26 00:39:13.207416

broker-csv-import-totals: add ``positions.total_invested`` and
``positions.total_current`` columns to carry the broker-published
per-row totals from the CSV columns ``Total investido`` and ``Total
atual``.

Both columns are ``Numeric(18, 4)``, ``nullable=True``, with no
``server_default``. ``NULL`` signals "the source file did not
publish this column" and the dashboard treats the row as a zero
contribution — no fallback to ``qty * price`` (that recompute is the
drift source this change eliminates). Existing rows backfill to
``NULL`` (no recompute migration).

Downgrade drops both columns. Data loss is acceptable: the broker
CSV is the source of truth, and re-import rehydrates the totals.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1c73065cff10"
down_revision: str | None = "0015_bump_position_precision"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ``total_invested`` and ``total_current`` to ``positions``."""
    op.add_column(
        "positions",
        sa.Column("total_invested", sa.Numeric(18, 4), nullable=True),
    )
    op.add_column(
        "positions",
        sa.Column("total_current", sa.Numeric(18, 4), nullable=True),
    )


def downgrade() -> None:
    """Drop ``total_invested`` and ``total_current`` from ``positions``."""
    op.drop_column("positions", "total_current")
    op.drop_column("positions", "total_invested")
