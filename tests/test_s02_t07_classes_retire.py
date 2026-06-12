"""Tests for T07: GET /classes redirects to dashboard.

The /classes page was retired in S02/T07 — the standalone editor is
replaced by inline class management on the dashboard. Any request to
GET /classes now returns 302 with Location "/".
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_classes_redirects_to_dashboard(client: TestClient) -> None:
    """GET /classes returns 302 with Location '/' for an authenticated user."""
    # Log in with seed credentials and select the first profile
    client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )
    client.post("/profiles/1/select", follow_redirects=False)

    resp = client.get("/classes", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("location") == "/"
