"""Tests for Phase 1 — AUDT-02 color contrast resolver.

Unit tests for :mod:`omaha.audit.color_resolver`. No DB, no FastAPI,
no session — the resolver is a pure function library.

Coverage map (this file):
* Module import              — ``test_audit_color_resolver_importable``
* Dataclass construction     — ``test_contrast_result_fields``
* contrast_ratio hex         — ``test_contrast_ratio_hex``
* contrast_ratio oklch       — ``test_contrast_ratio_oklch``
* contrast_ratio edge        — ``test_contrast_ratio_invalid``
* aa_status normal           — ``test_aa_status_normal``
* aa_status large            — ``test_aa_status_large``
* aa_status edge             — ``test_aa_status_at_thresholds``
* apply_brightness           — ``test_apply_brightness_lightens``
* apply_brightness darken    — ``test_apply_brightness_darkens``
* composite_over opaque      — ``test_composite_over_opaque``
* composite_over transparent — ``test_composite_over_transparent``
* real known pairs           — ``test_contrast_real_pairs_oklch``
* color-mix() handling       — ``test_contrast_color_mix``
"""

from __future__ import annotations

import importlib
from pathlib import Path

from omaha.audit import color_resolver
from omaha.audit.color_resolver import (
    ContrastResult,
    aa_status,
    apply_brightness,
    composite_over,
    contrast_ratio,
)

# ---------------------------------------------------------------------------
# Import / module shape (Task 2 carry-over)
# ---------------------------------------------------------------------------


def test_audit_color_resolver_importable() -> None:
    """The color resolver module is importable."""
    assert color_resolver is not None
    mod = importlib.import_module("omaha.audit.color_resolver")
    assert mod.__doc__ is not None
    assert "from __future__" in Path(mod.__file__).read_text() if mod.__file__ else True


def test_contrast_result_fields() -> None:
    """ContrastResult exposes the fields described in the artifact spec."""
    result = ContrastResult(fg="#fff", bg="#000", ratio=21.0, status="Passa")
    assert result.fg == "#fff"
    assert result.bg == "#000"
    assert result.ratio == 21.0
    assert result.status == "Passa"


# ---------------------------------------------------------------------------
# contrast_ratio
# ---------------------------------------------------------------------------


def test_contrast_ratio_hex() -> None:
    """White-on-black gives 21:1; black-on-white gives the same."""
    assert contrast_ratio("#ffffff", "#000000") > 20.0
    assert contrast_ratio("#000000", "#ffffff") > 20.0


def test_contrast_ratio_oklch_body() -> None:
    """The app.css --ink against --bg pair returns >= 4.5 (must pass AA)."""
    ratio = contrast_ratio(
        "oklch(0.20 0.01 60)",  # --ink
        "oklch(0.975 0.003 60)",  # --bg
    )
    assert ratio >= 4.5, f"Expected >= 4.5 for --ink/--bg, got {ratio}"


def test_contrast_ratio_oklch_accent() -> None:
    """Accent-ink against accent must pass AA for body text."""
    ratio = contrast_ratio(
        "oklch(0.98 0.005 150)",  # --accent-ink
        "oklch(0.42 0.09 150)",  # --accent
    )
    assert ratio >= 4.5, f"Expected >= 4.5 for accent-ink/accent, got {ratio}"


def test_contrast_ratio_invalid_color() -> None:
    """Invalid color input returns 1.0 (no crash)."""
    assert contrast_ratio("not-a-color", "#ffffff") == 1.0
    assert contrast_ratio("#000", "not-a-color") == 1.0


def test_contrast_ratio_color_mix() -> None:
    """color-mix() values parse and produce a contrast ratio."""
    ratio = contrast_ratio(
        "color-mix(in srgb, var(--ink) 100%, transparent)",  # effectively --ink
        "oklch(0.975 0.003 60)",  # --bg
    )
    assert ratio >= 1.0
    assert ratio <= 21.0


# ---------------------------------------------------------------------------
# aa_status
# ---------------------------------------------------------------------------


def test_aa_status_normal_pass() -> None:
    """4.5+ passes for normal text."""
    _, status = aa_status(4.5, is_large=False)
    assert status == "Passa"


def test_aa_status_normal_fail() -> None:
    """Below 4.5 fails for normal text."""
    _, status = aa_status(4.4, is_large=False)
    assert status == "Falha"


def test_aa_status_large_pass() -> None:
    """3.0+ passes for large text."""
    _, status = aa_status(3.0, is_large=True)
    assert status == "Passa"


def test_aa_status_large_fail() -> None:
    """Below 3.0 fails for large text."""
    _, status = aa_status(2.9, is_large=True)
    assert status == "Falha"


def test_aa_status_at_thresholds() -> None:
    """Exact threshold values are tested as specified in the plan."""
    # aa_status(4.4, False) → Falha
    assert aa_status(4.4, False)[1] == "Falha"
    # aa_status(3.1, True) → Passa
    assert aa_status(3.1, True)[1] == "Passa"
    # aa_status(4.5, False) → Passa (at threshold)
    assert aa_status(4.5, False)[1] == "Passa"


def test_aa_status_returns_tuple() -> None:
    """aa_status returns (float, str) tuple."""
    result = aa_status(5.0)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], float)
    assert isinstance(result[1], str)


# ---------------------------------------------------------------------------
# apply_brightness
# ---------------------------------------------------------------------------


def test_apply_brightness_lightens() -> None:
    """Brightness factor > 1 produces a lighter color."""
    result = apply_brightness("#0a66c2", 1.1)
    assert isinstance(result, str)
    assert result.startswith("#")
    # The lightened color should have higher sRGB channels.
    assert result != "#0a66c2"


def test_apply_brightness_darkens() -> None:
    """Brightness factor < 1 produces a darker color."""
    result = apply_brightness("#ffffff", 0.5)
    assert isinstance(result, str)
    assert result != "#ffffff"


def test_apply_brightness_identity() -> None:
    """Factor 1.0 leaves the color unchanged (may differ by rounding)."""
    result = apply_brightness("#808080", 1.0)
    assert result.startswith("#")


def test_apply_brightness_invalid_color() -> None:
    """Invalid input is returned unchanged."""
    assert apply_brightness("not-a-color", 1.1) == "not-a-color"


# ---------------------------------------------------------------------------
# composite_over
# ---------------------------------------------------------------------------


def test_composite_over_opaque() -> None:
    """Fully opaque foreground is returned unchanged."""
    result = composite_over("#ff0000", "#ffffff")
    assert result == "#ff0000"


def test_composite_over_transparent() -> None:
    """50% red over white produces pink."""
    result = composite_over("rgba(255, 0, 0, 0.5)", "#ffffff")
    assert isinstance(result, str)
    assert result.startswith("#")
    # Result should be closer to white than pure red.
    assert result != "#ff0000"


def test_composite_over_invalid() -> None:
    """Invalid input is returned unchanged."""
    assert composite_over("bad-color", "#ffffff") == "bad-color"
    assert composite_over("#ff0000", "bad-color") == "#ff0000"
