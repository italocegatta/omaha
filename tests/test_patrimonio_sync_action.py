"""Focused F60 Patrimônio action and F59 boundary rendering contracts.

These tests inspect server-rendered markup and the existing internal job
boundary only. They do not launch a browser, connector, network service, or
external MyProfit dependency.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

TEST_PASSWORD = "test-password"


def _login(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={"username": "Italo", "password": TEST_PASSWORD},
    )
    assert response.status_code in {200, 303}, response.text


@pytest.fixture(autouse=True)
def clean_sync_rows() -> None:
    from omaha.db import SessionLocal
    from omaha.main import app
    from omaha.models import ImportPreview, MyProfitSyncJob

    app.state.myprofit_sync_service.shutdown()
    with SessionLocal() as db:
        db.query(MyProfitSyncJob).delete()
        db.query(ImportPreview).delete()
        db.commit()
    yield


def test_real_profile_action_pair(client: TestClient) -> None:
    _login(client)

    response = client.get("/patrimonio")

    assert response.status_code == 200, response.text
    body = response.text
    action_start = body.index('<section class="patrimonio-actions"')
    action_end = body.index("</section>", action_start)
    action = body[action_start:action_end]
    assert 'data-testid="dashboard-import-btn"' in action
    assert 'data-testid="dashboard-sync-btn"' in action
    assert action.index('data-testid="dashboard-sync-btn"') < action.index(
        'data-testid="dashboard-import-btn"'
    )
    assert '<span class="icon icon--md" aria-hidden="true">sync</span>' in action
    assert 'data-testid="patrimonio-notifications"' in action
    assert 'data-testid="dashboard-sync-status"' not in action
    assert 'x-init="$store.patrimonioSync.init(' in action


def test_family_sync_action_is_disabled(client: TestClient) -> None:
    from omaha.db import SessionLocal
    from omaha.models import Profile

    _login(client)
    with SessionLocal() as db:
        sentinel = db.query(Profile).filter(Profile.is_family_sentinel.is_(True)).one()

    selected = client.post(f"/profiles/{sentinel.id}/select", follow_redirects=False)
    assert selected.status_code == 303
    response = client.get("/patrimonio")

    assert response.status_code == 200, response.text
    body = response.text
    action_start = body.index('<section class="patrimonio-actions"')
    action_end = body.index("</section>", action_start)
    action = body[action_start:action_end]
    assert 'data-testid="dashboard-sync-btn"' not in action
    assert "Atualizar posição" not in action
    assert "@click" not in action
    assert "/api/myprofit/sync" not in action
    assert 'data-testid="dashboard-import-btn"' not in action


def test_page_renders_safe_sync_error(client: TestClient) -> None:
    from omaha.db import SessionLocal
    from omaha.models import MyProfitSyncJob, Profile

    _login(client)
    with SessionLocal() as db:
        profile = db.query(Profile).filter(Profile.name == "Italo").one()
        db.add(
            MyProfitSyncJob(
                job_id=str(uuid.uuid4()),
                profile_id=profile.id,
                status="failed",
                error_stage="login",
                error_code="raw-secret-must-not-escape",
                expires_at=datetime.now(tz=UTC).replace(tzinfo=None) + timedelta(hours=1),
            )
        )
        db.commit()

    response = client.get("/patrimonio")

    assert response.status_code == 200, response.text
    assert "Não foi possível entrar no MyProfit." in response.text
    assert "raw-secret-must-not-escape" not in response.text


def test_family_page_has_no_sync_detail(client: TestClient) -> None:
    from omaha.db import SessionLocal
    from omaha.models import Profile

    _login(client)
    with SessionLocal() as db:
        sentinel = db.query(Profile).filter(Profile.is_family_sentinel.is_(True)).one()
    client.post(f"/profiles/{sentinel.id}/select", follow_redirects=False)

    response = client.get("/patrimonio")

    assert response.status_code == 200, response.text
    action_start = response.text.index('<section class="patrimonio-actions"')
    action_end = response.text.index("</section>", action_start)
    action = response.text[action_start:action_end]
    assert "Não foi possível entrar no MyProfit." not in action
    assert 'data-testid="dashboard-sync-btn"' not in action
    assert "Atualizar posição" not in action
    assert 'data-testid="patrimonio-notifications"' not in action


def test_sync_state_machine_and_preview_handoff_contract_is_rendered(client: TestClient) -> None:
    _login(client)

    response = client.get("/patrimonio")

    assert response.status_code == 200, response.text
    body = response.text
    assert "state: 'idle'" in body
    assert "self.state = 'loading'" in body
    assert "self.state = 'success'" in body
    assert "this.state = 'error'" in body
    assert "payload.status !== 'succeeded'" in body
    assert "payload.status === 'failed'" in body
    assert "payload.status === 'expired'" in body
    assert "POST /api/import/commit" not in body
    assert "openPreview" in body
    assert "hydratePreview" in body
    assert "setNotificationInteraction" in body
    assert "resetAfterReview" in body
