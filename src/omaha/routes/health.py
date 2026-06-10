"""``/healthz`` readiness probe with DB reachability check.

Returns 200 + a JSON payload when the database is reachable,
503 + a structured failure payload when the engine raises. The
endpoint takes no auth and no user input; it is a pure
readiness probe for the orchestrator + Dockerfile HEALTHCHECK.

Contract
--------
- 200: ``{"status": "ok", "db": "ok", "service": "omaha", "version": "<app>"}``
- 503: ``{"status": "degraded", "db": "down", "reason": "<ExcClass>",
         "service": "omaha", "version": "<app>"}``

The 200/503 split lets the orchestrator distinguish process death
(restart the container) from a DB-side problem (alert, don't restart).
The ``reason`` field surfaces the exception class name (not the
traceback) so log shippers can route on it without parsing free-form
text.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from omaha.auth import DbSession

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz(request: Request, db: DbSession) -> JSONResponse:
    """Run ``SELECT 1`` and return 200/503 based on the outcome."""
    version = request.app.version
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — endpoint must never 500
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "db": "down",
                "reason": type(exc).__name__,
                "service": "omaha",
                "version": version,
            },
        )
    return JSONResponse(
        content={
            "status": "ok",
            "db": "ok",
            "service": "omaha",
            "version": version,
        }
    )


__all__ = ["router"]
