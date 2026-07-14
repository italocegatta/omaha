"""Shared test constants — single source of truth for harness-wide values.

Per-suite constants (port, DB path, secret suffix) stay in their conftest
files — only the truly shared values live here.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
TEST_ADMIN_PASSWORD: str = "test-password"
TEST_SECRET_KEY: str = "test-secret-do-not-use"
