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
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from omaha.config import settings
from omaha.logging_config import configure_logging
from omaha.middleware import AccessLogMiddleware, NoStoreHTMLMiddleware
from omaha.routes import assets as assets_routes
from omaha.routes import auth as auth_routes
from omaha.routes import classes as classes_routes
from omaha.routes import health as health_routes
from omaha.routes import imports as imports_routes
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


def _brl(value: object) -> str:
    """Format a numeric value as Brazilian Real (R$ X.XXX,XX).

    Used by the dashboard's portfolio + per-asset rows. Negative
    values are emitted as ``-R$ X.XXX,XX`` so the dashboard's
    color-coding can pivot on the sign without re-parsing. ``None``
    renders as a neutral dash (``—``) so an empty portfolio shows
    a placeholder rather than ``R$ 0,00`` (which would be visually
    identical to a real 0.00 total).
    """
    if value is None:
        return "—"
    quantized = value if isinstance(value, Decimal) else Decimal(str(value))
    sign = "-" if quantized < 0 else ""
    abs_value = abs(quantized)
    # ``f"{abs_value:.2f}"`` is locale-independent (always '.') and
    # matches the rest of the project's formatting style; the final
    # swap converts the decimal point to a comma for the BR locale.
    formatted = f"{abs_value:.2f}".replace(".", ",")
    # Thousands separator: walk backwards from the decimal and insert
    # '.' every 3 digits. ``formatted`` always ends in ",dd" so we
    # split off the fractional part first.
    int_part, _, frac_part = formatted.partition(",")
    grouped: list[str] = []
    while len(int_part) > 3:
        grouped.append(int_part[-3:])
        int_part = int_part[:-3]
    grouped.append(int_part)
    grouped.reverse()
    int_grouped = ".".join(grouped)
    return f"{sign}R$ {int_grouped},{frac_part}"


def create_app() -> FastAPI:
    """Build and return a fully-configured :class:`FastAPI` instance."""
    app = FastAPI(title="Omaha", version="0.1.0")

    # SessionMiddleware signs the ``omaha_session`` cookie with
    # ``settings.SECRET_KEY``. ``https_only`` follows ``OMAHA_ENV``:
    # True in production (TLS terminates at nginx), False in dev so
    # the cookie is sent over plain HTTP. Starlette accepts
    # ``same_site`` (snake-case) here, not ``samesite`` — the
    # camelCase spelling from older docs is no longer supported.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="omaha_session",
        https_only=os.environ.get("OMAHA_ENV") == "production",
        same_site="lax",
    )
    # AccessLogMiddleware is added AFTER SessionMiddleware so it ends
    # up OUTERMOST in Starlette's LIFO middleware stack — the access
    # log wraps the request, then Session runs, then the app. The
    # 303 redirect that SessionMiddleware issues for an
    # unauthenticated GET / therefore flows through wrapped_send and
    # shows up as a single ``status=303`` line in the access log.
    # NoStoreHTMLMiddleware is added AFTER AccessLogMiddleware so it
    # sits just outside the app (closer to the client) — the access
    # log sees the final response status, but the no-store header is
    # injected on the way OUT to the browser.
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(NoStoreHTMLMiddleware)

    # Bind a single Jinja2Templates to app.state so every route can
    # reach it via ``request.app.state.templates``. Sharing one
    # instance is also what makes ``TemplateResponse(request, ...)``
    # pick up our context processors later (T04 will add them).
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    # Register the BRL currency filter on the shared templates
    # instance — the dashboard (S05) is the only consumer for now,
    # but a future reports slice will reuse the same formatter.
    templates.env.filters["brl"] = _brl
    app.state.templates = templates

    app.include_router(health_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(pages_routes.router)
    app.include_router(classes_routes.router)
    app.include_router(assets_routes.router)
    app.include_router(imports_routes.router)

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


# Configure structured logging at module load. We skip this in
# pytest (the ``pytest`` entry is in ``sys.modules`` because pytest
# has already imported its own machinery by the time it imports
# ``omaha.main``) so the test client and ``caplog`` keep their
# default handlers; the dedicated logging tests in
# ``tests/test_t06_logging.py`` call :func:`configure_logging`
# explicitly with the format they want to assert against.
if "pytest" not in sys.modules:
    configure_logging(level=settings.LOG_LEVEL, fmt=settings.effective_log_format)

# Module-level singleton for ``uvicorn omaha.main:app`` and for the
# convenience ``omaha`` console script defined in ``pyproject.toml``.
app = create_app()


def main() -> None:  # pragma: no cover - console entry point
    """Run the app under uvicorn when invoked as ``python -m omaha.main``."""
    import uvicorn

    uvicorn.run("omaha.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
