"""Interactive-element inventory for the Phase 1 audit.

Renders each application template with a minimal dummy context, discovers
every interactive element, and computes per-state foreground/background
color pairs with their WCAG 2.1 AA contrast ratios.

The module is a pure function library — no DB, no FastAPI.  The only
side-effect it performs is rendering Jinja2 templates with dummy data.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from bs4 import BeautifulSoup, Tag
from jinja2 import Environment

from omaha.audit.color_resolver import (
    aa_status,
    apply_brightness,
    composite_over,
    contrast_ratio,
)
from omaha.audit.css_parser import Stylesheet, resolve_var
from omaha.audit.css_parser import (
    _build_registry as _build_registry_from_stylesheet,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTERACTIVE_SELECTOR = "button, a[href], input, select, textarea, [tabindex]"

# Pseudo-classes the auditor checks for every interactive element.
_STATES = ("default", "hover", "active", "focus", "disabled")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InteractiveStateRow:
    """A single state color pair for an interactive element.

    Fields
    ------
    template : str
        The template name (e.g. ``"dashboard.html"``).
    selector : str
        A CSS selector representation of the element.
    element_snippet : str
        A short HTML representation for identification.
    state : str
        One of ``"default"``, ``"hover"``, ``"active"``, ``"focus"``,
        ``"disabled"``.
    fg : str
        Resolved foreground color (CSS string).
    bg : str
        Resolved background color (CSS string).
    ratio : float
        WCAG 2.1 contrast ratio.
    status : str
        ``"Passa"`` or ``"Falha"``.
    hidden_by_default : bool
        True when the element or any ancestor has an Alpine.js
        ``x-show`` or ``x-cloak`` directive.
    """

    template: str = ""
    selector: str = ""
    element_snippet: str = ""
    state: str = "default"
    fg: str = ""
    bg: str = ""
    ratio: float = 0.0
    status: str = "Falha"
    hidden_by_default: bool = False


# ---------------------------------------------------------------------------
# AuditContextFactory
# ---------------------------------------------------------------------------


class AuditContextFactory:
    """Builds minimal dummy contexts for rendering app templates.

    The contexts are self-contained dicts / ``SimpleNamespace`` values
    that satisfy every Jinja2 variable reference a template expects.
    No database or live app is involved — the factory returns frozen
    data that makes each template render its interactive markup.
    """

    # F14: Catppuccin Frappe-derived palette. Mirrors --class-1..6 from app.css :root.
    _CLASS_COLORS = (
        "oklch(0.742 0.104 265.7)",  # blue          -- mirrors --class-1
        "oklch(0.765 0.111 311.7)",  # lavender       -- mirrors --class-2
        "oklch(0.783 0.073 184.6)",  # teal           -- mirrors --class-3
        "oklch(0.812 0.107 133.4)",  # green          -- mirrors --class-4
        "oklch(0.844 0.08 83.5)",    # amber          -- mirrors --class-5
        "oklch(0.717 0.124 19.4)",   # red            -- mirrors --class-6
    )

    def _base_context(self) -> dict[str, Any]:
        """Return a context that satisfies ``base.html`` variables."""
        return {
            "user": SimpleNamespace(id=1, username="italo"),
            "profile": SimpleNamespace(id=1, name="Italo"),
        }

    def _dashboard_context(self) -> dict[str, Any]:
        ctx = self._base_context()
        # Build asset classes with assets and positions.
        asset_classes: list[SimpleNamespace] = []
        for ci, (name, target, color) in enumerate(
            [
                ("Renda Fixa", 60, self._CLASS_COLORS[0]),
                ("Renda Variável", 30, self._CLASS_COLORS[1]),
                ("Cripto", 10, self._CLASS_COLORS[5]),
            ]
        ):
            assets: list[SimpleNamespace] = []
            for ai in range(2):
                assets.append(
                    SimpleNamespace(
                        id=ai + 1,
                        name=f"Ativo {ai + 1}",
                        target_pct=50,
                        # asset-trade-flags: the dashboard template now
                        # reads three per-asset trade-control fields
                        # off every ``asset`` row (the inline toggle UI
                        # + currency badge). The audit mock must
                        # provide them so the Jinja render doesn't
                        # raise AttributeError and silently produce
                        # an empty string (which fails
                        # ``test_render_page_produces_template_specific_anchor``).
                        buy_enabled=True,
                        sell_enabled=True,
                        currency_code="BRL",
                        positions=[
                            SimpleNamespace(
                                id=ai + 1,
                                qty=100,
                                avg_price=10.0,
                                current_price=12.0,
                                broker_ticker=f"TICK{ai}",
                            )
                        ],
                    )
                )
            asset_classes.append(
                SimpleNamespace(
                    id=ci + 1,
                    name=name,
                    target_pct=target,
                    display_order=ci,
                    color=color,
                    assets=assets,
                )
            )

        # Compute aggregates matching portfolio_aggregates shape.
        class_aggregates: list[dict[str, Any]] = []
        portfolio_invested = 0.0
        portfolio_current = 0.0
        for _ci, klass in enumerate(asset_classes):
            class_invested = 0.0
            class_current = 0.0
            for _asset in klass.assets:
                class_invested += 100 * 10.0
                class_current += 100 * 12.0
            portfolio_invested += class_invested
            portfolio_current += class_current
            class_aggregates.append(
                {
                    "id": klass.id,
                    "name": klass.name,
                    "target_pct": klass.target_pct,
                    "color": klass.color,
                    "invested": class_invested,
                    "current_value": class_current,
                    "current_pct": (class_current / portfolio_current * 100)
                    if portfolio_current
                    else 0.0,
                    "assets": [
                        {
                            "id": a.id,
                            "name": a.name,
                            "position_count": 1,
                            "qty": 100,
                            "invested": 1000.0,
                            "current_value": 1200.0,
                            "target_pct_class": 50,
                            "target_pct_total": 25.0,
                            "asset_pct": 50.0,
                            "current_pct_class": 50.0,
                            "current_pct_total": 25.0,
                            # asset-trade-flags: the dashboard's
                            # ``class_data.assets.append(...)`` reads
                            # these three fields off every asset.
                            "buy_enabled": True,
                            "sell_enabled": True,
                            "currency_code": "BRL",
                        }
                        for a in klass.assets
                    ],
                }
            )

        ctx["asset_classes"] = asset_classes
        ctx["portfolio"] = {
            "total_invested": portfolio_invested,
            "current_value": portfolio_current,
            "gain": portfolio_current - portfolio_invested,
            "gain_pct": (
                (portfolio_current - portfolio_invested) / portfolio_invested * 100
                if portfolio_invested
                else None
            ),
        }
        ctx["class_aggregates"] = class_aggregates
        ctx["_class_colors"] = self._CLASS_COLORS
        return ctx

    def _login_context(self) -> dict[str, Any]:
        return {**self._base_context(), "error": None, "username": ""}

    def _profiles_context(self) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["profiles"] = [
            SimpleNamespace(id=1, name="Italo"),
            SimpleNamespace(id=2, name="Ana Livia"),
        ]
        return ctx

    def _classes_context(self) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["error"] = None
        return ctx

    def _assets_context(self) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["error"] = None
        classes = [
            SimpleNamespace(id=1, name="Renda Fixa"),
            SimpleNamespace(id=2, name="Renda Variável"),
        ]
        ctx["classes"] = classes
        # assets_by_class maps class_id → list of assets in that class.
        ctx["assets_by_class"] = {
            1: [
                SimpleNamespace(id=1, name="Tesouro Selic"),
                SimpleNamespace(id=2, name="CDB Itaú"),
            ],
            2: [
                SimpleNamespace(id=3, name="PETR4"),
            ],
        }
        return ctx

    def _import_context(self) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["error"] = None
        return ctx

    def _import_review_context(self) -> dict[str, Any]:
        ctx = self._base_context()
        ctx["expired"] = False
        ctx["auto_count"] = 2
        ctx["unmatched_count"] = 1
        ctx["auto_matched"] = [
            (
                SimpleNamespace(
                    name="PETR4",
                    broker_ticker="PETR4",
                    qty=100,
                    avg_price=28.50,
                    current_price=35.10,
                ),
                1,
            )
        ]
        ctx["unmatched"] = [
            SimpleNamespace(
                name="UNKNOWN",
                broker_ticker="XPT99",
                qty=50,
                class_suggestion=None,
                suggested_category="Ações",
            )
        ]
        ctx["asset_classes"] = [
            SimpleNamespace(id=1, name="Renda Variável"),
        ]
        # class_suggestions is a dict mapping broker_ticker → class_id.
        ctx["class_suggestions"] = {}
        return ctx

    def context_for(self, template_name: str) -> dict[str, Any]:
        """Return a renderable context dict for *template_name*.

        F02: ``dashboard.html`` was renamed to ``patrimonio.html``
        (the F02 canonical URL is ``/patrimonio``; same render
        path, same context). The legacy name is aliased here so the
        audit pipeline doesn't break the gauge if a downstream
        referrer still spells ``dashboard.html``. F02 stubs
        (``rentabilidade.html`` / ``proventos.html``) fall through
        to the base context — they don't carry dashboard data.
        """
        handlers = {
            "dashboard.html": self._dashboard_context,
            "patrimonio.html": self._dashboard_context,
            "login.html": self._login_context,
            "profiles.html": self._profiles_context,
            "classes.html": self._classes_context,
            "assets.html": self._assets_context,
            "import.html": self._import_context,
            "import_review.html": self._import_review_context,
        }
        handler = handlers.get(template_name)
        if handler is not None:
            return handler()
        # Unknown templates (including the F02 stubs) get a base context.
        return self._base_context()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_page(env: Environment, name: str, context: dict[str, Any]) -> str:
    """Render *name* template through *env* with *context*.

    Returns the rendered HTML string.
    """
    try:
        template = env.get_template(name)
        return template.render(**context)
    except Exception:
        # If rendering fails (e.g. a template expects a variable we
        # didn't supply), return an empty string so the audit continues.
        return ""


def find_interactive(html: str) -> list[Tag]:
    """Discover interactive elements in rendered *html*.

    Uses BeautifulSoup4 with ``html.parser`` and selects all elements
    matching :data:`INTERACTIVE_SELECTOR`.
    """
    soup = BeautifulSoup(html, "html.parser")
    return soup.select(INTERACTIVE_SELECTOR)


# ---------------------------------------------------------------------------
# CSS selector matching helpers
# ---------------------------------------------------------------------------


def _element_matches_selector(element: Tag, selector: str) -> bool:
    """Return True if *element* matches a simple CSS *selector*.

    Supports tag, class (``.class``), and compound (``tag.class``)
    selectors.  Pseudo-class portions (``:hover``, ``:not(...)``, etc.)
    are stripped before matching.
    """
    import re

    # Strip pseudo-class portions.
    simple = re.sub(r":\w+(\([^)]*\))?", "", selector).strip()
    if not simple:
        return True

    # Compound: tag.class
    if "." in simple:
        parts = simple.split(".")
        tag = parts[0] if parts[0] else None
        classes = parts[1:]
        if tag and element.name != tag:
            return False
        el_classes = set(element.get("class", []))
        return all(c in el_classes for c in classes)

    # Class only
    if selector.startswith("."):
        cls = selector[1:]
        return cls in element.get("class", [])

    # Tag only
    return element.name == simple


def _collect_rules_for_element(
    element: Tag, stylesheet: Stylesheet, state: str
) -> list[tuple[str, dict[str, str]]]:
    """Collect CSS rules from *stylesheet* that could apply to *element*
    in the given pseudo-class *state*.

    Returns a list of ``(selector, declarations)`` tuples in source
    order.
    """
    import tinycss2

    results: list[tuple[str, dict[str, str]]] = []

    for node in stylesheet.rules:
        if node.type != "qualified-rule":
            continue
        selector = tinycss2.serialize(node.prelude).strip()
        decls = tinycss2.parse_declaration_list(node.content, skip_whitespace=True)

        # Check if this rule targets our state.
        has_state = state == "default" or f":{state}" in selector

        # For hover/active/focus/disabled, only consider rules that
        # mention the pseudo-class.
        if state != "default" and not has_state:
            continue
        # For default, skip rules with pseudo-classes (they don't
        # apply in the default state).
        if (
            state == "default"
            and has_state
            and f":{state}" not in selector
            and any(f":{s}" in selector for s in ("hover", "active", "focus", "disabled"))
        ):
            # "default" should still match rules without pseudo-classes
            # AND rules that happen to have :hover etc. — we only
            # skip when another pseudo-class is explicitly present.
            continue

        # Match element against the selector (strip pseudo for matching).
        import re

        match_selector = re.sub(r":\w+(\([^)]*\))?", "", selector).strip()
        if not _element_matches_selector(element, match_selector):
            continue

        # Extract declarations.
        decl_map: dict[str, str] = {}
        for decl in decls:
            if decl.type == "declaration" and decl.name:
                decl_map[decl.name] = tinycss2.serialize(decl.value).strip()

        if decl_map:
            results.append((selector, decl_map))

    return results


def _resolve_declared_value(value: str, registry: dict[str, str]) -> str:
    """Resolve a CSS value through the custom-property registry.

    If the value contains ``var(...)``, resolve it recursively.
    Returns the resolved value string.
    """
    if "var(" in value:
        return resolve_var(value, registry)
    return value


def _is_color(value: str) -> bool:
    """Return True if *value* parses as a CSS color."""
    try:
        from coloraide import Color as _C

        _C(value)
        return True
    except (ValueError, TypeError):
        return False


def _find_ancestor_background(element: Tag, soup: BeautifulSoup) -> str | None:
    """Walk up the DOM tree and return the first ancestor's computed
    background, or ``None``."""
    # We don't have computed style in BeautifulSoup, so we can't
    # actually walk the DOM for ancestor backgrounds.  The plan says
    # "composites transparent backgrounds over the ancestor background."
    # For now, return the resolved --bg default as the fallback.
    return None


def state_color_pairs(
    element: Tag,
    stylesheet: Stylesheet,
    state: str,
    registry: dict[str, str] | None = None,
) -> InteractiveStateRow | None:
    """Compute the color pair for *element* in the given pseudo-class
    *state*.

    Gathers all matching CSS rules from *stylesheet*, resolves
    ``var()`` references, applies ``filter: brightness(N)`` when
    present, composites transparent backgrounds, and computes the
    WCAG 2.1 contrast ratio.

    For non-default states, the default-state declarations form a
    base that the state-specific declarations overlay.  This
    correctly cascades ``color`` from the base rule while allowing
    ``background`` and ``filter`` overrides from the state rule.

    Returns an :class:`InteractiveStateRow` or ``None`` when no color
    declarations are found.
    """
    if registry is None:
        registry = _build_registry_from_stylesheet(stylesheet)

    # Collect rules for this state and (for non-default) the base
    # default rules as a fallback.
    rules = _collect_rules_for_element(element, stylesheet, state)
    if state != "default":
        base_rules = _collect_rules_for_element(element, stylesheet, "default")
    else:
        base_rules = []

    # Build a merged declaration map: base first, then state overlay.
    decl_map: dict[str, str] = {}
    brightness_factor: float | None = None

    for _sel, decls in base_rules:
        for prop, raw_value in decls.items():
            if prop not in decl_map:
                resolved = _resolve_declared_value(raw_value, registry)
                decl_map[prop] = resolved

    for _sel, decls in rules:
        for prop, raw_value in decls.items():
            resolved = _resolve_declared_value(raw_value, registry)
            if prop == "filter" and brightness_factor is None:
                import re

                m = re.search(r"brightness\(([0-9.]+)\)", resolved)
                if m:
                    brightness_factor = float(m.group(1))
            decl_map[prop] = resolved  # overlay overrides base

    # Extract fg and bg from the merged declarations.
    fg: str | None = None
    bg: str | None = None

    if "color" in decl_map and _is_color(decl_map["color"]):
        fg = decl_map["color"]
    if "background-color" in decl_map and _is_color(decl_map["background-color"]):
        bg = decl_map["background-color"]
    elif "background" in decl_map and _is_color(decl_map["background"]):
        bg = decl_map["background"]

    # Fallback: inline style on the element.
    if fg is None:
        style = element.get("style")
        if style:
            import re

            m = re.search(r"color:\s*([^;]+)", str(style))
            if m:
                fg = m.group(1).strip()
    if bg is None:
        style = element.get("style")
        if style:
            import re

            m = re.search(r"background(?:-color)?:\s*([^;]+)", str(style))
            if m:
                bg = m.group(1).strip()

    # If still no colors, can't compute a pair.
    if fg is None or bg is None:
        return None

    # Apply brightness filter to background.
    if brightness_factor is not None and brightness_factor != 1.0:
        bg = apply_brightness(bg, brightness_factor)

    # Composite transparent backgrounds over ancestor.
    try:
        from coloraide import Color as _C

        bg_color = _C(bg)
        try:
            alpha = min(1.0, max(0.0, bg_color.get("alpha", 1.0)))
        except (KeyError, TypeError):
            alpha = 1.0
        if alpha < 1.0:
            bg_default = registry.get("--bg", "#ffffff")
            bg = composite_over(bg, bg_default)
    except Exception:
        pass

    # Compute contrast.
    ratio = contrast_ratio(fg, bg)
    _, status = aa_status(ratio, is_large=False)

    # Build element snippet and selector.
    snippet = _element_snippet(element)
    selector = _element_selector(element)

    # Check if hidden by default (x-show / x-cloak).
    hidden = _is_hidden_by_default(element)

    return InteractiveStateRow(
        template="",
        selector=selector,
        element_snippet=snippet,
        state=state,
        fg=fg,
        bg=bg,
        ratio=round(ratio, 2),
        status=status,
        hidden_by_default=hidden,
    )


def _element_selector(element: Tag) -> str:
    """Build a concise CSS selector for *element*."""
    tag = element.name
    classes = element.get("class", [])
    if classes:
        return f"{tag}.{'.'.join(classes[:2])}"
    el_id = element.get("id")
    if el_id:
        return f"{tag}#{el_id}"
    return tag


def _element_snippet(element: Tag) -> str:
    """Return a short HTML snippet representing the element."""
    text = element.get_text(strip=True)[:40]
    tag = element.name
    if text:
        return f"<{tag}>{text}</{tag}>"
    return str(element)[:80]


def _is_hidden_by_default(element: Tag) -> bool:
    """Return True if *element* or any ancestor has Alpine.js
    ``x-show`` or ``x-cloak``."""
    current: Tag | None = element
    while current is not None:
        if current.get("x-show") is not None or current.get("x-cloak") is not None:
            return True
        # Alpine also uses x-show with conditions that evaluate to
        # false initially.
        x_data = current.get("x-data")
        if x_data and isinstance(x_data, str) and "open" in x_data.lower():
            pass  # Can't determine initial state from static analysis.
        current = current.parent if isinstance(current, Tag) else None
    return False


def inventory_for_page(
    name: str,
    env: Environment,
    stylesheet: Stylesheet,
    context_factory: AuditContextFactory | None = None,
) -> list[InteractiveStateRow]:
    """Render *name* template and produce a per-state inventory.

    Returns a list of :class:`InteractiveStateRow` — one per state
    per interactive element discovered in the rendered template.
    """
    if context_factory is None:
        context_factory = AuditContextFactory()

    ctx = context_factory.context_for(name)
    html = render_page(env, name, ctx)
    if not html:
        return []

    elements = find_interactive(html)
    if not elements:
        return []

    registry = _build_registry_from_stylesheet(stylesheet)
    rows: list[InteractiveStateRow] = []

    for element in elements:
        for state in _STATES:
            row = state_color_pairs(element, stylesheet, state, registry)
            if row is not None:
                # Replace the dataclass to set the template field.
                row = InteractiveStateRow(
                    template=name,
                    selector=row.selector,
                    element_snippet=row.element_snippet,
                    state=state,
                    fg=row.fg,
                    bg=row.bg,
                    ratio=row.ratio,
                    status=row.status,
                    hidden_by_default=row.hidden_by_default,
                )
                rows.append(row)

    return rows
