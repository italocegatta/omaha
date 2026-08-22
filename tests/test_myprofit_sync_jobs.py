"""Focused internal contracts for F59 synchronization jobs.

These tests stop at the application-owned job, file, parser, and preview
boundaries. They do not construct or invoke any external service adapter.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
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
    "PETR4,PETR4,1,10,12,10,12\n"
).encode()


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
    with SessionLocal() as db:
        db.query(MyProfitSyncJob).delete()
        db.query(ImportPreview).delete()
        db.commit()
    yield
    service.shutdown()
    with service._lock:
        service._reservations.clear()
        service._owned_dirs.clear()


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
