"""Shared test-server lifecycle manager for Omaha test harnesses."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from tests.support.browser import (
    compose_server_env,
    port_is_free,
    read_log_tail,
    shutdown_uvicorn,
    uvicorn_log_file,
    wait_for_port,
)
from tests.support.constants import REPO_ROOT, TEST_ADMIN_PASSWORD, TEST_SECRET_KEY


def _server_event(log_handle, *, run_id: str, lane: str, phase: str, **details: object) -> None:
    """Write flushed run/lane server lifecycle evidence to owned log."""
    line = "T29_SERVER_EVENT " + json.dumps(
        {
            "run_id": run_id,
            "lane": lane,
            "phase": phase,
            "recorded_at": time.time(),
            **details,
        }
    )
    payload = line + "\n"
    if "b" in getattr(log_handle, "mode", "b"):
        payload = payload.encode()
    log_handle.write(payload)
    log_handle.flush()
    if run_id != "unscoped":
        print(f"\n{line}", flush=True)


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
    run_id = os.environ.get("T29_RUN_ID", "unscoped")
    lane = os.environ.get("T29_DB_RECEIPT_LANE", label)
    parent_pid = os.getpid()
    parent_pgid = os.getpgrp()
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
        # Stay in lane-owned process group. Runner terminates lane group on
        # deadline/fail-fast; a detached server would survive as orphan.
        start_new_session=False,
    )
    child_pid = proc.pid
    try:
        pgid = os.getpgid(child_pid) if proc.poll() is None else None
    except OSError as exc:
        pgid = None
        _server_event(
            log_handle,
            run_id=run_id,
            lane=lane,
            phase="launch-pgid-error",
            parent_pid=parent_pid,
            parent_pgid=parent_pgid,
            child_pid=child_pid,
            pgid=None,
            error=f"{exc.__class__.__name__}: {exc}",
        )
    _server_event(
        log_handle,
        run_id=run_id,
        lane=lane,
        phase="launch",
        parent_pid=parent_pid,
        parent_pgid=parent_pgid,
        child_pid=child_pid,
        pgid=pgid,
        host="127.0.0.1",
        port=port,
        log=str(log_path),
    )

    try:
        wait_for_port(
            "127.0.0.1",
            port,
            timeout=30.0,
            process=proc,
            log_path=log_path,
            run_id=run_id,
            lane=lane,
        )
        _server_event(
            log_handle,
            run_id=run_id,
            lane=lane,
            phase="ready",
            parent_pid=parent_pid,
            child_pid=child_pid,
            pgid=pgid,
            host="127.0.0.1",
            port=port,
        )
    except Exception as exc:
        _server_event(
            log_handle,
            run_id=run_id,
            lane=lane,
            phase="startup-failed",
            parent_pid=parent_pid,
            child_pid=child_pid,
            pgid=pgid,
            return_code=proc.poll(),
            error=f"{exc.__class__.__name__}: {exc}",
        )
        shutdown_uvicorn(
            proc,
            label=label,
            host="127.0.0.1",
            port=port,
            log_handle=log_handle,
            log_path=log_path,
            pgid=pgid,
            parent_pgid=parent_pgid,
        )
        with log_path.open("a", encoding="utf-8") as event_log:
            _server_event(
                event_log,
                run_id=run_id,
                lane=lane,
                phase="teardown-complete",
                parent_pid=parent_pid,
                parent_pgid=parent_pgid,
                child_pid=child_pid,
                pgid=pgid,
                return_code=proc.poll(),
                port_free=port_is_free("127.0.0.1", port),
            )
        raise RuntimeError(
            f"uvicorn did not start ({exc}). output:\n{read_log_tail(log_path)}"
        ) from None

    base_url = f"http://127.0.0.1:{port}"
    try:
        yield base_url
    finally:
        _server_event(
            log_handle,
            run_id=run_id,
            lane=lane,
            phase="teardown-start",
            parent_pid=parent_pid,
            child_pid=child_pid,
            pgid=pgid,
            return_code=proc.poll(),
        )
        shutdown_uvicorn(
            proc,
            label=label,
            host="127.0.0.1",
            port=port,
            log_handle=log_handle,
            log_path=log_path,
            pgid=pgid,
            parent_pgid=parent_pgid,
        )
        with log_path.open("a", encoding="utf-8") as event_log:
            _server_event(
                event_log,
                run_id=run_id,
                lane=lane,
                phase="teardown-complete",
                parent_pid=parent_pid,
                parent_pgid=parent_pgid,
                child_pid=child_pid,
                pgid=pgid,
                return_code=proc.poll(),
                port_free=port_is_free("127.0.0.1", port),
            )
