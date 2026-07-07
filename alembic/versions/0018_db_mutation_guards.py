"""Add DB mutation safety tables (R06).

Revision ID: 0018_db_mutation_guards
Revises: 0017_is_family_sentinel
Create Date: 2026-07-07

R06 — DB mutation guards. Two new tables to back the
``db-mutation-safety`` and ``admin-recovery`` capabilities:

* ``db_snapshots`` — a row per auto-captured pre-mutation SQLite
  snapshot under ``data/snapshots/``. The path is the absolute
  filesystem location; the size is the file size at capture time.
  ``mutation_id`` is nullable: it stays ``NULL`` for the few
  seconds between the snapshot capture and the audit-row insert,
  and is back-filled to the new :class:`DbMutation.id` once the
  mutation commits. The ``admin-recovery`` spec joins on this
  column to attach "which mutation triggered this snapshot" to
  the listing payload.

* ``db_mutations`` — a row per destructive mutation that fires
  the gate. ``route`` is the HTTP method + path template (e.g.
  ``"POST /api/import/commit"``); ``actor_user_id`` and
  ``profile_id`` are nullable because some system-initiated
  mutations (e.g. ``db-reset``) have no actor. ``before_json``
  and ``after_json`` are JSON-serialised counts of
  classes / assets / positions at the boundary; the route
  computes them via the same SQL counts the dashboard uses
  so the values are directly comparable. ``snapshot_path``
  points at the corresponding ``db_snapshots`` row's
  ``path`` and is also nullable for mutations that did not
  fire the gate (single-row edits).

Backfill
--------
Both tables are empty on upgrade — no backfill needed. The
``db-reset`` path is unaffected: it drops and recreates the DB,
which drops both new tables along with everything else, then
the upgrade re-runs against the fresh file and the migration
applies from scratch.

Downgrade
---------
Drops both tables in reverse dependency order
(``db_mutations`` first, then ``db_snapshots``). Snapshot
files on disk become orphans and can be removed with
``rm data/snapshots/portfolio-*.db``.

Why ``String`` for JSON columns
-------------------------------
Matches the existing ``ImportPreview.raw_json`` convention:
SQLite has no native JSON type, and the project stores JSON
as ``String`` + ``json.dumps/loads`` rather than ``JSON`` to
keep the schema portable to PostgreSQL without surprise type
mapping (``JSONB`` round-trips break for ``Decimal`` and
``datetime``). The spec's "before/after counts" payload
serialises to a small dict that fits comfortably in a ``TEXT``
column.

Indexes
-------
``db_mutations`` gets two single-column indexes on
``actor_user_id`` and ``profile_id`` so the admin
``/admin/audit`` listing can filter by either without a
table scan. ``db_snapshots`` is small (FIFO-pruned to 50) so
no secondary index is needed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018_db_mutation_guards"
down_revision: str | None = "0017_is_family_sentinel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ``db_snapshots`` and ``db_mutations`` tables."""
    op.create_table(
        "db_mutations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("route", sa.String(length=128), nullable=False),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("before_json", sa.String(), nullable=False),
        sa.Column("after_json", sa.String(), nullable=False),
        sa.Column("snapshot_path", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_db_mutations_actor_user_id", "db_mutations", ["actor_user_id"])
    op.create_index("ix_db_mutations_profile_id", "db_mutations", ["profile_id"])
    op.create_index("ix_db_mutations_created_at", "db_mutations", ["created_at"])

    op.create_table(
        "db_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "mutation_id",
            sa.Integer(),
            sa.ForeignKey("db_mutations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_db_snapshots_created_at", "db_snapshots", ["created_at"])


def downgrade() -> None:
    """Drop ``db_snapshots`` and ``db_mutations`` tables."""
    op.drop_index("ix_db_snapshots_created_at", table_name="db_snapshots")
    op.drop_table("db_snapshots")
    op.drop_index("ix_db_mutations_created_at", table_name="db_mutations")
    op.drop_index("ix_db_mutations_profile_id", table_name="db_mutations")
    op.drop_index("ix_db_mutations_actor_user_id", table_name="db_mutations")
    op.drop_table("db_mutations")
