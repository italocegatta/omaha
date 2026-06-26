"""T02: POST /classes server-side sum/pct/name validation (snapshot model).

Ten test cases, each backed by the session-scoped
``_omaha_test_env`` from ``tests/conftest.py`` (per-test
:class:`TestClient` for cookie isolation, but a single SQLite
file at the session level so the T01 ``asset_classes`` table is
already present).

Snapshot semantics (D016)
-------------------------
``POST /classes`` is delete-all-then-insert: the form payload
replaces every existing row for the active profile in a single
transaction. There is no ``class_id[]`` field — the route
ignores identity, only the submitted ``(name, target_pct)``
pairs matter. Empty form arrays mean "clear all".

The flow exercised by every test:

1. ``POST /login`` with the seed credentials.
2. ``POST /profiles/{id}/select`` to bind ``active_profile_id``.
3. ``POST /classes`` with the rows under test.

Helper conventions
------------------
- :func:`_login_and_select` performs the two-step cookie bootstrap.
- :func:`_post_classes` builds the parallel-array form body the
  same way a real browser would (multiple ``name[]`` and
  ``target_pct[]`` fields) and POSTs it. The list values in the
  dict make :class:`httpx.Client` emit
  ``application/x-www-form-urlencoded`` with repeated keys —
  identical to a real form submission.
- :func:`_count_classes` opens a fresh session and counts rows
  for the active profile so a test can assert that a rejected
  POST did not commit.
- :func:`_seed_classes` inserts rows directly via SQLAlchemy so
  a test can pre-populate the profile before exercising the
  snapshot semantics (the "RED test of the bug" — pre-existing
  rows must be wiped on save).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Per-test cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_asset_classes() -> None:
    """Wipe the ``asset_classes`` table before each T02 test.

    The shared ``_omaha_test_env`` fixture is session-scoped, so a
    successful ``POST /classes`` in one test leaves rows on disk
    that the next test then trips over. Tests that need a clean
    slate (e.g. ``assert _count_classes == 0``) would otherwise
    depend on pytest's collection order. We delete instead of
    dropping the schema so 0002's row format and indexes stay
    intact for the next test.
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_PROFILE_OWNERS = {1: "Italo", 2: "Ana"}


def _login_and_select(client: TestClient, profile_id: int = 1, username: str = "Italo") -> None:
    """Log in with the seed credentials and bind ``active_profile_id``.

    direct-landing-with-header-profile-switcher: ``POST /login``
    auto-binds the logged-in user's own first profile, so logging
    in as ``Italo`` already binds profile 1; logging in as
    ``Ana`` already binds profile 2. The explicit
    ``/profiles/{id}/select`` step is only needed when the caller
    explicitly opts to authenticate as a user who does NOT own the
    requested profile (cross-profile viewing tests).
    """
    client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    if _PROFILE_OWNERS.get(profile_id) != username:
        client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _post_classes(
    client: TestClient,
    rows: list[tuple[str, str]],
    *,
    follow_redirects: bool = False,
) -> Any:
    """POST ``/classes`` with one form row per ``(name, target_pct)``.

    Mirrors the wire format a real browser produces for parallel
    arrays: repeated ``name[]`` and ``target_pct[]`` keys,
    urlencoded body. Snapshot model: no ``class_id[]`` field is
    sent (the route would ignore it if we did).
    """
    data: dict[str, list[str]] = {"name[]": [], "target_pct[]": []}
    for name, pct in rows:
        data["name[]"].append(name)
        data["target_pct[]"].append(pct)
    return client.post("/classes", data=data, follow_redirects=follow_redirects)


def _count_classes(profile_id: int) -> int:
    """Return the number of ``asset_classes`` rows for ``profile_id``.

    Opens a fresh session (the test client's session is bound to
    the request lifecycle) so the count reflects the on-disk DB
    state, not the in-flight session.
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db: Session = SessionLocal()
    try:
        return db.query(AssetClass).filter(AssetClass.profile_id == profile_id).count()
    finally:
        db.close()


def _classes_for_profile(profile_id: int) -> list[tuple[str, float]]:
    """Return ``[(name, float(target_pct)), ...]`` for ``profile_id``.

    Used by tests that need to assert the on-disk rows after a
    successful POST, ordered by ``display_order`` (which is
    ``Profile.asset_classes``'s default ordering).
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db: Session = SessionLocal()
    try:
        rows = (
            db.query(AssetClass)
            .filter(AssetClass.profile_id == profile_id)
            .order_by(AssetClass.display_order)
            .all()
        )
        return [(r.name, float(r.target_pct)) for r in rows]
    finally:
        db.close()


def _seed_classes(profile_id: int, rows: list[tuple[str, str]]) -> None:
    """Insert ``(name, target_pct)`` rows directly via SQLAlchemy.

    Used by the snapshot-replaces-pre-existing test to set up a
    non-empty starting state. The route does the wipe.
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db: Session = SessionLocal()
    try:
        for idx, (name, pct) in enumerate(rows):
            db.add(
                AssetClass(
                    profile_id=profile_id,
                    name=name,
                    target_pct=Decimal(pct),
                    display_order=idx,
                )
            )
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_post_classes_sum_100_commits_with_display_order(
    client: TestClient,
) -> None:
    """`POST /classes` with sum=100 commits, 303s to /, and sets display_order.

    Submits three new rows (Renda Fixa 60, Acoes 30, Reserva 10).
    The route 303s to /, and a fresh session sees all three rows
    with sequential ``display_order`` values (the editor's stable
    iteration order depends on this).
    """
    _login_and_select(client, profile_id=1)
    assert _count_classes(profile_id=1) == 0

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
            ("Reserva", "10"),
        ],
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    rows = _classes_for_profile(profile_id=1)
    assert rows == [
        ("Renda Fixa", 60.0),
        ("Acoes", 30.0),
        ("Reserva", 10.0),
    ]
    # display_order must be unique + sequential for the editor's
    # stable ordering. The first save against a fresh profile
    # gets 0, 1, 2.
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        orders = [
            r.display_order
            for r in db.query(AssetClass)
            .filter(AssetClass.profile_id == 1)
            .order_by(AssetClass.display_order)
            .all()
        ]
    finally:
        db.close()
    assert orders == [0, 1, 2]


def test_post_classes_sum_90_succeeds(client: TestClient) -> None:
    """`POST /classes` with sum=90 succeeds — allocation is informational, not blocking.

    The snapshot form no longer validates the sum-to-100 invariant.
    Classes at any valid percentage are created; the user builds
    the portfolio incrementally. The route returns 303 redirect
    to the dashboard.
    """
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "20"),
            ("Reserva", "10"),
        ],
    )

    # 303 redirect to / (success, not error re-render)
    assert response.status_code == 303
    assert response.headers.get("location") == "/"

    # The classes were committed
    assert _count_classes(profile_id=1) == 3


def test_post_classes_sum_110_succeeds(client: TestClient) -> None:
    """`POST /classes` with sum=110 succeeds — allocation is informational, not blocking.

    The snapshot form no longer validates the sum-to-100 invariant.
    Classes at any valid percentage are created. The route returns
    303 redirect to the dashboard.
    """
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "70"),
            ("Acoes", "30"),
            ("Reserva", "10"),
        ],
    )

    # 303 redirect to / (success, not error re-render)
    assert response.status_code == 303
    assert response.headers.get("location") == "/"

    # The classes were committed
    assert _count_classes(profile_id=1) == 3


def test_post_classes_empty_name_rejected(client: TestClient) -> None:
    """An empty name surfaces "obrigatório" and commits nothing."""
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("", "30"),
            ("Reserva", "10"),
        ],
    )

    assert response.status_code == 200
    assert "obrigatório" in response.text
    assert "class-editor-error" in response.text
    assert _count_classes(profile_id=1) == 0


def test_post_classes_name_too_long_rejected(client: TestClient) -> None:
    """A 65-char name surfaces the length cap (64) and commits nothing.

    The other rows sum to 100, so the only failing check is the
    name length. The error message must include "64" so a future
    agent inspecting the body can see the limit without reading
    the route.
    """
    _login_and_select(client, profile_id=1)
    long_name = "x" * 65

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            (long_name, "30"),
            ("Reserva", "10"),
        ],
    )

    assert response.status_code == 200
    assert "64" in response.text
    assert "class-editor-error" in response.text
    assert _count_classes(profile_id=1) == 0


def test_post_classes_negative_pct_rejected(client: TestClient) -> None:
    """A negative target_pct is rejected with the "entre 0 e 100" message."""
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "40"),
            ("Reserva", "-1"),
        ],
    )

    assert response.status_code == 200
    assert "0" in response.text and "100" in response.text
    assert "class-editor-error" in response.text
    assert _count_classes(profile_id=1) == 0


def test_post_classes_pct_above_100_rejected(client: TestClient) -> None:
    """A target_pct of 101 is rejected with the "entre 0 e 100" message."""
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
            ("Reserva", "101"),
        ],
    )

    assert response.status_code == 200
    assert "0" in response.text and "100" in response.text
    assert "class-editor-error" in response.text
    assert _count_classes(profile_id=1) == 0


def test_post_classes_duplicate_name_in_form_rejected(
    client: TestClient,
) -> None:
    """Two rows with the same name in one submission are rejected with "Já existe"."""
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
            ("Renda Fixa", "10"),  # duplicate of row 0
        ],
    )

    assert response.status_code == 200
    assert "Já existe" in response.text
    assert "class-editor-error" in response.text
    assert _count_classes(profile_id=1) == 0


def test_post_classes_cross_profile_isolation(client: TestClient) -> None:
    """A POST as profile 1 only mutates profile 1's classes; profile 2 is untouched.

    The active profile is sourced from the session, so even if the
    submitted rows happen to collide with profile 2's existing
    data, the route's :func:`require_active_profile` gates the
    writes. This test also covers the S02 must-have "cross-profile
    isolation enforced".
    """
    _login_and_select(client, profile_id=1)
    _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
            ("Reserva", "10"),
        ],
    )
    assert _classes_for_profile(profile_id=1) == [
        ("Renda Fixa", 60.0),
        ("Acoes", 30.0),
        ("Reserva", 10.0),
    ]
    assert _classes_for_profile(profile_id=2) == []

    # Switch to profile 2 and POST its own rows. Profile 1's
    # classes must be untouched. Re-auth as Ana (profile 2's owner).
    _login_and_select(client, profile_id=2, username="Ana")
    _post_classes(
        client,
        [
            ("Stocks", "70"),
            ("Bonds", "30"),
        ],
    )
    assert _classes_for_profile(profile_id=1) == [
        ("Renda Fixa", 60.0),
        ("Acoes", 30.0),
        ("Reserva", 10.0),
    ]
    assert _classes_for_profile(profile_id=2) == [
        ("Stocks", 70.0),
        ("Bonds", 30.0),
    ]


def test_post_classes_delete_removes_class(client: TestClient) -> None:
    """`POST /classes/{id}/delete` removes a class that has no children (S03 will add children)."""
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    _login_and_select(client, profile_id=1)
    _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
            ("Reserva", "10"),
        ],
    )

    # Pick the middle row to delete (display_order=1).
    db = SessionLocal()
    try:
        reserva = (
            db.query(AssetClass)
            .filter(
                AssetClass.profile_id == 1,
                AssetClass.name == "Acoes",
            )
            .one()
        )
        reserva_id = reserva.id
    finally:
        db.close()

    response = client.post(f"/classes/{reserva_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    assert _classes_for_profile(profile_id=1) == [
        ("Renda Fixa", 60.0),
        ("Reserva", 10.0),
    ]


def test_get_classes_redirects_to_dashboard(client: TestClient) -> None:
    """`GET /classes` now 302s to `/` (S02/T07 retired the standalone editor).

    S02 consolidated class editing into the dashboard. The standalone
    /classes route was retired via a 302 redirect so bookmarks and
    stale links still work.
    """
    _login_and_select(client, profile_id=1)
    response = client.get("/classes", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_post_classes_snapshot_replaces_pre_existing(
    client: TestClient,
) -> None:
    """RED test for BUG-002: a POST wipes pre-existing rows for the profile.

    Scenario: profile already has 2 classes (Acoes 50, Bonds 50).
    The user opens the editor (D014 = empty) and submits 3
    different classes summing to 100. The DB must end up with
    exactly the 3 new rows — not 5 (which would be the partial-
    update bug the route used to have).

    Also covers: ``display_order`` is reassigned 0, 1, 2 for
    the new set; the snapshot runs in a single transaction
    (IntegrityError on duplicate name rolls back, not commits).
    """
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[("Acoes", "50"), ("Bonds", "50")],
    )
    assert _count_classes(profile_id=1) == 2

    response = _post_classes(
        client,
        [
            ("Renda Fixa", "60"),
            ("Acoes", "30"),
            ("Reserva", "10"),
        ],
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    # Snapshot semantics: exactly 3 rows, the new set, with
    # display_order reset to 0/1/2.
    assert _count_classes(profile_id=1) == 3
    assert _classes_for_profile(profile_id=1) == [
        ("Renda Fixa", 60.0),
        ("Acoes", 30.0),
        ("Reserva", 10.0),
    ]
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    db = SessionLocal()
    try:
        orders = [
            r.display_order
            for r in db.query(AssetClass)
            .filter(AssetClass.profile_id == 1)
            .order_by(AssetClass.display_order)
            .all()
        ]
    finally:
        db.close()
    assert orders == [0, 1, 2]


def test_post_classes_empty_form_clears_all(client: TestClient) -> None:
    """Submitting an empty form array deletes every class for the profile.

    The "clear all" use case. The editor's save button is
    disabled on zero rows, so a browser user cannot trigger
    this — only programmatic submissions reach the route. We
    treat empty as intentional (D014 = no UX guard against
    intentional wipe).
    """
    _login_and_select(client, profile_id=1)
    _seed_classes(
        profile_id=1,
        rows=[("Acoes", "50"), ("Bonds", "50")],
    )
    assert _count_classes(profile_id=1) == 2

    response = _post_classes(client, [])
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert _count_classes(profile_id=1) == 0
