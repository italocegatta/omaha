"""Integration tests for the audit report pipeline.

Runs the end-to-end :func:`omaha.audit.report.generate_report` and
the ``omaha.audit.cli.main`` entry point against the live
``src/omaha/static/app.css`` and ``src/omaha/templates/``. Marked
``@pytest.mark.integration`` so it is excluded from the unit
subset (``task test-unit``) and runs under ``task test-integration``.

The fixtures in this file (``tmp_path``, ``client``, etc.) come from
the parent :mod:`tests.conftest` — pytest's hierarchical conftest
discovery applies.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------


def test_generate_report_writes_file(tmp_path: Path) -> None:
    """generate_report runs the full pipeline and writes a non-empty HTML file."""
    from omaha.audit.report import generate_report

    css_path = Path("src/omaha/static/app.css")
    templates_dir = Path("src/omaha/templates")
    output_path = tmp_path / "contrast_audit.html"

    result = generate_report(css_path, templates_dir, output_path)

    assert result == output_path
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Inventário de contraste — Omaha" in content
    assert len(content) > 5_000, f"report unexpectedly small: {len(content)} bytes"


def test_generate_report_is_self_contained(tmp_path: Path) -> None:
    """The generated HTML carries no external stylesheet or script refs."""
    from omaha.audit.report import generate_report

    css_path = Path("src/omaha/static/app.css")
    templates_dir = Path("src/omaha/templates")
    output_path = tmp_path / "contrast_audit.html"

    generate_report(css_path, templates_dir, output_path)
    content = output_path.read_text(encoding="utf-8")

    assert '<link rel="stylesheet"' not in content
    assert "<script src=" not in content


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def test_cli_writes_report(tmp_path: Path) -> None:
    """``cli.main`` with default-shaped args writes the report and exits 0."""
    from omaha.audit.cli import main

    output_path = tmp_path / "contrast_audit.html"
    exit_code = main(
        [
            "--css",
            "src/omaha/static/app.css",
            "--templates-dir",
            "src/omaha/templates",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert "Inventário de contraste — Omaha" in output_path.read_text(encoding="utf-8")


def test_cli_missing_css_returns_nonzero(tmp_path: Path) -> None:
    """``cli.main`` exits 1 when the CSS path doesn't exist."""
    from omaha.audit.cli import main

    output_path = tmp_path / "out.html"
    exit_code = main(
        [
            "--css",
            "nonexistent.css",
            "--templates-dir",
            "src/omaha/templates",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 1
