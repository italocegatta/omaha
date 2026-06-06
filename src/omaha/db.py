"""Database engine, session factory, and FastAPI dependency.

SQLAlchemy 2.0 typed style. A single `Base` is exported and shared by every
model in the project. Future slices (S02-S05) add their model classes to
``omaha.models`` so that ``Base.metadata`` is fully populated for Alembic
autogenerate.

SQLite single-writer caveat
---------------------------
The default deployment uses SQLite (``sqlite:///./data/portfolio.db``). SQLite
holds a file-level write lock, so a single process can only have one
outstanding write transaction at a time. We disable ``check_same_thread`` so
SQLAlchemy's connection pool can hand connections to worker threads
(FastAPI sync routes, Starlette's threadpool); *read* concurrency is fine,
but heavy concurrent writes will serialise. This is acceptable for the
family-portfolio use case (low write volume) and avoids the operational
overhead of Postgres in the first milestone.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from omaha.config import settings


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model in the project."""


# SQLite requires ``check_same_thread=False`` to allow connections to be
# shared across threads (FastAPI's threadpool). Other backends don't need
# the override.
_connect_args: dict[str, Any] = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped :class:`Session`.

    The session is closed automatically when the request finishes, even if
    the handler raised an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "engine", "SessionLocal", "get_db"]
