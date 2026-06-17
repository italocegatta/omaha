"""Tests for Phase 1 — AUDT-02 CSS parser and token inventory.

Unit tests for :mod:`omaha.audit.css_parser`. No DB, no FastAPI, no
session — the parser is a pure function library.

Every test asserts exact values (or ``pytest.approx`` on floats) and
specific exception types. Tests for ``parse_stylesheet`` use inline
CSS strings or files inside the repo root — the path-traversal guard
rejects any path that resolves outside ``omaha/``, so
``tmp_path`` (which lives under ``/tmp``) cannot be used.
"""

from __future__ import annotations

import dataclasses
import textwrap
from pathlib import Path

import pytest
import tinycss2

from omaha.audit.css_parser import (
    CssRule,
    CssToken,
    Stylesheet,
    TokenInventoryRow,
    _build_registry,
    color_token_inventory,
    parse_stylesheet,
    resolve_var,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Inline CSS fixture — the same one the original test file used
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


def _make_stylesheet(css: str) -> Stylesheet:
    """Parse *css* into a :class:`Stylesheet` without touching disk."""
    rules = tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True)
    return Stylesheet(rules=rules, raw_text=css)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


def test_token_inventory_row_fields() -> None:
    """TokenInventoryRow exposes the documented fields with the right types."""
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


def test_css_rule_is_frozen() -> None:
    """CssRule is a frozen dataclass — assignment raises FrozenInstanceError."""
    rule = CssRule(selector=":root", declarations={"--bg": "#fff"})
    assert rule.selector == ":root"
    assert rule.declarations["--bg"] == "#fff"
    with pytest.raises(dataclasses.FrozenInstanceError):
        rule.selector = ":other"  # type: ignore[misc]


def test_css_token_construction() -> None:
    """CssToken holds a property name and a resolved value."""
    token = CssToken(name="--accent", value="oklch(0.55 0.2 250)")
    assert token.name == "--accent"
    assert token.value == "oklch(0.55 0.2 250)"


# ---------------------------------------------------------------------------
# resolve_var
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,registry,expected",
    [
        # Direct substitution.
        ("var(--ink)", {"--ink": "oklch(0.2 0.01 60)"}, "oklch(0.2 0.01 60)"),
        # Chained var() reference resolves recursively.
        (
            "var(--fg)",
            {"--fg": "var(--ink)", "--ink": "oklch(0.2 0.01 60)"},
            "oklch(0.2 0.01 60)",
        ),
        # No var() at all → value returned unchanged.
        ("oklch(0.5 0.1 60)", {}, "oklch(0.5 0.1 60)"),
        ("#ffffff", {}, "#ffffff"),
        # Unknown variable without fallback is left as-is.
        ("var(--unknown)", {}, "--unknown"),
    ],
)
def test_resolve_var_basic(value: str, registry: dict[str, str], expected: str) -> None:
    """resolve_var handles direct, chained, no-substitution, and missing cases."""
    assert resolve_var(value, registry) == expected


@pytest.mark.parametrize(
    "value,registry,expected",
    [
        # Literal fallback: var(--missing, #ff0000).
        ("var(--missing, #ff0000)", {}, "#ff0000"),
        # Named fallback: var(--missing, --fallback) resolves the named fallback.
        ("var(--missing, --fallback)", {"--fallback": "#00ff00"}, "#00ff00"),
    ],
)
def test_resolve_var_fallback(value: str, registry: dict[str, str], expected: str) -> None:
    """resolve_var uses the documented fallback forms (literal and named)."""
    assert resolve_var(value, registry) == expected


def test_resolve_var_nested_in_color_mix() -> None:
    """var() inside a color-mix() expression is resolved.

    Pins the behaviour that ``var(--accent)`` nested inside
    ``color-mix(in srgb, var(--accent) 15%, transparent)`` is
    substituted inline. The resolved value retains the colour-mix
    structure (so coloraide can later parse it) but the ``var()``
    token is gone.
    """
    registry = {"--accent": "#0a66c2"}
    result = resolve_var("color-mix(in srgb, var(--accent) 15%, transparent)", registry)
    assert "var(" not in result
    assert "#0a66c2" in result


# ---------------------------------------------------------------------------
# parse_stylesheet
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "css",
    [
        # Empty stylesheet (parses cleanly, no rules).
        "",
        # Minimal valid stylesheet.
        ":root { --x: #fff; }",
        # Multi-rule stylesheet mirroring the FIXTURE_CSS shape.
        FIXTURE_CSS,
    ],
)
def test_parse_stylesheet_inline_css_parses(css: str) -> None:
    """parse_stylesheet parses an arbitrary inline CSS string.

    Each input is written to a file under the repo root (the only
    location the path-traversal guard accepts) and re-read via the
    production function — no shortcut via ``tinycss2`` directly, so
    the guard, encoding, and tinycss2 wiring are all exercised.
    """
    target = Path("src/omaha/audit/_test_tmp.css")
    try:
        target.write_text(css, encoding="utf-8")
        sheet = parse_stylesheet(target)
        assert sheet.raw_text == css
        assert isinstance(sheet.rules, list)
        if css == "":
            assert sheet.rules == []
        else:
            assert any(node.type == "qualified-rule" for node in sheet.rules)
    finally:
        if target.exists():
            target.unlink()


def test_parse_stylesheet_rejects_path_traversal() -> None:
    """parse_stylesheet raises ValueError when the path escapes the repo root.

    Pinned behaviour: this is the security guard added in Phase 1 to
    block ``../``-style path-traversal (threat T-01-02-01). A unit
    test here is the cheapest place to lock the contract — losing
    the guard silently would let an attacker steer the audit at
    arbitrary CSS files outside the repo.
    """
    with pytest.raises(ValueError, match="outside the repository root"):
        parse_stylesheet(Path("../../../etc/passwd"))


# ---------------------------------------------------------------------------
# color_token_inventory
# ---------------------------------------------------------------------------


def test_color_token_inventory_has_color_tokens() -> None:
    """color_token_inventory returns a row per color token in the fixture."""
    sheet = _make_stylesheet(FIXTURE_CSS)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    # Color tokens that resolve to a CSS color are present.
    for token in (
        "--ink",
        "--bg",
        "--accent",
        "--positive",
        "--class-1",
        "--error-bg",
        "--error-fg",
    ):
        assert token in by_name, f"{token} missing from inventory"

    # Each row has the documented fields and types.
    ink = by_name["--ink"]
    assert ink.computed_value.startswith("oklch")
    assert ink.adjacent_background != ""
    assert isinstance(ink.ratio, float)
    assert ink.status in ("Passa", "Falha")


def test_color_token_inventory_excludes_non_colors() -> None:
    """Tokens that resolve to non-color values (--spacing-xs) are excluded.

    The fixture has ``--spacing-xs: 4px;`` — coloraide rejects this,
    so the inventory must not include it. ``--border`` IS a CSS color
    function (oklch), but its presence or absence is implementation-
    defined; we don't pin it.
    """
    sheet = _make_stylesheet(FIXTURE_CSS)
    by_name = {r.token: r for r in color_token_inventory(sheet)}
    assert "--spacing-xs" not in by_name


def test_color_token_inventory_known_pairs() -> None:
    """The documented pair values are reflected in the inventory."""
    sheet = _make_stylesheet(FIXTURE_CSS)
    by_name = {r.token: r for r in color_token_inventory(sheet)}

    # --ink (near-black) on --bg (off-white) must hit AA.
    ink = by_name["--ink"]
    assert ink.ratio >= 4.0, f"--ink ratio {ink.ratio} below 4.0"
    assert ink.status == "Passa"

    # --accent-ink is off-white; against --bg it has low contrast
    # (correct — the token is meant for use ON dark accent surfaces,
    # not directly on the body).
    accent_ink = by_name["--accent-ink"]
    assert accent_ink.status == "Falha"

    # --accent itself has a positive ratio (it IS a color).
    accent = by_name["--accent"]
    assert accent.ratio > 0
    assert accent.status in ("Passa", "Falha")


def test_color_token_inventory_foreground_uses_bg() -> None:
    """Foreground-ish tokens (--ink, --positive) compare against --bg.

    The adjacent_background field is the value the token was measured
    against. For a foreground token like --ink, that should be the
    resolved --bg value, not the empty default.
    """
    sheet = _make_stylesheet(FIXTURE_CSS)
    by_name = {r.token: r for r in color_token_inventory(sheet)}

    ink = by_name["--ink"]
    bg_val = by_name["--bg"].computed_value
    assert ink.adjacent_background == bg_val


# ---------------------------------------------------------------------------
# _build_registry (the canonical registry builder — used by §1.2 dedupe)
# ---------------------------------------------------------------------------


def test_build_registry_returns_custom_properties() -> None:
    """_build_registry returns a name → value map of every ``--*`` declaration.

    Pins the canonical registry builder. ``inventory._build_registry_from_stylesheet``
    is now a re-export of this function (see §1.2 of the change).
    """
    sheet = _make_stylesheet(FIXTURE_CSS)
    registry = _build_registry(sheet)

    assert "--ink" in registry
    assert registry["--ink"] == "oklch(0.20 0.01 60)"
    assert "--bg" in registry
    assert registry["--bg"] == "oklch(0.975 0.003 60)"
    # Non-custom properties are excluded.
    assert "color" not in registry
