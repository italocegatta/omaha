"""T02: POST /classes server-side sum/pct/name validation.

Ten test cases, each backed by the session-scoped
``_omaha_test_env`` from ``tests/conftest.py`` (per-test
:class:`TestClient` for cookie isolation, but a single SQLite
file at the session level so the T01 ``asset_classes`` table is
already present).

The flow exercised by every test:

1. ``POST /login`` with the seed credentials.
2. ``POST /profiles/{id}/select`` to bind ``active_profile_id``.
3. ``POST /classes`` with the rows under test.

The ``client`` fixture's session-scoped DB is the one T01 left
behind: ``alembic upgrade head`` has already run inside
``_omaha_test_env`` and the 0002 migration is in the chain
(``alembic current`` reports ``0002_macro_classes (head)``).
T02 does not run alembic again — it just reads/writes through
the existing engine.

Helper conventions
------------------
- :func:`_login_and_select` performs the two-step cookie bootstrap.
- :func:`_post_classes` builds the parallel-array form body the
  same way a real browser would (multiple ``class_id[]``,
  ``name[]``, ``target_pct[]`` fields) and POSTs it. The list
  values in the dict make :class:`httpx.Client` emit
  ``application/x-www-form-urlencoded`` with repeated keys —
  identical to a real form submission.
- :func:`_count_classes` opens a fresh session and counts rows
  for the active profile so a test can assert that a rejected
  POST did not commit.
"""

from __future__ import annotations

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


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    """Log in with the seed credentials and bind ``active_profile_id``.

    The seed creates profile 1 = Italo (display_order=0) and
    profile 2 = Ana Livia (display_order=1). Default is profile 1
    because that's what the T04 happy-path flow uses.
    """
    client.post(
        "/login",
        data={"username": "family", "password": "test-password"},
        follow_redirects=False,
    )
    client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _post_classes(
    client: TestClient,
    rows: list[tuple[str, str, str]],
    *,
    follow_redirects: bool = False,
) -> Any:
    """POST ``/classes`` with one form row per ``(class_id, name, target_pct)``.

    Mirrors the wire format a real browser produces for parallel
    arrays: repeated ``class_id[]`` / ``name[]`` / ``target_pct[]``
    keys, urlencoded body. ``class_id`` of ``""`` is the "new row"
    sentinel — the route treats it as a fresh insert.
    """
    data: dict[str, list[str]] = {"class_id[]": [], "name[]": [], "target_pct[]": []}
    for cid, name, pct in rows:
        data["class_id[]"].append(cid)
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
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "30"),
            ("", "Reserva", "10"),
        ],
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/classes"

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


def test_post_classes_sum_90_rejected_with_falta(client: TestClient) -> None:
    """`POST /classes` with sum=90 re-renders with "Falta 10" and commits nothing."""
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "20"),
            ("", "Reserva", "10"),
        ],
    )

    assert response.status_code == 200
    assert "Falta 10" in response.text
    # The error is rendered into a dedicated element so the test
    # does not couple to copy that T03 may rewrite.
    assert "class-editor-error" in response.text
    assert _count_classes(profile_id=1) == 0


def test_post_classes_sum_110_rejected_with_sobra(client: TestClient) -> None:
    """`POST /classes` with sum=110 re-renders with "Sobra 10" and commits nothing."""
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("", "Renda Fixa", "70"),
            ("", "Acoes", "30"),
            ("", "Reserva", "10"),
        ],
    )

    assert response.status_code == 200
    assert "Sobra 10" in response.text
    assert "class-editor-error" in response.text
    assert _count_classes(profile_id=1) == 0


def test_post_classes_empty_name_rejected(client: TestClient) -> None:
    """An empty name surfaces "obrigatório" and commits nothing."""
    _login_and_select(client, profile_id=1)

    response = _post_classes(
        client,
        [
            ("", "Renda Fixa", "60"),
            ("", "", "30"),
            ("", "Reserva", "10"),
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
            ("", "Renda Fixa", "60"),
            ("", long_name, "30"),
            ("", "Reserva", "10"),
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
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "40"),
            ("", "Reserva", "-1"),
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
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "30"),
            ("", "Reserva", "101"),
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
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "30"),
            ("", "Renda Fixa", "10"),  # duplicate of row 0
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
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "30"),
            ("", "Reserva", "10"),
        ],
    )
    assert _classes_for_profile(profile_id=1) == [
        ("Renda Fixa", 60.0),
        ("Acoes", 30.0),
        ("Reserva", 10.0),
    ]
    assert _classes_for_profile(profile_id=2) == []

    # Switch to profile 2 and POST its own rows. Profile 1's
    # classes must be untouched.
    client.post("/profiles/2/select", follow_redirects=False)
    _post_classes(
        client,
        [
            ("", "Stocks", "70"),
            ("", "Bonds", "30"),
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
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "30"),
            ("", "Reserva", "10"),
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


def test_get_classes_renders_editor(client: TestClient) -> None:
    """`GET /classes` renders the S03 class editor template.

    The route is the canonical view of a profile's asset classes.
    The dashboard surfaces a "Gerenciar classes" shortcut that
    links here.
    """
    _login_and_select(client, profile_id=1)
    response = client.get("/classes", follow_redirects=False)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'data-testid="class-editor"' in response.text


def test_post_classes_update_existing_row(client: TestClient) -> None:
    """Submitting rows that reference existing class_ids updates them in place.

    The first POST creates three rows; the second POST sends
    ``class_id`` values for all three (one updated name/pct,
    one updated pct, one unchanged) plus one new row. The route
    must: (a) update the existing rows in place rather than
    insert duplicates, (b) preserve all three existing ids, and
    (c) set ``display_order`` on the new row to ``max + 1``
    (i.e. 3, since 0, 1, 2 are taken).
    """
    from omaha.db import SessionLocal
    from omaha.models import AssetClass

    _login_and_select(client, profile_id=1)
    _post_classes(
        client,
        [
            ("", "Renda Fixa", "60"),
            ("", "Acoes", "30"),
            ("", "Reserva", "10"),
        ],
    )

    db = SessionLocal()
    try:
        renda = (
            db.query(AssetClass)
            .filter(AssetClass.profile_id == 1, AssetClass.name == "Renda Fixa")
            .one()
        )
        acoes = (
            db.query(AssetClass)
            .filter(AssetClass.profile_id == 1, AssetClass.name == "Acoes")
            .one()
        )
        reserva = (
            db.query(AssetClass)
            .filter(AssetClass.profile_id == 1, AssetClass.name == "Reserva")
            .one()
        )
        renda_id, acoes_id, reserva_id = renda.id, acoes.id, reserva.id
    finally:
        db.close()

    response = _post_classes(
        client,
        [
            (str(renda_id), "Renda Fixa Plus", "50"),  # updated
            (str(acoes_id), "Acoes", "30"),  # unchanged
            (str(reserva_id), "Reserva", "10"),  # updated pct only
            ("", "Crypto", "10"),  # new row
        ],
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/classes"

    # The existing IDs must still exist (updates, not delete+insert),
    # and the new row must be present with the next display_order.
    db = SessionLocal()
    try:
        all_rows = (
            db.query(AssetClass)
            .filter(AssetClass.profile_id == 1)
            .order_by(AssetClass.display_order)
            .all()
        )
    finally:
        db.close()

    assert len(all_rows) == 4
    by_id = {r.id: r for r in all_rows}
    assert renda_id in by_id
    assert acoes_id in by_id
    assert reserva_id in by_id
    assert by_id[renda_id].name == "Renda Fixa Plus"
    assert float(by_id[renda_id].target_pct) == 50.0
    assert by_id[acoes_id].name == "Acoes"
    assert float(by_id[acoes_id].target_pct) == 30.0
    assert by_id[reserva_id].name == "Reserva"
    assert float(by_id[reserva_id].target_pct) == 10.0

    # The new row's display_order is 3 (max existing 2 + 1).
    new_row = next(r for r in all_rows if r.id not in (renda_id, acoes_id, reserva_id))
    assert new_row.name == "Crypto"
    assert float(new_row.target_pct) == 10.0
    assert new_row.display_order == 3
