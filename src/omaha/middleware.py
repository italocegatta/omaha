"""ASGI middleware for the Omaha app.

Currently exposes a single :class:`AccessLogMiddleware` that emits
one structured log line per HTTP request, capturing the method,
path, response status, wall-clock duration, and the client IP. The
redirect chain (e.g. ``/`` → 303 → ``/login`` → 200) shows up in the
logs as a single ``http_request`` line per request, *not* as a line
per HTTP hop — the middleware is server-side and only sees what the
ASGI app actually returns to the client.
"""

from __future__ import annotations

import logging
import time

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("omaha.access")


class AccessLogMiddleware:
    """ASGI middleware that emits one ``http_request`` log line per request.

    The message uses ``%``-formatting (not f-strings) so the
    :class:`JsonFormatter` receives a stable ``msg`` template;
    operators can search for ``http_request method=GET path=...`` in
    log shippers without depending on the actual values.

    The middleware wraps ``send`` rather than introspecting the
    response object because ASGI is callback-based: the inner app
    emits status headers via ``await send({"type": "http.response.start", "status": ...})``
    and the body via one or more ``http.response.body`` messages.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Lifespan, websocket, and other non-HTTP scope types pass
        # through untouched. Without this guard the middleware would
        # log lifespan events as ``http_request method=None path=None``
        # and the format contract would be ambiguous.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.monotonic()
        # Default to 500 so an app that crashes *before* calling
        # ``send`` (e.g. an unhandled exception in a route handler
        # that Starlette converts to a 500) still reports a real
        # status code in the access log.
        status_code = 500

        async def wrapped_send(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            # The ``finally`` block guarantees a log line even when
            # the inner app raises — that's exactly when ops most
            # needs to see the access log.
            duration_ms = (time.monotonic() - start) * 1000.0
            client = scope.get("client")
            client_ip = client[0] if client else "-"
            logger.info(
                "http_request method=%s path=%s status=%d duration_ms=%.1f client_ip=%s",
                scope.get("method", "-"),
                scope.get("path", "-"),
                status_code,
                duration_ms,
                client_ip,
            )


__all__ = ["AccessLogMiddleware"]
