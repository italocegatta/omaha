"""Add is_family_sentinel flag to Profile (F07).

Revision ID: 0017_is_family_sentinel
Revises: 0016_asset_trade_flags
Create Date: 2026-07-05

F07 — Família-as-profile option. The Família sentinel is a new
``Profile`` row with ``is_family_sentinel=True`` that represents the
cross-User family aggregate as a peer of the real profiles in the
``profile-switcher`` chip (replacing the F06 header toggle). The
column defaults to ``False`` so existing rows (including any F01
``Italo RF2`` fixture rows still present in legacy databases)
backfill to ``False`` and continue to behave as ordinary per-User
profiles. A future R-slice can drop those legacy rows; this
migration is non-destructive by design.

Schema
------

* ``profiles.is_family_sentinel BOOLEAN NOT NULL DEFAULT 0`` —
  flag indicating the row is the Família sentinel. The flag is
  the contract :func:`omaha.auth.get_active_profile` and
  :func:`omaha.routes.pages._resolve_view_mode` read to decide
  whether the active session is rendering the family aggregate
  (read-only) or a real per-profile view.

Defaults favor ``False`` so existing data is untouched and the
canonical ``db-reset`` (which now also creates the Família
sentinel row with ``True``) is the only producer of ``True``
rows. No CHECK constraint — the flag is advisory; the sentinel
shape is enforced at the seed layer (single Família row owned by
``User("family")``) rather than via a DB constraint.

Downgrade
---------

Drops the column. Existing rows lose the sentinel flag (the
column never had business meaning for them — only the Família
row uses ``True``). The Família sentinel row is left in place;
the application layer (``_resolve_view_mode``) gracefully
ignores the absence of the column by reading the column via a
``try/except`` in the ORM model. A full downgrade + cleanup is
out of scope for this migration.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017_is_family_sentinel"
down_revision: str | None = "0016_asset_trade_flags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ``is_family_sentinel`` column to ``profiles``."""
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_family_sentinel",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def downgrade() -> None:
    """Drop ``is_family_sentinel`` column from ``profiles``."""
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_column("is_family_sentinel")
