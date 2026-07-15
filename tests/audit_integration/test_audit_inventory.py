"""Tests for the interactive-element inventory (AUDT-01).

Covers :class:`AuditContextFactory`, :func:`render_page`,
:func:`find_interactive`, :func:`state_color_pairs`, and
:func:`inventory_for_page`.

Every test in this file reads the production ``src/omaha/templates/``
directory and ``src/omaha/static/app.css`` — neither lives in
``tests/fixtures/``.  The file lives under ``tests/audit_integration/``
and is excluded from unit and integration subsets; it is run by
``task test-audit-integration`` and the full ``task test``.

Collapsed: the 7 ``context_for_*`` tests, 8 ``render_*`` tests, and 3
``finds_elements_in_*`` tests collapse into single parametrized
tests.  The ``row_has_all_fields`` dataclass-shape check and the
``create_row``/``row_is_frozen`` pair are dropped — dataclass
construction is locked at the cheapest layer by
:mod:`tests.test_audit_css_parser`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from omaha.audit.css_parser import Stylesheet, parse_stylesheet
from omaha.audit.inventory import (
    INTERACTIVE_SELECTOR,
    AuditContextFactory,
    find_interactive,
    inventory_for_page,
    render_page,
    state_color_pairs,
)

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Paths and fixtures (session-scoped — the production files are large
# and immutable during a test run; parsing once per session saves ~2-3s)
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "src" / "omaha" / "templates"
_CSS_PATH = Path(__file__).resolve().parents[2] / "src" / "omaha" / "static" / "app.css"


@pytest.fixture(scope="session")
def jinja_env() -> Environment:
    """A Jinja2 Environment pointed at the production templates.

    Session-scoped: the production templates directory does not change
    during a test run, so parsing once per session is safe and avoids
    rebuilding the Environment per module (~1-2s savings over module scope).
    Read-only — no test should mutate this fixture.
    """
    env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))

    def _brl(value, *args, **kwargs):
        return f"R${value:,.2f}"

    env.filters["brl"] = _brl
    return env


@pytest.fixture(scope="session")
def stylesheet() -> Stylesheet:
    """The parsed production app.css.

    Session-scoped: ``app.css`` is a production file (~2500 lines) that
    does not change during a test run.  Parsing once per session avoids
    redundant CSS parsing per module (~2-3s savings over module scope).
    Read-only — no test should mutate this fixture.
    """
    return parse_stylesheet(_CSS_PATH)


@pytest.fixture(scope="module")
def factory() -> AuditContextFactory:
    """An AuditContextFactory instance."""
    return AuditContextFactory()


# ---------------------------------------------------------------------------
# AuditContextFactory.context_for
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "template_name,required_keys",
    [
        # Each template gets a context with at least the base keys, plus
        # the template-specific ones the inventory loop consumes.
        # F02: dashboard.html → patrimonio.html (same render path,
        # same context dict).
        ("patrimonio.html", {"user", "profile", "asset_classes", "portfolio", "class_aggregates"}),
        ("classes.html", {"user", "profile"}),
        ("assets.html", {"user", "profile", "classes"}),
        ("import.html", {"user", "profile"}),
        ("import_review.html", {"user", "profile", "auto_count", "unmatched_count"}),
        ("login.html", {"user", "error"}),
        # F02: stub pages — same render context as a generic
        # authenticated page (user + profile).
        ("rentabilidade.html", {"user", "profile"}),
        ("proventos.html", {"user", "profile"}),
        # direct-landing-with-header-profile-switcher: profiles.html
        # was deleted (the picker page is gone); the dashboard picks up
        # the chip + viewer label via the new common context instead.
    ],
)
def test_context_for_templates(
    factory: AuditContextFactory,
    template_name: str,
    required_keys: set[str],
) -> None:
    """``context_for`` returns a renderable dict with the documented keys per template."""
    ctx = factory.context_for(template_name)
    for key in required_keys:
        assert key in ctx, f"{template_name} context missing required key {key!r}"


def test_context_for_unknown_template_returns_base(factory: AuditContextFactory) -> None:
    """Unknown templates fall back to the base context (user + profile)."""
    ctx = factory.context_for("nonexistent.html")
    assert "user" in ctx
    assert "profile" in ctx


# ---------------------------------------------------------------------------
# render_page — template-specific anchors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "template_name,expected_anchor",
    [
        # ``base.html`` is the only template that contains the literal
        # product name; using it as the anchor lets the test catch a
        # misrender that drops the base layout entirely.
        ("base.html", "Omaha"),
        # F02: dashboard.html → patrimonio.html; the anchor is the
        # ``data-testid="patrimonio-portfolio-header"`` marker which
        # the patrimonio template renders when an asset class exists.
        ("patrimonio.html", "patrimonio-portfolio-header"),
        ("classes.html", "classes"),
        ("assets.html", "assets"),
        ("import.html", "import"),
        ("import_review.html", "import"),
        ("login.html", "login"),
        # F02 stubs.
        ("rentabilidade.html", "rentabilidade-stub"),
        ("proventos.html", "proventos-stub"),
        # direct-landing-with-header-profile-switcher: profiles.html
        # was deleted (the picker page is gone).
    ],
)
def test_render_page_produces_template_specific_anchor(
    jinja_env: Environment,
    factory: AuditContextFactory,
    template_name: str,
    expected_anchor: str,
) -> None:
    """Each rendered template contains a unique structural anchor.

    The anchors are the lowercase template stem or — for the
    patrimonio page — the new ``patrimonio-portfolio-header`` testid
    that wraps the legacy ``portfolio-header`` section. Successful
    render of the right template must contain at least one of these.
    """
    html = render_page(jinja_env, template_name, factory.context_for(template_name))
    assert isinstance(html, str)
    assert len(html) > 0
    assert expected_anchor.lower() in html.lower(), (
        f"rendered {template_name} missing anchor {expected_anchor!r}"
    )


# ---------------------------------------------------------------------------
# find_interactive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "template_name,expected_tag",
    [
        # Each page should have at least one of the documented interactive
        # tags in the rendered HTML.
        ("patrimonio.html", "button"),
        ("classes.html", "button"),
        ("login.html", "input"),
    ],
)
def test_find_interactive_finds_tag(
    jinja_env: Environment,
    factory: AuditContextFactory,
    template_name: str,
    expected_tag: str,
) -> None:
    """find_interactive discovers at least one element of the expected tag."""
    html = render_page(jinja_env, template_name, factory.context_for(template_name))
    elements = find_interactive(html)
    assert any(el.name == expected_tag for el in elements), (
        f"{template_name} should have a {expected_tag}, found "
        f"{[(e.name, e.get('class', [])) for e in elements]}"
    )


# ---------------------------------------------------------------------------
# state_color_pairs
# ---------------------------------------------------------------------------


def _find_btn_primary(html: str):
    """Return the first ``.btn-primary`` element in *html*, or ``None``."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one(".btn-primary")


def test_default_state_for_btn_primary_has_color_pair(
    jinja_env: Environment,
    factory: AuditContextFactory,
    stylesheet: Stylesheet,
) -> None:
    """The default-state color pair is computed for ``.btn-primary`` on patrimonio."""
    html = render_page(jinja_env, "patrimonio.html", factory.context_for("patrimonio.html"))
    btn = _find_btn_primary(html)
    assert btn is not None, "Patrimonio should render a .btn-primary button"

    row = state_color_pairs(btn, stylesheet, "default")
    assert row is not None
    assert row.state == "default"
    assert row.fg
    assert row.bg
    assert row.ratio > 0
    assert row.status in ("Passa", "Falha")


def test_hover_state_differs_from_default(
    jinja_env: Environment,
    factory: AuditContextFactory,
    stylesheet: Stylesheet,
) -> None:
    """The hover state differs from default (CSS ``filter: brightness`` applied)."""
    html = render_page(jinja_env, "import.html", factory.context_for("import.html"))
    btn = _find_btn_primary(html)
    assert btn is not None, "import.html should render a .btn-primary button"

    default_row = state_color_pairs(btn, stylesheet, "default")
    hover_row = state_color_pairs(btn, stylesheet, "hover")
    assert default_row is not None
    assert hover_row is not None
    assert default_row.bg != hover_row.bg or default_row.ratio != hover_row.ratio, (
        f"Hover must differ from default; default.bg={default_row.bg} hover.bg={hover_row.bg}"
    )


def test_element_without_colors_returns_none(stylesheet: Stylesheet) -> None:
    """state_color_pairs returns None when no color declarations are found."""
    soup = BeautifulSoup("<div class='no-colors'></div>", "html.parser")
    el = soup.select_one(".no-colors")
    assert state_color_pairs(el, stylesheet, "default") is None


# ---------------------------------------------------------------------------
# inventory_for_page
# ---------------------------------------------------------------------------


def test_inventory_for_patrimonio_has_rows_with_template_field(
    jinja_env: Environment,
    stylesheet: Stylesheet,
) -> None:
    """inventory_for_page produces rows and every row carries the template name."""
    rows = inventory_for_page("patrimonio.html", jinja_env, stylesheet)
    assert len(rows) > 0, "Patrimonio should produce inventory rows"
    for row in rows:
        assert row.template == "patrimonio.html"


def test_nonexistent_template_returns_empty(
    jinja_env: Environment,
    stylesheet: Stylesheet,
) -> None:
    """inventory_for_page returns [] when the template doesn't exist."""
    assert inventory_for_page("nonexistent.html", jinja_env, stylesheet) == []


# ---------------------------------------------------------------------------
# INTERACTIVE_SELECTOR constant
# ---------------------------------------------------------------------------


def test_interactive_selector_covers_expected_tags() -> None:
    """INTERACTIVE_SELECTOR names every tag the inventory loop treats as interactive."""
    for tag in ("button", "a[href]", "input", "select", "textarea", "[tabindex]"):
        assert tag in INTERACTIVE_SELECTOR, f"INTERACTIVE_SELECTOR missing {tag!r}"
