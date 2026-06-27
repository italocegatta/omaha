"""POST /api/rebalance route.

Runs the rebalance pipeline for the active profile and returns the
``RebalancePlanResponse`` wire format owned by
:mod:`omaha.rebalance.schemas`. The route is a thin shell around
:func:`omaha.rebalance.glue.run_rebalance`; the orchestration logic
lives in the glue module so it can be unit-tested without a TestClient.

Auth
----
Same as every other JSON route in the project:
``require_user`` + ``require_active_profile``. Unauthenticated
requests bounce to ``/login``; missing active profile is a 404.

Error mapping
-------------
``RebalanceValidationError`` (raised by the solver's
``_validate_rebalance_inputs``) maps to HTTP 400 with the
validation message in ``detail``. Pydantic validation errors
(e.g. ``contribution <= 0``) map to 422 via FastAPI's default
exception handler. Any other exception propagates to FastAPI's
default 500 handler — the route does NOT catch generic exceptions
(no stack-trace leakage in the response).

Stateless
---------
The route does not persist the plan. Each POST recomputes from
the current DB state. Phase 3b (``rebalance-page``) is responsible
for any client-side caching of the last plan if desired.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from omaha.auth import DbSession, require_active_profile, require_user
from omaha.models import Profile, User
from omaha.rebalance.glue import run_rebalance
from omaha.rebalance.models import RebalanceValidationError
from omaha.rebalance.schemas import RebalancePlanResponse, RebalanceRequest

router = APIRouter(tags=["rebalance"])


@router.post(
    "/api/rebalance", response_model=RebalancePlanResponse, response_model_exclude_none=False
)
def post_rebalance(
    payload: RebalanceRequest,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> RebalancePlanResponse:
    """Compute and return the rebalance plan for the active profile.

    The route enforces the auth contract (any logged-in user with an
    active profile can call this), delegates the orchestration to
    :func:`run_rebalance`, and maps ``RebalanceValidationError`` to
    HTTP 400 so the operator sees the validation message instead of
    a stack trace.
    """
    _ = user  # auth gate satisfied; user not consumed downstream
    try:
        return run_rebalance(db, profile, payload.contribution)
    except RebalanceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


__all__ = ["router"]
