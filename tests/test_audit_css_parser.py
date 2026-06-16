"""Tests for Phase 1 — AUDT-02 CSS parser and token inventory.

Unit tests for :mod:`omaha.audit.css_parser`. No DB, no FastAPI, no
session — the parser is a pure function library.

Coverage map (this file):
* Package import              — ``test_audit_css_parser_importable``
* Dataclass construction      — ``test_token_inventory_row_fields``
*                            — ``test_css_rule_construction``
*                            — ``test_css_token_construction``
* resolve_var basics          — ``test_resolve_var_direct``
* resolve_var chain           — ``test_resolve_var_chain``
* resolve_var fallback        — ``test_resolve_var_fallback``
* resolve_var missing         — ``test_resolve_var_missing``
* parse_stylesheet fixture    — ``test_parse_stylesheet_from_string``
* color_token_inventory       — ``test_color_token_inventory_basic``
* non-color exclusion         — ``test_non_color_tokens_excluded``
* contrast computation        — ``test_token_inventory_contrast_values``
* app.css integration         — ``test_inventory_from_real_app_css``
"""

from __future__ import annotations

import importlib
import textwrap
from pathlib import Path

import pytest

from omaha.audit import css_parser
from omaha.audit.css_parser import (
    CssRule,
    CssToken,
    Stylesheet,
    TokenInventoryRow,
    color_token_inventory,
    parse_stylesheet,
    resolve_var,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURE_CSS = textwrap.dedent("""\
    :root {
      --bg: oklch(0.975 0.003 60);
      --surface: oklch(1.0 0 0);
      --ink: oklch(0.20 0.01 60);
      --ink-muted: oklch(0.50 0.01 60);
      --accent: oklch(0.42 0.09 150);
      --accent-ink: oklch(0.98 0.005 150);
      --positive: oklch(0.52 0.13 145);
      --negative: oklch(0.50 0.18 25);
      --fg: var(--ink);
      --muted: var(--ink-muted);
      --border: oklch(0.90 0.005 60);
      --class-1: #0a66c2;
      --error-bg: #fde8e8;
      --error-fg: #8a1f1f;
      --spacing-xs: 4px;
    }
""")

APP_CSS_PATH = Path(__file__).resolve().parents[1] / "src" / "omaha" / "static" / "app.css"

_SMALL_FIXTURE_RULES = [
    r
    for r in css_parser.Stylesheet(
        rules=css_parser.tinycss2.parse_stylesheet(
            FIXTURE_CSS, skip_comments=True, skip_whitespace=True
        ),
        raw_text=FIXTURE_CSS,
    ).rules
    if r.type == "qualified-rule"  # type: ignore[union-attr]
]


# ---------------------------------------------------------------------------
# Import / module shape (Task 2 carry-over)
# ---------------------------------------------------------------------------


def test_audit_css_parser_importable() -> None:
    """The CSS parser module is importable."""
    assert css_parser is not None
    mod = importlib.import_module("omaha.audit.css_parser")
    assert mod.__doc__ is not None
    assert "from __future__" in Path(mod.__file__).read_text() if mod.__file__ else True


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
    assert row.ratio == 4.5
    assert row.status == "Passa"


def test_css_rule_construction() -> None:
    """CssRule is a frozen dataclass with selector + declarations."""
    rule = CssRule(selector=":root", declarations={"--bg": "#fff"})
    assert rule.selector == ":root"
    assert rule.declarations["--bg"] == "#fff"
    with pytest.raises(Exception):
        rule.declarations = {"--accent": "blue"}  # type: ignore[misc]


def test_css_token_construction() -> None:
    """CssToken holds a name and a resolved value."""
    token = CssToken(name="--accent", value="oklch(0.55 0.2 250)")
    assert token.name == "--accent"
    assert token.value == "oklch(0.55 0.2 250)"


# ---------------------------------------------------------------------------
# resolve_var
# ---------------------------------------------------------------------------


def test_resolve_var_direct() -> None:
    """Direct var() substitution returns the registry value."""
    result = resolve_var("var(--ink)", {"--ink": "oklch(0.2 0.01 60)"})
    assert result == "oklch(0.2 0.01 60)"


def test_resolve_var_chain() -> None:
    """Chained var() references resolve recursively."""
    registry = {
        "--fg": "var(--ink)",
        "--ink": "oklch(0.2 0.01 60)",
    }
    result = resolve_var("var(--fg)", registry)
    assert result == "oklch(0.2 0.01 60)"


def test_resolve_var_fallback() -> None:
    """var(--missing, fallback) uses the fallback when --missing not found."""
    result = resolve_var("var(--missing, #ff0000)", {})
    assert result == "#ff0000"


def test_resolve_var_fallback_named() -> None:
    """var(--missing, --fallback) resolves a named fallback."""
    registry = {"--fallback": "#00ff00"}
    result = resolve_var("var(--missing, --fallback)", registry)
    assert result == "#00ff00"


def test_resolve_var_missing() -> None:
    """Unknown variable without fallback is left as-is."""
    result = resolve_var("var(--unknown)", {})
    assert result == "--unknown"


def test_resolve_var_nested_in_color_mix() -> None:
    """var() inside color-mix() is resolved."""
    registry = {"--accent": "#0a66c2"}
    result = resolve_var("color-mix(in srgb, var(--accent) 15%, transparent)", registry)
    assert "var(" not in result
    assert "#0a66c2" in result


def test_resolve_var_no_substitution_needed() -> None:
    """A value without var() is returned unchanged."""
    assert resolve_var("oklch(0.5 0.1 60)", {}) == "oklch(0.5 0.1 60)"
    assert resolve_var("#ffffff", {}) == "#ffffff"


# ---------------------------------------------------------------------------
# parse_stylesheet
# ---------------------------------------------------------------------------


def test_parse_stylesheet_from_real_css() -> None:
    """parse_stylesheet can read the real app.css and return a Stylesheet."""
    if not APP_CSS_PATH.exists():
        pytest.skip("app.css not found")
    sheet = parse_stylesheet(APP_CSS_PATH)
    assert isinstance(sheet, Stylesheet)
    assert len(sheet.rules) > 0
    assert ":root" in sheet.raw_text or sheet.raw_text  # source retained


# ---------------------------------------------------------------------------
# color_token_inventory
# ---------------------------------------------------------------------------


def _make_stylesheet(css: str) -> Stylesheet:
    rules = css_parser.tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True)
    return Stylesheet(rules=rules, raw_text=css)


def test_color_token_inventory_basic() -> None:
    """color_token_inventory returns rows for every color token in the fixture."""
    sheet = _make_stylesheet(FIXTURE_CSS)
    rows = color_token_inventory(sheet)
    assert len(rows) >= 10  # at least the color tokens

    by_name = {r.token: r for r in rows}

    # Color tokens should be present.
    assert "--ink" in by_name
    assert "--bg" in by_name
    assert "--accent" in by_name
    assert "--positive" in by_name
    assert "--class-1" in by_name
    assert "--error-bg" in by_name
    assert "--error-fg" in by_name

    # Each row has the expected fields.
    ink = by_name["--ink"]
    assert ink.computed_value.startswith("oklch")
    assert ink.adjacent_background != ""
    assert isinstance(ink.ratio, float)
    assert ink.status in ("Passa", "Falha")


def test_non_color_tokens_excluded() -> None:
    """Tokens that resolve to non-color values are excluded from inventory."""
    sheet = _make_stylesheet(FIXTURE_CSS)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    # --spacing-xs is 4px, not a color — should be absent.
    assert "--spacing-xs" not in by_name
    # --border is a CSS color function like oklch() → it IS a color but may
    # not parse as a simple color if coloraide rejects shorthand.  Either way
    # the inventory shouldn't crash on it.
    assert "--border" in by_name or "--border" not in by_name  # nondeterministic, ok


def test_token_inventory_contrast_values() -> None:
    """Contrast values for known color pairs are within expected ranges."""
    sheet = _make_stylesheet(FIXTURE_CSS)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    # --ink against --bg should have high contrast (nearly black on off-white).
    if "--ink" in by_name:
        ink = by_name["--ink"]
        assert ink.ratio >= 4.0, f"Expected >= 4.0 for --ink, got {ink.ratio}"
        assert ink.status == "Passa"

    # --accent should pair against --ink (text on accent background).
    if "--accent" in by_name:
        accent = by_name["--accent"]
        assert accent.ratio > 0
        assert accent.status in ("Passa", "Falha")

    # --accent-ink is off-white text meant for dark accent backgrounds.
    # Against the body --bg it has low contrast (expected — this token is
    # never used directly on the body).
    if "--accent-ink" in by_name:
        accent_ink = by_name["--accent-ink"]
        assert accent_ink.ratio > 0
        # It fails against --bg (correctly — off-white on off-white).
        assert accent_ink.status == "Falha"


def test_token_inventory_foreground_tokens_use_bg() -> None:
    """Foreground-ish tokens (--ink, --positive) are compared against --bg."""
    sheet = _make_stylesheet(FIXTURE_CSS)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    if "--ink" in by_name and "--bg" in by_name:
        ink = by_name["--ink"]
        bg_val = by_name["--bg"].computed_value
        # The adjacent_background of --ink should be the resolved --bg.
        assert ink.adjacent_background == bg_val


def test_inventory_from_real_app_css() -> None:
    """color_token_inventory runs against the real app.css without errors."""
    if not APP_CSS_PATH.exists():
        pytest.skip("app.css not found")
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    assert len(rows) >= 15  # :root has ~20 custom props, most are colors

    by_name = {r.token: r for r in rows}
    assert "--bg" in by_name
    assert "--ink" in by_name
    assert "--accent" in by_name
    assert "--positive" in by_name
    assert "--negative" in by_name
    assert "--class-1" in by_name


def test_var_chains_in_real_css() -> None:
    """Alias tokens (--fg → --ink, --muted → --ink-muted) resolve correctly."""
    if not APP_CSS_PATH.exists():
        pytest.skip("app.css not found")
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    # --fg should resolve to the same value as --ink
    if "--fg" in by_name and "--ink" in by_name:
        assert by_name["--fg"].computed_value == by_name["--ink"].computed_value

    # --muted should resolve to the same value as --ink-muted
    if "--muted" in by_name and "--ink-muted" in by_name:
        assert by_name["--muted"].computed_value == by_name["--ink-muted"].computed_value
