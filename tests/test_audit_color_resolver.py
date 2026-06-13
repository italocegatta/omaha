"""Tests for Phase 1 — AUDT-02 color contrast resolver.

Unit tests for :mod:`omaha.audit.color_resolver`. No DB, no FastAPI,
no session — the resolver is a pure function library.

Coverage map (this file):
* Package import              — ``test_audit_color_resolver_importable``
* Stub symbols exist          — ``test_contrast_ratio_sig``
* aa_status thresholds        — ``test_aa_status_sig``
* apply_brightness shape      — ``test_apply_brightness_sig``
* composite_over shape        — ``test_composite_over_sig``
* ContrastResult construction — ``test_contrast_result_fields``
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
# Import / module shape
# ---------------------------------------------------------------------------


def test_audit_color_resolver_importable() -> None:
    """The color resolver module is importable after Task 2 stub creation."""
    assert color_resolver is not None
    mod = importlib.import_module("omaha.audit.color_resolver")
    assert mod.__doc__ is not None
    assert "from __future__" in Path(mod.__file__).read_text() if mod.__file__ else True


def test_contrast_ratio_sig() -> None:
    """contrast_ratio exists, accepts two CSS color strings, returns a float."""
    assert callable(contrast_ratio)
    result = contrast_ratio("#ffffff", "#000000")
    assert isinstance(result, float)
    assert result >= 1.0


def test_aa_status_sig() -> None:
    """aa_status returns a (ratio, status) tuple with correct thresholds."""
    ratio, status = aa_status(4.5, is_large=False)
    assert isinstance(ratio, float)
    assert status in ("Passa", "Falha")

    # Body text threshold: 4.5
    assert aa_status(4.5, False)[1] == "Passa"
    assert aa_status(4.4, False)[1] == "Falha"

    # Large text threshold: 3.0
    assert aa_status(3.0, True)[1] == "Passa"
    assert aa_status(2.9, True)[1] == "Falha"


def test_apply_brightness_sig() -> None:
    """apply_brightness exists, accepts color + factor, returns a string."""
    assert callable(apply_brightness)
    result = apply_brightness("#0a66c2", 1.1)
    assert isinstance(result, str)
    assert result.startswith("#")


def test_composite_over_sig() -> None:
    """composite_over exists, accepts two color strings, returns a string."""
    assert callable(composite_over)
    result = composite_over("rgba(255,0,0,0.5)", "#ffffff")
    assert isinstance(result, str)


def test_contrast_result_fields() -> None:
    """ContrastResult exposes the fields described in the artifact spec."""
    result = ContrastResult(fg="#fff", bg="#000", ratio=21.0, status="Passa")
    assert result.fg == "#fff"
    assert result.bg == "#000"
    assert result.ratio == 21.0
    assert result.status == "Passa"
