"""ImportPreview stores parsed broker CSVs between upload and confirm.

Revision ID: 0005_import_previews
Revises: 0004_positions
Create Date: 2026-06-07

Adds the ``import_previews`` table the S04 CSV importer uses to
persist the parsed-but-not-yet-confirmed broker rows. The review
screen reads the preview back from this table (re-hydrating the
JSON-serialized RawPosition list) so the user does not have to
re-upload the file on every navigation.

``profile_id`` is the FK to the S01 ``profiles`` table; ``ON DELETE
CASCADE`` mirrors the S02 profile → class CASCADE, so deleting a
profile removes every preview underneath it in a single operation.

``raw_json`` is a plain ``String`` (no length cap) — the parser's
output is JSON, not a fixed-width CSV column, so the SQLAlchemy
default of NVARCHAR-derived length is the right fit. The
post-upload 1 MB cap on the upload route bounds the worst-case
size of a single row.

The index on ``profile_id`` is the only access pattern that matters
at the S04 scope: confirm + review both filter on the active
profile's id. We do not index ``created_at`` because the 1h
expiration check is performed in Python (single-row lookup) rather
than as a SQL filter.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_import_previews"
down_revision = "0004_positions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_previews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("raw_json", sa.String(), nullable=False),
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
            name="fk_import_preview_profile_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_import_previews_profile_id", "import_previews", ["profile_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_import_previews_profile_id", table_name="import_previews")
    op.drop_table("import_previews")
