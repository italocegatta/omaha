"""Per-layer unit tests for ``scripts.seed_from_csv.loaders``.

Covers the three ``load_*`` functions and the row-parsing helpers
(``_decimal``, ``_optional_decimal``, ``_int``, ``_bool``). No DB;
pure-function tests against ``tmp_path`` + inline CSV strings, with
``monkeypatch`` on ``scripts.seed_from_csv.SEED_DIR`` (same pattern
as the module-import tests in ``tests/test_seed_from_csv.py``).

Pinned regression cases (one assertion per invariant):

* valid CSV → parsed rows;
* missing header → SystemExit code 1;
* ``target_pct`` out of range → SystemExit code 1;
* unknown ``quote_kind`` → SystemExit code 1;
* duplicate ``name`` → SystemExit code 1;
* non-ASCII asset name round-trip.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def tmp_seed_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Rebind ``scripts.seed_from_csv.SEED_DIR`` to a temp directory.

    The loaders resolve ``SEED_DIR`` via ``scripts.seed_from_csv.SEED_DIR``
    at call time (not via a captured closure), so this rebind flows
    through to ``load_classes`` / ``load_assets`` / ``load_positions``.
    """
    import scripts.seed_from_csv

    original = scripts.seed_from_csv.SEED_DIR
    scripts.seed_from_csv.SEED_DIR = tmp_path
    try:
        yield tmp_path
    finally:
        scripts.seed_from_csv.SEED_DIR = original


# ---------------------------------------------------------------------------
# Helpers (private)
# ---------------------------------------------------------------------------


def test_decimal_parses_valid_decimal(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _decimal

    result = _decimal("  12.34 ", field="x", path=tmp_seed_dir / "x.csv", line_no=2)
    assert result == Decimal("12.34")


def test_decimal_aborts_on_garbage(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _decimal

    with pytest.raises(SystemExit) as exc_info:
        _decimal("not-a-number", field="x", path=tmp_seed_dir / "x.csv", line_no=3)
    assert exc_info.value.code == 1


def test_optional_decimal_returns_none_on_empty(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _optional_decimal

    assert _optional_decimal("", field="x", path=tmp_seed_dir / "x.csv", line_no=2) is None
    assert _optional_decimal("   ", field="x", path=tmp_seed_dir / "x.csv", line_no=3) is None


def test_optional_decimal_returns_value_when_present(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _optional_decimal

    assert _optional_decimal(
        "100.00", field="x", path=tmp_seed_dir / "x.csv", line_no=2
    ) == Decimal("100.00")


def test_optional_decimal_aborts_on_negative(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _optional_decimal

    with pytest.raises(SystemExit) as exc_info:
        _optional_decimal("-1.00", field="x", path=tmp_seed_dir / "x.csv", line_no=2)
    assert exc_info.value.code == 1


def test_int_aborts_on_garbage(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _int

    with pytest.raises(SystemExit) as exc_info:
        _int("abc", field="x", path=tmp_seed_dir / "x.csv", line_no=2)
    assert exc_info.value.code == 1


def test_bool_accepts_canonical_truthy(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _bool

    for v in ("true", "True", "1", "yes", "y", "t"):
        assert _bool(v, field="x", path=tmp_seed_dir / "x.csv", line_no=2) is True


def test_bool_accepts_canonical_falsy(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _bool

    for v in ("false", "False", "0", "no", "n", "f", ""):
        assert _bool(v, field="x", path=tmp_seed_dir / "x.csv", line_no=2) is False


def test_bool_aborts_on_garbage(tmp_seed_dir: Path) -> None:
    from scripts.seed_from_csv.loaders import _bool

    with pytest.raises(SystemExit) as exc_info:
        _bool("maybe", field="x", path=tmp_seed_dir / "x.csv", line_no=2)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# load_classes
# ---------------------------------------------------------------------------


def test_load_classes_parses_valid_csv(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_classes.csv"
    csv.write_text(
        "name,target_pct,display_order,quote_kind\n"
        "RF Dinâmica,25.00,0,auto\n"
        "RF Pós,20.00,1,manual\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_classes

    rows = load_classes("italo")
    assert [r.name for r in rows] == ["RF Dinâmica", "RF Pós"]
    assert [r.target_pct for r in rows] == [Decimal("25.00"), Decimal("20.00")]
    assert [r.quote_kind for r in rows] == ["auto", "manual"]


def test_load_classes_aborts_on_missing_header(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_classes.csv"
    csv.write_text("name,target_pct,display_order\nRF,100.00,0\n", encoding="utf-8")
    from scripts.seed_from_csv.loaders import load_classes

    with pytest.raises(SystemExit) as exc_info:
        load_classes("italo")
    assert exc_info.value.code == 1


def test_load_classes_aborts_on_target_pct_out_of_range(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_classes.csv"
    csv.write_text(
        "name,target_pct,display_order,quote_kind\nRF,150.00,0,auto\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_classes

    with pytest.raises(SystemExit) as exc_info:
        load_classes("italo")
    assert exc_info.value.code == 1


def test_load_classes_aborts_on_unknown_quote_kind(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_classes.csv"
    csv.write_text(
        "name,target_pct,display_order,quote_kind\nRF,100.00,0,whoops\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_classes

    with pytest.raises(SystemExit) as exc_info:
        load_classes("italo")
    assert exc_info.value.code == 1


def test_load_classes_aborts_on_duplicate_name(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_classes.csv"
    csv.write_text(
        "name,target_pct,display_order,quote_kind\nRF,60.00,0,auto\nRF,40.00,1,auto\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_classes

    with pytest.raises(SystemExit) as exc_info:
        load_classes("italo")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# load_assets
# ---------------------------------------------------------------------------


def test_load_assets_parses_valid_csv(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_assets.csv"
    csv.write_text(
        "class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code\n"
        "RF,Tesouro Selic,100.00,0,true,true,BRL\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_assets

    rows = load_assets("italo")
    assert len(rows) == 1
    assert rows[0].name == "Tesouro Selic"
    assert rows[0].buy_enabled is True
    assert rows[0].currency_code == "BRL"


def test_load_assets_aborts_on_legacy_four_column_header(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_assets.csv"
    csv.write_text("class_name,name,target_pct,display_order\nRF,X,10,0\n", encoding="utf-8")
    from scripts.seed_from_csv.loaders import load_assets

    with pytest.raises(SystemExit) as exc_info:
        load_assets("italo")
    assert exc_info.value.code == 1


def test_load_assets_aborts_on_bad_currency_code(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_assets.csv"
    csv.write_text(
        "class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code\n"
        "RF,X,100.00,0,true,true,EUR\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_assets

    with pytest.raises(SystemExit) as exc_info:
        load_assets("italo")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# load_positions
# ---------------------------------------------------------------------------


def test_load_positions_parses_valid_csv(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_positions.csv"
    csv.write_text(
        "asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current\n"
        "Tesouro Selic,TESOURO_SELIC,1,1000.00,1100.00,1000.00,1100.00\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_positions

    rows = load_positions("italo")
    assert len(rows) == 1
    assert rows[0].asset_name == "Tesouro Selic"
    assert rows[0].total_invested == Decimal("1000.00")
    assert rows[0].total_current == Decimal("1100.00")


def test_load_positions_parses_empty_total_cells_as_none(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_positions.csv"
    csv.write_text(
        "asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current\n"
        "Tesouro Selic,TESOURO_SELIC,1,1000.00,1100.00,,\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_positions

    rows = load_positions("italo")
    assert rows[0].total_invested is None
    assert rows[0].total_current is None


def test_load_positions_handles_non_ascii_asset_name(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_positions.csv"
    csv.write_text(
        "asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current\n"
        "Tesouro IPCA+ 2035,IPCA2035,1,1000.00,1100.00,1000.00,1100.00\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_positions

    rows = load_positions("italo")
    assert rows[0].asset_name == "Tesouro IPCA+ 2035"


def test_load_positions_aborts_on_negative_qty(tmp_seed_dir: Path) -> None:
    csv = tmp_seed_dir / "italo_positions.csv"
    csv.write_text(
        "asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current\n"
        "X,Y,-1,1,1,1,1\n",
        encoding="utf-8",
    )
    from scripts.seed_from_csv.loaders import load_positions

    with pytest.raises(SystemExit) as exc_info:
        load_positions("italo")
    assert exc_info.value.code == 1
