"""ASGI middleware for the Omaha app.

Currently exposes two middlewares:

- :class:`AccessLogMiddleware` emits one structured log line per
  HTTP request, capturing method, path, status, duration, and
  client IP. The redirect chain (e.g. ``/`` → 303 → ``/login`` → 200)
  shows up as a single ``http_request`` line per request.
- :class:`NoStoreHTMLMiddleware` injects ``Cache-Control: no-store``
  on HTML responses from authenticated routes so the browser always
  fetches the latest dashboard template (defense against stale
  ``<select>`` markup during dev / iteration on UI).
"""

from __future__ import annotations

import logging
import time

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("omaha.access")


# Paths the no-store middleware leaves alone. ``/login`` is the
# unauthenticated login page (no user data to protect); ``/static``
# is served by Starlette's StaticFiles with its own long-lived
# cache headers; ``/api/*`` is JSON and follows REST caching
# semantics; ``/healthz`` is the liveness probe and operators expect
# it to be cacheable by intermediaries.
_NO_STORE_SKIP_PREFIXES: tuple[str, ...] = (
    "/static/",
    "/api/",
    "/healthz",
)
_NO_STORE_SKIP_EXACT: frozenset[str] = frozenset({"/login"})


def _should_skip_no_store(path: str) -> bool:
    if path in _NO_STORE_SKIP_EXACT:
        return True
    return any(path.startswith(p) for p in _NO_STORE_SKIP_PREFIXES)


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


__all__ = ["AccessLogMiddleware", "NoStoreHTMLMiddleware"]


class NoStoreHTMLMiddleware:
    """Inject ``Cache-Control: no-store`` on HTML responses.

    The dashboard is the only authenticated HTML surface today
    (``GET /``), but the middleware applies to every HTML response
    that is not on the skip-list so future page routes pick up the
    header automatically. JSON responses (``/api/*``) keep their
    REST caching semantics; static assets keep their long-lived
    cache headers; the login page keeps the browser default.

    The middleware inspects the ``http.response.start`` message that
    Starlette sends before the body and, when the ``Content-Type``
    starts with ``text/html`` AND the request path is not on the
    skip-list, replaces any existing ``cache-control`` header with
    ``Cache-Control: no-store``. ASGI headers are a list of
    ``[name, value]`` byte tuples — we rebuild the list with the
    new header in place of any prior match (case-insensitive name
    comparison because HTTP header names are case-insensitive).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        skip = _should_skip_no_store(path)

        async def wrapped_send(message: dict) -> None:
            if skip or message["type"] != "http.response.start":
                await send(message)
                return

            raw_headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
            content_type = ""
            for name, value in raw_headers:
                if name.lower() == b"content-type":
                    content_type = value.decode("latin-1", errors="replace")
                    break

            if not content_type.split(";", 1)[0].strip().lower().startswith("text/html"):
                await send(message)
                return

            # Drop any existing Cache-Control, then append no-store so
            # downstream caches (and the browser back/forward cache)
            # never serve a stale HTML snapshot.
            new_headers: list[tuple[bytes, bytes]] = []
            replaced = False
            for name, value in raw_headers:
                if name.lower() == b"cache-control":
                    if not replaced:
                        new_headers.append((b"cache-control", b"no-store"))
                        replaced = True
                    # Drop subsequent Cache-Control headers too.
                    continue
                new_headers.append((name, value))
            if not replaced:
                new_headers.append((b"cache-control", b"no-store"))

            new_message = dict(message)
            new_message["headers"] = new_headers
            await send(new_message)

        await self.app(scope, receive, wrapped_send)
