"""Tests for Phase 1 — AUDT-02 CSS parser and token inventory.

Unit tests for :mod:`omaha.audit.css_parser`. No DB, no FastAPI, no
session — the parser is a pure function library.

Coverage map (this file):
* Package import              — ``test_audit_css_parser_importable``
* Stub symbols exist          — ``test_parse_stylesheet_sig``
* Dataclass construction      — ``test_token_inventory_row_fields``
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from omaha.audit import css_parser
from omaha.audit.css_parser import (
    CssRule,
    CssToken,
    TokenInventoryRow,
    Stylesheet,
    color_token_inventory,
    parse_stylesheet,
    resolve_var,
)


# ---------------------------------------------------------------------------
# Import / module shape
# ---------------------------------------------------------------------------


def test_audit_css_parser_importable() -> None:
    """The CSS parser module is importable after Task 2 stub creation."""
    assert css_parser is not None
    mod = importlib.import_module("omaha.audit.css_parser")
    assert mod.__doc__ is not None
    assert "from __future__" in Path(mod.__file__).read_text() if mod.__file__ else True


def test_parse_stylesheet_sig() -> None:
    """parse_stylesheet exists and accepts a Path argument."""
    assert callable(parse_stylesheet)


def test_resolve_var_sig() -> None:
    """resolve_var exists and accepts str + dict arguments."""
    result = resolve_var("var(--x)", {"--x": "red"})
    assert isinstance(result, str)


def test_color_token_inventory_sig() -> None:
    """color_token_inventory exists, accepts a Stylesheet, returns a list."""
    sheet = Stylesheet()
    rows = color_token_inventory(sheet)
    assert isinstance(rows, list)


def test_token_inventory_row_fields() -> None:
    """TokenInventoryRow exposes the fields described in the artifact spec."""
    row = TokenInventoryRow(
        token="--ink",
        computed_value="oklch(0.20 0.01 60)",
        adjacent_background="#ffffff",
        ratio=4.5,
        status="Passa",
    )
    assert row.token == "--ink"
    assert row.computed_value == "oklch(0.20 0.01 60)"
    assert row.adjacent_background == "#ffffff"
    assert row.ratio == 4.5
    assert row.status == "Passa"


def test_css_rule_construction() -> None:
    """CssRule is a frozen dataclass with selector + declarations."""
    rule = CssRule(selector=":root", declarations={"--bg": "#fff"})
    assert rule.selector == ":root"
    assert rule.declarations["--bg"] == "#fff"
    # frozen -> cannot reassign field, but dict contents are still mutable
    with pytest.raises(Exception):
        rule.declarations = {"--accent": "blue"}  # type: ignore[misc]


def test_css_token_construction() -> None:
    """CssToken holds a name and a resolved value."""
    token = CssToken(name="--accent", value="oklch(0.55 0.2 250)")
    assert token.name == "--accent"
    assert token.value == "oklch(0.55 0.2 250)"
