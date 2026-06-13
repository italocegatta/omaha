"""Tests for the interactive-element inventory (AUDT-01).

Covers ``AuditContextFactory.context_for``, ``render_page``,
``find_interactive``, ``state_color_pairs``, and ``inventory_for_page``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

from omaha.audit import inventory
from omaha.audit.css_parser import parse_stylesheet
from omaha.audit.inventory import (
    INTERACTIVE_SELECTOR,
    AuditContextFactory,
    InteractiveStateRow,
    find_interactive,
    inventory_for_page,
    render_page,
    state_color_pairs,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "src" / "omaha" / "templates"
_CSS_PATH = Path(__file__).resolve().parents[1] / "src" / "omaha" / "static" / "app.css"


@pytest.fixture(scope="module")
def jinja_env() -> Environment:
    """Return a Jinja2 Environment pointed at the application templates."""
    env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR))
    # Register the brl filter that templates expect.
    def _brl(value, *args, **kwargs):
        return f"R${value:,.2f}"
    env.filters["brl"] = _brl
    return env


@pytest.fixture(scope="module")
def stylesheet():
    """Return the parsed app.css Stylesheet."""
    return parse_stylesheet(_CSS_PATH)


@pytest.fixture(scope="module")
def factory() -> AuditContextFactory:
    """Return an AuditContextFactory instance."""
    return AuditContextFactory()


# ---------------------------------------------------------------------------
# AuditContextFactory
# ---------------------------------------------------------------------------


class TestAuditContextFactory:
    """Verify every template gets a renderable context."""

    def test_context_for_dashboard(self, factory):
        ctx = factory.context_for("dashboard.html")
        assert "user" in ctx
        assert "profile" in ctx
        assert "asset_classes" in ctx
        assert "portfolio" in ctx
        assert "class_aggregates" in ctx

    def test_context_for_classes(self, factory):
        ctx = factory.context_for("classes.html")
        assert "user" in ctx
        assert "profile" in ctx

    def test_context_for_assets(self, factory):
        ctx = factory.context_for("assets.html")
        assert "user" in ctx
        assert "profile" in ctx
        assert "classes" in ctx

    def test_context_for_import(self, factory):
        ctx = factory.context_for("import.html")
        assert "user" in ctx
        assert "profile" in ctx

    def test_context_for_import_review(self, factory):
        ctx = factory.context_for("import_review.html")
        assert "user" in ctx
        assert "auto_count" in ctx
        assert "unmatched_count" in ctx

    def test_context_for_login(self, factory):
        ctx = factory.context_for("login.html")
        assert "user" in ctx
        assert "error" in ctx

    def test_context_for_profiles(self, factory):
        ctx = factory.context_for("profiles.html")
        assert "user" in ctx
        assert "profiles" in ctx
        assert len(ctx["profiles"]) == 2

    def test_context_for_unknown_template(self, factory):
        ctx = factory.context_for("nonexistent.html")
        assert "user" in ctx
        assert "profile" in ctx


# ---------------------------------------------------------------------------
# render_page
# ---------------------------------------------------------------------------


class TestRenderPage:
    """Verify templates render successfully with dummy contexts."""

    def test_render_dashboard(self, jinja_env, factory):
        html = render_page(jinja_env, "dashboard.html", factory.context_for("dashboard.html"))
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_classes(self, jinja_env, factory):
        html = render_page(jinja_env, "classes.html", factory.context_for("classes.html"))
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_assets(self, jinja_env, factory):
        html = render_page(jinja_env, "assets.html", factory.context_for("assets.html"))
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_import(self, jinja_env, factory):
        html = render_page(jinja_env, "import.html", factory.context_for("import.html"))
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_import_review(self, jinja_env, factory):
        html = render_page(
            jinja_env, "import_review.html", factory.context_for("import_review.html")
        )
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_login(self, jinja_env, factory):
        html = render_page(jinja_env, "login.html", factory.context_for("login.html"))
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_profiles(self, jinja_env, factory):
        html = render_page(jinja_env, "profiles.html", factory.context_for("profiles.html"))
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_base(self, jinja_env, factory):
        html = render_page(jinja_env, "base.html", factory.context_for("base.html"))
        assert isinstance(html, str)
        assert "Omaha" in html


# ---------------------------------------------------------------------------
# find_interactive
# ---------------------------------------------------------------------------


class TestFindInteractive:
    """Verify interactive elements are discovered."""

    def test_finds_elements_in_dashboard(self, jinja_env, factory):
        html = render_page(jinja_env, "dashboard.html", factory.context_for("dashboard.html"))
        elements = find_interactive(html)
        assert len(elements) > 0, "Dashboard should have interactive elements"

    def test_finds_elements_in_classes(self, jinja_env, factory):
        html = render_page(jinja_env, "classes.html", factory.context_for("classes.html"))
        elements = find_interactive(html)
        assert len(elements) > 0, "Classes editor should have interactive elements"

    def test_finds_elements_in_login(self, jinja_env, factory):
        html = render_page(jinja_env, "login.html", factory.context_for("login.html"))
        elements = find_interactive(html)
        assert len(elements) > 0, "Login page should have interactive elements"

    def test_finds_buttons(self, jinja_env, factory):
        html = render_page(jinja_env, "dashboard.html", factory.context_for("dashboard.html"))
        elements = find_interactive(html)
        buttons = [e for e in elements if e.name == "button"]
        assert len(buttons) > 0, "Dashboard should have buttons"

    def test_empty_html_returns_empty(self):
        elements = find_interactive("")
        assert elements == []

    def test_no_interactive_elements(self):
        html = "<div><p>Hello</p><span>World</span></div>"
        elements = find_interactive(html)
        assert len(elements) == 0


# ---------------------------------------------------------------------------
# state_color_pairs
# ---------------------------------------------------------------------------


class TestStateColorPairs:
    """Verify state color pair computation."""

    def test_default_state_for_btn_primary(self, jinja_env, factory, stylesheet):
        html = render_page(jinja_env, "dashboard.html", factory.context_for("dashboard.html"))
        elements = find_interactive(html)
        btn_primary = None
        for el in elements:
            classes = el.get("class", [])
            if "btn-primary" in classes:
                btn_primary = el
                break
        assert btn_primary is not None, "Should find a .btn-primary element"

        row = state_color_pairs(btn_primary, stylesheet, "default")
        assert row is not None, "Should compute colors for button default state"
        assert row.state == "default"
        assert row.fg
        assert row.bg
        assert row.ratio > 0
        assert row.status in ("Passa", "Falha")

    def test_hover_state_differs_from_default(self, jinja_env, factory, stylesheet):
        # Use import.html which has a <button class="btn btn-primary">
        html = render_page(jinja_env, "import.html", factory.context_for("import.html"))
        elements = find_interactive(html)
        btn_primary = None
        for el in elements:
            classes = el.get("class", [])
            if "btn-primary" in classes:
                btn_primary = el
                break
        assert btn_primary is not None, f"Should find .btn-primary in import.html. Elements: {[(e.name, e.get('class', [])) for e in elements]}"

        default_row = state_color_pairs(btn_primary, stylesheet, "default")
        hover_row = state_color_pairs(btn_primary, stylesheet, "hover")
        assert default_row is not None
        assert hover_row is not None, f"Hover row is None. Selector classes: {btn_primary.get('class', [])}"

        # Hover should differ from default (brightness filter applied).
        assert (
            default_row.bg != hover_row.bg or default_row.ratio != hover_row.ratio
        ), f"Hover state should differ from default due to brightness. Default bg={default_row.bg}, Hover bg={hover_row.bg}"

    def test_row_has_all_fields(self, jinja_env, factory, stylesheet):
        html = render_page(jinja_env, "dashboard.html", factory.context_for("dashboard.html"))
        elements = find_interactive(html)
        assert len(elements) > 0

        row = state_color_pairs(elements[0], stylesheet, "default")
        if row is None:
            pytest.skip("Element has no color declarations")
        assert isinstance(row.template, str)
        assert isinstance(row.selector, str)
        assert isinstance(row.element_snippet, str)
        assert isinstance(row.state, str)
        assert isinstance(row.fg, str)
        assert isinstance(row.bg, str)
        assert isinstance(row.ratio, float)
        assert isinstance(row.status, str)
        assert isinstance(row.hidden_by_default, bool)

    def test_element_without_colors_returns_none(self, stylesheet):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div class='no-colors'></div>", "html.parser")
        el = soup.select_one(".no-colors")
        row = state_color_pairs(el, stylesheet, "default")
        assert row is None


# ---------------------------------------------------------------------------
# inventory_for_page
# ---------------------------------------------------------------------------


class TestInventoryForPage:
    """Verify the full inventory_for_page pipeline."""

    def test_inventory_for_dashboard(self, jinja_env, stylesheet):
        rows = inventory_for_page("dashboard.html", jinja_env, stylesheet)
        assert len(rows) > 0, "Dashboard should produce inventory rows"

    def test_inventory_for_login(self, jinja_env, stylesheet):
        rows = inventory_for_page("login.html", jinja_env, stylesheet)
        # Login form button has no CSS class, so no color rules may apply.
        # The test verifies the pipeline runs without error.
        assert isinstance(rows, list)

    def test_inventory_for_classes(self, jinja_env, stylesheet):
        rows = inventory_for_page("classes.html", jinja_env, stylesheet)
        assert len(rows) > 0, "Classes should produce inventory rows"

    def test_rows_have_different_states(self, jinja_env, stylesheet):
        rows = inventory_for_page("dashboard.html", jinja_env, stylesheet)
        states = {r.state for r in rows}
        assert "default" in states
        # At least one interactive element should have a hover state defined.
        assert any(
            r.state == "hover" and r.bg for r in rows
        ) or "hover" in states, f"Should have hover states. Got: {states}"

    def test_rows_have_template_field_set(self, jinja_env, stylesheet):
        rows = inventory_for_page("dashboard.html", jinja_env, stylesheet)
        for row in rows:
            assert row.template == "dashboard.html"

    def test_nonexistent_template_returns_empty(self, jinja_env, stylesheet):
        rows = inventory_for_page("nonexistent.html", jinja_env, stylesheet)
        assert rows == []


# ---------------------------------------------------------------------------
# InteractiveStateRow dataclass
# ---------------------------------------------------------------------------


class TestInteractiveStateRow:
    """Verify the dataclass shape."""

    def test_create_row(self):
        row = InteractiveStateRow(
            template="dashboard.html",
            selector="button.btn-primary",
            element_snippet="<button>Importar CSV</button>",
            state="default",
            fg="#ffffff",
            bg="#0a66c2",
            ratio=7.5,
            status="Passa",
            hidden_by_default=False,
        )
        assert row.template == "dashboard.html"
        assert row.selector == "button.btn-primary"
        assert row.ratio == 7.5
        assert row.status == "Passa"

    def test_row_is_frozen(self):
        row = InteractiveStateRow(template="test.html")
        with pytest.raises(Exception):
            row.template = "other.html"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# INTERACTIVE_SELECTOR constant
# ---------------------------------------------------------------------------


def test_interactive_selector_covers_expected_tags():
    assert "button" in INTERACTIVE_SELECTOR
    assert "a[href]" in INTERACTIVE_SELECTOR
    assert "input" in INTERACTIVE_SELECTOR
    assert "select" in INTERACTIVE_SELECTOR
    assert "textarea" in INTERACTIVE_SELECTOR
    assert "[tabindex]" in INTERACTIVE_SELECTOR
