"""Tests for T09: GET /import and GET /import/review redirect to dashboard.

The standalone import pages were retired in S04/T04 — import now lives
in the dashboard modal. Any request to GET /import or GET /import/review
returns 302 with Location "/".
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_import_redirects_to_dashboard(client: TestClient) -> None:
    """GET /import returns 302 with Location '/' for an authenticated user."""
    # Log in with seed credentials and select the first profile
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    client.post("/profiles/1/select", follow_redirects=False)

    resp = client.get("/import", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("location") == "/"


def test_get_import_review_redirects_to_dashboard(client: TestClient) -> None:
    """GET /import/review returns 302 with Location '/' for an authenticated user."""
    # Log in with seed credentials and select the first profile
    client.post(
        "/login",
        data={"username": "Italo", "password": "test-password"},
        follow_redirects=False,
    )
    client.post("/profiles/1/select", follow_redirects=False)

    resp = client.get("/import/review", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers.get("location") == "/"
