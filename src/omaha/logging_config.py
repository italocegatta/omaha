"""Structured logging configuration.

Two formatters (JSON and text) and a single :func:`configure_logging`
entry point that wires one of them into the ``omaha`` and
``omaha.access`` loggers via :func:`logging.config.dictConfig`.

The JSON shape is contractually pinned by ``tests/test_t06_logging.py``:

* ``ts``     — ISO-8601 UTC with microsecond precision.
* ``level``  — record level name (``INFO``, ``WARNING``, ...), not numeric.
* ``logger`` — the logger name (``omaha.routes.health``,
               ``omaha.access``, ...).
* ``msg``    — the fully-formatted message after ``%``-style argument
               interpolation. Operators can search for stable templates
               like ``http_request method=GET path=...`` because
               application code calls ``logger.info("http_request ... %s", arg)``
               rather than f-strings.
* ``module`` — the source module that emitted the record.
* ``line``   — source line number.
* ``exc_info`` — formatted traceback string, or ``null`` when no
                 exception is in flight.
"""

from __future__ import annotations

import datetime
import json
import logging
import logging.config
import sys
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit each :class:`logging.LogRecord` as a single-line JSON object.

    The seven-key shape is the public contract — log shippers depend
    on the exact key set and on the level being a *name* rather than
    a numeric code (the name is what most alert rules match on).
    """

    def format(self, record: logging.LogRecord) -> str:
        # ISO-8601 UTC with microsecond precision. ``record.created``
        # is the POSIX timestamp the logging module sets at emission
        # time, so this gives every record a wall-clock identifier
        # independent of the host's local timezone.
        ts = (
            datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
            .isoformat()
        )
        # ``getMessage()`` applies %-formatting with ``record.args``;
        # application code is expected to use ``logger.info("template %s", arg)``
        # so the formatter gets a stable template plus the live values.
        message = record.getMessage()
        # ``formatException`` returns the formatted traceback string or
        # ``None`` when no exception is in flight. The ternary keeps
        # the JSON value as ``null`` in the no-exception case so log
        # shippers can rely on the key always being present.
        exc_info: str | None
        if record.exc_info:
            exc_info = self.formatException(record.exc_info)
        else:
            exc_info = None
        payload: dict[str, Any] = {
            "ts": ts,
            "level": record.levelname,
            "logger": record.name,
            "msg": message,
            "module": record.module,
            "line": record.lineno,
            "exc_info": exc_info,
        }
        # ``ensure_ascii=False`` keeps non-ASCII (e.g. Brazilian
        # Portuguese asset class names in route logs) as-is so the
        # downstream tool can choose its own encoding policy.
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str, fmt: str) -> None:
    """Install the requested formatter on the ``omaha`` loggers.

    The function is idempotent: it can be called from ``main.py`` at
    module load (production) and from individual tests (which need a
    known formatter to assert JSON shape). ``disable_existing_loggers``
    stays ``False`` so test fixtures that set up their own handlers
    keep working.
    """
    formatter = "json" if fmt == "json" else "text"
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": "omaha.logging_config.JsonFormatter"},
            "text": {
                # Human-readable for local dev. The format string
                # follows the same key order as the JSON formatter
                # (ts, level, logger, msg) so an operator tailing dev
                # logs has a consistent mental model.
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": formatter,
            },
        },
        "loggers": {
            "omaha": {
                "level": level,
                "handlers": ["stdout"],
                # Don't propagate to root — root has uvicorn's handler
                # in production and pytest's capture handler in tests.
                # Either way we own the omaha.* logging surface.
                "propagate": False,
            },
            "omaha.access": {
                "level": level,
                "handlers": ["stdout"],
                "propagate": False,
            },
        },
        "root": {"level": level, "handlers": ["stdout"]},
    }
    logging.config.dictConfig(config)


__all__ = ["JsonFormatter", "configure_logging"]
