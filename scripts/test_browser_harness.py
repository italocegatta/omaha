"""Focused tests for uvicorn process teardown diagnostics."""

from __future__ import annotations

import socket
from pathlib import Path

from tests.support.browser import port_is_free, shutdown_uvicorn


class _FakeProcess:
    def __init__(self, returncode: int | None, *, terminate_error: Exception | None = None):
        self.returncode = returncode
        self.terminate_error = terminate_error
        self.terminate_calls = 0

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminate_calls += 1
        if self.terminate_error is not None:
            raise self.terminate_error
        self.returncode = -15

    def wait(self, timeout: float) -> int:
        return self.returncode  # type: ignore[return-value]

    def kill(self) -> None:
        self.returncode = -9


def test_shutdown_uvicorn_terminates_alive_process() -> None:
    proc = _FakeProcess(None)

    shutdown_uvicorn(proc, label="alive", host="127.0.0.1", port=0)

    assert proc.terminate_calls == 1
    assert proc.returncode == -15


def test_shutdown_uvicorn_handles_already_exited_process(capsys) -> None:
    proc = _FakeProcess(1)

    shutdown_uvicorn(proc, label="dead", host="127.0.0.1", port=0)

    output = capsys.readouterr().err
    assert "server died" in output
    assert "returncode=1" in output


def test_shutdown_uvicorn_handles_missing_pid(capsys) -> None:
    proc = _FakeProcess(None, terminate_error=ProcessLookupError())

    shutdown_uvicorn(proc, label="missing", host="127.0.0.1", port=0)

    assert proc.terminate_calls == 1
    assert "server died" in capsys.readouterr().err


def test_shutdown_uvicorn_reports_bounded_log_tail(tmp_path: Path, capsys) -> None:
    log_path = tmp_path / "uvicorn.log"
    log_path.write_bytes(b"prefix\n" + b"x" * 5000)
    proc = _FakeProcess(3)

    shutdown_uvicorn(
        proc,
        label="diagnostic",
        host="127.0.0.1",
        port=0,
        log_path=log_path,
    )

    output = capsys.readouterr().err
    assert "returncode=3" in output
    assert "log tail (max 4000 bytes)" in output
    assert "x" * 4000 in output
    assert "x" * 4001 not in output


def test_shutdown_uvicorn_checks_port_release() -> None:
    proc = _FakeProcess(-15)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    shutdown_uvicorn(proc, label="port", host="127.0.0.1", port=port)

    assert port_is_free("127.0.0.1", port)
