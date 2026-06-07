"""Macro asset-class buckets per profile.

Revision ID: 0002_macro_classes
Revises: 0001_initial
Create Date: 2026-06-07

Adds the ``asset_classes`` table that the S02 macro-class CRUD editor
reads and writes. Each row is one named allocation bucket (e.g.
"Renda Fixa" 60%, "Acoes" 30%, "Reserva" 10%) owned by a single
``profiles`` row; ``ON DELETE CASCADE`` on the FK mirrors the 0001
profile → user FK so deleting a profile removes its classes.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_macro_classes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("target_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["profiles.id"],
            ondelete="CASCADE",
            name="fk_asset_class_profile_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "name", name="uq_asset_class_profile_name"),
    )
    op.create_index("ix_asset_classes_profile_id", "asset_classes", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_asset_classes_profile_id", table_name="asset_classes")
    op.drop_table("asset_classes")
