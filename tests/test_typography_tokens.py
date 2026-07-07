"""Tests for F09 — typography refresh.

Pins the D02 §Gate 3 / §Typography contract in code so a future edit
to ``base.html`` or ``app.css`` cannot reintroduce Source Serif 4 or
silently drop one of the four Inter feature-settings without failing
the test suite. Reads the live ``src/omaha/templates/base.html`` and
``src/omaha/static/app.css`` so the contract is always calibrated
against the current build.

Companion to ``tests/test_dark_mode_tokens.py`` (color-token contract,
F05). Two files, one concern each — keeps the assertions focused and
avoids drift between the two contracts.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_HTML_PATH = REPO_ROOT / "src" / "omaha" / "templates" / "base.html"
APP_CSS_PATH = REPO_ROOT / "src" / "omaha" / "static" / "app.css"

EXPECTED_DISPLAY_SELECTORS = frozenset(
    {
        ".portfolio-stat-value",
        ".app-header-wordmark",
        ".empty-state-step-number",
        ".rebalance-stat-value",
        ".tab-nav__btn--active",
    }
)

REQUIRED_FEATURE_SETTINGS = ("tnum", "cv01", "ss01", "ss02")

# Serif family names that F09 retired. The system sans-serif keyword
# (``sans-serif``) at the end of the font-family chain is INTENDED per
# design D-F09.4 and must not trigger the assertion.
RETIRED_SERIF_FAMILIES = ("Source Serif 4", "IBM Plex Serif", "Georgia")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 4.2 — Google Fonts URL declares Red Hat Display 700+800
# ---------------------------------------------------------------------------


def test_google_fonts_url_declares_red_hat_display_700_800() -> None:
    """D02 §Gate 3 + F09 D-F09.3 — display face is Red Hat Display 700/800.

    The Google Fonts URL in ``base.html`` MUST contain the
    ``Red+Hat+Display`` family with weights 700 and 800 so the
    portfolio hero and active tab render in the correct face.
    """
    html = _read(BASE_HTML_PATH)
    assert "Red+Hat+Display:wght@700;800" in html, (
        "Google Fonts URL is missing Red Hat Display 700;800. Check src/omaha/templates/base.html"
    )


# ---------------------------------------------------------------------------
# 4.3 — Source Serif 4 is absent from the URL
# ---------------------------------------------------------------------------


def test_google_fonts_url_drops_source_serif_4() -> None:
    """D02 §Gate 3 + F09 D-F09.4 — Source Serif 4 is retired.

    The Google Fonts URL MUST NOT declare ``Source+Serif+4``. The
    family has been removed from the build per the D02 register
    decision; reintroducing it would violate the sans-display
    contract.
    """
    html = _read(BASE_HTML_PATH)
    assert "Source+Serif+4" not in html, (
        "Source Serif 4 still declared in Google Fonts URL. Remove per F09 D-F09.4."
    )


# ---------------------------------------------------------------------------
# 4.4 — URL ends in display=swap
# ---------------------------------------------------------------------------


def test_google_fonts_url_ends_in_display_swap() -> None:
    """F09 D-F09.7 — ``font-display: swap`` avoids FOIT.

    The URL MUST end in ``&display=swap`` so body text renders in
    the system fallback during the font load window.
    """
    html = _read(BASE_HTML_PATH)
    url_match = re.search(
        r'href="(https://fonts\.googleapis\.com/css2\?[^"]+)"',
        html,
    )
    assert url_match is not None, "Google Fonts URL not found in base.html"
    url = url_match.group(1)
    assert url.endswith("&display=swap"), (
        f"Google Fonts URL must end in &display=swap for font-display: swap. Got: {url}"
    )


# ---------------------------------------------------------------------------
# 4.5 — both preconnects present (googleapis without crossorigin,
#       gstatic with crossorigin)
# ---------------------------------------------------------------------------


def test_both_preconnect_links_present() -> None:
    """F09 D-F09.6 — preconnect to fonts.googleapis.com AND fonts.gstatic.com.

    The googleapis preconnect fetches the CSS (same-origin style
    fetch, no crossorigin needed); the gstatic preconnect fetches
    the WOFF2 files (CORS fetch, crossorigin attribute required).
    """
    html = _read(BASE_HTML_PATH)
    # googleapis without crossorigin
    assert re.search(
        r'<link\s+rel="preconnect"\s+href="https://fonts\.googleapis\.com"\s*>',
        html,
    ), "Missing preconnect to fonts.googleapis.com (without crossorigin)"
    # gstatic WITH crossorigin (separate, distinct from googleapis)
    assert re.search(
        r'<link\s+rel="preconnect"\s+href="https://fonts\.gstatic\.com"\s+crossorigin\s*>',
        html,
    ), "Missing preconnect to fonts.gstatic.com with crossorigin attribute"


# ---------------------------------------------------------------------------
# 4.6 — body declares all four feature-settings
# ---------------------------------------------------------------------------


def test_body_declares_all_four_feature_settings() -> None:
    """D02 §Typography + F09 D-F09.2 — body carries tnum, cv01, ss01, ss02.

    All four Inter stylistic settings MUST be declared on the ``body``
    rule so the variable font picks them up. Order-insensitive
    substring check on the body block.
    """
    css = _read(APP_CSS_PATH)
    body_match = re.search(r"body\s*\{([^}]+)\}", css)
    assert body_match is not None, "No `body { ... }` rule found in app.css"
    body_block = body_match.group(1)
    feature_line = re.search(
        r"font-feature-settings\s*:\s*([^;]+);",
        body_block,
    )
    assert feature_line is not None, "body { } rule does not declare font-feature-settings"
    declared = feature_line.group(1)
    for feature in REQUIRED_FEATURE_SETTINGS:
        assert f'"{feature}"' in declared, (
            f"body font-feature-settings is missing {feature!r}. "
            f"Declared: {declared!r}. Required: {REQUIRED_FEATURE_SETTINGS}"
        )


# ---------------------------------------------------------------------------
# 4.7 — app.css contains zero Source Serif 4 declarations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family_name", RETIRED_SERIF_FAMILIES)
def test_no_retired_serif_family_in_css(family_name: str) -> None:
    """F09 D-F09.4 — Source Serif 4 + IBM Plex Serif + Georgia are retired.

    None of the three serif family names may appear in any
    ``font-family`` declaration in ``app.css``. The system
    ``sans-serif`` keyword at the end of the chain is the only
    sanctioned appearance of the substring "serif".
    """
    css = _read(APP_CSS_PATH)
    assert family_name not in css, (
        f"app.css still references retired serif family {family_name!r}. "
        f"F09 retired all three (Source Serif 4, IBM Plex Serif, Georgia)."
    )


# ---------------------------------------------------------------------------
# 4.8 — app.css declares Red Hat Display on the display selectors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("selector", sorted(EXPECTED_DISPLAY_SELECTORS))
def test_red_hat_display_on_display_selector(selector: str) -> None:
    """F09 D-F09.4 + D-F09.5 — Red Hat Display on every display selector.

    Each known display selector MUST declare
    ``font-family: "Red Hat Display", ...`` so the visual register
    is consistent across the portfolio hero, the header wordmark,
    empty-state step numbers, rebalance stat values, and the active
    tab.

    Implementation note: this test scans **every** rule body in
    ``app.css`` that targets the selector (not just the first one).
    A second ``.portfolio-stat-value { font-size: ... font-weight:
    600; }`` rule further down the file would silently override the
    font-family because CSS cascade picks the last matching rule —
    the first-regex-match approach missed this regression during
    F09 apply.
    """
    css = _read(APP_CSS_PATH)
    # Escape the selector for regex (dots are literals, not regex meta)
    escaped = re.escape(selector)
    # Match every rule body targeting this selector (base rule + variant
    # rules like ``.portfolio-stat-value.positive`` share the base
    # selector prefix; we want every block whose header starts with
    # ``selector`` followed by whitespace + ``{``).
    rule_bodies = re.findall(
        rf"{escaped}(?:[\.\w-]*)\s*\{{([^}}]+)\}}",
        css,
    )
    assert rule_bodies, f"Display selector {selector!r} not found in app.css"
    # Every block targeting the selector (base + variants) must either
    # declare Red Hat Display explicitly OR be a pure color override
    # (which inherits font-family from the base rule).
    for idx, rule_body in enumerate(rule_bodies):
        # If this block declares font-family, it MUST be Red Hat Display.
        if "font-family" in rule_body:
            assert '"Red Hat Display"' in rule_body, (
                f"Display selector {selector!r} rule #{idx + 1} declares "
                f"font-family but NOT Red Hat Display. Got: {rule_body!r}. "
                f"F09 retired Source Serif 4 from all display selectors — "
                f"a duplicate rule with a different font-family will "
                f"silently override the base declaration via CSS cascade."
            )
        # No retired serif family may appear in any rule body
        # targeting the selector.
        for retired in RETIRED_SERIF_FAMILIES:
            assert retired not in rule_body, (
                f"Display selector {selector!r} rule #{idx + 1} still "
                f"references retired serif family {retired!r}"
            )
