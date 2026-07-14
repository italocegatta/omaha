"""Shared test-server lifecycle manager for Omaha test harnesses."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from tests.support.browser import (
    compose_server_env,
    read_log_tail,
    shutdown_uvicorn,
    uvicorn_log_file,
    wait_for_port,
)
from tests.support.constants import REPO_ROOT, TEST_ADMIN_PASSWORD, TEST_SECRET_KEY


@contextmanager
def run_test_server(
    db_path: Path,
    port: int,
    *,
    label: str,
    secret_key: str = TEST_SECRET_KEY,
    admin_password: str = TEST_ADMIN_PASSWORD,
    extra_env: dict[str, str] | None = None,
) -> Iterator[str]:
    """Start uvicorn, wait for port, yield base URL, shutdown.

    Caller owns DB file deletion before calling.  Context manager
    guarantees uvicorn shutdown on exit (normal or exception).

    Returns base URL string (e.g. ``http://127.0.0.1:8765``).
    """
    env = compose_server_env(
        db_path,
        admin_password=admin_password,
        secret_key=secret_key,
        extra={"OMAHA_SKIP_STARTUP": "", **(extra_env or {})},
    )

    log_handle = uvicorn_log_file(REPO_ROOT, label)
    log_path = Path(log_handle.name)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "omaha.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )

    try:
        wait_for_port("127.0.0.1", port, timeout=30.0)
    except Exception:
        proc.terminate()
        log_handle.close()
        raise RuntimeError(
            f"uvicorn did not start. output:\n{read_log_tail(log_path)}"
        ) from None

    base_url = f"http://127.0.0.1:{port}"
    try:
        yield base_url
    finally:
        shutdown_uvicorn(
            proc,
            label=label,
            host="127.0.0.1",
            port=port,
            log_handle=log_handle,
            log_path=log_path,
        )
