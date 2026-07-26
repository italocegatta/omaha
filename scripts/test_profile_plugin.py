"""Emit lossless per-node timings for the T29 inventory."""

from __future__ import annotations

import os

import pytest

_TIMING_FILE = None


@pytest.hookimpl
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when == "call" or (report.when == "setup" and report.skipped):
        path = os.environ.get("T29_PROFILE_PATH")
        if path:
            global _TIMING_FILE
            if _TIMING_FILE is None:
                _TIMING_FILE = open(path, "a", encoding="utf-8")  # noqa: SIM115 - plugin retains handle until session finish
            _TIMING_FILE.write(
                f"T29_PROFILE {report.duration:.9f}s {report.when} "
                f"{report.outcome.upper()} {report.nodeid}\n"
            )
            _TIMING_FILE.flush()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    del session, exitstatus
    if _TIMING_FILE is not None:
        _TIMING_FILE.close()
