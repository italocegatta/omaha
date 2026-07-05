"""F06 + F07 — family full-join cross-User aggregate tests.

Verifies the family aggregate view (``?view=household`` AND
``Família`` sentinel selected via the profile-switcher chip):

1. The dashboard renders the **cross-User** summed portfolio +
   per-class totals when the querystring carries
   ``view=household`` OR the Família sentinel is bound via the
   chip. The aggregate is identical regardless of which family
   operator is logged in (the F06 invariant
   "Italo logged in == Ana logged in == same total").
2. ``AssetClass`` rows with identical ``name`` across profiles
   collapse into a single rendered class row (full-join by
   name). The same rule applies to ``Asset`` rows inside the
   collapsed class.
3. F07 — Família is selectable via the profile-switcher chip
   (peer of Italo / Ana); the toggle form is gone from the
   header. Selecting the sentinel activates the family view
   with no querystring. The sentinel ``<option>`` carries
   ``data-testid="profile-option-family"`` so e2e selectors
   keep working.
4. ``class-target-pct-view`` is **not** rendered in family mode
   (allocation targets are undefined for the aggregated portfolio).
5. The five mutation endpoints (``POST /classes``,
   ``POST /api/assets``, ``PATCH /api/assets/{id}``,
   ``DELETE /api/assets/{id}``, ``POST /import``) plus
   ``POST /rebalanceamento`` still return
   ``409 {"reason": "household_read_only"}`` while family mode
   is active in the session, and behave unchanged when family
   mode is off.

The session flag is set server-side in
:func:`omaha.routes.pages.select_profile` (when the sentinel is
bound) so the ``require_profile_writable`` dep can read it from
``request.session`` — the JSON POST from the select form does not
carry a querystring. F06 renames the internal flag to
``view_mode == "family"``; the dep accepts both the new and the
legacy ``"household"`` value during cutover.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from omaha.models import Asset, AssetClass, Position, Profile, User

TEST_PASSWORD = "test-password"


@pytest.fixture(autouse=True)
def _clean_state_for_family_aggregate():
    """Seed canonical F07 state: two Users (Italo, Ana) with their
    namesake profiles + the Família sentinel row.

    The F01 autouse fixture added an "Italo RF2" second profile to
    Italo's User row to exercise the intra-User aggregate. F06
    superseded F01 with cross-User; F07 retires the toggle and
    retires the F01 fixture row entirely — the canonical
    ``db-reset`` state is exactly two real profiles + one
    sentinel. This fixture:

    1. Wipes classes / assets / positions so per-test setup starts
       from a clean slate.
    2. Drops any test-only Users (not in the seeded pair).
    3. Restores Ana's profile if a previous test deleted it.
    4. Drops synthetic second profiles owned by Italo so the
       canonical two-User setup is preserved across tests.
    5. Ensures the Família sentinel Profile row exists (idempotent
       — the canonical seed layer also enforces this).
    """
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        # Clean slate so each test starts with no leftover state.
        db.query(Position).delete()
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        seeded_usernames = {"Italo", "Ana"}
        for u in db.query(User).all():
            if u.username not in seeded_usernames:
                db.delete(u)
        # Restore Ana's profile if a previous test deleted it.
        ana = db.query(User).filter(User.username == "Ana").one_or_none()
        if ana is not None and not any(p.name == "Ana" for p in ana.profiles):
            db.add(Profile(user_id=ana.id, name="Ana", display_order=0))
        # Drop synthetic profiles owned by Italo so the canonical
        # F07 setup (Italo with one profile, Ana with one profile)
        # is preserved across tests. ``Italo RF2`` is retired.
        italo = db.query(User).filter(User.username == "Italo").one_or_none()
        if italo is not None:
            for p in list(italo.profiles):
                if p.name != "Italo":
                    db.delete(p)
        # Flush the pending deletes so the Família sentinel
        # re-creation below sees a clean DB state — without the
        # flush, SQLAlchemy's identity map returns the
        # pending-deleted family User (and its cascaded Família
        # Profile) as if they still exist, and
        # ``_ensure_family_sentinel`` short-circuits without
        # creating anything.
        db.flush()
        # Ensure the Família sentinel row exists (idempotent — the
        # canonical seed layer also enforces this; the fixture is a
        # backstop for tests that bypass the seed layer).
        from omaha.seed import (
            FAMILY_SENTINEL_PROFILE_NAME,
            FAMILY_SENTINEL_USER,
            _ensure_family_sentinel,
        )

        _ensure_family_sentinel(db)
        db.commit()
        sentinel = (
            db.query(Profile).filter(Profile.name == FAMILY_SENTINEL_PROFILE_NAME).one_or_none()
        )
        assert sentinel is not None, (
            f"F07 sentinel {FAMILY_SENTINEL_PROFILE_NAME!r} must exist; "
            f"seed layer did not create it. user {FAMILY_SENTINEL_USER!r}."
        )
        assert sentinel.is_family_sentinel is True
    finally:
        db.close()
    yield


def _login(client: TestClient, username: str) -> None:
    """Log in as ``username`` (no profile selection — F06 doesn't
    need a specific active profile because the aggregate is
    cross-User)."""
    r = client.post(
        "/login",
        data={"username": username, "password": TEST_PASSWORD},
    )
    assert r.status_code in (200, 303), r.text


def _login_and_select(client: TestClient, profile_name: str) -> int:
    """Log in as ``profile_name`` and return the profile id."""
    client.post(
        "/login",
        data={"username": profile_name, "password": TEST_PASSWORD},
    )
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.name == profile_name).first()
        assert profile is not None, f"profile {profile_name!r} not seeded"
        return profile.id
    finally:
        db.close()


def _seed_class_with_position(
    profile_id: int,
    class_name: str,
    target_pct: str,
    asset_name: str,
    qty: str,
    avg: str,
    cur: str,
    broker_ticker: str,
) -> None:
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        klass = AssetClass(
            profile_id=profile_id,
            name=class_name,
            target_pct=Decimal(target_pct),
            display_order=0,
        )
        db.add(klass)
        db.flush()
        asset = Asset(
            asset_class_id=klass.id,
            name=asset_name,
            display_order=0,
        )
        db.add(asset)
        db.flush()
        db.add(
            Position(
                asset_id=asset.id,
                qty=Decimal(qty),
                avg_price=Decimal(avg),
                current_price=Decimal(cur),
                broker_ticker=broker_ticker,
                total_invested=Decimal(qty) * Decimal(avg),
                total_current=Decimal(qty) * Decimal(cur),
            )
        )
        db.commit()
    finally:
        db.close()


def _activate_family(client: TestClient) -> None:
    """Visit ``/patrimonio?view=household`` so the session flag flips on."""
    r = client.get("/patrimonio?view=household")
    assert r.status_code == 200, r.text


def _clear_family(client: TestClient) -> None:
    """Visit ``/patrimonio`` (no querystring) so the flag flips off."""
    r = client.get("/patrimonio")
    assert r.status_code == 200, r.text


def _italo_profile_id() -> int:
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        italo_profile = db.query(Profile).filter(Profile.name == "Italo").one()
        return italo_profile.id
    finally:
        db.close()


def _ana_profile_id() -> int:
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        ana_profile = db.query(Profile).filter(Profile.name == "Ana").one()
        return ana_profile.id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# F06 cross-User symmetric aggregate
# ---------------------------------------------------------------------------


def test_family_view_is_symmetric_across_operators(client: TestClient) -> None:
    """F06 D-F06.1 — the family aggregate is identical regardless of
    which family operator is logged in.

    Seed: Italo holds "RF Italo" with 10 TESOURO @ 100/110, Ana
    holds "RF Ana" with 5 CDB @ 200/220. Cross-User totals:
    10*100 + 5*200 = 2000 invested, 10*110 + 5*220 = 2200 current.

    Log in as Italo, request ``?view=household``, capture totals;
    log in as Ana, same request, same totals.
    """
    italo_id = _italo_profile_id()
    ana_id = _ana_profile_id()
    _seed_class_with_position(
        profile_id=italo_id,
        class_name="RF Italo",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )
    _seed_class_with_position(
        profile_id=ana_id,
        class_name="RF Ana",
        target_pct="100.00",
        asset_name="CDB",
        qty="5",
        avg="200",
        cur="220",
        broker_ticker="CDB_BANCO_X",
    )

    # Operator A: Italo.
    _login(client, "Italo")
    _activate_family(client)
    r_italo = client.get("/patrimonio?view=household")
    assert r_italo.status_code == 200, r_italo.text
    body_italo = r_italo.text
    # Both classes collapse into a single cross-User render.
    assert "RF Italo" in body_italo, body_italo
    assert "RF Ana" in body_italo, body_italo
    assert "R$ 2.200,00" in body_italo, body_italo
    assert "R$ 2.000,00" in body_italo, body_italo
    assert "R$ 200,00" in body_italo, body_italo

    # Operator B: Ana — same DB state, same total.
    _login(client, "Ana")
    _activate_family(client)
    r_ana = client.get("/patrimonio?view=household")
    assert r_ana.status_code == 200, r_ana.text
    body_ana = r_ana.text
    # The exact totals match Italo's view — the aggregate is
    # cross-User and identical regardless of which operator is
    # authenticated.
    assert "R$ 2.200,00" in body_ana, body_ana
    assert "R$ 2.000,00" in body_ana, body_ana
    assert "R$ 200,00" in body_ana, body_ana
    # Ana's class is in the render too — there is no per-User
    # isolation in family mode.
    assert "RF Italo" in body_ana, body_ana
    assert "RF Ana" in body_ana, body_ana


# ---------------------------------------------------------------------------
# F06 full-join by name (classes + assets collapse)
# ---------------------------------------------------------------------------


def test_family_view_collapses_classes_with_identical_names(
    client: TestClient,
) -> None:
    """F06 D-F06.2 — ``AssetClass`` rows with identical ``name`` across
    profiles collapse into a single rendered class row.

    Seed: Italo and Ana both hold a class named "Renda Fixa" with
    different totals (10*100 vs 5*200). The family aggregate must
    render one "Renda Fixa" row whose ``current_value`` is the sum
    10*110 + 5*220 = 2200.
    """
    italo_id = _italo_profile_id()
    ana_id = _ana_profile_id()
    _seed_class_with_position(
        profile_id=italo_id,
        class_name="Renda Fixa",
        target_pct="60.00",
        asset_name="TESOURO_IPCA",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )
    _seed_class_with_position(
        profile_id=ana_id,
        class_name="Renda Fixa",
        target_pct="100.00",
        asset_name="CDB_BANCO_X",
        qty="5",
        avg="200",
        cur="220",
        broker_ticker="CDB_BANCO_X",
    )

    _login(client, "Italo")
    r = client.get("/patrimonio?view=household")
    assert r.status_code == 200, r.text
    body = r.text

    # Exactly one class section with the collapsed name.
    assert body.count('data-testid="class-summary-row"') == 1, body
    assert body.count("Renda Fixa") >= 1, body
    # Cross-User sum: 1100 + 1100 = 2200.
    assert "R$ 2.200,00" in body, body


def test_family_view_collapses_assets_with_identical_names(
    client: TestClient,
) -> None:
    """F06 D-F06.2 — within the aggregated class, ``Asset`` rows with
    identical ``name`` across profiles also collapse.

    Seed: Italo and Ana both hold "Renda Fixa" → "Tesouro IPCA" with
    different totals (10*100 vs 5*200). The collapsed "Renda Fixa"
    section must render one asset row for "Tesouro IPCA" whose
    current_value is the sum 10*110 + 5*220 = 2200.
    """
    italo_id = _italo_profile_id()
    ana_id = _ana_profile_id()
    _seed_class_with_position(
        profile_id=italo_id,
        class_name="Renda Fixa",
        target_pct="60.00",
        asset_name="Tesouro IPCA",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_IPCA_2029",
    )
    _seed_class_with_position(
        profile_id=ana_id,
        class_name="Renda Fixa",
        target_pct="100.00",
        asset_name="Tesouro IPCA",
        qty="5",
        avg="200",
        cur="220",
        broker_ticker="TESOURO_IPCA_2035",
    )

    _login(client, "Italo")
    r = client.get("/patrimonio?view=household")
    assert r.status_code == 200, r.text
    body = r.text

    # Exactly one class section + one asset row.
    assert body.count('data-testid="class-summary-row"') == 1, body
    assert body.count('data-testid="dashboard-asset-row"') == 1, body
    # Sum rendering preserved.
    assert "R$ 2.200,00" in body, body


def test_family_view_keeps_classes_with_distinct_names(
    client: TestClient,
) -> None:
    """F06 D-F06.2 — classes with different ``name`` values stay
    separate (no spurious collapse across distinct names)."""
    italo_id = _italo_profile_id()
    ana_id = _ana_profile_id()
    _seed_class_with_position(
        profile_id=italo_id,
        class_name="Renda Fixa",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )
    _seed_class_with_position(
        profile_id=ana_id,
        class_name="Ações",
        target_pct="100.00",
        asset_name="PETR4",
        qty="20",
        avg="30",
        cur="35",
        broker_ticker="PETR4",
    )

    _login(client, "Italo")
    r = client.get("/patrimonio?view=household")
    assert r.status_code == 200, r.text
    body = r.text

    # Two distinct class sections.
    assert body.count('data-testid="class-summary-row"') == 2, body
    assert "Renda Fixa" in body, body
    assert "Ações" in body, body


# ---------------------------------------------------------------------------
# F06 target_pct suppression in family mode
# ---------------------------------------------------------------------------


def test_family_view_omits_class_target_pct_pill(client: TestClient) -> None:
    """F06 D-F06.3 — the ``class-target-pct-view`` pill is not
    rendered in family mode (allocation target is undefined for the
    aggregated portfolio)."""
    italo_id = _italo_profile_id()
    _seed_class_with_position(
        profile_id=italo_id,
        class_name="RF",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )

    _login(client, "Italo")
    r = client.get("/patrimonio?view=household")
    assert r.status_code == 200, r.text
    body = r.text

    assert 'data-testid="class-target-pct-view"' not in body, body


# ---------------------------------------------------------------------------
# F07 sentinel option in profile-switcher (peer of Italo / Ana)
# ---------------------------------------------------------------------------


def _familia_sentinel_id() -> int:
    from omaha.db import SessionLocal

    db = SessionLocal()
    try:
        sentinel = db.query(Profile).filter(Profile.is_family_sentinel.is_(True)).one()
        return sentinel.id
    finally:
        db.close()


def test_profile_switcher_renders_familia_option(client: TestClient) -> None:
    """F07 D-F07.1 — the profile-switcher chip renders the Família
    sentinel as a peer of Italo / Ana. The sentinel ``<option>``
    carries ``data-testid="profile-option-family"`` so e2e
    selectors keep working."""
    _login(client, "Italo")

    r = client.get("/patrimonio")
    assert r.status_code == 200, r.text
    body = r.text
    # Sentinel option present with the canonical testid.
    assert 'data-testid="profile-option-family"' in body, body
    # Sentinel option label matches the F07 spec.
    assert "Família" in body, body
    # No more header toggle form — F07 retired it.
    assert 'data-testid="family-toggle"' not in body, body
    assert 'data-testid="family-toggle-enter"' not in body, body


def test_select_familia_via_chip_renders_family_view(
    client: TestClient,
) -> None:
    """F07 D-F07.1 — ``POST /profiles/{familia_id}/select`` flips
    the session to family mode and redirects to
    ``/patrimonio?view=household``. The next ``GET /patrimonio``
    renders the cross-User aggregate with the read-only banner."""
    _login(client, "Italo")
    sentinel_id = _familia_sentinel_id()

    # Operator picks Família in the chip — the form posts to the
    # same /profiles/{id}/select endpoint the real-profile picker
    # uses; the handler detects the sentinel and short-circuits
    # the session to view_mode="family".
    r = client.post(f"/profiles/{sentinel_id}/select", follow_redirects=False)
    assert r.status_code == 303, r.text
    # Sentinel select redirects to the canonical family-view URL
    # so the URL bar shows the family entry point even though the
    # chip is what flipped the state.
    assert r.headers["location"] == "/patrimonio?view=household", r.headers

    # Follow the redirect — the dashboard renders the family
    # aggregate.
    r2 = client.get("/patrimonio")
    assert r2.status_code == 200, r2.text
    body = r2.text
    assert 'data-testid="patrimonio-read-only-note"' in body, body
    # The Família sentinel is the selected option in the chip —
    # assert the ``selected`` attribute appears in the same
    # ``<option>`` element that carries ``profile-option-family``.
    # Walk back from the data-testid attribute to the opening
    # ``<option`` tag and assert ``selected`` is somewhere between
    # them (whitespace-tolerant).
    sentinel_marker = 'data-testid="profile-option-family"'
    marker_idx = body.find(sentinel_marker)
    assert marker_idx > 0, body
    # Find the opening ``<option`` tag for this element (scan
    # backwards until we hit it).
    open_tag_start = body.rfind("<option", 0, marker_idx)
    assert open_tag_start > 0, body
    open_tag_end = body.find(">", marker_idx)
    assert open_tag_end > 0, body
    option_open_tag = body[open_tag_start:open_tag_end]
    assert "selected" in option_open_tag, (
        f"Família option must carry the ``selected`` attribute when sentinel is active; "
        f"got opening tag {option_open_tag!r}"
    )


def test_select_real_profile_clears_family_mode(client: TestClient) -> None:
    """F07 — selecting a real profile from the chip clears the
    ``view_mode`` session flag (F01 contract: any real-profile
    select exits family view)."""
    _login(client, "Italo")
    sentinel_id = _familia_sentinel_id()
    client.post(f"/profiles/{sentinel_id}/select", follow_redirects=False)

    # Sanity: family view is on.
    family = client.get("/patrimonio?view=household")
    assert family.status_code == 200, family.text
    assert 'data-testid="patrimonio-read-only-note"' in family.text

    # Pick the real Italo profile — exits family view.
    italo_profile = (
        # _clean_state_for_family_aggregate guarantees Italo owns
        # exactly the canonical "Italo" profile.
        _italo_profile_id()
    )
    r = client.post(f"/profiles/{italo_profile}/select", follow_redirects=False)
    assert r.status_code == 303, r.text
    assert r.headers["location"] == "/", r.headers

    cleared = client.get("/patrimonio")
    assert cleared.status_code == 200, cleared.text
    assert 'data-testid="patrimonio-read-only-note"' not in cleared.text
    # The "Família (agregado)" option is still in the chip — the
    # toggle is a peer of profiles, not an exit affordance.
    assert 'data-testid="profile-option-family"' in cleared.text


def test_family_mode_clears_when_sentinel_dropped_from_db(
    client: TestClient,
) -> None:
    """F07 — if the Família sentinel is removed from the database
    while the session holds its id, the dashboard re-renders the
    per-profile view (no error). The ``active_profile_id`` is
    cleared and the route redirects to /login if no other profile
    is bound; here Italo still owns a profile so the dashboard
    shows the per-profile view after the sentinel select attempt
    is treated as stale by ``get_active_profile``.

    This scenario is brittle in practice (the sentinel is created
    on every seed) — the assertion is mainly that the application
    does not crash on a sentinel-id that no longer maps to a row.
    """
    from omaha.db import SessionLocal

    _login(client, "Italo")
    sentinel_id = _familia_sentinel_id()

    # Drop the sentinel row.
    db = SessionLocal()
    try:
        sentinel = db.query(Profile).filter(Profile.id == sentinel_id).one()
        db.delete(sentinel)
        db.commit()
    finally:
        db.close()

    # The session still references the sentinel id — visiting
    # /patrimonio must NOT crash and must NOT show the family view.
    # The route clears ``active_profile_id`` and falls through to
    # the per-profile view via the post-login flow (since
    # ``get_active_profile`` returns None for the missing sentinel).
    r = client.get("/patrimonio", follow_redirects=False)
    assert r.status_code in (200, 303), r.text
    if r.status_code == 303:
        assert r.headers["location"] == "/login", r.headers


# ---------------------------------------------------------------------------
# F06 mutation gate — wire shape stays "household_read_only" for
# backward compat (D-F06.5). The session flag is "family" but the
# 409 JSON body is unchanged.
# ---------------------------------------------------------------------------


def _assert_family_read_only(response) -> None:
    """Common assertions for the 409 + JSON body contract. The wire
    reason stays ``"household_read_only"`` for backward compat with
    F01 consumers (D-F06.5)."""
    assert response.status_code == 409, (
        f"expected 409 household_read_only, got {response.status_code}: {response.text[:500]}"
    )
    body = response.json()
    assert body == {"reason": "household_read_only"}, body


def test_post_classes_returns_409_in_family_mode(client: TestClient) -> None:
    italo_id = _login_and_select(client, "Italo")
    _seed_class_with_position(
        profile_id=italo_id,
        class_name="RF",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )
    _activate_family(client)

    response = client.post(
        "/classes",
        data={"name[]": ["Should not be created"], "target_pct[]": ["100"]},
    )
    _assert_family_read_only(response)


def test_post_api_asset_returns_409_in_family_mode(client: TestClient) -> None:
    from omaha.db import SessionLocal

    italo_id = _login_and_select(client, "Italo")
    db = SessionLocal()
    try:
        klass = AssetClass(
            profile_id=italo_id, name="RF", target_pct=Decimal("60"), display_order=0
        )
        db.add(klass)
        db.commit()
        klass_id = klass.id
    finally:
        db.close()
    _activate_family(client)

    response = client.post(
        "/api/assets",
        json={"name": "Should not be created", "asset_class_id": klass_id},
    )
    _assert_family_read_only(response)


def test_patch_api_asset_returns_409_in_family_mode(client: TestClient) -> None:
    from omaha.db import SessionLocal

    italo_id = _login_and_select(client, "Italo")
    db = SessionLocal()
    try:
        klass = AssetClass(
            profile_id=italo_id, name="RF", target_pct=Decimal("60"), display_order=0
        )
        db.add(klass)
        db.flush()
        asset = Asset(asset_class_id=klass.id, name="TESOURO", display_order=0)
        db.add(asset)
        db.commit()
        asset_id = asset.id
    finally:
        db.close()
    _activate_family(client)

    response = client.patch(
        f"/api/assets/{asset_id}",
        json={"target_pct": "50"},
    )
    _assert_family_read_only(response)


def test_delete_api_asset_returns_409_in_family_mode(client: TestClient) -> None:
    from omaha.db import SessionLocal

    italo_id = _login_and_select(client, "Italo")
    db = SessionLocal()
    try:
        klass = AssetClass(
            profile_id=italo_id, name="RF", target_pct=Decimal("60"), display_order=0
        )
        db.add(klass)
        db.flush()
        asset = Asset(asset_class_id=klass.id, name="TESOURO", display_order=0)
        db.add(asset)
        db.commit()
        asset_id = asset.id
    finally:
        db.close()
    _activate_family(client)

    response = client.delete(f"/api/assets/{asset_id}")
    _assert_family_read_only(response)


def test_post_import_returns_409_in_family_mode(client: TestClient) -> None:
    italo_id = _login_and_select(client, "Italo")
    _seed_class_with_position(
        profile_id=italo_id,
        class_name="RF",
        target_pct="60.00",
        asset_name="TESOURO",
        qty="10",
        avg="100",
        cur="110",
        broker_ticker="TESOURO_2029",
    )
    _activate_family(client)

    csv_bytes = b"ativo;quantidade;preco_medio;preco_atual\nPETR4;10;30;35\n"
    response = client.post(
        "/api/import/preview",
        files={"file": ("positions.csv", csv_bytes, "text/csv")},
    )
    _assert_family_read_only(response)


def test_mutation_succeeds_when_family_mode_is_off(client: TestClient) -> None:
    """Sanity check: clearing family mode restores the original
    mutation contract (the dependency must not leak into the
    default flow)."""
    _login_and_select(client, "Italo")
    # Activate then deactivate.
    _activate_family(client)
    # Sanity: GET /patrimonio (no querystring) renders the dashboard
    # with the read-only banner ABSENT (i.e. the flag cleared on
    # the GET round-trip).
    cleared = client.get("/patrimonio")
    assert cleared.status_code == 200, cleared.text
    assert 'data-testid="patrimonio-read-only-note"' not in cleared.text

    response = client.post(
        "/classes",
        data={"name[]": ["Volta ao normal"], "target_pct[]": ["100"]},
        follow_redirects=False,
    )
    # 303 to the dashboard on success — the dependency is a no-op
    # when the session flag is absent. ``follow_redirects=False``
    # so we observe the raw 303 instead of the 200 the redirected
    # GET would render.
    assert response.status_code == 303, (
        f"expected 303 on cleared family mode, got {response.status_code}: {response.text[:500]}"
    )


# ---------------------------------------------------------------------------
# rebalance page-side form — gated by the same dep
# ---------------------------------------------------------------------------


def test_post_rebalanceamento_returns_409_in_family_mode(
    client: TestClient,
) -> None:
    """The page-side rebalance POST shares the same read-only gate
    so a hand-crafted form submit from a stale tab can't bypass the
    UI's button-disable."""
    _login_and_select(client, "Italo")
    _activate_family(client)

    response = client.post("/rebalanceamento", data={"contribution": "100"})
    _assert_family_read_only(response)
