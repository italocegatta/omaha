"""CSS parser and property resolver for the contrast audit.

Parses CSS files with ``tinycss2``, builds a custom-property registry
from ``:root`` and component-scoped rules, resolves ``var()``
substitutions recursively, and inventories every ``--*`` custom
property whose resolved value parses as a color.

The module is intentionally dependency-free beyond ``tinycss2`` — it
does not talk to the DB, FastAPI, or Jinja2. The unit-tested
contract:

* :func:`parse_stylesheet` reads a CSS file from disk and returns
  parsed qualified rules and declarations.
* :func:`resolve_var` substitutes ``var(…)`` tokens recursively
  against a custom-property registry.
* :func:`color_token_inventory` walks the parsed stylesheet and
  returns a list of :class:`TokenInventoryRow` — one for every
  ``--*`` custom property whose resolved value is a color.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tinycss2


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CssRule:
    """A single qualified CSS rule extracted from a parsed stylesheet.

    ``selector`` is the serialized prelude (e.g. ``":root"``,
    ``".btn-primary:hover"``). ``declarations`` maps property names
    (e.g. ``"--bg"``, ``"color"``) to their serialized values.
    """

    selector: str
    declarations: dict[str, str]


@dataclass(frozen=True)
class CssToken:
    """A resolved custom property that holds a color value.

    ``name`` is the property name with the leading ``--`` (e.g.
    ``"--ink"``). ``value`` is the resolved, substituted value
    after all ``var()`` and ``color-mix()`` references have been
    expanded.
    """

    name: str
    value: str


@dataclass(frozen=True)
class TokenInventoryRow:
    """One row in the CSS token inventory.

    ``token`` is the property name (e.g. ``"--ink"``).
    ``computed_value`` is the fully-resolved CSS color string.
    ``adjacent_background`` is the background against which
    contrast is computed (typically ``"#ffffff"`` or the resolved
    ``--bg`` / ``--surface`` value).
    ``ratio`` is the WCAG 2.1 contrast ratio (float).
    ``status`` is ``"Passa"`` when the ratio meets the AA
    threshold, ``"Falha"`` otherwise.
    """

    token: str
    computed_value: str
    adjacent_background: str
    ratio: float = 0.0
    status: str = "Falha"


# ---------------------------------------------------------------------------
# Stylesheet — a thin wrapper that carries the rules + a raw reference
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Stylesheet:
    """Parsed representation of a CSS file.

    ``rules`` is the raw ``tinycss2`` parse tree (list of
    ``tinycss2.ast.Node``). Callers should not iterate this list
    directly; use :func:`color_token_inventory` or the helper
    functions in this module.

    ``raw_text`` is the original CSS source string, kept so
    downstream code can re-parse or inspect it.
    """

    rules: list[tinycss2.ast.Node] = field(default_factory=list)
    raw_text: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_stylesheet(path: Path) -> Stylesheet:
    """Read a CSS file and return a parsed :class:`Stylesheet`.

    Uses ``tinycss2.parse_stylesheet`` with comments and whitespace
    nodes skipped so the rule list contains only qualified rules and
    at-rules.
    """
    css_text = path.read_text(encoding="utf-8")
    rules = tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True)
    return Stylesheet(rules=rules, raw_text=css_text)


def resolve_var(value: str, registry: dict[str, str]) -> str:
    """Resolve ``var(--name)`` tokens in *value* against *registry*.

    Substitution is recursive — if a variable's fallback is another
    ``var()`` reference, it is resolved in turn. Returns the
    substituted string. Unknown variable names (not in *registry*)
    are left as-is.
    """
    return value  # placeholder — Task 3 implements the full resolver


def color_token_inventory(stylesheet: Stylesheet) -> list[TokenInventoryRow]:
    """Walk a parsed :class:`Stylesheet` and return the color token inventory.

    For every ``--*`` custom property defined in ``:root`` or a
    component-scoped rule whose resolved value is a CSS color, a
    :class:`TokenInventoryRow` is created pairing the token with its
    adjacent background (derived from the token name) and a
    placeholder contrast ratio of ``0.0`` / ``"Falha"``.

    Contrast ratios are computed later by :mod:`omaha.audit.color_resolver`.
    """
    return []  # placeholder — Task 3 implements the full inventory
