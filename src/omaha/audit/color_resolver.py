"""Color contrast resolution for the Phase 1 audit.

Wraps ``coloraide`` to parse CSS color strings (hex, ``oklch()``,
``color-mix()``, named colors), compute WCAG 2.1 contrast ratios,
and apply brightness adjustments / alpha compositing.

The module is a pure function library — no DB, no FastAPI, no
templates. The unit-tested contract:

* :func:`contrast_ratio` computes the WCAG 2.1 contrast ratio
  between two CSS color strings.
* :func:`aa_status` returns the ratio plus a ``"Passa"`` or
  ``"Falha"`` verdict based on AA thresholds.
* :func:`apply_brightness` scales sRGB channels to simulate the
  effect of a CSS ``filter: brightness(N)`` declaration.
* :func:`composite_over` alpha-blends a foreground color over a
  backdrop.
"""

from __future__ import annotations

from dataclasses import dataclass

from coloraide import Color

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContrastResult:
    """Output of a single contrast computation.

    ``fg`` and ``bg`` are the input color strings. ``ratio`` is the
    WCAG 2.1 contrast ratio as a float. ``status`` is ``"Passa"``
    when the ratio meets the AA threshold for the given text size,
    ``"Falha"`` otherwise.
    """

    fg: str
    bg: str
    ratio: float
    status: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def contrast_ratio(fg: str, bg: str) -> float:
    """Compute the WCAG 2.1 contrast ratio between *fg* and *bg*.

    Uses ``Color(fg).contrast(bg, method="wcag21")`` under the hood.
    Both arguments are CSS color strings — hex, ``oklch()``,
    ``color-mix()``, or named colors.

    Returns a float in the range [1.0, 21.0].
    """
    try:
        return Color(fg).contrast(bg, method="wcag21")
    except (ValueError, TypeError):
        return 1.0


def aa_status(ratio: float, is_large: bool = False) -> tuple[float, str]:
    """Return a ``(ratio, status)`` pair using WCAG 2.1 AA thresholds.

    ``is_large`` selects the relaxed 3:1 threshold for large text
    (≥18pt or ≥14pt bold). The default (``False``) uses the normal
    4.5:1 threshold.
    """
    threshold = 3.0 if is_large else 4.5
    status = "Passa" if ratio >= threshold else "Falha"
    return ratio, status


def apply_brightness(color: str, factor: float) -> str:
    """Scale the sRGB channels of *color* by *factor*.

    Simulates the effect of ``filter: brightness(N)`` by
    multiplying each RGB channel by *factor* and clamping to
    [0, 255].

    Returns a CSS hex string (e.g. ``"#1a2b3c"``).
    """
    try:
        c = Color(color)
        # Apply brightness factor to linear RGB and convert back
        rgb = c.convert("srgb")
        r = min(1.0, max(0.0, rgb["r"] * factor))
        g = min(1.0, max(0.0, rgb["g"] * factor))
        b = min(1.0, max(0.0, rgb["b"] * factor))
        return Color("srgb", [r, g, b]).to_string(hex=True)
    except (ValueError, TypeError):
        return color


def composite_over(color: str, backdrop: str) -> str:
    """Alpha-composite *color* over *backdrop* using straight-alpha.

    When a computed background has alpha < 1 (e.g. from
    ``color-mix()``), the effective color must be blended over the
    nearest opaque ancestor. Returns a CSS hex string.
    """
    try:
        fg_c = Color(color).convert("srgb")
        bg_c = Color(backdrop).convert("srgb")
        try:
            alpha = min(1.0, max(0.0, fg_c["alpha"]))
        except (KeyError, TypeError):
            alpha = 1.0
        if alpha >= 1.0:
            return color
        r = fg_c["r"] * alpha + bg_c["r"] * (1 - alpha)
        g = fg_c["g"] * alpha + bg_c["g"] * (1 - alpha)
        b = fg_c["b"] * alpha + bg_c["b"] * (1 - alpha)
        return Color("srgb", [r, g, b]).to_string(hex=True)
    except (ValueError, TypeError):
        return color
