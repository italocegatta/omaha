"""Emit stable pytest node IDs for T29 collection-only preflight."""

from __future__ import annotations

import pytest


def pytest_collection_finish(session: pytest.Session) -> None:
    for item in session.items:
        print(f"T29_NODE {item.nodeid}")
