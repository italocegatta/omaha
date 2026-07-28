"""ASGI middleware for the Omaha app.

Currently exposes three middlewares:

- :class:`AccessLogMiddleware` emits one structured log line per
  HTTP request, capturing method, path, status, duration, and
  client IP. The redirect chain (e.g. ``/`` → 303 → ``/login`` → 200)
  shows up as a single ``http_request`` line per request.
- :class:`NoStoreHTMLMiddleware` injects ``Cache-Control: no-store``
  on HTML responses from authenticated routes so the browser always
  fetches the latest dashboard template (defense against stale
  ``<select>`` markup during dev / iteration on UI).
- :class:`StaticCacheControlMiddleware` injects
  ``Cache-Control: no-cache`` on ``/static/`` asset responses so the
  browser revalidates them every load (cheap 304 via the etag that
  StaticFiles already emits). Without an explicit directive the
  browser applies heuristic caching to ``app.css`` / ``echarts.min.js``
  and can paint a stale pre-change asset even after the HTML document
  is fresh — the recurring "empty cards" symptom during UI iteration.
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


__all__ = ["AccessLogMiddleware", "NoStoreHTMLMiddleware", "StaticCacheControlMiddleware"]


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


_STATIC_PREFIX = "/static/"


class StaticCacheControlMiddleware:
    """Inject ``Cache-Control: no-cache`` on ``/static/`` asset responses.

    Starlette's :class:`~starlette.staticfiles.StaticFiles` emits an
    ``etag`` and ``last-modified`` but no ``Cache-Control``. In the
    absence of an explicit directive the browser falls back to
    heuristic caching and may reuse a stale ``app.css`` /
    ``echarts.min.js`` without revalidating — even when the HTML
    document itself is fresh (``NoStoreHTMLMiddleware`` already forces
    ``no-store`` on HTML). The result is the recurring "empty cards"
    symptom: a fresh page wiring up a stale, pre-change asset.

    ``no-cache`` forces the browser to revalidate before reuse; the
    existing etag turns that revalidation into a cheap ``304 Not
    Modified`` so assets are still effectively cached on the LAN. This
    deliberately uses ``no-cache`` (not ``no-store``) so the asset
    bytes stay stored and only the freshness check hits the server.

    The middleware only touches paths under ``/static/`` and replaces
    any pre-existing ``cache-control`` header (case-insensitive) so the
    directive is unambiguous. HTML, JSON (``/api/*``), and the login
    page are left to their existing handling.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope.get("path", "").startswith(_STATIC_PREFIX):
            await self.app(scope, receive, send)
            return

        async def wrapped_send(message: dict) -> None:
            if message["type"] != "http.response.start":
                await send(message)
                return

            raw_headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
            new_headers: list[tuple[bytes, bytes]] = []
            replaced = False
            for name, value in raw_headers:
                if name.lower() == b"cache-control":
                    if not replaced:
                        new_headers.append((b"cache-control", b"no-cache"))
                        replaced = True
                    # Drop subsequent Cache-Control headers too.
                    continue
                new_headers.append((name, value))
            if not replaced:
                new_headers.append((b"cache-control", b"no-cache"))

            new_message = dict(message)
            new_message["headers"] = new_headers
            await send(new_message)

        await self.app(scope, receive, wrapped_send)
