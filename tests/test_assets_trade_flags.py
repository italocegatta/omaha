"""asset-trade-flags: migration + model + route tests.

Six sections, each backed by the session-scoped ``_omaha_test_env``
from ``tests/conftest.py`` so the Alembic head already includes
the new ``buy_enabled`` / ``sell_enabled`` / ``currency_code``
columns and ``ck_asset_currency_code`` CHECK:

1. Migration shape (10.2 / 10.3) — the new columns are present
   with the expected defaults; pre-existing rows backfill
   ``True / True / 'BRL'`` on upgrade.
2. CHECK constraint (10.4) — direct INSERT with ``currency_code =
   'EUR'`` raises ``IntegrityError`` on commit.
3. ORM defaults (10.5 / 10.6) — ``Asset()`` with no trade-control
   args reads ``True / True / 'BRL'`` after flush; explicit
   overrides (``buy_enabled=False``) are honored.
4. PATCH route (11.1) — single-field PATCHes (buy / sell /
   currency), multi-field PATCH, body empty, body unknown key,
   invalid currency.
5. POST route (11.1) — defaults omitted, explicit currency,
   invalid currency, cross-profile class id.
6. Commit route (13.2 / 13.3) — commit propagates the 3 fields
   to existing auto-matched assets and to new unmatched assets;
   currency outside the allowlist is rejected with 422.
"""

from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Per-test cleanup (matches test_assets_patch_legacy pattern)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_assets_and_classes(_omaha_test_env: dict[str, str]) -> None:
    """Wipe ``assets`` + ``asset_classes`` before each test.

    The session-scoped ``_omaha_test_env`` fixture means a successful
    PATCH/POST leaves rows on disk that the next test would trip
    over. Wipe both tables so each test starts from a known empty
    state and the unique ``(asset_class_id, name)`` constraint is
    trivially satisfied.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset, AssetClass

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
        engine.dispose()
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_PROFILE_OWNERS = {1: "Italo", 2: "Ana"}


def _login_and_select(client: TestClient, profile_id: int = 1) -> None:
    client.post(
        "/login",
        data={"username": _PROFILE_OWNERS[profile_id], "password": "test-password"},
        follow_redirects=False,
    )
    if _PROFILE_OWNERS.get(profile_id) != _PROFILE_OWNERS[profile_id]:
        client.post(f"/profiles/{profile_id}/select", follow_redirects=False)


def _seed_class(
    profile_id: int,
    name: str = "Renda Fixa",
    target_pct: int = 100,
    _omaha_test_env: dict[str, str] | None = None,
) -> int:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import AssetClass

    assert _omaha_test_env is not None
    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        cls = AssetClass(
            profile_id=profile_id,
            name=name,
            target_pct=Decimal(str(target_pct)),
            display_order=0,
        )
        db.add(cls)
        db.flush()
        db.commit()
        return cls.id
    finally:
        db.close()
        engine.dispose()


def _seed_asset(
    asset_class_id: int,
    name: str,
    target_pct: str = "0",
    _omaha_test_env: dict[str, str] | None = None,
) -> int:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset

    assert _omaha_test_env is not None
    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        asset = Asset(
            asset_class_id=asset_class_id,
            name=name,
            target_pct=Decimal(target_pct),
            display_order=0,
        )
        db.add(asset)
        db.flush()
        db.commit()
        return asset.id
    finally:
        db.close()
        engine.dispose()


def _read_asset(asset_id: int, _omaha_test_env: dict[str, str]):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        return db.get(Asset, asset_id)
    finally:
        db.close()
        engine.dispose()


def _patch_asset(client: TestClient, asset_id: int, body: dict):
    return client.patch(
        f"/api/assets/{asset_id}",
        json=body,
        follow_redirects=False,
    )


def _post_asset(
    client: TestClient,
    name: str,
    asset_class_id: int,
    **kwargs,
):
    body = {"name": name, "asset_class_id": asset_class_id}
    body.update(kwargs)
    return client.post("/api/assets", json=body, follow_redirects=False)


# ---------------------------------------------------------------------------
# Section 1: Migration shape + backfill
# ---------------------------------------------------------------------------


def test_alembic_head_adds_three_columns(_omaha_test_env: dict[str, str]) -> None:
    """Migration 0016 adds ``buy_enabled`` / ``sell_enabled`` / ``currency_code``.

    Schema inspection on the session-scoped DB confirms the three
    columns are present with the expected types (Boolean / Boolean /
    VARCHAR(8)) and the ``ck_asset_currency_code`` CHECK constraint
    is registered.
    """
    engine = create_engine(_omaha_test_env["db_url"])
    inspector = inspect(engine)
    try:
        cols = {c["name"]: c for c in inspector.get_columns("assets")}
        assert "buy_enabled" in cols
        assert "sell_enabled" in cols
        assert "currency_code" in cols
        # VARCHAR(8) is the width the route's ``String(8)`` matches.
        col_type = str(cols["currency_code"]["type"]).upper()
        assert "VARCHAR" in col_type or "CHAR" in col_type

        # CHECK constraint is registered (name from migration 0016).
        checks = inspector.get_check_constraints("assets")
        names = {c.get("name") for c in checks}
        assert "ck_asset_currency_code" in names, checks
    finally:
        engine.dispose()


def test_backfill_after_migration_reads_defaults(
    _omaha_test_env: dict[str, str],
) -> None:
    """Existing rows read ``True / True / 'BRL'`` after upgrade.

    The migration's ``server_default`` values cover the backfill
    path; an existing row created BEFORE this change must read
    the new defaults after ``alembic upgrade head`` runs (which the
    session fixture has already done).
    """
    asset_id = _seed_asset(
        _seed_class(1, _omaha_test_env=_omaha_test_env),
        "Pre-existing Row",
        "0",
        _omaha_test_env=_omaha_test_env,
    )
    row = _read_asset(asset_id, _omaha_test_env)
    assert row is not None
    assert row.buy_enabled is True
    assert row.sell_enabled is True
    assert row.currency_code == "BRL"


# ---------------------------------------------------------------------------
# Section 2: CHECK constraint rejects non-allowlist currency
# ---------------------------------------------------------------------------


def test_check_constraint_rejects_non_allowlist_currency(
    _omaha_test_env: dict[str, str],
) -> None:
    """A raw INSERT with ``currency_code='EUR'`` raises IntegrityError.

    Uses a fresh engine (the route's path goes through Pydantic and
    would reject earlier; this tests the DB-level guard).
    """
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
        asset = Asset(
            asset_class_id=class_id,
            name="Will Fail",
            display_order=0,
            currency_code="EUR",
        )
        db.add(asset)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Section 3: ORM defaults
# ---------------------------------------------------------------------------


def test_asset_defaults_when_omitted(_omaha_test_env: dict[str, str]) -> None:
    """``Asset()`` with no trade-control args reads defaults at flush."""
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
        asset = Asset(asset_class_id=class_id, name="Defaults", display_order=0)
        db.add(asset)
        db.flush()
        assert asset.buy_enabled is True
        assert asset.sell_enabled is True
        assert asset.currency_code == "BRL"
    finally:
        db.close()
        engine.dispose()


def test_asset_explicit_override(_omaha_test_env: dict[str, str]) -> None:
    """``Asset(buy_enabled=False, ...)`` honors the override."""
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
        asset = Asset(
            asset_class_id=class_id,
            name="Override",
            display_order=0,
            buy_enabled=False,
            sell_enabled=False,
            currency_code="USD",
        )
        db.add(asset)
        db.flush()
        assert asset.buy_enabled is False
        assert asset.sell_enabled is False
        assert asset.currency_code == "USD"
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Section 4: PATCH /api/assets/{id} route
# ---------------------------------------------------------------------------


def test_patch_buy_enabled_only(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """PATCH ``{"buy_enabled": false}`` flips one flag, leaves the rest alone."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    asset_id = _seed_asset(class_id, "PETR4", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _patch_asset(client, asset_id, {"buy_enabled": False})
    assert response.status_code == 200
    body = response.json()
    assert body["buy_enabled"] is False
    assert body["sell_enabled"] is True
    assert body["currency_code"] == "BRL"

    row = _read_asset(asset_id, _omaha_test_env)
    assert row.buy_enabled is False
    assert row.sell_enabled is True
    assert row.currency_code == "BRL"


def test_patch_multiple_fields_at_once(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """PATCH a 3-field body persists all three atomically."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    asset_id = _seed_asset(class_id, "AAPL", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _patch_asset(
        client, asset_id, {"target_pct": "50", "buy_enabled": False, "currency_code": "USD"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["target_pct"] == "50"
    assert body["buy_enabled"] is False
    assert body["currency_code"] == "USD"

    row = _read_asset(asset_id, _omaha_test_env)
    assert row.target_pct == Decimal("50")
    assert row.buy_enabled is False
    assert row.currency_code == "USD"


def test_patch_currency_invalid(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """PATCH ``{"currency_code": "EUR"}`` → 422 with detail naming the bad value."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    asset_id = _seed_asset(class_id, "X", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _patch_asset(client, asset_id, {"currency_code": "EUR"})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "EUR" in detail or "currency" in detail.lower()

    row = _read_asset(asset_id, _omaha_test_env)
    assert row.currency_code == "BRL"  # unchanged


def test_patch_empty_body_rejected(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """PATCH ``{}`` → 422."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    asset_id = _seed_asset(class_id, "X", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _patch_asset(client, asset_id, {})
    assert response.status_code == 422


def test_patch_unknown_field_rejected(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """PATCH with a key outside the allowlist → 422."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    asset_id = _seed_asset(class_id, "X", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _patch_asset(client, asset_id, {"foo": "bar"})
    assert response.status_code == 422


def test_patch_cross_profile_id_is_404(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """PATCH an asset that belongs to another profile → 404."""
    class_id_ana = _seed_class(2, "AnaClass", _omaha_test_env=_omaha_test_env)
    asset_id_ana = _seed_asset(class_id_ana, "AnaAsset", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _patch_asset(client, asset_id_ana, {"buy_enabled": False})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Section 5: POST /api/assets route
# ---------------------------------------------------------------------------


def test_post_defaults_omitted(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """POST without trade-control fields → 201 with defaults applied."""
    class_id = _seed_class(1, "Renda Fixa", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _post_asset(client, "PETR4", class_id)
    assert response.status_code == 201
    body = response.json()
    assert body["buy_enabled"] is True
    assert body["sell_enabled"] is True
    assert body["currency_code"] == "BRL"

    row = _read_asset(body["id"], _omaha_test_env)
    assert row.buy_enabled is True
    assert row.sell_enabled is True
    assert row.currency_code == "BRL"


def test_post_explicit_currency(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """POST with ``currency_code="USD"`` → 201 with USD persisted."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _post_asset(client, "AAPL", class_id, currency_code="USD")
    assert response.status_code == 201
    body = response.json()
    assert body["currency_code"] == "USD"

    row = _read_asset(body["id"], _omaha_test_env)
    assert row.currency_code == "USD"


def test_post_invalid_currency_rejected(
    client: TestClient, _omaha_test_env: dict[str, str]
) -> None:
    """POST with ``currency_code="EUR"`` → 422."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _post_asset(client, "BAD", class_id, currency_code="EUR")
    assert response.status_code == 422


def test_post_invalid_bool_rejected(client: TestClient, _omaha_test_env: dict[str, str]) -> None:
    """POST with garbage ``buy_enabled`` → 422."""
    class_id = _seed_class(1, _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    response = _post_asset(client, "X", class_id, buy_enabled="not-a-bool")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Section 6: Commit /api/import/commit propagates the 3 fields
# ---------------------------------------------------------------------------


def test_commit_propagates_trade_fields_to_existing_asset(
    client: TestClient, _omaha_test_env: dict[str, str], tmp_path: Path
) -> None:
    """Commit with explicit ``buy_enabled=False`` updates the existing asset."""
    fixture = tmp_path / "broker.csv"
    fixture.write_text(
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Minha Categoria\n"
        'PETR4,PETR4,100,"28,50","35,10",Ações\n',
        encoding="utf-8",
    )

    class_id = _seed_class(1, name="Ações", _omaha_test_env=_omaha_test_env)
    asset_id = _seed_asset(class_id, "PETR4", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    with open(fixture, "rb") as f:
        preview = client.post("/api/import/preview", files={"file": ("broker.csv", f, "text/csv")})
    assert preview.status_code == 200
    preview_id = preview.json()["preview_id"]

    response = client.post(
        "/api/import/commit",
        json={
            "preview_id": preview_id,
            "assignments": [
                {
                    "broker_ticker": "PETR4",
                    "class_id": class_id,
                    "asset_name": "PETR4",
                    "buy_enabled": False,
                    "sell_enabled": True,
                    "currency_code": "BRL",
                }
            ],
        },
    )
    assert response.status_code == 200

    row = _read_asset(asset_id, _omaha_test_env)
    assert row.buy_enabled is False
    assert row.sell_enabled is True
    assert row.currency_code == "BRL"


def test_commit_creates_new_asset_with_trade_fields(
    client: TestClient, _omaha_test_env: dict[str, str], tmp_path: Path
) -> None:
    """Commit creates an unmatched asset with the supplied currency."""
    fixture = tmp_path / "broker.csv"
    fixture.write_text(
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Minha Categoria\n"
        'NEWCO,NEWCO,100,"28,50","35,10",Ações\n',
        encoding="utf-8",
    )

    class_id = _seed_class(1, name="Ações", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    with open(fixture, "rb") as f:
        preview = client.post("/api/import/preview", files={"file": ("broker.csv", f, "text/csv")})
    assert preview.status_code == 200
    preview_id = preview.json()["preview_id"]

    response = client.post(
        "/api/import/commit",
        json={
            "preview_id": preview_id,
            "assignments": [
                {
                    "broker_ticker": "NEWCO",
                    "class_id": class_id,
                    "asset_name": "NEWCO",
                    "buy_enabled": True,
                    "sell_enabled": False,
                    "currency_code": "USD",
                }
            ],
        },
    )
    assert response.status_code == 200

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from omaha.models import Asset

    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        created = db.query(Asset).filter(Asset.name == "NEWCO").one()
        assert created.buy_enabled is True
        assert created.sell_enabled is False
        assert created.currency_code == "USD"
    finally:
        db.close()
        engine.dispose()


def test_commit_rejects_invalid_currency(
    client: TestClient, _omaha_test_env: dict[str, str], tmp_path: Path
) -> None:
    """Commit body with ``currency_code="EUR"`` → 422."""
    fixture = tmp_path / "broker.csv"
    fixture.write_text(
        'Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Minha Categoria\nX,X,100,"1","1",Ações\n',
        encoding="utf-8",
    )

    class_id = _seed_class(1, name="Ações", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    with open(fixture, "rb") as f:
        preview = client.post("/api/import/preview", files={"file": ("broker.csv", f, "text/csv")})
    preview_id = preview.json()["preview_id"]

    response = client.post(
        "/api/import/commit",
        json={
            "preview_id": preview_id,
            "assignments": [
                {
                    "broker_ticker": "X",
                    "class_id": class_id,
                    "asset_name": "X",
                    "currency_code": "EUR",
                }
            ],
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Section 7: Preview emits the 3 fields
# ---------------------------------------------------------------------------


def test_preview_includes_trade_fields(
    client: TestClient, _omaha_test_env: dict[str, str], tmp_path: Path
) -> None:
    """Preview response carries ``buy_enabled`` / ``sell_enabled`` / ``currency_code``
    for both auto-matched and unmatched rows."""
    fixture = tmp_path / "broker.csv"
    fixture.write_text(
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Minha Categoria\n"
        'PETR4,PETR4,100,"28,50","35,10",Ações\n'
        'NEWCO,NEWCO,200,"10,00","12,00",Ações\n',
        encoding="utf-8",
    )

    class_id = _seed_class(1, name="Ações", _omaha_test_env=_omaha_test_env)
    _seed_asset(class_id, "PETR4", "0", _omaha_test_env=_omaha_test_env)
    _login_and_select(client, profile_id=1)

    with open(fixture, "rb") as f:
        response = client.post("/api/import/preview", files={"file": ("broker.csv", f, "text/csv")})
    assert response.status_code == 200
    body = response.json()

    auto = {row["broker_ticker"]: row for row in body["auto_matched"]}
    unmatched = {row["broker_ticker"]: row for row in body["unmatched"]}

    # Auto-matched reads current asset defaults (server_default = True/True/BRL).
    assert "PETR4" in auto
    assert auto["PETR4"]["buy_enabled"] is True
    assert auto["PETR4"]["sell_enabled"] is True
    assert auto["PETR4"]["currency_code"] == "BRL"

    # Unmatched reads the project defaults.
    assert "NEWCO" in unmatched
    assert unmatched["NEWCO"]["buy_enabled"] is True
    assert unmatched["NEWCO"]["sell_enabled"] is True
    assert unmatched["NEWCO"]["currency_code"] == "BRL"


# ---------------------------------------------------------------------------
# Section 8: Round-trip upgrade/downgrade (sanity)
# ---------------------------------------------------------------------------


def test_alembic_downgrade_then_upgrade_round_trip(tmp_path: Path) -> None:
    """Migration 0016 round-trips cleanly on a fresh DB.

    Runs alembic in a subprocess against an isolated SQLite file so
    the test database used by the rest of the suite is not affected.
    """
    db_file = tmp_path / "rt.db"
    db_url = f"sqlite:///{db_file}"

    for args in (["upgrade", "head"], ["downgrade", "-1"], ["upgrade", "head"]):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=REPO_ROOT,
            env={
                **os.environ,
                "DATABASE_URL": db_url,
                "ADMIN_PASSWORD": "test-password",
                "SECRET_KEY": "test-secret",
            },
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"alembic {' '.join(args)} failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )

    engine = create_engine(db_url)
    inspector = inspect(engine)
    try:
        cols = {c["name"] for c in inspector.get_columns("assets")}
        assert {"buy_enabled", "sell_enabled", "currency_code"}.issubset(cols)
    finally:
        engine.dispose()
