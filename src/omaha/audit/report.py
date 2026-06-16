"""Static HTML report generator for the Phase 1 audit.

Renders a self-contained Portuguese report titled
"Inventário de contraste — Omaha" with summary cards, table of
contents, per-page interactive-element inventory, CSS token
inventory, and a consolidated failure log.

The module uses a dedicated Jinja2 environment so it never touches
the FastAPI request/response cycle.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from omaha.audit.css_parser import TokenInventoryRow, color_token_inventory, parse_stylesheet
from omaha.audit.inventory import (
    AuditContextFactory,
    InteractiveStateRow,
    inventory_for_page,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_report(
    inventory_rows: list[InteractiveStateRow],
    token_rows: list[TokenInventoryRow],
    generation_time: str,
    show_only_failures: bool = False,
) -> str:
    """Render the full audit report as an HTML string.

    Parameters
    ----------
    inventory_rows:
        Per-state color pairs from :func:`omaha.audit.inventory.inventory_for_page`.
    token_rows:
        CSS token inventory from :func:`omaha.audit.css_parser.color_token_inventory`.
    generation_time:
        Human-readable timestamp for the report header.
    show_only_failures:
        Whether the "Mostrar apenas falhas" toggle starts checked.
    """
    # Deduplicate page list in inventory order.
    seen: set[str] = set()
    pages: list[str] = []
    for row in inventory_rows:
        if row.template not in seen:
            seen.add(row.template)
            pages.append(row.template)

    # Compute summary counts.
    total_interactive = len({(r.template, r.selector) for r in inventory_rows})
    total_failures = sum(1 for r in inventory_rows if r.status == "Falha")
    total_tokens = len(token_rows)

    summary = {
        "total_interactive": total_interactive,
        "total_tokens": total_tokens,
        "total_failures": total_failures,
    }

    # Build failure log grouped by page.
    failure_log: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
    for row in inventory_rows:
        if row.status != "Falha":
            continue
        group = row.template
        if group not in failure_log:
            failure_log[group] = []
        failure_log[group].append(
            {
                "selector": row.selector,
                "state": row.state,
                "fg": row.fg,
                "bg": row.bg,
                "ratio": row.ratio,
            }
        )
    # Also group token failures.
    token_failures = [r for r in token_rows if r.status == "Falha"]
    if token_failures:
        failure_log["Tokens CSS"] = [
            {
                "selector": r.token,
                "state": "—",
                "fg": r.computed_value,
                "bg": r.adjacent_background,
                "ratio": r.ratio,
            }
            for r in token_failures
        ]

    # Set up a dedicated Jinja2 environment for the audit report.
    package_dir = Path(__file__).resolve().parent.parent
    templates_dir = package_dir / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("audit_report.html")

    return template.render(
        generation_time=generation_time,
        summary=summary,
        inventory_rows=inventory_rows,
        token_rows=token_rows,
        pages=pages,
        failure_log=failure_log,
        show_only_failures=show_only_failures,
    )


def generate_report(
    css_path: Path,
    templates_dir: Path,
    output_path: Path,
) -> Path:
    """Run the full audit pipeline and write the report to *output_path*.

    Parameters
    ----------
    css_path:
        Path to the application CSS file (e.g. ``src/omaha/static/app.css``).
    templates_dir:
        Path to the Jinja2 templates directory.
    output_path:
        Path where the HTML report will be written.

    Returns
    -------
    Path
        The *output_path* where the report was saved.

    Raises
    ------
    ValueError
        If *css_path* does not exist or is outside the repository root.
    """
    repo_root = Path(__file__).resolve().parents[3]
    resolved_css = (repo_root / css_path).resolve()
    if repo_root not in resolved_css.parents and resolved_css != repo_root:
        raise ValueError(f"CSS path {css_path!s} is outside the repository root")

    resolved_tpl = (repo_root / templates_dir).resolve()
    if repo_root not in resolved_tpl.parents and resolved_tpl != repo_root:
        raise ValueError(f"Templates path {templates_dir!s} is outside the repository root")

    # Parse the stylesheet.
    stylesheet = parse_stylesheet(css_path)

    # Build token inventory.
    token_rows = color_token_inventory(stylesheet)

    # Set up Jinja2 for template rendering.
    env = Environment(loader=FileSystemLoader(resolved_tpl))
    env.filters["brl"] = lambda v, *a, **kw: f"R${v:,.2f}"

    # Inventory every page template.
    factory = AuditContextFactory()
    page_names = [
        "base.html",
        "dashboard.html",
        "classes.html",
        "assets.html",
        "import.html",
        "import_review.html",
        "login.html",
        "profiles.html",
    ]

    all_rows: list[InteractiveStateRow] = []
    for name in page_names:
        rows = inventory_for_page(name, env, stylesheet, factory)
        all_rows.extend(rows)

    # Generate timestamp.
    now = datetime.now(UTC)
    generation_time = now.strftime("%d/%m/%Y %H:%M UTC")

    # Render report.
    html = render_report(all_rows, token_rows, generation_time)

    # Write to disk.  The output path is allowed outside the repo root
    # (e.g. to a temp directory during tests).  Only input paths are
    # subject to the path-traversal guard.
    resolved_output = (
        (repo_root / output_path).resolve()
        if not output_path.is_absolute()
        else output_path.resolve()
    )
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(html, encoding="utf-8")

    return output_path
