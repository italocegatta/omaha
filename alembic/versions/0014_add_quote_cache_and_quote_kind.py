"""Add ``quotes`` table and ``asset_classes.quote_kind`` column.

Revision ID: 0014_add_quote_cache_and_quote_kind
Revises: 0006_asset_target_pct
Create Date: 2026-06-24

Adds the market-quote cache and the per-class ``quote_kind`` enum that
controls which asset classes the QuoteService refreshes.

Schema
------

* ``quotes(symbol TEXT PRIMARY KEY, price NUMERIC(18, 4) NOT NULL,
  currency TEXT NOT NULL, fetched_at TIMESTAMP NOT NULL)`` — the
  DB-backed cache. ``symbol`` is the yfinance-mapped ticker (the
  consumer key, not the raw broker ticker); ``fetched_at`` is what
  the cache uses to compute freshness at read time against
  ``QUOTE_TTL_SECONDS``. No FK to ``positions`` because one quote
  row can serve multiple broker positions across profiles.

* ``asset_classes.quote_kind VARCHAR(8) NOT NULL DEFAULT 'none'`` —
  with a CHECK constraint restricting the value to
  ``('auto', 'manual', 'none')``. Default ``none`` so existing rows
  on upgrade opt out of live fetching until the user explicitly
  flips the toggle via the editor or the CSV seed.

Why the CHECK constraint, not a SQLAlchemy ``Enum``
---------------------------------------------------

The CSV seed path (``scripts/seed_from_csv.py``) writes values from
the ``{profile}_classes.csv`` ``quote_kind`` column. A bare
``String(8)`` column with a DB CHECK lets the Python enum
(:class:`~omaha.models.QuoteKind`) and the SQL CHECK stay in sync
without locking the column to a SQLAlchemy enum type (which would
require an Alembic migration to ALTER TYPE every time a value is
added, and would force every raw ``INSERT`` to cast).

Downgrade
---------

Drops the ``quotes`` table (one shot) and the ``quote_kind`` column
from ``asset_classes``. No data loss in the rest of the schema.
The QuoteService background loop will be a no-op on the next
startup because every class defaults to ``none`` and no quotes
will be written.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_add_quote_cache_and_quote_kind"
down_revision = "0006_asset_target_pct"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ``quotes`` and add ``quote_kind`` to ``asset_classes``."""
    op.create_table(
        "quotes",
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("symbol", name="pk_quotes"),
    )

    # SQLite cannot ALTER an existing table to add a CHECK constraint,
    # so use batch mode which copies + rewrites the table transparently.
    # On Postgres this becomes a plain ALTER + ADD CONSTRAINT.
    with op.batch_alter_table("asset_classes") as batch_op:
        batch_op.add_column(
            sa.Column(
                "quote_kind",
                sa.String(length=8),
                nullable=False,
                server_default="none",
            )
        )
        batch_op.create_check_constraint(
            "ck_asset_class_quote_kind",
            "quote_kind IN ('auto', 'manual', 'none')",
        )


def downgrade() -> None:
    """Drop the CHECK + column + table in reverse order."""
    with op.batch_alter_table("asset_classes") as batch_op:
        batch_op.drop_constraint("ck_asset_class_quote_kind", type_="check")
        batch_op.drop_column("quote_kind")
    op.drop_table("quotes")