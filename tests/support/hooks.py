"""Shared pytest hooks for Omaha test harnesses.

Provides the ``pytest_runtest_makereport`` hook implementation used by
e2e, BDD, and visual suites to store the call-phase report on each
test item for trace-artifact decisions.
"""

from __future__ import annotations

from typing import Any


def remember_call_report(item: Any, report: Any) -> None:
    """Store the call-phase report on the item for trace artifact decisions."""
    if report.when == "call":
        item._omaha_call_report = report


def make_report_hook():
    """Return a ``pytest_runtest_makereport`` hookimpl wrapper.

    Importing pytest inside the function body avoids collection-time
    side effects when this module is imported early.
    """
    import pytest  # noqa: E401  (import inside function body by design)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
        outcome = yield
        remember_call_report(item, outcome.get_result())

    return pytest_runtest_makereport
