"""Focused internal contracts for F59 synchronization jobs.

These tests stop at the application-owned job, file, parser, and preview
boundaries. They do not construct or invoke any external service adapter.
"""

from __future__ import annotations

import json
import logging
import math
import os
import platform
import statistics
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import BackgroundTasks
from fastapi.requests import Request
from fastapi.testclient import TestClient
from sqlalchemy import inspect

CSV = (
    "Ticker,Nome,Quantidade,Preço médio,Preço atual,Total investido,Total atual\n"
    "F59UNMATCHED,F59UNMATCHED,1,10,12,10,12\n"
).encode()


def _t36_percentile(values: list[float], percentile: float) -> float:
    """Calculate an inclusive, linearly interpolated percentile in ms."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    rank = (len(ordered) - 1) * percentile / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _t36_metrics(values: list[float]) -> dict[str, float]:
    """Return T36 distribution metrics using the documented percentile method."""
    p50 = _t36_percentile(values, 50)
    deviations = [abs(value - p50) for value in values]
    p25 = _t36_percentile(values, 25)
    p75 = _t36_percentile(values, 75)
    return {
        "mean": statistics.mean(values),
        "p50": p50,
        "p95": _t36_percentile(values, 95),
        "p99": _t36_percentile(values, 99),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values),
        "iqr": p75 - p25,
        "mad": statistics.median(deviations),
    }


def _now() -> datetime:
    return datetime.now(tz=UTC).replace(tzinfo=None)


def _profile(name: str = "Italo"):
    from omaha.db import SessionLocal
    from omaha.models import Profile

    with SessionLocal() as db:
        return db.query(Profile).filter(Profile.name == name).one()


def _request(app) -> Request:
    return Request(
        {
            "type": "http",
            "app": app,
            "method": "POST",
            "path": "/api/myprofit/sync",
            "raw_path": b"/api/myprofit/sync",
            "query_string": b"",
            "headers": [],
            "client": ("test", 0),
            "server": ("test", 80),
            "scheme": "http",
        }
    )


def _new_job(profile_id: int, *, status: str = "running", expires_at: datetime | None = None):
    from omaha.db import SessionLocal
    from omaha.models import MyProfitSyncJob

    with SessionLocal() as db:
        job = MyProfitSyncJob(
            job_id=str(uuid.uuid4()),
            profile_id=profile_id,
            status=status,
            expires_at=expires_at or _now() + timedelta(hours=1),
        )
        db.add(job)
        db.commit()
        return job.job_id


@pytest.fixture(autouse=True)
def clean_sync_rows() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import ImportPreview, MyProfitSyncJob

    service = app.state.myprofit_sync_service
    service.shutdown()
    with service._lock:
        service._reservations.clear()
        service._owned_dirs.clear()
        service._terminal_observed.clear()
    with SessionLocal() as db:
        db.query(MyProfitSyncJob).delete()
        db.query(ImportPreview).delete()
        db.commit()
    yield
    service.shutdown()
    with service._lock:
        service._reservations.clear()
        service._owned_dirs.clear()
        service._terminal_observed.clear()


def _login(client: TestClient, username: str = "Italo") -> None:
    response = client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_job_model_and_migration_round_trip(tmp_path: Path) -> None:
    """Migration creates only F59 table, downgrade removes only that table."""
    db_path = tmp_path / "migration.sqlite"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "SECRET_KEY": "test-secret-do-not-use",
        "ADMIN_PASSWORD": "test-password",
        "OMAHA_SKIP_STARTUP": "1",
    }
    repo_root = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    import sqlite3

    connection = sqlite3.connect(db_path)
    try:
        assert connection.execute(
            "select name from sqlite_master where type='table' and name='myprofit_sync_jobs'"
        ).fetchone()
        columns = {row[1] for row in connection.execute("pragma table_info(myprofit_sync_jobs)")}
        assert {"job_id", "profile_id", "status", "preview_id", "expires_at"} <= columns
        assert connection.execute(
            "select name from sqlite_master where type='table' and name='assets'"
        ).fetchone()
    finally:
        connection.close()

    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0019_asset_target_pct_precision"],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    connection = sqlite3.connect(db_path)
    try:
        assert not connection.execute(
            "select name from sqlite_master where type='table' and name='myprofit_sync_jobs'"
        ).fetchone()
        assert connection.execute(
            "select name from sqlite_master where type='table' and name='assets'"
        ).fetchone()
    finally:
        connection.close()


def test_status_serializer_is_sanitized() -> None:
    from omaha.models import MyProfitSyncJob

    job = MyProfitSyncJob(
        job_id="00000000-0000-0000-0000-000000000002",
        profile_id=1,
        status="failed",
        error_stage="login",
        error_code="failed",
        work_dir="/secret/absolute/path",
        work_file="credentials.csv",
        expires_at=_now(),
    )
    payload = job.to_status_dict(error_message="Não foi possível entrar no MyProfit.")
    rendered = json.dumps(payload, ensure_ascii=False)
    assert "/secret/absolute/path" not in rendered
    assert "credentials.csv" not in rendered
    assert payload["error"] == {
        "stage": "login",
        "code": "failed",
        "message": "Não foi possível entrar no MyProfit.",
    }


def test_start_returns_202_without_running_scheduled_task() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.routes.imports import start_myprofit_sync

    profile = _profile()
    tasks = BackgroundTasks()
    with SessionLocal() as db:
        response = start_myprofit_sync(tasks, db, _request(app), profile=profile)
        assert response.status_code == 202
        body = json.loads(response.body)
        assert body["status"] == "queued"
        assert body["job_id"] == tasks.tasks[0].args[0]
    assert len(tasks.tasks) == 1


def test_duplicate_profile_start_is_rejected() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.routes.imports import SyncInProgress

    service = app.state.myprofit_sync_service
    profile = _profile()
    with SessionLocal() as db:
        first = service.start(db, profile, BackgroundTasks())
        with pytest.raises(SyncInProgress) as error:
            service.start(db, profile, BackgroundTasks())
    assert error.value.job_id == first.job_id


def test_profiles_run_independently() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app

    service = app.state.myprofit_sync_service
    with SessionLocal() as db:
        italo = db.get(type(_profile()), _profile("Italo").id)
        ana = db.get(type(_profile()), _profile("Ana").id)
        italo_job = service.start(db, italo, BackgroundTasks())
        ana_job = service.start(db, ana, BackgroundTasks())
    assert italo_job.profile_id != ana_job.profile_id
    assert service._reservations == {italo.id: italo_job.job_id, ana.id: ana_job.job_id}


def test_shutdown_settles_owned_jobs_and_releases_reservations(tmp_path: Path) -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import MyProfitSyncJob

    service = app.state.myprofit_sync_service
    profile = _profile()
    job_id = _new_job(profile.id, status="running")
    work_dir = tmp_path / "owned-shutdown-job"
    work_dir.mkdir()
    with SessionLocal() as db:
        job = db.get(MyProfitSyncJob, job_id)
        job.work_dir = str(work_dir)
        job.work_file = str(work_dir / "positions.csv")
        db.commit()
    with service._lock:
        service._reservations[profile.id] = job_id
        service._owned_dirs[job_id] = work_dir

    service.shutdown()

    with SessionLocal() as db:
        settled = db.get(MyProfitSyncJob, job_id)
        assert settled.status == "expired"
        assert settled.preview_id is None
        assert settled.retention_until is not None
        assert settled.work_dir is None
    assert not work_dir.exists()
    assert profile.id not in service._reservations

    with SessionLocal() as db:
        replacement = service.start(db, profile, BackgroundTasks())
    assert replacement.job_id != job_id


def test_worker_cap_is_two() -> None:
    from omaha.main import app

    service = app.state.myprofit_sync_service
    first = service._worker_slots.acquire(blocking=False)
    second = service._worker_slots.acquire(blocking=False)
    third = service._worker_slots.acquire(blocking=False)
    try:
        assert first and second and not third
        assert service._max_workers == 2
    finally:
        if first:
            service._worker_slots.release()
        if second:
            service._worker_slots.release()


def test_poll_states_and_foreign_job_is_404(client: TestClient) -> None:
    _login(client, "Italo")
    italo_job = _new_job(1, status="queued")
    running_job = _new_job(1, status="running")
    ana_job = _new_job(2, status="failed")
    assert client.get(f"/api/myprofit/sync/{italo_job}").json()["preview"] is None
    assert client.get(f"/api/myprofit/sync/{running_job}").json()["preview"] is None
    assert client.get(f"/api/myprofit/sync/{ana_job}").status_code == 404


def test_internal_csv_handoff_reuses_preview_shape_and_does_not_mutate() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import Asset, DbMutation, MyProfitSyncJob, Position, Profile

    service = app.state.myprofit_sync_service
    profile = _profile()
    job_id = _new_job(profile.id)
    with SessionLocal() as db:
        job = db.get(MyProfitSyncJob, job_id)
        owner = db.get(Profile, profile.id)
        before = (db.query(Asset).count(), db.query(Position).count(), db.query(DbMutation).count())
        service._process_downloaded_csv(db, job, owner, filename="../../positions.csv", content=CSV)
        db.refresh(job)
        payload = service.status_for_profile(db, owner, job_id)
        after = (db.query(Asset).count(), db.query(Position).count(), db.query(DbMutation).count())
        assert payload is not None
        assert payload["status"] == "succeeded"
        assert set(payload["preview"]) == {
            "preview_id",
            "auto_matched",
            "unmatched",
            "asset_classes",
            "triage",
        }
        assert payload["preview"]["unmatched"]
        assert before == after
        assert job.filename == "positions.csv"
        assert job.work_dir is not None
        assert Path(job.work_dir).exists()
        service._cleanup_owned_dir(job)
        job.work_dir = None
        job.work_file = None
        db.commit()


def test_invalid_csv_fails_before_preview_and_cleanup_is_owned(tmp_path: Path) -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import MyProfitSyncJob, Profile

    service = app.state.myprofit_sync_service
    service.temp_root = tmp_path
    profile = _profile()
    job_id = _new_job(profile.id)
    with SessionLocal() as db:
        job = db.get(MyProfitSyncJob, job_id)
        owner = db.get(Profile, profile.id)
        service._process_downloaded_csv(db, job, owner, filename="bad.csv", content=b"\xff\xfe")
        db.refresh(job)
        assert job.status == "failed"
        assert job.preview_id is None
        assert job.error_stage == "preview"
        owned_dir = Path(job.work_dir)
        assert owned_dir.parent == tmp_path
        assert owned_dir.exists()
        assert service._cleanup_owned_dir(job)
        assert not owned_dir.exists()
        job.work_dir = None
        job.work_file = None
        db.commit()


def test_expiry_cleans_preview_and_files(tmp_path: Path) -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import ImportPreview, MyProfitSyncJob

    service = app.state.myprofit_sync_service
    profile = _profile()
    work_dir = tmp_path / "owned-job"
    work_dir.mkdir()
    owned_file = work_dir / "positions.csv"
    owned_file.write_bytes(CSV)
    with SessionLocal() as db:
        preview = ImportPreview(profile_id=profile.id, raw_json="[]")
        db.add(preview)
        db.flush()
        job = MyProfitSyncJob(
            job_id="00000000-0000-0000-0000-000000000099",
            profile_id=profile.id,
            status="succeeded",
            preview_id=preview.id,
            work_dir=str(work_dir),
            work_file=str(owned_file),
            expires_at=_now() - timedelta(seconds=1),
        )
        db.add(job)
        db.commit()
        assert service.expire_myprofit_sync_job(job.job_id, db=db)
        db.refresh(job)
        assert job.status == "expired"
        assert job.preview_id is None
        assert job.work_dir is None
        assert db.get(ImportPreview, preview.id) is None
    assert not work_dir.exists()


def test_expired_jobs_are_retained_then_pruned_with_bound() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import ImportPreview, MyProfitSyncJob

    service = app.state.myprofit_sync_service
    profile = _profile()
    now = _now()
    old_id = _new_job(profile.id, status="expired")
    retained_id = _new_job(profile.id, status="expired")
    with SessionLocal() as db:
        old = db.get(MyProfitSyncJob, old_id)
        old.finished_at = now - timedelta(hours=2)
        old.retention_until = now - timedelta(hours=1)
        retained = db.get(MyProfitSyncJob, retained_id)
        retained.finished_at = now - timedelta(minutes=1)
        retained.retention_until = now + timedelta(minutes=1)
        unrelated_preview = ImportPreview(profile_id=profile.id, raw_json="[]")
        db.add(unrelated_preview)
        db.commit()
        unrelated_id = unrelated_preview.id

        assert service.prune_expired_jobs(db, profile_id=profile.id, now=now, limit=1) == 1
        assert db.get(MyProfitSyncJob, old_id) is None
        assert db.get(MyProfitSyncJob, retained_id) is not None
        assert db.get(ImportPreview, unrelated_id) is not None


def test_late_worker_cannot_publish_after_expiry(tmp_path: Path) -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import MyProfitSyncJob, Profile

    service = app.state.myprofit_sync_service
    service.temp_root = tmp_path
    profile = _profile()
    job_id = _new_job(profile.id, expires_at=_now() - timedelta(seconds=1))
    with SessionLocal() as db:
        job = db.get(MyProfitSyncJob, job_id)
        owner = db.get(Profile, profile.id)
        service._process_downloaded_csv(db, job, owner, filename="late.csv", content=CSV)
        db.refresh(job)
        assert job.status == "expired"
        assert job.preview_id is None


def test_late_connector_failure_keeps_expired_precedence() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import MyProfitSyncJob

    service = app.state.myprofit_sync_service
    profile = _profile()
    job_id = _new_job(profile.id, status="running", expires_at=_now() - timedelta(seconds=1))
    with SessionLocal() as db:
        job = db.get(MyProfitSyncJob, job_id)
        service._mark_failed(db, job, stage="download", code="failed")
        db.refresh(job)
        assert job.status == "expired"
        assert job.error_stage is None
        assert job.error_code is None
        assert job.retention_until is not None


def test_failed_sync_is_page_safe_error(client: TestClient) -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import MyProfitSyncJob
    from omaha.routes import pages

    _login(client)
    job_id = _new_job(1, status="failed")
    with SessionLocal() as db:
        job = db.get(MyProfitSyncJob, job_id)
        job.error_stage = "login"
        job.error_code = "raw-secret-must-not-escape"
        db.commit()
        request = _request(app)
        context = pages._common_context(
            request, db, db.get(type(_profile()), 1), db.get(type(_profile()), 1)
        )
        assert context["myprofit_sync_error"]["status"] == "failed"
        assert context["myprofit_sync_error"]["error"]["message"] == (
            "Não foi possível entrar no MyProfit."
        )
        assert "raw-secret" not in json.dumps(context["myprofit_sync_error"], ensure_ascii=False)
    assert client.get(f"/api/myprofit/sync/{job_id}").json()["preview"] is None


def test_error_stage_and_code_are_allowlisted() -> None:
    from omaha.models import MyProfitSyncJob

    job = MyProfitSyncJob(
        job_id="00000000-0000-0000-0000-000000000003",
        profile_id=1,
        status="failed",
        error_stage="https://secret.example/path",
        error_code="/tmp/credentials.csv",
        expires_at=_now(),
    )
    payload = job.to_status_dict(error_message="Não foi possível sincronizar com o MyProfit.")
    assert payload["error"] == {
        "stage": "connector",
        "code": "failed",
        "message": "Não foi possível sincronizar com o MyProfit.",
    }


def _telemetry_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records if record.name == "omaha"]


def test_telemetry_event_shape_and_sanitization(caplog: pytest.LogCaptureFixture) -> None:
    from omaha.myprofit.telemetry import CODES, DOMAINS, EVENTS, STAGES, STATUSES, telemetry_context

    job_id = "12345678-1234-4234-8234-123456789012"
    logger = logging.getLogger("omaha")
    logger.setLevel(logging.INFO)
    with telemetry_context(job_id) as recorder:
        recorder.transition(
            domain="https://secret.example/path",
            status="running",
            stage="/tmp/credentials.csv",
            code="raw-exception-password",
        )
        recorder.stage(
            domain="connector",
            status="succeeded",
            stage="download",
            code="success",
            duration_ms=float("nan"),
        )
        recorder.terminal(status="succeeded", code="success", total_duration_ms=-1)
        recorder.ui_limit()

    messages = _telemetry_messages(caplog)
    assert len(messages) == 4
    job_ids = set()
    for message in messages:
        fields = dict(token.split("=", 1) for token in message.split()[1:])
        assert fields["event"] in EVENTS
        assert fields["domain"] in DOMAINS
        assert fields["status"] in STATUSES
        assert fields["stage"] in STAGES
        assert fields["code"] in CODES
        assert fields["duration_ms"] == "na" or fields["duration_ms"].isdigit()
        assert fields["total_duration_ms"] == "na" or fields["total_duration_ms"].isdigit()
        job_ids.add(fields["job_id"])
    assert job_ids == {job_id}
    rendered = "\n".join(messages)
    for forbidden in ("secret.example", "credentials.csv", "raw-exception-password", "/tmp/"):
        assert forbidden not in rendered


def test_terminal_telemetry_emits_new_jobs_after_bounded_dedup_window(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from omaha.main import app
    from omaha.models import MyProfitSyncJob
    from omaha.routes.imports import TERMINAL_DEDUP_LIMIT

    service = app.state.myprofit_sync_service
    with service._lock:
        service._terminal_observed.clear()

    job_ids = [
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"t38-terminal-{index}"))
        for index in range(TERMINAL_DEDUP_LIMIT + 1)
    ]
    with caplog.at_level(logging.INFO, logger="omaha"):
        for job_id in job_ids:
            service._emit_terminal_once(
                MyProfitSyncJob(job_id=job_id, profile_id=1, status="succeeded"),
                status="succeeded",
                code="success",
            )
        service._emit_terminal_once(
            MyProfitSyncJob(job_id=job_ids[-1], profile_id=1, status="succeeded"),
            status="succeeded",
            code="success",
        )

    messages = [
        message
        for message in _telemetry_messages(caplog)
        if "event=terminal" in message and "code=success" in message
    ]
    assert len(messages) == TERMINAL_DEDUP_LIMIT + 1
    assert {f"job_id={job_id}" for job_id in job_ids} <= set(
        token for message in messages for token in message.split() if token.startswith("job_id=")
    )
    with service._lock:
        assert len(service._terminal_observed) == TERMINAL_DEDUP_LIMIT


def test_stage_telemetry_metadata_failure_preserves_original_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from omaha.myprofit.telemetry import stage_span, telemetry_context

    class ExplodingMetadataError(RuntimeError):
        @property
        def stage(self):
            raise RuntimeError("raw-stage-property")

        @property
        def code(self):
            raise RuntimeError("raw-code-property")

    job_id = "12345678-1234-4234-8234-123456789013"
    failure = ExplodingMetadataError("original-sync-failure")
    with (
        caplog.at_level(logging.INFO, logger="omaha"),
        telemetry_context(job_id),
        pytest.raises(ExplodingMetadataError) as caught,
        stage_span(job_id, domain="connector", stage="download"),
    ):
        raise failure

    assert caught.value is failure
    messages = [message for message in _telemetry_messages(caplog) if "event=stage" in message]
    assert len(messages) == 1
    assert "stage=download" in messages[0]
    assert "code=unknown" in messages[0]
    assert "raw-stage-property" not in messages[0]
    assert "raw-code-property" not in messages[0]
    assert "original-sync-failure" not in messages[0]


def test_ui_limit_signal_is_owned_and_non_mutating(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    from omaha.db import SessionLocal
    from omaha.models import MyProfitSyncJob

    _login(client)
    job_id = _new_job(1, status="running")
    foreign_job_id = _new_job(2, status="running")
    with SessionLocal() as db:
        before = (db.query(MyProfitSyncJob).count(), db.get(MyProfitSyncJob, job_id).status)

    logger = logging.getLogger("omaha")
    logger.setLevel(logging.INFO)
    response = client.post(f"/api/myprofit/sync/{job_id}/ui-limit")
    repeated = client.post(f"/api/myprofit/sync/{job_id}/ui-limit")
    foreign = client.post(f"/api/myprofit/sync/{foreign_job_id}/ui-limit")

    assert response.status_code == 204
    assert repeated.status_code == 204
    assert foreign.status_code == 404
    messages = [message for message in _telemetry_messages(caplog) if "event=ui_limit" in message]
    assert len(messages) == 1
    assert f"job_id={job_id}" in messages[0]
    assert "domain=polling_ui" in messages[0]
    assert "code=local_limit_reached" in messages[0]
    with SessionLocal() as db:
        after = (db.query(MyProfitSyncJob).count(), db.get(MyProfitSyncJob, job_id).status)
    assert after == before


def test_myprofit_telemetry_runbook() -> None:
    runbook = Path("docs/runbooks/myprofit-sync-telemetry.md").read_text(encoding="utf-8")
    required = (
        "four weeks",
        "eight weeks",
        "4–8 real runs per week",
        "domain/stage/code",
        "p50",
        "p95",
        "p99",
        "connector",
        "Polling/UI",
        "Browser",
        "Process",
        "Preview/handoff",
        "Concurrency",
        "insufficient-evidence",
        "50% of failed runs",
        "at least two runs",
    )
    for token in required:
        assert token in runbook
    for forbidden in ("password=", "https://", "positions.csv", "raw exception text"):
        assert forbidden not in runbook


def test_family_start_and_poll_are_blocked_before_lookup(client: TestClient) -> None:
    from omaha.db import SessionLocal
    from omaha.models import MyProfitSyncJob, Profile

    _login(client)
    with SessionLocal() as db:
        sentinel = db.query(Profile).filter(Profile.is_family_sentinel.is_(True)).one()
        foreign_job = _new_job(1, status="failed")
        before = db.query(MyProfitSyncJob).count()
    selected = client.post(f"/profiles/{sentinel.id}/select", follow_redirects=False)
    assert selected.status_code == 303
    assert client.post("/api/myprofit/sync").json() == {"reason": "household_read_only"}
    response = client.get(f"/api/myprofit/sync/{foreign_job}")
    assert response.status_code == 409
    with SessionLocal() as db:
        assert db.query(MyProfitSyncJob).count() == before


def test_family_page_has_no_sync_detail(client: TestClient) -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import Profile
    from omaha.routes import pages

    _login(client)
    with SessionLocal() as db:
        sentinel = db.query(Profile).filter(Profile.is_family_sentinel.is_(True)).one()
        request = _request(app)
        context = pages._common_context(request, db, db.get(Profile, sentinel.id), None)
        assert context["myprofit_sync_error"] is None
        assert context["myprofit_sync"] is None


def test_model_table_has_profile_status_index() -> None:
    from omaha.db import engine

    indexes = {index["name"] for index in inspect(engine).get_indexes("myprofit_sync_jobs")}
    assert "ix_myprofit_sync_jobs_profile_status" in indexes


def test_t36_sync_duration_measurement(tmp_path: Path) -> None:
    """Measure exactly 15 offline jobs and emit the T36 evidence receipt."""
    from omaha.config import settings
    from omaha.db import SessionLocal
    from omaha.models import Asset, DbMutation, Position, Profile
    from omaha.myprofit.connector import (
        MyProfitConnectorError,
        MyProfitConnectorTimeouts,
        MyProfitCsvDownload,
    )
    from omaha.routes.imports import PREVIEW_TTL, MyProfitSyncService

    schedule = [
        {"delay_s": 0.002},
        {"delay_s": 0.003},
        {"delay_s": 0.004},
        {"delay_s": 0.005},
        {"delay_s": 0.006, "failure": ("download", "timeout")},
        {"delay_s": 0.008},
        {"delay_s": 0.010},
        {"delay_s": 0.012},
        {"delay_s": 0.015},
        {"delay_s": 0.020, "failure": ("login", "failed")},
        {"delay_s": 0.030},
        {"delay_s": 0.050},
        {"delay_s": 0.002},
        {"delay_s": 0.004},
        {"delay_s": 0.006, "failure": ("browser", "browser_failed")},
    ]

    class FakeConnector:
        def __init__(self) -> None:
            self.calls = 0

        def download_positions_csv(self, profile: Profile) -> MyProfitCsvDownload:
            assert not profile.is_family_sentinel
            item = schedule[self.calls]
            self.calls += 1
            time.sleep(item["delay_s"])
            if item.get("failure") is not None:
                stage, code = item["failure"]
                raise MyProfitConnectorError(stage, code)
            return MyProfitCsvDownload(filename="t36-fake.csv", content=CSV)

    assert settings.PREVIEW_TTL_SECONDS == 3600
    assert int(PREVIEW_TTL.total_seconds() * 1000) == 3_600_000
    connector_timeouts = MyProfitConnectorTimeouts()
    fake = FakeConnector()
    temp_root = tmp_path / "t36-myprofit-sync"
    temp_root.mkdir()
    service = MyProfitSyncService(
        connector=fake,
        session_factory=SessionLocal,
        temp_root=temp_root,
        max_workers=1,
    )
    failure_schedule = {
        "failed|download|timeout": 1,
        "failed|login|failed": 1,
        "failed|browser|browser_failed": 1,
    }
    attempts: list[dict[str, object]] = []
    success_durations: list[float] = []

    with SessionLocal() as db:
        owner = db.query(Profile).filter(Profile.name == "Italo").one()
        before_counts = {
            "Asset": db.query(Asset).count(),
            "Position": db.query(Position).count(),
            "DbMutation": db.query(DbMutation).count(),
        }

    try:
        for index, expected in enumerate(schedule, start=1):
            started = time.perf_counter()
            with SessionLocal() as db:
                job = service.start(db, owner, BackgroundTasks())
                job_id = job.job_id
            service.run_myprofit_sync_job(job_id, owner.id)
            duration_ms = (time.perf_counter() - started) * 1000

            with SessionLocal() as db:
                job = db.get(type(job), job_id)
                assert job is not None
                assert job.started_at is not None
                assert job.finished_at is not None
                persisted_ms = (job.finished_at - job.started_at).total_seconds() * 1000
                assert math.isfinite(duration_ms) and duration_ms >= 0
                assert math.isfinite(persisted_ms) and persisted_ms >= 0
                assert job.work_dir is None and job.work_file is None
                assert not list(temp_root.iterdir())
                if expected.get("failure") is None:
                    assert job.status == "succeeded"
                    assert job.preview_id is not None
                    success_durations.append(duration_ms)
                    attempts.append(
                        {
                            "attempt": index,
                            "outcome": "success",
                            "duration_ms": round(duration_ms, 3),
                            "persisted_duration_ms": round(persisted_ms, 3),
                            "terminal_status": job.status,
                        }
                    )
                else:
                    stage, code = expected["failure"]
                    assert job.status == "failed"
                    assert (job.error_stage, job.error_code) == (stage, code)
                    attempts.append(
                        {
                            "attempt": index,
                            "outcome": "failure",
                            "duration_ms": round(duration_ms, 3),
                            "persisted_duration_ms": round(persisted_ms, 3),
                            "terminal_status": job.status,
                            "stage": job.error_stage,
                            "code": job.error_code,
                        }
                    )

        with SessionLocal() as db:
            after_counts = {
                "Asset": db.query(Asset).count(),
                "Position": db.query(Position).count(),
                "DbMutation": db.query(DbMutation).count(),
            }
    finally:
        service.shutdown()

    assert fake.calls == 15
    assert len(attempts) == 15
    assert len(success_durations) == 12
    assert all(attempt["terminal_status"] in {"succeeded", "failed"} for attempt in attempts)
    assert before_counts == after_counts
    assert service.active_worker_count == 0
    assert not service._reservations
    assert not service._owned_dirs
    assert not list(temp_root.iterdir())

    metrics = _t36_metrics(success_durations)
    candidate_ms = int(math.ceil((metrics["p99"] + max(2 * metrics["iqr"], 5_000)) / 5_000) * 5_000)
    assert candidate_ms <= 60_000
    assert candidate_ms < 3_600_000
    evidence = {
        "change_id": "t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao",
        "run_id": datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ"),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pytest": pytest.__version__,
        },
        "sample_size": len(attempts),
        "successes": len(success_durations),
        "failures": len(attempts) - len(success_durations),
        "failure_rate": (len(attempts) - len(success_durations)) / len(attempts),
        "percentile_method": "inclusive linear interpolation over successful samples",
        "attempts": attempts,
        "success_duration_ms": {key: round(value, 3) for key, value in metrics.items()},
        "failure_statuses": failure_schedule,
        "boundaries_ms": {
            "poll_delay": 500,
            "max_polls": 120,
            "poll_delay_x_max_polls": 60_000,
            "job_expiry": 3_600_000,
            "preview_ttl": 3_600_000,
            "terminal_retention": 3_600_000,
        },
        "playwright_stage_timeouts_ms": {
            "navigation": connector_timeouts.navigation_ms,
            "login_settle": connector_timeouts.login_settle_ms,
            "two_factor_probe": connector_timeouts.two_factor_probe_ms,
            "export_button": connector_timeouts.export_button_ms,
            "csv_option": connector_timeouts.csv_option_ms,
            "download": connector_timeouts.download_ms,
        },
        "playwright_harness_timeouts_ms": {
            "local_success_state": 3_000,
            "sync_terminal_state": 8_000,
            "sync_review_modal": 2_000,
            "import_review": 15_000,
            "import_review_table": 5_000,
        },
        "portfolio_counts_before": before_counts,
        "portfolio_counts_after": after_counts,
        "candidate_timeout_ms": candidate_ms,
        "decision": "covered",
        "recommendation": (
            "F68 change not justified; current nominal polling boundary covers candidate."
        ),
        "limitation": (
            "15 deterministic fake samples describe application-boundary overhead only; "
            "they do not establish MyProfit network performance or an external SLA."
        ),
    }
    print("T36_EVIDENCE " + json.dumps(evidence, sort_keys=True), flush=True)
