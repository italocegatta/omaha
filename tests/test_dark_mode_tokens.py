"""Tests for F05 — dark mode palette swap.

Replaces ``tests/test_tokens.py`` (formerly "Phase 2 — PALT-01 /
PALT-02 palette contrast verification") with the dark-mode contract.
Same parsers (``omaha.audit.css_parser``, ``omaha.audit.color_resolver``);
new token values calibrated against the dark warm-neutral surface
(``--bg: oklch(0.18 0.01 60)``, hue 60, D-F05.1).

Each test reads the live ``src/omaha/static/app.css`` so the test
suite is the contract — any regression lands as a failing
``test_*`` call rather than a delayed visual surprise.

Structural checks (delete-confirm rule body, OKLCH-only token shape)
live in ``tests/audit_integration/test_app_css_shape.py``.
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


def _resolved_value(sheet: Stylesheet, name: str) -> str:
    """Return the resolved value of *name* from the :root inventory."""
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}
    if name not in by_name:
        raise AssertionError(f"Token {name!r} not found in inventory")
    return by_name[name].computed_value


# ---------------------------------------------------------------------------
# F05 D-F05.1 — body background renders as dark warm-neutral
# ---------------------------------------------------------------------------


def test_body_bg_is_dark_warm_neutral() -> None:
    """``--bg`` SHALL resolve to dark warm-neutral (NOT pure black, NOT cold).

    Scenario from ``color-tokens`` spec: "Body background renders as
    dark warm-neutral". F05 D-F05.1 sets the target to
    ``oklch(L≈0.18 hue≈60 chroma≈0.01)``. Tolerance: lightness in
    [0.14, 0.22], hue in [40, 80], chroma ≤ 0.02.
    """
    from coloraide import Color

    bg = _resolved_value(parse_stylesheet(APP_CSS_PATH), "--bg")
    color = Color(bg).convert("oklch")
    coords = color.coords()
    L, C, H = coords[0], coords[1], coords[2]
    assert 0.14 <= L <= 0.22, f"--bg lightness {L:.3f} not in [0.14, 0.22]"
    assert C <= 0.02, f"--bg chroma {C:.3f} > 0.02 (must stay neutral)"
    # hue is undefined when chroma == 0; treat that as passing the warmth constraint
    if C > 0:
        # coloraide returns hue in [0, 360); collapse to nearest equivalent
        hue = H % 360
        warm = min(hue, 360 - hue) if abs(hue - 60) > 180 else abs(hue - 60)
        assert warm <= 20, f"--bg hue {hue:.1f} not within 20° of 60 (warm-neutral)"


# ---------------------------------------------------------------------------
# F05 D-F05.1 / D-F05.3 — body text contrasts against --bg
# ---------------------------------------------------------------------------


def test_ink_on_bg_passes_aa() -> None:
    """``--ink`` on ``--bg`` must reach 4.5:1 (body text)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    bg = _resolved_value(sheet, "--bg")
    ink = _resolved_value(sheet, "--ink")
    ratio = contrast_ratio(ink, bg)
    assert ratio >= 4.5, f"--ink on --bg: {ratio:.2f}:1 (need >= 4.5:1)"


def test_ink_muted_on_bg_passes_aa() -> None:
    """``--ink-muted`` on ``--bg`` must reach 4.5:1 (secondary text)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    bg = _resolved_value(sheet, "--bg")
    ink_muted = _resolved_value(sheet, "--ink-muted")
    ratio = contrast_ratio(ink_muted, bg)
    assert ratio >= 4.5, f"--ink-muted on --bg: {ratio:.2f}:1 (need >= 4.5:1)"


# ---------------------------------------------------------------------------
# F05 D-F05.4 — class swatch contrast and hue disambiguation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slot", [1, 2, 3, 4, 5, 6])
def test_class_swatches_against_bg(slot: int) -> None:
    """Each ``--class-N`` token reaches >= 4.5:1 against the dark ``--bg``."""
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
        f"against dark --bg ({bg!r}); must be >= 4.5:1"
    )


def test_class_2_hue_disambiguated_from_positive() -> None:
    """``--class-2`` SHALL be hue-shifted (≤ 135) to disambiguate from ``--positive`` (hue 145).

    Scenario from ``color-tokens`` spec: "Class swatch tokens meet
    body text contrast on dark surface". F05 D-F05.4 shifts
    ``--class-2`` from hue 145 to hue 130 so it doesn't collide
    visually with the gain indicator.
    """
    from coloraide import Color

    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}
    assert "--class-2" in by_name and "--positive" in by_name

    class_2_color = Color(by_name["--class-2"].computed_value).convert("oklch")
    positive_color = Color(by_name["--positive"].computed_value).convert("oklch")

    class_2_hue = class_2_color.coords()[2] % 360
    positive_hue = positive_color.coords()[2] % 360

    assert class_2_hue <= 135, (
        f"--class-2 hue {class_2_hue:.1f}° must be ≤ 135° (positive is {positive_hue:.1f}°)"
    )


# ---------------------------------------------------------------------------
# F05 D-F05.3 — status ink on status fills (lifted-lightness)
# ---------------------------------------------------------------------------


def test_positive_ink_on_positive_passes_aa() -> None:
    """``--positive-ink`` on ``--positive`` must reach 4.5:1 (body text)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    positive = _resolved_value(sheet, "--positive")
    positive_ink = _resolved_value(sheet, "--positive-ink")
    ratio = contrast_ratio(positive_ink, positive)
    assert ratio >= 4.5, f"--positive-ink on --positive: {ratio:.2f}:1 (need >= 4.5:1)"


def test_negative_ink_on_negative_passes_aa() -> None:
    """``--negative-ink`` on ``--negative`` must reach 4.5:1 (body text)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    negative = _resolved_value(sheet, "--negative")
    negative_ink = _resolved_value(sheet, "--negative-ink")
    ratio = contrast_ratio(negative_ink, negative)
    assert ratio >= 4.5, f"--negative-ink on --negative: {ratio:.2f}:1 (need >= 4.5:1)"


def test_status_inks_are_dark_on_dark_mode() -> None:
    """``--positive-ink`` and ``--negative-ink`` SHALL be dark (lightness ≤ 0.25).

    D-F05.3: fills are lightness-lifted to ≥ 0.65 on dark mode, so the
    inks have to be dark to maintain AAA contrast.
    """
    from coloraide import Color

    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    for name in ("--positive-ink", "--negative-ink"):
        color = Color(by_name[name].computed_value).convert("oklch")
        L = color.coords()[0]
        assert L <= 0.25, f"{name} lightness {L:.3f} > 0.25 (must be dark on lifted fills)"


# ---------------------------------------------------------------------------
# F05 D-F05.7 — error feedback pair
# ---------------------------------------------------------------------------


def test_error_fg_on_error_bg_passes_aa() -> None:
    """``--error-fg`` on ``--error-bg`` must reach 4.5:1."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    error_bg = _resolved_value(sheet, "--error-bg")
    error_fg = _resolved_value(sheet, "--error-fg")
    ratio = contrast_ratio(error_fg, error_bg)
    assert ratio >= 4.5, f"--error-fg on --error-bg: {ratio:.2f}:1 (need >= 4.5:1)"


def test_error_pair_is_dark_bg_with_lifted_fg() -> None:
    """``--error-bg`` SHALL be dark red (L <= 0.35); ``--error-fg`` SHALL be lifted (L >= 0.70).

    D-F05.7 inverts the lightness split: background sinks, foreground
    lifts. Same hue family preserved.
    """
    from coloraide import Color

    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    error_bg_L = Color(by_name["--error-bg"].computed_value).convert("oklch").coords()[0]
    error_fg_L = Color(by_name["--error-fg"].computed_value).convert("oklch").coords()[0]

    assert error_bg_L <= 0.35, f"--error-bg lightness {error_bg_L:.3f} > 0.35"
    assert error_fg_L >= 0.70, f"--error-fg lightness {error_fg_L:.3f} < 0.70"


# ---------------------------------------------------------------------------
# F05 D-F05.6 — focus on dark surface
# ---------------------------------------------------------------------------


def test_color_focus_against_bg_passes_3to1() -> None:
    """``--color-focus`` on ``--bg`` must reach 3:1 (UI component, 3:1 OK)."""
    sheet = parse_stylesheet(APP_CSS_PATH)
    bg = _resolved_value(sheet, "--bg")
    color_focus = _resolved_value(sheet, "--color-focus")
    ratio = contrast_ratio(color_focus, bg)
    assert ratio >= 3.0, f"--color-focus on --bg: {ratio:.2f}:1 (need >= 3:1)"


# ---------------------------------------------------------------------------
# F05 D-F05.2 — surface elevation via lightness
# ---------------------------------------------------------------------------


def test_surface_lights_over_bg() -> None:
    """``--surface`` SHALL be lightness >= +0.03 over ``--bg`` (cards lift via claridade)."""
    from coloraide import Color

    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    bg_L = Color(by_name["--bg"].computed_value).convert("oklch").coords()[0]
    surface_L = Color(by_name["--surface"].computed_value).convert("oklch").coords()[0]

    delta = surface_L - bg_L
    assert delta >= 0.03, (
        f"--surface - --bg lightness delta {delta:.3f} < 0.03 "
        f"(cards must lift via claridade, D-F05.2)"
    )


def test_surface_sunk_drops_below_bg() -> None:
    """``--surface-sunk`` SHALL be lightness <= -0.02 under ``--bg`` (form wells descem)."""
    from coloraide import Color

    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    bg_L = Color(by_name["--bg"].computed_value).convert("oklch").coords()[0]
    sunk_L = Color(by_name["--surface-sunk"].computed_value).convert("oklch").coords()[0]

    delta = sunk_L - bg_L
    assert delta <= -0.02, (
        f"--surface-sunk - --bg lightness delta {delta:.3f} > -0.02 "
        f"(form wells must sink below --bg, D-F05.2)"
    )


# ---------------------------------------------------------------------------
# Legacy aliases preserved (D-05 from prior phase)
# ---------------------------------------------------------------------------


def test_legacy_aliases_intact() -> None:
    """``--fg → --ink`` and ``--muted → --ink-muted`` still resolve.

    Pins the alias contract. Both aliases must resolve to exactly the
    same colour value as the canonical token, not just any passing
    contrast.
    """
    sheet = parse_stylesheet(APP_CSS_PATH)
    rows = color_token_inventory(sheet)
    by_name = {r.token: r for r in rows}

    assert by_name["--fg"].computed_value == by_name["--ink"].computed_value
    assert by_name["--muted"].computed_value == by_name["--ink-muted"].computed_value


# ---------------------------------------------------------------------------
# F05 D-F05.10 — no light-mode toggle (single register dark)
# ---------------------------------------------------------------------------


def test_color_scheme_is_dark() -> None:
    """``color-scheme`` SHALL be ``dark`` (not ``light dark``, no toggle)."""
    raw = APP_CSS_PATH.read_text(encoding="utf-8")
    assert "color-scheme: dark;" in raw, "color-scheme must be 'dark' (D-F05.10)"
    assert "color-scheme: light dark;" not in raw, (
        "color-scheme must not advertise a light mode (D-F05.10, no toggle)"
    )


def test_no_prefers_color_scheme_media_query() -> None:
    """No ``@media (prefers-color-scheme: ...)`` blocks SHALL exist (D-F05.10)."""
    raw = APP_CSS_PATH.read_text(encoding="utf-8")
    assert "prefers-color-scheme" not in raw, (
        "No prefers-color-scheme media query — single register dark (D-F05.10)"
    )


# ---------------------------------------------------------------------------
# Aggregate — every documented pair from DESIGN.md passes AA on dark surface
# ---------------------------------------------------------------------------


# (foreground token, background token, minimum ratio) — sourced from
# the "Tokens (current)" table in DESIGN.md after F05. The audit's
# name-based pairing heuristic resolves the pair right for body text
# tokens but reverses it for fill/ink pairs (--accent on --ink, etc);
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
    ("--color-focus", "--bg", 3.0),
    ("--class-1", "--bg", 4.5),
    ("--class-2", "--bg", 4.5),
    ("--class-3", "--bg", 4.5),
    ("--class-4", "--bg", 4.5),
    ("--class-5", "--bg", 4.5),
    ("--class-6", "--bg", 4.5),
)


@pytest.mark.integration
def test_documented_pairs_pass() -> None:
    """Every pair listed in DESIGN.md must meet its documented minimum."""
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
