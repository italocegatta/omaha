"""Assets belong to asset classes.

Revision ID: 0003_assets
Revises: 0002_macro_classes
Create Date: 2026-06-07

Adds the ``assets`` table that the S03 asset CRUD editor reads and
writes. Each row is one specific financial instrument (e.g.
"Tesouro Selic 2029", "PETR4", "IVVB11") owned by a single
``asset_classes`` row; ``ON DELETE CASCADE`` on the FK mirrors the
0002 class → profile FK so deleting an asset class removes its
assets, and the existing profile → class CASCADE (0002) plus
profile → user CASCADE (0001) mean deleting a profile removes
every class and asset underneath it in a single transaction.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_assets"
down_revision = "0002_macro_classes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_class_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["asset_class_id"],
            ["asset_classes.id"],
            ondelete="CASCADE",
            name="fk_asset_asset_class_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asset_class_id", "name", name="uq_asset_asset_class_name"),
    )
    op.create_index("ix_assets_asset_class_id", "assets", ["asset_class_id"])


def downgrade() -> None:
    op.drop_index("ix_assets_asset_class_id", table_name="assets")
    op.drop_table("assets")
