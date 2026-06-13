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

import re
from dataclasses import dataclass, field
from pathlib import Path

import tinycss2

from omaha.audit.color_resolver import aa_status, contrast_ratio


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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Regex for var(--name, fallback?) — captures the property name and an
# optional fallback value.  The fallback may itself be another var().
_VAR_RE = re.compile(r"var\(\s*(--[^,)]+)\s*(?:,\s*([^)]+))?\s*\)")

# Max recursion depth for var() resolution — guards against accidental
# circular references (e.g. --a: var(--b); --b: var(--a)).
_MAX_VAR_DEPTH = 10

# Token name → default adjacent background token name.
# Foreground-ish tokens are compared against the body background (--bg).
# Surface-ish tokens are compared against the default text color (--ink)
# — the ratio answers "is text readable on this surface?".
_FOREGROUND_TOKENS: set[str] = {
    "--ink",
    "--ink-muted",
    "--fg",
    "--muted",
    "--accent-ink",
    "--positive",
    "--negative",
    "--error-fg",
    "--class-1",
    "--class-2",
    "--class-3",
    "--class-4",
    "--class-5",
    "--class-6",
    "--color-focus",
}
_SURFACE_TOKENS: set[str] = {
    "--bg",
    "--surface",
    "--surface-sunk",
    "--error-bg",
    "--accent",
}

# Sentinel for unresolvable var() references.
_UNRESOLVED = object()


def _is_color_value(value: str) -> bool:
    """Return True if *value* looks like a CSS color to ``coloraide``."""
    try:
        from coloraide import Color as _C

        _C(value)
        return True
    except (ValueError, TypeError):
        return False


def _extract_declarations(
    rule: tinycss2.ast.QualifiedRule,
) -> dict[str, str]:
    """Extract declaration name → serialized value from a qualified rule.

    Skips whitespace tokens and non-declaration nodes.
    """
    decls: dict[str, str] = {}
    # tinycss2 places declaration tokens inside the rule's content block.
    nodes = tinycss2.parse_declaration_list(rule.content, skip_whitespace=True)
    for node in nodes:
        if node.type == "declaration":
            name = node.name
            # Serialize the value — tinycss2 returns a list of component
            # value tokens; serialize turns them back to a CSS string.
            value = tinycss2.serialize(node.value).strip()
            if name and value:
                decls[name] = value
    return decls


def _selector_text(rule: tinycss2.ast.QualifiedRule) -> str:
    """Return the serialized selector text of a qualified rule."""
    return tinycss2.serialize(rule.prelude).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_stylesheet(path: Path) -> Stylesheet:
    """Read a CSS file and return a parsed :class:`Stylesheet`.

    Uses ``tinycss2.parse_stylesheet`` with comments and whitespace
    nodes skipped so the rule list contains only qualified rules and
    at-rules.

    The *path* is resolved under the repo root to prevent path
    traversal (threat T-01-02-01).
    """
    # Resolve path under repo root — reject parent-dir escapes.
    repo_root = Path(__file__).resolve().parents[3]
    resolved = (repo_root / path).resolve()
    if repo_root not in resolved.parents and resolved != repo_root:
        raise ValueError(f"Path {path!s} is outside the repository root")
    css_text = resolved.read_text(encoding="utf-8")
    rules = tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True)
    return Stylesheet(rules=rules, raw_text=css_text)


def resolve_var(value: str, registry: dict[str, str], depth: int = 0) -> str:
    """Resolve ``var(--name)`` tokens in *value* against *registry*.

    Substitution is recursive — if a variable's resolved value still
    contains ``var()`` references, they are resolved in turn (up to
    ``_MAX_VAR_DEPTH`` iterations).  Unknown variable names are
    replaced with their fallback if provided, otherwise left as-is.

    Examples::

        >>> resolve_var("var(--ink)", {"--ink": "oklch(0.2 0.01 60)"})
        'oklch(0.2 0.01 60)'
        >>> resolve_var("var(--missing, #fff)", {})
        '#fff'
    """
    if depth > _MAX_VAR_DEPTH:
        return value  # bail out — likely a circular reference

    def _sub(m: re.Match) -> str:
        name = m.group(1).strip()
        fallback_raw = m.group(2)
        fallback = fallback_raw.strip() if fallback_raw else name

        resolved = registry.get(name)
        if resolved is None:
            # Unknown variable — use fallback if it differs from the name.
            if fallback != name and fallback.startswith("--"):
                inner = registry.get(fallback)
                return inner if inner is not None else fallback
            return fallback

        # The resolved value may itself reference another variable.
        if "var(" in resolved:
            return resolve_var(resolved, registry, depth + 1)
        return resolved

    result = _VAR_RE.sub(_sub, value)
    # After one pass, there might still be var() refs from fallback
    # chains — iterate until stable or out of depth.
    if "var(" in result and depth < _MAX_VAR_DEPTH:
        return resolve_var(result, registry, depth + 1)
    return result


def _build_registry(stylesheet: Stylesheet) -> dict[str, str]:
    """Walk qualified rules and return a ``name → serialized-value``
    map of all ``--*`` custom properties (raw, not yet resolved).
    """
    registry: dict[str, str] = {}
    for node in stylesheet.rules:
        if node.type == "qualified-rule":
            selector = _selector_text(node)
            decls = _extract_declarations(node)
            for name, value in decls.items():
                if name.startswith("--"):
                    # First-definition wins (source order).  A token
                    # declared in :root takes precedence over a later
                    # re-declaration in a component rule — but a
                    # component-scoped override that appears *after*
                    # :root should also be collected for completeness.
                    # We keep a simple first-wins registry; the
                    # inventory can report component overrides
                    # separately if needed.
                    if name not in registry:
                        registry[name] = value
    return registry


def _adjacent_token(name: str) -> str:
    """Return the default adjacent-background token name for *name*."""
    if name in _FOREGROUND_TOKENS:
        return "--bg"
    if name in _SURFACE_TOKENS:
        return "--ink"
    # Unknown token — guess based on name heuristics.
    name_lower = name.lower()
    if any(kw in name_lower for kw in ("ink", "fg", "text", "color", "positive", "negative")):
        return "--bg"
    return "--ink"


def color_token_inventory(stylesheet: Stylesheet) -> list[TokenInventoryRow]:
    """Walk a parsed :class:`Stylesheet` and return the color token inventory.

    For every ``--*`` custom property defined in ``:root`` or a
    component-scoped rule whose **resolved** value is a CSS color, a
    :class:`TokenInventoryRow` is created with:

    * ``token`` — the property name (e.g. ``"--ink"``)
    * ``computed_value`` — the fully-resolved color string
    * ``adjacent_background`` — the default adjacent color against
      which contrast is measured
    * ``ratio`` — the WCAG 2.1 contrast ratio (float)
    * ``status`` — ``"Passa"`` or ``"Falha"``

    Tokens that resolve to non-color values (e.g. ``--border``,
    ``--spacing``) are silently excluded.
    """
    raw_registry = _build_registry(stylesheet)
    if not raw_registry:
        return []

    # Resolve every custom-property value through var() chains.
    resolved: dict[str, str] = {}
    for name, value in raw_registry.items():
        rv = resolve_var(value, raw_registry)
        if rv and not rv.startswith("--"):  # unresolved var() left as-is
            resolved[name] = rv

    # Fallback defaults for the two reference tokens.
    ink_default = resolved.get("--ink", "#000000")
    bg_default = resolved.get("--bg", "#ffffff")

    rows: list[TokenInventoryRow] = []
    for name, computed in sorted(resolved.items()):
        if not _is_color_value(computed):
            continue

        adj_token = _adjacent_token(name)
        if adj_token == "--bg":
            adjacent_value = bg_default
        elif adj_token == "--ink":
            adjacent_value = ink_default
        else:
            adjacent_value = resolved.get(adj_token, bg_default)

        ratio = contrast_ratio(computed, adjacent_value)
        _, status = aa_status(ratio, is_large=False)

        rows.append(
            TokenInventoryRow(
                token=name,
                computed_value=computed,
                adjacent_background=adjacent_value,
                ratio=round(ratio, 2),
                status=status,
            )
        )

    return rows
