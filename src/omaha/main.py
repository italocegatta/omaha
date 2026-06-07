"""FastAPI application composition and startup wiring.

Module surface
--------------
- ``app`` — the ASGI application imported by ``uvicorn`` (and used
  directly by the test :class:`TestClient`).
- ``create_app`` — factory form of the same composition. Exposed for
  tests that want to build a custom app (e.g. with overridden
  dependencies) without going through the module-level singleton.

Startup event
-------------
On application start the process runs ``alembic upgrade head`` and the
idempotent :func:`omaha.seed.seed`. Both steps are safe to re-run on
every container start, which is what makes "docker compose up --build"
recover from a wiped volume. Tests opt out by setting
``OMAHA_SKIP_STARTUP=1`` in the environment (the test fixture in
``tests/conftest.py`` sets up its own migration + seed before the
client is created).

The startup event is registered with ``@app.on_event`` because that
is what the T03 plan specifies. ``on_event`` is deprecated in favour
of the ``lifespan`` context manager; the warning is harmless for now
and the slice plan keeps the deprecation in scope for a future
refactor.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from omaha.config import settings
from omaha.routes import auth as auth_routes
from omaha.routes import classes as classes_routes
from omaha.routes import health as health_routes
from omaha.routes import pages as pages_routes

_PACKAGE_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _PACKAGE_DIR / "templates"
_STATIC_DIR = _PACKAGE_DIR / "static"


def _run_startup_migrations_and_seed() -> None:
    """Run ``alembic upgrade head`` then :func:`seed` on application start.

    Both steps are idempotent; on a populated database they are no-ops
    (alembic detects ``alembic_version = head`` and the seed skips when
    any user is present). The subprocess for alembic is necessary
    because the migration environment (``alembic/env.py``) reads
    ``DATABASE_URL`` directly from the environment, and the in-process
    SQLAlchemy engine is bound at import time.
    """
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    # Importing seed inside the function defers the database import
    # until startup; tests that opt out of the startup event never
    # touch the database via this path.
    from omaha.seed import seed

    seed()


def create_app() -> FastAPI:
    """Build and return a fully-configured :class:`FastAPI` instance."""
    app = FastAPI(title="Omaha", version="0.1.0")

    # SessionMiddleware signs the ``omaha_session`` cookie with
    # ``settings.SECRET_KEY``. ``https_only`` is False in dev so the
    # cookie is sent over plain HTTP; the deploy slice flips it on.
    # Starlette accepts ``same_site`` (snake-case) here, not
    # ``samesite`` — the camelCase spelling from older docs is no
    # longer supported.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="omaha_session",
        https_only=False,
        same_site="lax",
    )

    # Bind a single Jinja2Templates to app.state so every route can
    # reach it via ``request.app.state.templates``. Sharing one
    # instance is also what makes ``TemplateResponse(request, ...)``
    # pick up our context processors later (T04 will add them).
    app.state.templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    app.include_router(health_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(pages_routes.router)
    app.include_router(classes_routes.router)

    # ``/static`` is mounted at the package's static directory.
    # The directory must exist for the mount to succeed — the T03
    # ``__init__`` step created ``src/omaha/static/app.css`` so the
    # directory is on disk.
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    if os.environ.get("OMAHA_SKIP_STARTUP") != "1":
        # ``on_event`` is deprecated in favour of ``lifespan``; we keep
        # it for the T03 plan contract. The deprecation warning is
        # benign here.
        app.on_event("startup")(_run_startup_migrations_and_seed)

    return app


# Module-level singleton for ``uvicorn omaha.main:app`` and for the
# convenience ``omaha`` console script defined in ``pyproject.toml``.
app = create_app()


def main() -> None:  # pragma: no cover - console entry point
    """Run the app under uvicorn when invoked as ``python -m omaha.main``."""
    import uvicorn

    uvicorn.run("omaha.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
