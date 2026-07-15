"""Tests for F12 — Material Symbols icon system.

Pins the D02 §Iconography + F12 contract in code so a future edit to
``base.html``, ``app.css``, the templates, or ``DESIGN.md`` cannot
silently drop the catalog, introduce an out-of-catalog icon, or break
the size scale without failing the test suite. Reads the live files
under ``src/omaha/`` and ``DESIGN.md`` so the contract is always
calibrated against the current build.

Companion to ``tests/test_typography_tokens.py`` (F09 typography
contract) and ``tests/test_dark_mode_tokens.py`` (F05 color-token
contract). Three files, three concerns — keeps each set of
assertions focused and avoids drift between the three contracts.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_HTML_PATH = REPO_ROOT / "src" / "omaha" / "templates" / "base.html"
APP_CSS_PATH = REPO_ROOT / "src" / "omaha" / "static" / "app.css"
DESIGN_MD_PATH = REPO_ROOT / "DESIGN.md"

# Catalog of 10 icon names (D02 §Iconography + F12 D-F12.2). Any use of
# an icon name outside this set requires a new OpenSpec change (see
# ``Extension path`` in DESIGN.md §Iconography).
ICON_CATALOG = frozenset(
    {
        "add",
        "add_circle",
        "upload",
        "logout",
        "close",
        "warning",
        "expand_more",
        "expand_less",
        "check_circle",
        "help",
        "filter_alt",
    }
)

# Templates + partials that should reference the icon catalog.
# Drawn from F12 proposal §Impact.
TEMPLATES_WITH_ICONS = (
    "src/omaha/templates/base.html",
    "src/omaha/templates/_patrimonio_actions.html",
    "src/omaha/templates/_patrimonio_class_section.html",
    "src/omaha/templates/_filter_controls.html",
    "src/omaha/templates/_rebalance_plan.html",
    "src/omaha/templates/_patrimonio_add_asset_modal.html",
    "src/omaha/templates/import_review.html",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_icon_names(text: str) -> list[str]:
    """Return every Material Symbols ligature present in ``text``.

    A ligature is the inner text of a ``<span class="icon ...">``
    element. The pattern matches the canonical F12 markup documented
    in D-F12.5: a span carrying the ``.icon`` base class (and an
    optional size modifier) whose inner text is one ASCII word.
    """
    pattern = re.compile(
        r'<span\s+class="[^"]*\bicon\b[^"]*"[^>]*>\s*([a-z_]+)\s*</span>',
    )
    return pattern.findall(text)


# ---------------------------------------------------------------------------
# 7.1 — Material Symbols Outlined font URL is loaded in base.html
# ---------------------------------------------------------------------------


def test_material_symbols_font_url_present_in_base_html() -> None:
    """F12 D-F12.1 — Material Symbols Outlined loaded from Google Fonts.

    The font URL pattern MUST appear in ``base.html`` so the icon
    ligatures resolve. Format:
    ``https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined``
    """
    html = _read(BASE_HTML_PATH)
    assert re.search(
        r'<link\s+rel="stylesheet"\s+'
        r'href="https://fonts\.googleapis\.com/icon\?family=Material\+Symbols\+Outlined"',
        html,
    ), (
        "base.html is missing the Material Symbols Outlined stylesheet link. "
        "F12 D-F12.1 requires Google Fonts URL "
        "`https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined`."
    )


# ---------------------------------------------------------------------------
# 7.2 — fonts.gstatic.com preconnect present (reused from F09)
# ---------------------------------------------------------------------------


def test_gstatic_preconnect_present_in_base_html() -> None:
    """F12 D-F12.1 — preconnect to fonts.gstatic.com reused from F09.

    Material Symbols WOFF2 files ship from ``fonts.gstatic.com``,
    so the crossorigin preconnect added by F09 is also required
    here. The same preconnect serves both Inter/Red Hat Display
    and Material Symbols.
    """
    html = _read(BASE_HTML_PATH)
    assert re.search(
        r'<link\s+rel="preconnect"\s+href="https://fonts\.gstatic\.com"\s+crossorigin\s*>',
        html,
    ), "Missing preconnect to fonts.gstatic.com with crossorigin attribute"


# ---------------------------------------------------------------------------
# 7.3 — .icon base class declares Material Symbols Outlined font-family
# ---------------------------------------------------------------------------


def test_icon_base_class_declares_material_symbols_outlined() -> None:
    """F12 D-F12.3 — ``.icon`` rule binds Material Symbols Outlined.

    The base ``.icon`` rule MUST declare
    ``font-family: "Material Symbols Outlined"`` so the ligature
    text is rendered via the icon font.
    """
    css = _read(APP_CSS_PATH)
    icon_match = re.search(r"\.icon\s*\{([^}]+)\}", css)
    assert icon_match is not None, (
        "`.icon { ... }` base rule not found in app.css. F12 D-F12.3 requires the icon base class."
    )
    rule_body = icon_match.group(1)
    assert '"Material Symbols Outlined"' in rule_body, (
        f'`.icon` rule does not declare font-family: "Material Symbols Outlined". '
        f"Got: {rule_body!r}"
    )


# ---------------------------------------------------------------------------
# 7.4 — Size modifiers carry the documented pixel sizes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("modifier", "expected_size"),
    [
        (".icon--sm", "16px"),
        (".icon--md", "20px"),
        (".icon--lg", "24px"),
    ],
)
def test_size_modifier_declares_documented_font_size(
    modifier: str,
    expected_size: str,
) -> None:
    """F12 D-F12.3 — three size modifiers map to documented pixel values.

    ``.icon--sm`` is 16px (inline label), ``.icon--md`` is 20px
    (button), ``.icon--lg`` is 24px (hero / empty state). Each
    MUST declare the size via ``font-size``.
    """
    css = _read(APP_CSS_PATH)
    pattern = re.compile(rf"{re.escape(modifier)}\s*\{{([^}}]+)\}}")
    match = pattern.search(css)
    assert match is not None, f"Size modifier {modifier} not found in app.css"
    rule_body = match.group(1)
    assert f"font-size: {expected_size}" in rule_body, (
        f"Size modifier {modifier} does not declare font-size: {expected_size}. Got: {rule_body!r}"
    )


# ---------------------------------------------------------------------------
# 7.5 — No hardcoded color in .icon rules (D-F12.4 currentColor cascade)
# ---------------------------------------------------------------------------


def test_icon_rule_has_no_hardcoded_color() -> None:
    """F12 D-F12.4 — icons inherit color via currentColor cascade.

    No ``color:`` declaration with a literal value (hex, rgb, oklch,
    named) may appear inside any ``.icon*`` rule. ``currentColor``
    (the only sanctioned form) is exempt because it is a keyword
    that resolves at render time.
    """
    css = _read(APP_CSS_PATH)
    # Match every rule whose selector starts with ``.icon`` (base + sizes).
    rule_bodies = re.findall(r"\.icon[a-z-]*\s*\{([^}]+)\}", css)
    assert rule_bodies, "No `.icon*` rules found in app.css"
    for idx, rule_body in enumerate(rule_bodies):
        # ``color:`` followed by a non-keyword value is a violation.
        # currentColor and inherit are the only sanctioned values.
        color_match = re.search(r"color\s*:\s*([^;]+);", rule_body)
        if color_match:
            value = color_match.group(1).strip()
            assert value in {"currentColor", "inherit"}, (
                f".icon rule #{idx + 1} declares hardcoded color {value!r}. "
                f"F12 D-F12.4 requires currentColor cascade — icons inherit "
                f"color from the parent button or label."
            )


# ---------------------------------------------------------------------------
# 7.6 — All icon ligatures across the templates come from the catalog
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("template_relpath", TEMPLATES_WITH_ICONS)
def test_template_icons_are_within_catalog(template_relpath: str) -> None:
    """F12 D-F12.2 — every icon ligature in scope is in the catalog.

    For each template + partial that F12 touches, every Material
    Symbols ligature rendered via ``<span class="icon ...">`` MUST
    be one of the 10 catalog names. Out-of-catalog names require a
    new OpenSpec change.
    """
    text = _read(REPO_ROOT / template_relpath)
    icons_used = _extract_icon_names(text)
    # Strip duplicates for the failure message (the actual scan
    # below still enforces the per-occurrence rule).
    out_of_catalog = sorted({name for name in icons_used if name not in ICON_CATALOG})
    assert not out_of_catalog, (
        f"{template_relpath} renders icon(s) not in the F12 catalog: "
        f"{out_of_catalog!r}. Allowed catalog (D02 §Iconography + F12 D-F12.2): "
        f"{sorted(ICON_CATALOG)!r}. Out-of-catalog use requires a new OpenSpec change."
    )


# ---------------------------------------------------------------------------
# 7.7 — DESIGN.md §Iconography lists all 10 catalog names verbatim
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("icon_name", sorted(ICON_CATALOG))
def test_design_md_iconography_lists_catalog_name(icon_name: str) -> None:
    """F12 D-F12.7 — DESIGN.md §Iconography is the source of truth.

    All 10 catalog names MUST appear in ``DESIGN.md §Iconography``
    so the section stays the canonical reference. A future edit
    that drops a name from the catalog must update both the spec
    and this test.
    """
    md = _read(DESIGN_MD_PATH)
    # Locate the Iconography section (between its heading and the
    # next sibling heading). Markdown h2 ``## Iconography`` (D02
    # rewrote the section header to that form).
    section_match = re.search(
        r"##\s+Iconography\s*\n(.*?)(?=\n##\s|\Z)",
        md,
        re.DOTALL,
    )
    assert section_match is not None, (
        "DESIGN.md §Iconography section not found. F12 D-F12.7 requires "
        "the section to be present and updated."
    )
    section_body = section_match.group(1)
    assert icon_name in section_body, (
        f"DESIGN.md §Iconography does not mention catalog icon {icon_name!r}. "
        f"F12 D-F12.7 requires all 10 catalog names listed."
    )


# ---------------------------------------------------------------------------
# 7.8 — base.html Sair action uses the catalog `logout` icon
# ---------------------------------------------------------------------------


def test_base_html_sair_action_uses_logout_icon() -> None:
    """F12 task 3.4 — Sair action renders the ``logout`` icon.

    The Sair button in ``base.html`` MUST include a Material
    Symbols ligature of ``logout`` (with the ``.icon--md`` size
    modifier) so the icon catalog is exercised in the global
    header.
    """
    html = _read(BASE_HTML_PATH)
    icon_block = re.search(
        r'<form[^>]*class="logout-form"[^>]*>.*?</form>',
        html,
        re.DOTALL,
    )
    assert icon_block is not None, "logout-form not found in base.html"
    icons_in_form = _extract_icon_names(icon_block.group(0))
    assert "logout" in icons_in_form, (
        f"Sair action does not render the `logout` icon. Icons present: {icons_in_form!r}"
    )
