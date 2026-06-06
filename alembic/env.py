"""Alembic environment script for the Omaha project.

How the metadata is populated
-----------------------------
``omaha.models`` is imported for its side-effect of registering every
model class on :class:`omaha.db.Base`. The import is a no-op assignment
to ``target_metadata`` -- if a future slice adds new tables, just
importing the new module is enough to make Alembic see them.

The URL is sourced from :func:`omaha.config.settings` (which in turn
reads ``DATABASE_URL`` from the environment / ``.env`` file) so the
``alembic`` CLI and the FastAPI process always target the same database
without a second source of truth.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure ``src/`` is on sys.path so ``import omaha...`` works when alembic
# is invoked from a different working directory.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from omaha.config import settings  # noqa: E402
from omaha.db import Base  # noqa: E402

# Importing the models module registers every mapped class on ``Base``.
# Future slices: add their new model module imports here so autogenerate
# picks up new tables.
import omaha.models  # noqa: E402, F401

config = context.config

# Inject the runtime URL into the Alembic config so ``engine_from_config``
# sees a non-empty ``sqlalchemy.url`` regardless of what is in
# ``alembic.ini``.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a live DB)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
