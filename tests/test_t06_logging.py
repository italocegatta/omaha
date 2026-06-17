"""S06/T02 — JSON structured logging + access log middleware.

Three pure tests for the logging machinery — they do not need the
FastAPI app or a TestClient and stay in the unit subset:

1. :class:`JsonFormatter` emits exactly the seven documented keys
   and uses the level *name* (not the numeric code).
2. :class:`JsonFormatter` surfaces the formatted traceback as a
   string in the ``exc_info`` key when ``record.exc_info`` is set.
3. :func:`configure_logging` installs the JSON formatter and an
   :func:`logging.getLogger`("omaha").info() call after setup
   produces a JSON-parseable line on stdout.

The two ``AccessLogMiddleware`` tests (which need ``TestClient``)
live in ``tests/audit_integration/test_logging_middleware.py``.
"""

from __future__ import annotations

import json
import logging

import pytest

from omaha.logging_config import JsonFormatter, configure_logging

pytestmark = pytest.mark.unit


# Required module name for the formatter's ``module`` key. The
# ``JsonFormatter`` derives ``module`` from the record's ``pathname``,
# stripping ``tests/`` and ``.py`` automatically. The constant keeps
# the assertion on a single source of truth.
_THIS_MODULE = "test_t06_logging"


# The seven keys the JSON formatter is contractually required to
# emit. New keys can be added — the contract is on the union, not
# the strict set — but the test fails fast on accidental drops.
_EXPECTED_KEYS = {"ts", "level", "logger", "msg", "module", "line", "exc_info"}


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
    assert parsed["msg"] == "hello world"
    assert parsed["module"] == _THIS_MODULE
    assert parsed["line"] == 42
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


def test_configure_logging_json_format_emits_parseable_line(capsys) -> None:
    """``configure_logging(level="INFO", fmt="json")`` installs the
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
