"""Per-layer unit tests for ``scripts.seed_from_csv.validation``.

Covers ``validate()`` over pre-built ``ClassRow`` / ``AssetRow`` /
``PositionRow`` lists. No DB; pure-function tests.

Pinned regression cases (one assertion per cross-reference rule):

* asset referencing a missing class → aborts with line number;
* position referencing a missing asset → aborts with line number;
* class sum violation → ``Falta X%`` / ``Sobra X%``;
* per-class asset sum violation → ``<class>: Falta X%``.
"""

from __future__ import annotations

from decimal import Decimal

import pytest


@pytest.fixture()
def _suppress_sys_exit(monkeypatch: pytest.MonkeyPatch):
    """Capture the abort message instead of exiting.

    The package's ``abort()`` calls ``sys.exit(1)``; we replace it
    with a raising helper so the test can inspect the message and
    continue. The original is restored after the test.

    Patches both ``loaders.abort`` (canonical) and
    ``validation.abort`` (the binding ``validation.py`` actually
    invokes — it imported the symbol at module load).
    """
    from scripts.seed_from_csv import loaders, validation

    captured: list[str] = []

    def fake_abort(message: str) -> None:
        captured.append(message)
        raise SystemExit(1)

    monkeypatch.setattr(loaders, "abort", fake_abort)
    monkeypatch.setattr(validation, "abort", fake_abort)
    return captured


def _class(name: str, target_pct: str, line_no: int = 2):
    from scripts.seed_from_csv.loaders import ClassRow

    return ClassRow(
        name=name,
        target_pct=Decimal(target_pct),
        display_order=line_no,
        quote_kind="manual",
        line_no=line_no,
    )


def _asset(class_name: str, name: str, target_pct: str, line_no: int = 2):
    from scripts.seed_from_csv.loaders import AssetRow

    return AssetRow(
        class_name=class_name,
        name=name,
        target_pct=Decimal(target_pct),
        display_order=line_no,
        buy_enabled=True,
        sell_enabled=True,
        currency_code="BRL",
        line_no=line_no,
    )


def _position(asset_name: str, broker_ticker: str = "T", line_no: int = 2):
    from scripts.seed_from_csv.loaders import PositionRow

    return PositionRow(
        asset_name=asset_name,
        broker_ticker=broker_ticker,
        qty=Decimal("1"),
        avg_price=Decimal("1"),
        current_price=Decimal("1"),
        total_invested=Decimal("1"),
        total_current=Decimal("1"),
        line_no=line_no,
    )


# ---------------------------------------------------------------------------
# Cross-references
# ---------------------------------------------------------------------------


def test_validate_aborts_on_asset_referencing_missing_class(_suppress_sys_exit) -> None:
    from scripts.seed_from_csv.validation import validate

    classes = [_class("RF", "100.00")]
    assets = [_asset("RV", "X", "100.00", line_no=5)]  # RV not in classes

    with pytest.raises(SystemExit):
        validate("italo", classes, assets, [])

    msg = _suppress_sys_exit[0]
    assert "asset 'X'" in msg
    assert "missing class 'RV'" in msg
    assert ":5" in msg  # line number


def test_validate_aborts_on_position_referencing_missing_asset(_suppress_sys_exit) -> None:
    from scripts.seed_from_csv.validation import validate

    classes = [_class("RF", "100.00")]
    assets = [_asset("RF", "Y", "100.00")]
    positions = [_position("Z", line_no=7)]  # Z not in assets

    with pytest.raises(SystemExit):
        validate("italo", classes, assets, positions)

    msg = _suppress_sys_exit[0]
    assert "position references missing asset 'Z'" in msg
    assert ":7" in msg  # line number


def test_validate_aborts_on_duplicate_position_pair(_suppress_sys_exit) -> None:
    from scripts.seed_from_csv.validation import validate

    classes = [_class("RF", "100.00")]
    assets = [_asset("RF", "Y", "100.00")]
    positions = [
        _position("Y", broker_ticker="T", line_no=3),
        _position("Y", broker_ticker="T", line_no=4),  # duplicate
    ]

    with pytest.raises(SystemExit):
        validate("italo", classes, assets, positions)

    msg = _suppress_sys_exit[0]
    assert "duplicate (asset_name, broker_ticker)" in msg
    assert ":4" in msg  # line number of second occurrence


# ---------------------------------------------------------------------------
# Sum invariants
# ---------------------------------------------------------------------------


def test_validate_aborts_on_class_sum_violation_short(_suppress_sys_exit) -> None:
    from scripts.seed_from_csv.validation import validate

    # 99% across classes — "Falta 1.00%"
    classes = [_class("RF", "60.00"), _class("RV", "39.00")]
    assets: list = []
    positions: list = []

    with pytest.raises(SystemExit):
        validate("italo", classes, assets, positions)

    msg = _suppress_sys_exit[0]
    assert "class sum invalid" in msg
    assert "Falta" in msg or "Sobra" in msg


def test_validate_aborts_on_class_sum_violation_over(_suppress_sys_exit) -> None:
    from scripts.seed_from_csv.validation import validate

    # 101% across classes — "Sobra 1.00%"
    classes = [_class("RF", "60.00"), _class("RV", "41.00")]

    with pytest.raises(SystemExit):
        validate("italo", classes, [], [])

    msg = _suppress_sys_exit[0]
    assert "class sum invalid" in msg
    assert "Sobra" in msg


def test_validate_aborts_on_per_class_asset_sum_violation(_suppress_sys_exit) -> None:
    from scripts.seed_from_csv.validation import validate

    classes = [_class("RF", "100.00")]
    # RF assets sum to 90% — "Falta 10.00%"
    assets = [
        _asset("RF", "X", "60.00", line_no=2),
        _asset("RF", "Y", "30.00", line_no=3),
    ]

    with pytest.raises(SystemExit):
        validate("italo", classes, assets, [])

    msg = _suppress_sys_exit[0]
    assert "'RF':" in msg or "RF" in msg
    assert "Falta" in msg or "Sobra" in msg


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_validate_accepts_consistent_triplet() -> None:
    """A well-formed triplet returns without aborting."""
    from scripts.seed_from_csv.validation import validate

    classes = [_class("RF", "60.00"), _class("RV", "40.00")]
    assets = [
        _asset("RF", "X", "100.00", line_no=2),
        _asset("RV", "Y", "100.00", line_no=3),
    ]
    positions = [_position("X"), _position("Y")]

    # No SystemExit → no abort
    validate("italo", classes, assets, positions)
