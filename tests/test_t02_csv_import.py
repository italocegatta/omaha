"""Tests for T02: Pure CSV parser + 48-row synthetic fixture.

Unit tests for :mod:`omaha.csv_import`. No DB, no FastAPI, no
session — the parser is a pure function library and the tests pin
its observable contract.

Coverage map (all in this file):

* Header detection (Portuguese) — ``test_header_detection_portuguese``
* Header detection (English)   — ``test_header_detection_english``
* Banner-row skip              — ``test_banner_row_skipped``
* Positional fallback          — ``test_positional_fallback_no_header``
* Blank line skip              — ``test_blank_lines_skipped``
* Total footer skip            — ``test_total_footer_skipped``
* Empty-ticker skip            — ``test_empty_ticker_row_skipped``
* Brazilian number parse       — ``test_brazilian_number_parse``
* Plain US number parse        — ``test_plain_number_parse``
* Malformed row skipped        — ``test_malformed_row_skipped``
* Full 48-row fixture          — ``test_fixture_yields_48_positions``
* normalize_name canonical     — ``test_normalize_name_canonicalization``
* 43 auto / 5 unmatched        — ``test_match_positions_43_5_split``
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from omaha.csv_import import (
    MatchResult,
    RawPosition,
    match_positions,
    normalize_name,
    parse_positions,
    _parse_brazilian_number,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_broker.csv"
FIXTURE_TEXT = FIXTURE_PATH.read_text(encoding="utf-8")

# Names that the S04 plan calls out as the 5 "unmatched" rows. Every
# other name in the fixture has a corresponding fake asset in the
# matcher test.
UNMATCHED_NAMES = ["MXRF11", "BPAC11", "HGLG11", "XPLG11", "VINO11"]


# ---------------------------------------------------------------------------
# Header detection
# ---------------------------------------------------------------------------


def test_header_detection_portuguese() -> None:
    """Portuguese headers (Codigo, Ativo, Quantidade, Preco Medio, Preco Atual) are detected and consumed."""
    text = (
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\n"
        'PETR4,PETR4,100,"28,50","35,10"\n'
        'VALE3,VALE3,200,"65,20","72,40"\n'
    )
    positions = parse_positions(text)
    assert len(positions) == 2
    assert positions[0].broker_ticker == "PETR4"
    assert positions[0].avg_price == Decimal("28.50")
    assert positions[0].row_index == 2  # header is line 1


def test_header_detection_english() -> None:
    """English headers (Ticker, Name, Qty, Avg Price, Current Price) are also detected."""
    text = (
        "Ticker,Name,Qty,Avg Price,Current Price\n"
        "AAPL,AAPL,10,150.25,175.50\n"
        "MSFT,MSFT,5,300.10,420.80\n"
    )
    positions = parse_positions(text)
    assert len(positions) == 2
    assert positions[0].broker_ticker == "AAPL"
    assert positions[0].avg_price == Decimal("150.25")
    assert positions[1].broker_ticker == "MSFT"
    assert positions[1].current_price == Decimal("420.80")


# ---------------------------------------------------------------------------
# Banner row
# ---------------------------------------------------------------------------


def test_banner_row_skipped() -> None:
    """A leading row of non-numeric, non-label text is treated as a banner and skipped."""
    text = (
        '"Posição consolidada - 01/06/2026","Cliente: 12345"\n'
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\n"
        'PETR4,PETR4,100,"28,50","35,10"\n'
    )
    positions = parse_positions(text)
    assert len(positions) == 1
    assert positions[0].broker_ticker == "PETR4"
    # row_index 3: banner=1, header=2, data=3
    assert positions[0].row_index == 3


# ---------------------------------------------------------------------------
# Positional fallback
# ---------------------------------------------------------------------------


def test_positional_fallback_no_header() -> None:
    """When no header is detected, the first non-banner row is treated as data."""
    text = (
        'PETR4,PETR4,100,"28,50","35,10"\n'
        'VALE3,VALE3,200,"65,20","72,40"\n'
    )
    positions = parse_positions(text)
    assert len(positions) == 2
    assert positions[0].broker_ticker == "PETR4"
    assert positions[0].row_index == 1


# ---------------------------------------------------------------------------
# Blank lines, footer, empty-ticker
# ---------------------------------------------------------------------------


def test_blank_lines_skipped() -> None:
    """Blank lines anywhere in the file are silently skipped."""
    text = (
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\n"
        "\n"
        'PETR4,PETR4,100,"28,50","35,10"\n'
        "\n"
        "\n"
        'VALE3,VALE3,200,"65,20","72,40"\n'
    )
    positions = parse_positions(text)
    assert len(positions) == 2
    assert [p.broker_ticker for p in positions] == ["PETR4", "VALE3"]


def test_total_footer_skipped() -> None:
    """A 'Total' footer row at the bottom is consumed and not returned as a position."""
    text = (
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\n"
        'PETR4,PETR4,100,"28,50","35,10"\n'
        'Total,2 ativos,,,\n'
    )
    positions = parse_positions(text)
    assert len(positions) == 1
    assert positions[0].broker_ticker == "PETR4"


def test_empty_ticker_row_skipped() -> None:
    """A row with an empty ticker cell (a phantom/section divider) is skipped."""
    text = (
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\n"
        'PETR4,PETR4,100,"28,50","35,10"\n'
        ',Phantom Asset,10,"1,00","1,00"\n'
        'VALE3,VALE3,200,"65,20","72,40"\n'
    )
    positions = parse_positions(text)
    assert len(positions) == 2
    assert [p.broker_ticker for p in positions] == ["PETR4", "VALE3"]


# ---------------------------------------------------------------------------
# Number parsing
# ---------------------------------------------------------------------------


def test_brazilian_number_parse() -> None:
    """Brazilian '1.234,56' becomes Decimal('1234.56') — thousands dot + decimal comma."""
    assert _parse_brazilian_number("1.234,56") == Decimal("1234.56")
    assert _parse_brazilian_number("28,50") == Decimal("28.50")
    assert _parse_brazilian_number("R$ 990,92") == Decimal("990.92")
    assert _parse_brazilian_number('"1.234,56"') == Decimal("1234.56")


def test_plain_number_parse() -> None:
    """Plain US '1234.56' (no thousands separator) parses too."""
    assert _parse_brazilian_number("1234.56") == Decimal("1234.56")
    assert _parse_brazilian_number("0.50") == Decimal("0.50")


# ---------------------------------------------------------------------------
# Malformed row
# ---------------------------------------------------------------------------


def test_malformed_row_skipped() -> None:
    """A row whose numeric cells are not numbers is silently dropped — no exception bubbles."""
    text = (
        "Codigo,Ativo,Quantidade,Preco Medio,Preco Atual\n"
        'PETR4,PETR4,100,"28,50","35,10"\n'
        'BAD,BAD,abc,def,ghi\n'
        'VALE3,VALE3,200,"65,20","72,40"\n'
    )
    positions = parse_positions(text)
    # The malformed row is silently dropped; the two well-formed rows remain.
    assert len(positions) == 2
    assert [p.broker_ticker for p in positions] == ["PETR4", "VALE3"]


# ---------------------------------------------------------------------------
# Full fixture
# ---------------------------------------------------------------------------


def test_fixture_yields_48_positions() -> None:
    """The 48-row fixture (43 matched + 5 unmatched + 1 phantom + 1 footer + 1 banner + 1 header) yields exactly 48 RawPosition."""
    positions = parse_positions(FIXTURE_TEXT)
    assert len(positions) == 48
    # row_index 3 is the first data row (banner=1, header=2, data starts at 3)
    assert positions[0].row_index == 3
    assert positions[0].broker_ticker == "PETR4"
    # Last data row before the phantom/footer
    assert positions[-1].broker_ticker == "VINO11"


# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("PETR4", "petr4"),
        ("  PETR4  ", "petr4"),
        ("PETR4 ", "petr4"),
        ("Tesouro IPCA+ 2035", "tesouro ipca 2035"),
        ("TESOURO  IPCA  2035", "tesouro ipca 2035"),
        ("Préço Médio", "preco medio"),
        ("", ""),
    ],
)
def test_normalize_name_canonicalization(raw: str, expected: str) -> None:
    """normalize_name lower-cases, strips accents, drops punctuation, and collapses whitespace."""
    assert normalize_name(raw) == expected


# ---------------------------------------------------------------------------
# match_positions split
# ---------------------------------------------------------------------------


def test_match_positions_43_5_split() -> None:
    """With 43 assets matching the fixture's 43 matched names, the matcher splits 43 auto + 5 unmatched."""
    positions = parse_positions(FIXTURE_TEXT)
    assert len(positions) == 48

    # Build 43 fake assets: every fixture name EXCEPT the 5 declared unmatched.
    matched_names = [p.name for p in positions if p.name not in UNMATCHED_NAMES]
    assert len(matched_names) == 43
    assets = [
        SimpleNamespace(id=i + 1, name=name) for i, name in enumerate(matched_names)
    ]

    result = match_positions(positions, assets)
    assert isinstance(result, MatchResult)
    assert len(result.auto_matched) == 43
    assert len(result.unmatched) == 5

    # The 5 unmatched names are exactly the ones the plan called out.
    unmatched_names = {r.name for r in result.unmatched}
    assert unmatched_names == set(UNMATCHED_NAMES)

    # The auto_matched tuples carry the correct asset_id for each raw position.
    # Pick a few spot-checks:
    by_ticker = {r.broker_ticker: asset_id for r, asset_id in result.auto_matched}
    assert by_ticker["PETR4"] == 1
    assert by_ticker["Tesouro IPCA+ 2035"] == 43
