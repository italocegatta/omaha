"""``/healthz`` liveness probe.

Returns a fixed JSON payload with no auth, no DB access, and no
filesystem reads. The endpoint is intentionally trivial: a 200
response confirms the Python process is alive and the FastAPI router
is wired up; a non-200 response means the container is dead and the
orchestrator should restart it. Database readiness is exposed by a
separate route in a future slice so a transient DB hiccup does not
make the liveness probe flap.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> JSONResponse:
    """Return a static ``{"status": "ok", "service": "omaha"}`` payload."""
    return JSONResponse({"status": "ok", "service": "omaha"})


__all__ = ["router"]
