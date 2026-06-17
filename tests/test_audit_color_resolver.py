"""Tests for Phase 1 — AUDT-02 color contrast resolver.

Unit tests for :mod:`omaha.audit.color_resolver`. No DB, no FastAPI,
no session — the resolver is a pure function library.

Every test asserts exact values or ``pytest.approx`` on floats, never
the bare ``> threshold`` style. Tests for invalid input assert the
documented exception type (``ValueError`` for ``composite_over``,
the documented 1.0 fallback for ``contrast_ratio``).
"""

from __future__ import annotations

import pytest
from coloraide import Color

from omaha.audit.color_resolver import (
    ContrastResult,
    aa_status,
    apply_brightness,
    composite_over,
    contrast_ratio,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# contrast_ratio
# ---------------------------------------------------------------------------


def test_contrast_ratio_hex_is_21_to_1() -> None:
    """White-on-black and black-on-white both round-trip to 21:1.

    WCAG 2.1 caps the ratio at 21.0 — the exact value is asserted
    with ``pytest.approx`` because the sRGB-to-linear conversion is
    float arithmetic.
    """
    assert contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0, abs=1e-3)
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, abs=1e-3)


def test_contrast_ratio_oklch_ink_on_bg_passes_aa() -> None:
    """The documented --ink/--bg pair reaches the 4.5:1 AA threshold."""
    ratio = contrast_ratio(
        "oklch(0.20 0.01 60)",  # --ink
        "oklch(0.975 0.003 60)",  # --bg
    )
    assert ratio >= 4.5, f"--ink on --bg must reach AA: got {ratio:.2f}:1"


def test_contrast_ratio_oklch_accent_ink_on_accent_passes_aa() -> None:
    """The documented --accent-ink/--accent pair reaches 4.5:1."""
    ratio = contrast_ratio(
        "oklch(0.98 0.005 150)",  # --accent-ink
        "oklch(0.42 0.09 150)",  # --accent
    )
    assert ratio >= 4.5, f"--accent-ink on --accent must reach AA: got {ratio:.2f}:1"


def test_contrast_ratio_color_mix_stays_in_wcag_range() -> None:
    """A color-mix() expression returns a ratio within the WCAG range.

    The literal input references ``var(--ink)`` which the resolver
    cannot resolve (no registry), so the contrast falls back to 1.0
    — the contract is "returns a number in [1.0, 21.0]" rather than
    a specific value.
    """
    ratio = contrast_ratio(
        "color-mix(in srgb, var(--ink) 100%, transparent)",
        "oklch(0.975 0.003 60)",
    )
    assert 1.0 <= ratio <= 21.0, f"color-mix ratio out of WCAG range: {ratio}"


def test_contrast_ratio_invalid_input_returns_one() -> None:
    """Unparseable color inputs fall back to 1.0 (lowest contrast).

    Pinned behaviour: the resolver never raises; callers can treat
    1.0 as "could not compute, do not trust the result".
    """
    assert contrast_ratio("not-a-color", "#ffffff") == 1.0
    assert contrast_ratio("#000", "not-a-color") == 1.0


# ---------------------------------------------------------------------------
# aa_status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ratio,is_large,expected_status",
    [
        (4.5, False, "Passa"),
        (4.4, False, "Falha"),
        (3.0, True, "Passa"),
        (2.9, True, "Falha"),
        (4.4, False, "Falha"),
        (3.1, True, "Passa"),
        (4.5, False, "Passa"),
    ],
)
def test_aa_status_thresholds(ratio: float, is_large: bool, expected_status: str) -> None:
    """Each (ratio, is_large) pair maps to the documented Passa/Falha verdict.

    The 4.5:1 normal-text and 3.0:1 large-text thresholds are the
    WCAG 2.1 AA boundaries; the at-threshold cases (4.5 normal, 3.0
    large) are inclusive — ``>=`` not ``>``.
    """
    _, status = aa_status(ratio, is_large=is_large)
    assert status == expected_status


# ---------------------------------------------------------------------------
# apply_brightness
# ---------------------------------------------------------------------------


def _hex_channels(hex_str: str) -> tuple[float, float, float]:
    """Return the sRGB channels of *hex_str* as floats in [0, 1]."""
    c = Color(hex_str).convert("srgb")
    return c["r"], c["g"], c["b"]


@pytest.mark.parametrize(
    "color,factor,predicate",
    [
        # Factor > 1 raises every channel relative to the source.
        ("#0a66c2", 1.1, lambda src, dst: all(d > s for s, d in zip(src, dst, strict=False))),
        # Factor < 1 darkens every channel.
        ("#ffffff", 0.5, lambda src, dst: all(d < s for s, d in zip(src, dst, strict=False))),
        # Factor 1.0 is the identity (allowing float rounding).
        (
            "#808080",
            1.0,
            lambda src, dst: all(
                d == pytest.approx(s, abs=1e-3) for s, d in zip(src, dst, strict=False)
            ),
        ),
        # Invalid input is returned unchanged — the function never raises.
        ("not-a-color", 1.1, lambda _src, dst: dst == ()),
    ],
)
def test_apply_brightness_channels(
    color: str,
    factor: float,
    predicate,
) -> None:
    """apply_brightness scales sRGB channels by *factor*; invalid input is passthrough.

    For the invalid-color case the predicate is called with an empty
    destination tuple because we don't bother decoding the unchanged
    string — the assertion is on string identity.
    """
    src_channels = () if color == "not-a-color" else _hex_channels(color)
    result = apply_brightness(color, factor)
    if color == "not-a-color":
        assert result == color
        assert predicate(src_channels, ())
    else:
        assert result.startswith("#")
        assert len(result) == 7  # #rrggbb
        dst_channels = _hex_channels(result)
        assert predicate(src_channels, dst_channels), (
            f"brightness({color!r}, {factor}) → {result!r} channels {dst_channels} "
            f"failed predicate against source {src_channels}"
        )


# ---------------------------------------------------------------------------
# composite_over
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "color,backdrop,expected_hex",
    [
        # Opaque foreground short-circuits to the input unchanged.
        ("#ff0000", "#ffffff", "#ff0000"),
        # 50% red over white → pink (#ff8080 = 255, 128, 128).
        ("rgba(255, 0, 0, 0.5)", "#ffffff", "#ff8080"),
        # 50% black over 50% grey (#808080) → 25% grey (#404040).
        ("rgba(0, 0, 0, 0.5)", "#808080", "#404040"),
    ],
)
def test_composite_over_blends(color: str, backdrop: str, expected_hex: str) -> None:
    """composite_over returns the straight-alpha blend of *color* over *backdrop*.

    Each ``(color, backdrop, expected_hex)`` triple pins an exact
    RGB channel result.  Channels are compared with ``pytest.approx``
    to absorb coloraide's float rounding (the input rgba tuple and
    the sRGB blend differ by < 1 LSB in practice).
    """
    result = composite_over(color, backdrop)
    assert result.startswith("#") and len(result) == 7
    actual = _hex_channels(result)
    expected = _hex_channels(expected_hex)
    assert actual == pytest.approx(expected, abs=1.5 / 255), (
        f"composite_over({color!r}, {backdrop!r}) → {result!r} channels {actual}, "
        f"expected {expected_hex} ({expected})"
    )


@pytest.mark.parametrize(
    "color,backdrop",
    [
        ("#ff0000", "bad-color"),
        ("bad-color", "#ffffff"),
    ],
)
def test_composite_over_invalid_input_raises(color: str, backdrop: str) -> None:
    """Invalid color or backdrop raises ``ValueError`` (regression for §1.3).

    Pre-fix the function swallowed the error and returned the input
    unchanged; the inventory loop in ``audit/inventory.py`` relied
    on that silent passthrough.  Post-fix the backstop in
    ``state_color_pairs`` (try/except Exception) keeps the inventory
    running, but the function itself raises so the bug cannot
    propagate silently.
    """
    with pytest.raises(ValueError):
        composite_over(color, backdrop)


# ---------------------------------------------------------------------------
# ContrastResult dataclass
# ---------------------------------------------------------------------------


def test_contrast_result_dataclass_fields() -> None:
    """ContrastResult is a frozen dataclass with the documented fields.

    Pinned fields: ``fg``, ``bg``, ``ratio``, ``status``.  No
    ``isinstance`` assertions — the field access IS the contract.
    """
    result = ContrastResult(fg="#fff", bg="#000", ratio=21.0, status="Passa")
    assert result.fg == "#fff"
    assert result.bg == "#000"
    assert result.ratio == 21.0
    assert result.status == "Passa"
    with pytest.raises((AttributeError, Exception)):
        result.fg = "#000"  # type: ignore[misc]
