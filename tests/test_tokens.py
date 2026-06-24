"""Tests for Phase 2 — PALT-01 / PALT-02 palette contrast verification.

Unit tests for the per-class swatch and status-ink contrast contract.
The single ``test_documented_pairs_pass`` sweeps every (fg, bg)
pair documented in DESIGN.md against the live ``src/omaha/static/app.css``
— that test is marked ``@pytest.mark.integration`` and excluded
from the unit subset (``task test-unit``).

Structural checks that read the live CSS file directly (delete-confirm
rule body and OKLCH-only token shape) live in
``tests/audit_integration/test_app_css_shape.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from omaha.audit.color_resolver import contrast_ratio
from omaha.audit.css_parser import (
    Stylesheet,
    color_token_inventory,
    parse_stylesheet,
)

APP_CSS_PATH = Path(__file__).resolve().parents[1] / "src" / "omaha" / "static" / "app.css"

pytestmark = pytest.mark.unit


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


@pytest.mark.parametrize("slot", [1, 2, 3, 4, 5, 6])
def test_class_swatches_against_bg(slot: int) -> None:
    """Each ``--class-N`` token reaches >= 4.5:1 against ``--bg``.

    Phase 1 audit found ``--class-4`` at 3.84:1 and ``--class-6`` at
    4.02:1; Phase 2 pushed every slot back into the AA band.
    Parametrized over the six slots so a regression on any one
    produces a single targeted failure.
    """
    sheet = parse_stylesheet(APP_CSS_PATH)
    bg = _resolved_value(sheet, "--bg")
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    token = f"--class-{slot}"
    assert token in by_name, f"{token} missing from inventory"
    row = by_name[token]
    ratio = contrast_ratio(row.computed_value, bg)
    assert ratio >= 4.5, (
        f"{token} = {row.computed_value!r} has contrast {ratio:.2f}:1 "
        f"against --bg ({bg!r}); must be >= 4.5:1"
    )


# ---------------------------------------------------------------------------
# PALT-02 — status ink on status fills (split per sign for clarity)
# ---------------------------------------------------------------------------


def test_positive_ink_on_positive_passes_aa() -> None:
    """``--positive-ink`` on ``--positive`` must reach 4.5:1 (body-size text)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    positive = _resolved_value(sheet, "--positive")
    positive_ink = _resolved_value(sheet, "--positive-ink")
    ratio = contrast_ratio(positive_ink, positive)
    assert ratio >= 4.5, f"--positive-ink on --positive: {ratio:.2f}:1 (need >= 4.5:1)"


def test_negative_ink_on_negative_passes_aa() -> None:
    """``--negative-ink`` on ``--negative`` must reach 4.5:1 (body-size text)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    negative = _resolved_value(sheet, "--negative")
    negative_ink = _resolved_value(sheet, "--negative-ink")
    ratio = contrast_ratio(negative_ink, negative)
    assert ratio >= 4.5, f"--negative-ink on --negative: {ratio:.2f}:1 (need >= 4.5:1)"


# ---------------------------------------------------------------------------
# Error feedback pair
# ---------------------------------------------------------------------------


def test_error_fg_on_error_bg_passes_aa() -> None:
    """``--error-fg`` on ``--error-bg`` must reach 4.5:1.

    The inline ``.error`` / ``.import-modal-error`` block uses this
    pair directly; Phase 2 replaced the prior hex pair with OKLCH
    equivalents.
    """
    sheet = parse_stylesheet(APP_CSS_PATH)
    error_bg = _resolved_value(sheet, "--error-bg")
    error_fg = _resolved_value(sheet, "--error-fg")
    ratio = contrast_ratio(error_fg, error_bg)
    assert ratio >= 4.5, f"--error-fg on --error-bg: {ratio:.2f}:1 (need >= 4.5:1)"


# ---------------------------------------------------------------------------
# Legacy aliases intact (D-05)
# ---------------------------------------------------------------------------


def test_legacy_aliases_intact() -> None:
    """``--fg → --ink`` and ``--muted → --ink-muted`` still resolve.

    Pins the alias contract from D-05. Both aliases must resolve to
    exactly the same colour value as the canonical token, not just
    any passing contrast.
    """
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


@pytest.mark.integration
def test_documented_pairs_pass() -> None:
    """Every pair listed in DESIGN.md must meet its documented minimum.

    Loops over the contract table above — the only test in this file
    that loops over many pairs and is allowed to read the live
    ``src/omaha/static/app.css``.  The specific class-swatch and
    status-ink tests above cover the headline Phase 2 fixes; this
    sweep catches any future token change that regresses a documented
    pair.
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
