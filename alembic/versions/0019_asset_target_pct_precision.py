"""Widen ``assets.target_pct`` from ``Numeric(5, 2)`` to ``Numeric(9, 6)``.

Revision ID: 0019_asset_target_pct_precision
Revises: 0018_db_mutation_guards
Create Date: 2026-07-08

F17 makes ``Asset.target_pct`` canonical for both direct ``% ativo na
classe`` edits and server-side conversion of the dashboard's ``% ativo
na carteira`` shortcut. Two decimal places were enough for direct class
editing but not for round-tripping a global target through a class
anchor like ``20 * 100 / 30 = 66.666666...``. ``Numeric(9, 6)`` keeps
the persisted value faithful while staying simple across SQLite and
Postgres.

Upgrade is widening-only, so existing values are preserved verbatim.
Downgrade narrows back to ``Numeric(5, 2)``; any values written at more
than two decimal places after this migration will be rounded by the
database cast on the way down.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0019_asset_target_pct_precision"
down_revision = "0018_db_mutation_guards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("assets") as batch_op:
        batch_op.alter_column(
            "target_pct",
            existing_type=sa.Numeric(5, 2),
            type_=sa.Numeric(9, 6),
            existing_nullable=False,
            existing_server_default="0",
        )


def downgrade() -> None:
    with op.batch_alter_table("assets") as batch_op:
        batch_op.alter_column(
            "target_pct",
            existing_type=sa.Numeric(9, 6),
            type_=sa.Numeric(5, 2),
            existing_nullable=False,
            existing_server_default="0",
        )
