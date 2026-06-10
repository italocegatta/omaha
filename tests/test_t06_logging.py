"""S06/T02 \u2014 JSON structured logging + access log middleware.

Three tests, one per pin in the S06 success criteria:

1. :class:`JsonFormatter` emits exactly the seven documented keys
   and uses the level *name* (not the numeric code).
2. :class:`AccessLogMiddleware` emits one ``http_request`` line per
   HTTP request containing the four required fields (method, path,
   status, duration_ms) plus the client IP. The second case pins
   the redirect-chain behaviour \u2014 an unauthenticated GET ``/``
   must surface as ``status=303`` in the access log (not as the 200
   the redirect target eventually returns, because the redirect is
   server-side and only counts as a single request).
3. :func:`configure_logging` applies without error and an
   :func:`logging.getLogger`(\"omaha\").info() call after setup
   produces a JSON-parseable line on stdout.

Module-level imports stay outside the test functions; the conftest's
``_omaha_test_env`` fixture clears ``sys.modules['omaha.*']`` and
re-imports them, but the names tested here (logging stdlib symbols
+ :class:`AccessLogMiddleware` / :class:`JsonFormatter` /
:func:`configure_logging`) all refer to objects whose identity is
stable across the re-import, so late-binding is not needed for the
tests themselves.
"""

from __future__ import annotations

import json
import logging
import re

from omaha.logging_config import JsonFormatter, configure_logging

# Required module: the test-t06-logging module name is what the
# JsonFormatter picks up as ``record.module`` when a test creates a
# LogRecord with ``pathname=__file__`` and the formatter derives the
# module name from the path. The constant keeps the assertion on a
# single source of truth.
_THIS_MODULE = "test_t06_logging"

# The seven keys the JSON formatter is contractually required to
# emit. New keys can be added \u2014 the contract is on the union, not
# the strict set \u2014 but the test fails fast on accidental drops.
_EXPECTED_KEYS = {"ts", "level", "logger", "msg", "module", "line", "exc_info"}

# Stable regex pieces for the http_request access log message. The
# values are interpolated by the logging module from ``record.args``,
# so the literal template (``"http_request method=%s path=%s status=%d duration_ms=%.1f client_ip=%s"``)
# is the part operators search on.
_ACCESS_LOG_RE = re.compile(
    r"http_request method=(?P<method>\S+) path=(?P<path>\S+) "
    r"status=(?P<status>\d+) duration_ms=(?P<duration_ms>[\d.]+) "
    r"client_ip=(?P<client_ip>\S+)"
)


def test_json_formatter_emits_seven_documented_keys() -> None:
    """``JsonFormatter().format(record)`` returns a JSON string with the
    seven expected keys and the level *name* (not numeric).
    """
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="omaha.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )

    output = formatter.format(record)
    parsed = json.loads(output)

    assert set(parsed.keys()) == _EXPECTED_KEYS
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "omaha.test"
    # ``getMessage()`` applies %-formatting with ``record.args``.
    assert parsed["msg"] == "hello world"
    # ``record.module`` is derived from ``pathname`` \u2014 it strips
    # the ``tests/`` prefix and the ``.py`` suffix automatically.
    assert parsed["module"] == _THIS_MODULE
    assert parsed["line"] == 42
    # No exception in flight \u2192 ``exc_info`` is the JSON literal
    # ``null``, not the string ``"None"`` and not the empty string.
    assert parsed["exc_info"] is None


def test_json_formatter_includes_formatted_traceback_when_exc_info_set() -> None:
    """When ``record.exc_info`` is set the formatter surfaces the
    formatted traceback as a string in the ``exc_info`` key.

    Pins the behaviour log shippers rely on for routing on
    exception class (the traceback always contains the class name
    on the final ``...`` line).
    """
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="omaha.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=10,
            msg="failed",
            args=(),
            exc_info=sys.exc_info(),
        )

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["exc_info"] is not None
    assert "ValueError" in parsed["exc_info"]
    assert "boom" in parsed["exc_info"]


def test_access_log_middleware_emits_http_request_line_for_get_healthz(
    client, caplog
) -> None:
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
    # The Starlette TestClient reports ``client`` as ``("testclient", 50000)``
    # when no X-Forwarded-For is set; either way the field is present
    # and non-empty.
    assert fields["client_ip"] != ""


def test_access_log_middleware_captures_303_redirect_for_unauthenticated_root(
    client, caplog
) -> None:
    """An unauthenticated GET ``/`` returns 303 to ``/login``.

    The access log must capture the 303 (not the eventual 200 from
    ``/login``), because the redirect is server-side and the
    middleware only sees the response the ASGI app sends to the
    client. This is the behaviour the S06 plan called out: "the
    access log captures the 303 to /login on an unauthenticated
    GET /".
    """
    with caplog.at_level(logging.INFO, logger="omaha.access"):
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    access_records = [r for r in caplog.records if r.name == "omaha.access"]
    # Exactly one line for the 303 \u2014 NOT two (303 + 200). The
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


def test_configure_logging_json_format_emits_parseable_line(capsys) -> None:
    """``configure_logging(level=\"INFO\", fmt=\"json\")`` installs the
    JSON formatter and a follow-up ``omaha`` log call produces a
    JSON-parseable line on stdout.
    """
    configure_logging(level="INFO", fmt="json")
    logging.getLogger("omaha").info("hi %s", "there")

    captured = capsys.readouterr()
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert lines, "expected at least one log line on stdout"
    # Parse the *last* line (the most recent ``hi there``). Earlier
    # lines may exist from the StreamHandler being set up after
    # dictConfig propagates to the root logger.
    parsed = json.loads(lines[-1])
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "omaha"
    assert parsed["msg"] == "hi there"
