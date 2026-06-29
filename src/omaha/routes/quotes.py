"""HTTP routes for the market-quote cache.

Mounted at ``/api/quotes`` by ``main.py``. Endpoints:

* ``GET /api/quotes/{symbol}`` — single quote; 404 when missing.
* ``GET /api/quotes?symbols=A,B,C`` — batch quote lookup; returns
  ``{"results": [...]}`` with one entry per symbol that has a row,
  omitting missing symbols.
* ``POST /api/quotes/refresh`` — schedules a refresh via FastAPI's
  :class:`BackgroundTasks`; returns ``202 Accepted`` with
  ``{"status": "scheduled"}``. Reuses the QuoteService lock so the
  manual trigger does not overlap with the background loop.

Auth
----
All endpoints require a logged-in user (same as the other ``/api/*``
slices). The optimizer feature that consumes ``POST /refresh`` will
gain a token-based auth path in its own change; for v1 the cookie
session is the gate.

The :class:`QuoteService` is fetched off ``app.state`` (set by
``main.py`` at startup). When startup is skipped (tests), the state
is absent and ``POST /refresh`` returns ``503`` with a clear message
— the test suite injects a stub via ``app.state.quote_service`` for
deterministic behavior.

BackgroundTasks vs asyncio.create_task
--------------------------------------
The first cut used ``asyncio.create_task`` directly, which fails in
the sync TestClient (no event loop in the request thread).
:func:`BackgroundTasks.add_task` runs after the response in the
app's event loop — works under both uvicorn and TestClient without
sprinkling ``asyncio.get_event_loop()`` calls.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from omaha.auth import require_user
from omaha.models import User
from omaha.quotes.cache import QuoteCache

router = APIRouter(prefix="/api/quotes", tags=["quotes"])


def _serialize(
    symbol: str,
    price,
    currency: str,
    fetched_at: datetime,
    fresh: bool,
) -> dict[str, object]:
    """Render a quote row as a JSON-safe dict."""
    if fetched_at.tzinfo is not None:
        fetched_at = fetched_at.astimezone(UTC).replace(tzinfo=None)
    return {
        "symbol": symbol,
        "price": str(price),
        "currency": currency,
        "fetched_at": fetched_at.isoformat(),
        "fresh": fresh,
    }


def _get_service_or_503(request: Request):
    """Return ``app.state.quote_service`` or raise 503."""
    service = getattr(request.app.state, "quote_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="quote service not running",
        )
    return service


@router.get("/{symbol}", response_model=None)
def get_quote(
    symbol: str,
    _: Annotated[User, Depends(require_user)],
) -> JSONResponse:
    """Return one cached quote or 404 when missing."""
    cache = QuoteCache()
    result = cache.get(symbol)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    quote = result.quote
    return JSONResponse(
        content=_serialize(
            symbol=quote.symbol,
            price=quote.price,
            currency=quote.currency,
            fetched_at=quote.fetched_at,
            fresh=result.fresh,
        )
    )


@router.get("", response_model=None)
def get_quotes_batch(
    symbols: str = "",
    _: Annotated[User, Depends(require_user)] = None,  # type: ignore[assignment]
) -> JSONResponse:
    """Batch read. Returns ``{"results": [...]}`` for symbols with rows.

    Symbols without a row are silently omitted (not 404) so a caller
    asking for ``['PETR4.SA', 'UNKNOWN']`` gets the row it can use
    and a short result list rather than a 404 that would block the
    whole batch.
    """
    if not symbols:
        return JSONResponse(content={"results": []})
    wanted = [s.strip() for s in symbols.split(",") if s.strip()]
    if not wanted:
        return JSONResponse(content={"results": []})
    cache = QuoteCache()
    rows = cache.get_many(wanted)
    results = [
        _serialize(
            symbol=r.quote.symbol,
            price=r.quote.price,
            currency=r.quote.currency,
            fetched_at=r.quote.fetched_at,
            fresh=r.fresh,
        )
        for r in rows.values()
    ]
    return JSONResponse(content={"results": results})


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED, response_model=None)
def post_refresh(
    request: Request,
    background_tasks: BackgroundTasks,
    _: Annotated[User, Depends(require_user)],
) -> JSONResponse:
    """Schedule an immediate refresh; returns 202 immediately.

    The refresh coroutine runs after the response is sent via
    :class:`BackgroundTasks` (works under both uvicorn and the
    sync TestClient — :func:`asyncio.create_task` would fail in a
    sync handler because the request thread has no running loop).
    The task acquires the same lock the background loop uses, so
    it serializes with the loop and never overlaps.
    """
    service = _get_service_or_503(request)
    background_tasks.add_task(_run_refresh, service)
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "scheduled"},
    )


async def _run_refresh(service) -> None:
    """Coroutine body for :func:`BackgroundTasks.add_task`."""
    try:
        await service.refresh_once()
    except Exception:  # noqa: BLE001 — task must not crash silently
        # The service's own logger already wrote the details; we
        # swallow here so the background task doesn't propagate.
        pass


__all__ = ["router"]
