"""S06/T02 — AccessLogMiddleware integration tests.

Tests that exercise the access-log middleware against the live
``omaha.main.app`` via :class:`fastapi.testclient.TestClient`. Marked
``@pytest.mark.integration`` so they run with the audit-integration
subset (``task test-integration``), not the fast unit subset.

The ``client`` and ``caplog`` fixtures come from
:mod:`tests.conftest` — pytest's hierarchical conftest discovery
applies.

Three tests, mirroring the original :mod:`tests.test_t06_logging`:

1. GET /healthz triggers exactly one ``http_request`` access line
   with the four required fields plus the client IP.
2. An unauthenticated GET / returns 303 to /login — the access log
   must capture the 303, not the eventual 200 from /login (the
   redirect is server-side and the middleware only sees the
   response the ASGI app sends).
3. configure_logging installs the JSON formatter and a follow-up
   ``omaha`` log call produces a JSON-parseable line on stdout.
   (Kept here because the original test_t06_logging covers the
   formatter+configure surface; this is the runtime check that the
   middleware + JSON formatter work together.)
"""

from __future__ import annotations

import logging
import re

import pytest

pytestmark = pytest.mark.integration


# Stable regex pieces for the http_request access log message. The
# values are interpolated by the logging module from ``record.args``,
# so the literal template
# (``"http_request method=%s path=%s status=%d duration_ms=%.1f client_ip=%s"``)
# is the part operators search on.
_ACCESS_LOG_RE = re.compile(
    r"http_request method=(?P<method>\S+) path=(?P<path>\S+) "
    r"status=(?P<status>\d+) duration_ms=(?P<duration_ms>[\d.]+) "
    r"client_ip=(?P<client_ip>\S+)"
)


def test_access_log_middleware_emits_http_request_line_for_get_healthz(client, caplog) -> None:
    """A GET /healthz triggers exactly one ``http_request`` line on the
    ``omaha.access`` logger, with the four required fields plus the
    client IP.
    """
    with caplog.at_level(logging.INFO, logger="omaha.access"):
        response = client.get("/healthz")

    assert response.status_code == 200
    access_records = [r for r in caplog.records if r.name == "omaha.access"]
    assert len(access_records) == 1

    message = access_records[0].getMessage()
    match = _ACCESS_LOG_RE.search(message)
    assert match is not None, f"access log line did not match template: {message!r}"
    fields = match.groupdict()
    assert fields["method"] == "GET"
    assert fields["path"] == "/healthz"
    assert int(fields["status"]) == 200
    assert float(fields["duration_ms"]) >= 0.0
    assert fields["client_ip"] != ""


def test_access_log_middleware_captures_303_redirect_for_unauthenticated_root(
    client, caplog
) -> None:
    """An unauthenticated GET ``/`` returns 303 to ``/login``.

    The access log must capture the 303 (not the eventual 200 from
    ``/login``), because the redirect is server-side and the
    middleware only sees the response the ASGI app sends to the
    client.
    """
    with caplog.at_level(logging.INFO, logger="omaha.access"):
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    access_records = [r for r in caplog.records if r.name == "omaha.access"]
    # Exactly one line for the 303 — NOT two (303 + 200). The
    # ``follow_redirects=False`` above would have produced two if
    # the client were doing the redirect, but Starlette short-
    # circuits at the 303 response so only one record fires.
    assert len(access_records) == 1

    message = access_records[0].getMessage()
    match = _ACCESS_LOG_RE.search(message)
    assert match is not None, f"access log line did not match template: {message!r}"
    fields = match.groupdict()
    assert fields["method"] == "GET"
    assert fields["path"] == "/"
    assert int(fields["status"]) == 303
