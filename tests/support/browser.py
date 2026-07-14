"""Common browser and uvicorn harness primitives."""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def log_harness(message: str) -> None:
    print(f"[omaha-test-harness] {message}", file=sys.stderr, flush=True)


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    """Block until ``host:port`` accepts a TCP connection or raise."""
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((host, port))
                return
            except OSError as exc:
                last_err = exc
                time.sleep(0.1)
    raise RuntimeError(
        f"server on {host}:{port} did not become ready in {timeout}s (last error: {last_err})"
    )


def uvicorn_log_file(repo_root: Path, label: str):
    log_dir = repo_root / "tmp" / "uvicorn-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-") or "uvicorn"
    return NamedTemporaryFile(prefix=f"{slug}-", suffix=".log", dir=log_dir, delete=False)


def read_log_tail(log_path: Path, max_bytes: int = 4000) -> str:
    if not log_path.exists():
        return "<missing log file>"
    return log_path.read_bytes()[-max_bytes:].decode(errors="replace")


def shutdown_uvicorn(
    proc: subprocess.Popen[bytes],
    *,
    label: str,
    host: str,
    port: int,
    log_handle: Any | None = None,
    log_path: Path | None = None,
) -> None:
    proc.terminate()
    with suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=3)
    if proc.poll() is None:
        log_harness(f"{label}: terminate timeout on {host}:{port}; sending kill()")
        proc.kill()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            log_harness(f"{label}: process still alive after kill() on {host}:{port}")
    if not port_is_free(host, port):
        log_harness(f"{label}: port {port} still bound after teardown")
    if log_handle is not None:
        log_handle.close()
    if log_path is not None and proc.returncode not in (0, -15):
        log_harness(f"{label}: uvicorn log tail\n{read_log_tail(log_path)}")


def resolve_chromium() -> str:
    """Resolve Chromium using existing E2E override/cache/system order."""
    candidates: list[Path] = []
    if env := os.environ.get("E2E_CHROMIUM_PATH"):
        candidates.append(Path(env))
    cache = Path.home() / ".cache" / "ms-playwright"
    if cache.exists():
        candidates.extend(sorted(cache.glob("chromium-*/chrome-linux*/chrome"), reverse=True))
        candidates.extend(
            sorted(cache.glob("chromium-*/chrome-linux*/headless_shell"), reverse=True)
        )
    candidates.append(Path("/usr/bin/chromium-browser"))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise RuntimeError(
        "chromium binary not found. Tried: "
        + ", ".join(
            str(candidate) for candidate in candidates if not str(candidate).startswith("~")
        )
        + ". Run `uv run playwright install chromium --with-deps` "
        "or set E2E_CHROMIUM_PATH=/path/to/chrome."
    )


def launch_chromium(playwright: Any, executable: str):
    """Launch Chromium with harness-standard headless arguments."""
    try:
        return playwright.chromium.launch(
            headless=True,
            executable_path=executable,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to launch chromium at {executable}: {exc}. "
            "If this looks like 'shared library not found', run "
            "`uv run playwright install chromium --with-deps` to install "
            "system dependencies (libnss3, libxkbcommon0, libgbm1, etc.)."
        ) from exc


def compose_server_env(
    db_path: Path,
    *,
    admin_password: str,
    secret_key: str,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    return {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "ADMIN_PASSWORD": admin_password,
        "SECRET_KEY": secret_key,
        **(extra or {}),
    }


def run_setup_command(args: list[str], *, repo_root: Path, env: dict[str, str]) -> None:
    subprocess.run(args, cwd=repo_root, env=env, check=True)


# ---------------------------------------------------------------------------
# HarnessPage — goto retry guard for same-URL navigation
# ---------------------------------------------------------------------------

_GOTO_INTERRUPT_RE = re.compile(
    r'Navigation to "(?P<target>[^"]+)" is interrupted by another navigation to "(?P<other>[^"]+)"'
)


class HarnessPage:
    """Thin Page proxy with retry-on-same-URL navigation guard.

    Some Omaha test workflows click a UI action that triggers
    ``window.location.reload()`` and then immediately call
    ``page.goto()`` to the same dashboard URL. Under slower harness
    paths (notably trace/debug runs), Playwright can surface this as
    a same-URL navigation interruption even though the in-flight
    reload already heads to the requested page. Treat that narrow
    case as wait-for-completion instead of hard failure.
    """

    def __init__(self, page: Any):
        self._page = page

    def __getattr__(self, name: str) -> Any:
        return getattr(self._page, name)

    def goto(self, url: str, *args: Any, **kwargs: Any):
        try:
            return self._page.goto(url, *args, **kwargs)
        except Exception as exc:
            from playwright.sync_api import Error as PlaywrightError

            if not isinstance(exc, PlaywrightError):
                raise
            match = _GOTO_INTERRUPT_RE.search(str(exc))
            if match is None or match.group("target") != url or match.group("other") != url:
                raise
            timeout = int(kwargs.get("timeout", 30_000))
            wait_until = kwargs.get("wait_until", "load")
            log_harness(f"same-URL goto interrupted by in-flight reload; waiting instead: {url}")
            self._page.wait_for_url(url, wait_until=wait_until, timeout=timeout)
            return None
