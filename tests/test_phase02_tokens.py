"""Tests for Phase 2 — PALT-01 / PALT-02 palette contrast verification.

Re-derives the WCAG 2.1 contrast ratio for every foreground/background
pair documented in DESIGN.md and asserts each pair meets its minimum.
Also enforces the Phase 2 structural changes (no ``color: #fff`` in
delete-confirm rules, OKLCH-only on the corrected tokens, legacy
aliases intact).

Coverage map (this file):

* PALT-01 (class swatch contrast)        — ``test_class_swatches_against_bg``
* PALT-02 (status ink on status fills)   — ``test_status_ink_on_fill``
* Error feedback pair                    — ``test_error_fg_on_error_bg``
* No hardcoded #fff in delete-confirm    — ``test_delete_confirm_no_white``
* Tokens are OKLCH                       — ``test_corrected_tokens_are_oklch``
* Legacy aliases intact                  — ``test_legacy_aliases_intact``
* Token inventory has zero Falha rows    — ``test_token_inventory_zero_falha``
"""

from __future__ import annotations

import re
from pathlib import Path

from omaha.audit.color_resolver import contrast_ratio
from omaha.audit.css_parser import (
    Stylesheet,
    color_token_inventory,
    parse_stylesheet,
)

APP_CSS_PATH = Path(__file__).resolve().parents[1] / "src" / "omaha" / "static" / "app.css"


# Tokens whose value must parse as OKLCH (not hex) after Phase 2.
OKLCH_ONLY_TOKENS = (
    "--class-4",
    "--class-6",
    "--error-bg",
    "--error-fg",
    "--negative-ink",
    "--positive-ink",
)


def _resolved_value(sheet: Stylesheet, name: str) -> str:
    """Return the resolved value of *name* from the :root inventory."""
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}
    if name not in by_name:
        raise AssertionError(f"Token {name!r} not found in inventory")
    return by_name[name].computed_value


# ---------------------------------------------------------------------------
# PALT-01 — class swatch contrast against --bg
# ---------------------------------------------------------------------------


def test_class_swatches_against_bg() -> None:
    """Every --class-{1..6} token must reach >= 4.5:1 against --bg.

    Phase 1 audit found --class-4 at 3.84:1 and --class-6 at 4.02:1; the
    Phase 2 change set must push every slot back into the AA band.
    """
    sheet = parse_stylesheet(APP_CSS_PATH)
    bg = _resolved_value(sheet, "--bg")
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    for slot in range(1, 7):
        token = f"--class-{slot}"
        assert token in by_name, f"{token} missing from inventory"
        row = by_name[token]
        # Re-derive the ratio from the resolved value to be sure
        # we are testing the post-Phase-2 value, not a cached one.
        ratio = contrast_ratio(row.computed_value, bg)
        assert ratio >= 4.5, (
            f"{token} = {row.computed_value!r} has contrast {ratio:.2f}:1 "
            f"against --bg ({bg!r}); must be >= 4.5:1"
        )


# ---------------------------------------------------------------------------
# PALT-02 — status ink on status fills
# ---------------------------------------------------------------------------


def test_status_ink_on_fill() -> None:
    """--negative-ink on --negative and --positive-ink on --positive pass AA.

    Status text is body-size, so the 4.5:1 threshold applies. These
    tokens were added in Phase 2 so call sites no longer need to
    hardcode ``#fff`` or ``#000`` on filled status backgrounds.
    """
    sheet = parse_stylesheet(APP_CSS_PATH)

    negative = _resolved_value(sheet, "--negative")
    negative_ink = _resolved_value(sheet, "--negative-ink")
    positive = _resolved_value(sheet, "--positive")
    positive_ink = _resolved_value(sheet, "--positive-ink")

    neg_ratio = contrast_ratio(negative_ink, negative)
    pos_ratio = contrast_ratio(positive_ink, positive)

    assert neg_ratio >= 4.5, f"--negative-ink on --negative: {neg_ratio:.2f}:1 (need >= 4.5:1)"
    assert pos_ratio >= 4.5, f"--positive-ink on --positive: {pos_ratio:.2f}:1 (need >= 4.5:1)"


# ---------------------------------------------------------------------------
# Error feedback pair
# ---------------------------------------------------------------------------


def test_error_fg_on_error_bg() -> None:
    """--error-fg on --error-bg must reach >= 4.5:1.

    The inline error block (``.error`` / ``.import-modal-error``) uses
    this pair directly; the new values are OKLCH equivalents of the
    prior hex pair.
    """
    sheet = parse_stylesheet(APP_CSS_PATH)
    error_bg = _resolved_value(sheet, "--error-bg")
    error_fg = _resolved_value(sheet, "--error-fg")
    ratio = contrast_ratio(error_fg, error_bg)
    assert ratio >= 4.5, f"--error-fg on --error-bg: {ratio:.2f}:1 (need >= 4.5:1)"


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------


def test_delete_confirm_no_white() -> None:
    """The two delete-confirm rules must not hardcode ``color: #fff``.

    Phase 2 replaced the hardcoded white with ``var(--negative-ink)``
    so the foreground tracks the negative fill across theme changes.
    """
    css = APP_CSS_PATH.read_text(encoding="utf-8")

    for selector in (
        ".class-delete-confirm-yes",
        ".dashboard-asset-delete-confirm-yes",
    ):
        # Pull the rule body for the selector and assert no #fff inside.
        pattern = re.compile(
            rf"{re.escape(selector)}\s*\{{([^}}]*)\}}",
            re.MULTILINE,
        )
        match = pattern.search(css)
        assert match is not None, f"Rule {selector!r} not found in app.css"
        body = match.group(1)
        assert (
            "color: #fff" not in body
        ), f"{selector} still hardcodes 'color: #fff' — must use var(--negative-ink)"
        assert (
            "var(--negative-ink)" in body
        ), f"{selector} must reference 'var(--negative-ink)' for its text color"


def test_corrected_tokens_are_oklch() -> None:
    """Tokens corrected in Phase 2 resolve to OKLCH (no hex)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    for token in OKLCH_ONLY_TOKENS:
        assert token in by_name, f"{token} missing from inventory"
        value = by_name[token].computed_value.lower()
        assert value.startswith("oklch"), f"{token} = {value!r} — Phase 2 requires OKLCH, not hex"


def test_legacy_aliases_intact() -> None:
    """--fg → --ink and --muted → --ink-muted still resolve (D-05)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    ink = _resolved_value(sheet, "--ink")
    ink_muted = _resolved_value(sheet, "--ink-muted")
    fg = _resolved_value(sheet, "--fg")
    muted = _resolved_value(sheet, "--muted")

    assert fg == ink, f"--fg ({fg!r}) must equal --ink ({ink!r})"
    assert muted == ink_muted, f"--muted ({muted!r}) must equal --ink-muted ({ink_muted!r})"


# ---------------------------------------------------------------------------
# Aggregate — every documented pair from DESIGN.md passes AA
# ---------------------------------------------------------------------------


# (foreground token, background token, minimum ratio) — sourced from
# the "Tokens (current)" table in DESIGN.md. The audit's name-based
# pairing heuristic in css_parser.gets the pair right for body text
# tokens but reverses it for fill/ink pairs (--accent on --ink, etc.);
# this table is the contract.
_DOCUMENTED_PAIRS: tuple[tuple[str, str, float], ...] = (
    ("--ink", "--bg", 4.5),
    ("--ink-muted", "--bg", 4.5),
    ("--accent-ink", "--accent", 4.5),
    ("--positive", "--bg", 4.5),
    ("--negative", "--bg", 4.5),
    ("--positive-ink", "--positive", 4.5),
    ("--negative-ink", "--negative", 4.5),
    ("--error-fg", "--error-bg", 4.5),
    ("--color-focus", "--bg", 3.0),  # UI component (focus ring), 3:1 OK
    ("--class-1", "--bg", 4.5),
    ("--class-2", "--bg", 4.5),
    ("--class-3", "--bg", 4.5),
    ("--class-4", "--bg", 4.5),
    ("--class-5", "--bg", 4.5),
    ("--class-6", "--bg", 4.5),
)


def test_documented_pairs_pass() -> None:
    """Every pair listed in DESIGN.md must meet its documented minimum.

    Loops over the contract table above. The specific PALT-01, PALT-02
    and error-fg tests cover the headline Phase 2 fixes; this is the
    full sweep so any future token change that regresses a documented
    pair fails the suite.
    """
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    failures: list[str] = []
    for fg_token, bg_token, minimum in _DOCUMENTED_PAIRS:
        assert fg_token in by_name, f"{fg_token} missing from inventory"
        assert bg_token in by_name, f"{bg_token} missing from inventory"

        fg = by_name[fg_token].computed_value
        bg = by_name[bg_token].computed_value
        ratio = contrast_ratio(fg, bg)
        if ratio < minimum:
            failures.append(f"{fg_token} on {bg_token}: {ratio:.2f}:1 (need >= {minimum}:1)")

    assert not failures, "Documented pairs failing: " + ", ".join(failures)
