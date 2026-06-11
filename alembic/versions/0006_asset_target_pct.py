"""Add ``target_pct`` to ``assets`` for the S01 inline-edit slice.

Revision ID: 0006_asset_target_pct
Revises: 0005_import_previews
Create Date: 2026-06-11

Adds the per-asset ``target_pct`` column that the S01 dashboard
displays next to every asset and the Alpine inline editor mutates
through PATCH ``/api/assets/{id}``.

Schema
------

* ``target_pct NUMERIC(5, 2) NOT NULL DEFAULT 0`` mirrors the
  :class:`~omaha.models.AssetClass` ``target_pct`` shape so the
  per-class sum invariant (enforced by
  :func:`omaha.validators.validate_target_pct_sum`) can mix
  asset-level and class-level percentages without precision
  mismatches. ``NUMERIC(5, 2)`` is the same width as the class
  column, so the largest legitimate value is 999.99 and rounding
  is to 2 decimal places (matches the S02 class-level editor).
* ``NOT NULL`` with a server default of ``0`` so existing rows
  backfill cleanly on upgrade (D015 — the previous M002-CONTEXT
  draft was ``0007``, but the next free sequence on disk is
  ``0006``; deviation recorded in T01).
* No check constraint on the sum. The sum-to-100 invariant is
  enforced by the validator and the PATCH route, not the DB —
  SQLite would reject ``ALTER TABLE ... ADD CONSTRAINT``
  anyway. The ``NOT NULL`` is the only DB-level guard.

Downgrade
---------

Drops the column. The S01 Alpine editor will start returning 0
for every asset's target_pct on the next request, which the T03
dashboard renders as a "—" placeholder. No data loss beyond the
inline-edited percentages, which the user can re-enter.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_asset_target_pct"
down_revision = "0005_import_previews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ``target_pct`` to ``assets`` with a 0 default for backfill."""
    op.add_column(
        "assets",
        sa.Column(
            "target_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Drop the ``target_pct`` column from ``assets``."""
    op.drop_column("assets", "target_pct")
