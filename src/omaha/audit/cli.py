"""CLI entry point for the Omaha contrast audit.

Generates the self-contained "Inventário de contraste — Omaha" HTML
report by analysing the application's CSS and rendered templates.

Usage::

    uv run python scripts/generate_contrast_audit.py
    uv run python -m omaha.audit.cli --output reports/my-audit.html
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from omaha.audit.report import generate_report


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the Omaha contrast audit report. "
            "Parses app.css, renders every page template, and produces "
            "a self-contained HTML inventory of interactive-element "
            "color pairs with WCAG 2.1 AA contrast ratios."
        )
    )
    parser.add_argument(
        "--css",
        default="src/omaha/static/app.css",
        help=(
            "Path to the application CSS file, relative to the "
            "repository root. Default: %(default)s"
        ),
    )
    parser.add_argument(
        "--templates-dir",
        default="src/omaha/templates",
        help=(
            "Path to the Jinja2 templates directory, relative to "
            "the repository root. Default: %(default)s"
        ),
    )
    parser.add_argument(
        "--output",
        default="reports/contrast_audit.html",
        help=(
            "Path where the HTML report will be written, relative "
            "to the repository root. Default: %(default)s"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the contrast audit and print the output path on success.

    Returns 0 on success, 1 on failure.
    """
    args = _parse_args(argv)
    css_path = Path(args.css)
    templates_dir = Path(args.templates_dir)
    output_path = Path(args.output)

    try:
        result = generate_report(
            css_path=css_path,
            templates_dir=templates_dir,
            output_path=output_path,
        )
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"audit FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"Inventário gerado: {result}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
