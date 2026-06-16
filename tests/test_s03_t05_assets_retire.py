"""Tests for T05: GET /assets redirects to dashboard.

The /assets page was retired in S03/T05 — the dedicated editor is
replaced by inline asset management on the dashboard (S03/T03 + T04).
Any request to GET /assets now returns 302 with Location "/".

The form-encoded POST /assets and POST /assets/{id}/delete routes
remain wired in the router (per the S03 research — they are dead
code but a future polish slice may prune them).
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_assets_redirects_to_dashboard(client: TestClient) -> None:
    """GET /assets returns 302 with Location '/' for an authenticated user."""
    # Log in with seed credentials and select the first profile
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    client.post("/profiles/1/select", follow_redirects=False)

    resp = client.get("/assets", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("location") == "/"
