"""Bounded, best-effort telemetry for one MyProfit synchronization job."""

from __future__ import annotations

import contextlib
import contextvars
import logging
import math
import re
import time
from collections.abc import Iterator
from typing import Any
from uuid import UUID

from omaha.models import MyProfitSyncJob

TELEMETRY_EVENT = "myprofit_telemetry"
TELEMETRY_VERSION = "1"
MAX_DURATION_MS = 86_400_000
UUID_SHAPE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
EVENTS = frozenset({"transition", "stage", "terminal", "ui_limit"})
DOMAINS = frozenset({"job", "connector", "browser", "preview_handoff", "polling_ui", "concurrency"})
STATUSES = frozenset({"queued", "running", "succeeded", "failed", "expired", "rejected"})
STAGES = frozenset(MyProfitSyncJob.SAFE_ERROR_STAGES) | frozenset(
    {"queue", "poll", "ui", "handoff", "terminal", "concurrency", "unknown"}
)
CODES = frozenset(MyProfitSyncJob.SAFE_ERROR_CODES) | frozenset(
    {"started", "transitioned", "local_limit_reached", "sync_in_progress", "success", "unknown"}
)

_ACTIVE_RECORDER: contextvars.ContextVar[TelemetryRecorder | None] = contextvars.ContextVar(
    "myprofit_telemetry_recorder", default=None
)


def _uuid_job_id(value: object) -> str | None:
    if not isinstance(value, str) or not UUID_SHAPE.fullmatch(value):
        return None
    try:
        UUID(value)
    except (ValueError, AttributeError):
        return None
    return value.lower()


def _allow(value: object, allowed: frozenset[str], fallback: str) -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def _duration_ms(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    if not math.isfinite(number) or number < 0:
        return 0
    return min(MAX_DURATION_MS, int(number))


def elapsed_ms(started: float) -> int:
    """Return bounded monotonic elapsed milliseconds."""
    return _duration_ms((time.perf_counter() - started) * 1000)


class TelemetryRecorder:
    """Emit only fixed-shape events for one UUID-shaped job."""

    def __init__(self, job_id: str, *, started_at: float | None = None) -> None:
        self.job_id = _uuid_job_id(job_id)
        self.started_at = started_at if started_at is not None else time.perf_counter()
        self._logger = logging.getLogger("omaha")

    def _emit(
        self,
        event: object,
        *,
        domain: object,
        status: object,
        stage: object,
        code: object,
        duration_ms: object = None,
        total_duration_ms: object = None,
    ) -> None:
        if self.job_id is None:
            return
        try:
            event_name = _allow(event, EVENTS, "stage")
            safe_domain = _allow(domain, DOMAINS, "job")
            safe_status = _allow(status, STATUSES, "failed")
            safe_stage = _allow(stage, STAGES, "unknown")
            safe_code = _allow(code, CODES, "unknown")
            duration = "na" if duration_ms is None else str(_duration_ms(duration_ms))
            total = "na" if total_duration_ms is None else str(_duration_ms(total_duration_ms))
            message = (
                f"{TELEMETRY_EVENT} version={TELEMETRY_VERSION} event={event_name} "
                f"job_id={self.job_id} domain={safe_domain} status={safe_status} "
                f"stage={safe_stage} code={safe_code} duration_ms={duration} "
                f"total_duration_ms={total}"
            )
            self._logger.info("%s", message)
        except Exception:
            # Observability must never alter synchronization behavior.
            return

    def transition(self, *, domain: object, status: object, stage: object, code: object) -> None:
        self._emit("transition", domain=domain, status=status, stage=stage, code=code)

    def stage(
        self,
        *,
        domain: object,
        status: object,
        stage: object,
        code: object,
        duration_ms: object,
    ) -> None:
        self._emit(
            "stage",
            domain=domain,
            status=status,
            stage=stage,
            code=code,
            duration_ms=duration_ms,
        )

    def terminal(
        self,
        *,
        status: object,
        code: object,
        total_duration_ms: object,
    ) -> None:
        self._emit(
            "terminal",
            domain="job",
            status=status,
            stage="terminal",
            code=code,
            total_duration_ms=total_duration_ms,
        )

    def ui_limit(self, *, status: object = "running") -> None:
        self._emit(
            "ui_limit",
            domain="polling_ui",
            status=status,
            stage="ui",
            code="local_limit_reached",
        )


def _current_or_new(job_id: str) -> TelemetryRecorder:
    current = _ACTIVE_RECORDER.get()
    if current is not None and current.job_id == _uuid_job_id(job_id):
        return current
    return TelemetryRecorder(job_id)


@contextlib.contextmanager
def telemetry_context(
    job_id: str, *, started_at: float | None = None
) -> Iterator[TelemetryRecorder]:
    """Make recorder active across service/connector boundaries."""
    recorder = TelemetryRecorder(job_id, started_at=started_at)
    if recorder.job_id is None:
        yield recorder
        return
    token = _ACTIVE_RECORDER.set(recorder)
    try:
        yield recorder
    finally:
        _ACTIVE_RECORDER.reset(token)


def current_recorder() -> TelemetryRecorder | None:
    return _ACTIVE_RECORDER.get()


def _failure_metadata(failure: BaseException | None, name: str, fallback: str) -> object:
    """Read exception metadata without allowing hostile accessors to escape."""
    if failure is None:
        return fallback
    try:
        return getattr(failure, name)
    except BaseException:
        return fallback


def emit_transition(job_id: str, *, status: str, stage: str, code: str) -> None:
    _current_or_new(job_id).transition(domain="job", status=status, stage=stage, code=code)


def emit_stage(
    job_id: str,
    *,
    domain: str,
    status: str,
    stage: str,
    code: str,
    duration_ms: object,
) -> None:
    _current_or_new(job_id).stage(
        domain=domain,
        status=status,
        stage=stage,
        code=code,
        duration_ms=duration_ms,
    )


def emit_terminal(job_id: str, *, status: str, code: str, total_duration_ms: object) -> None:
    _current_or_new(job_id).terminal(status=status, code=code, total_duration_ms=total_duration_ms)


def emit_ui_limit(job_id: str, *, status: str = "running") -> None:
    _current_or_new(job_id).ui_limit(status=status)


@contextlib.contextmanager
def stage_span(job_id: str, *, domain: str, stage: str) -> Iterator[None]:
    """Record completion/failure of named connector stage without raw errors."""
    recorder = current_recorder()
    started = time.perf_counter()
    failure: Any = None
    try:
        yield
    except BaseException as exc:
        failure = exc
        raise
    finally:
        try:
            if recorder is not None and recorder.job_id == _uuid_job_id(job_id):
                safe_stage = _failure_metadata(failure, "stage", stage)
                safe_code = _failure_metadata(failure, "code", "unknown")
                recorder.stage(
                    domain=domain,
                    status="failed" if failure is not None else "succeeded",
                    stage=safe_stage,
                    code=safe_code,
                    duration_ms=elapsed_ms(started),
                )
        except BaseException:
            # A telemetry failure must never replace the synchronization error.
            return


__all__ = [
    "CODES",
    "DOMAINS",
    "EVENTS",
    "MAX_DURATION_MS",
    "STAGES",
    "STATUSES",
    "TelemetryRecorder",
    "current_recorder",
    "elapsed_ms",
    "emit_stage",
    "emit_terminal",
    "emit_transition",
    "emit_ui_limit",
    "stage_span",
    "telemetry_context",
]
