"""Tests for the audit report generator (AUDT-01) — pure-function subset.

Unit tests for :mod:`omaha.audit.report` that do not touch the live
``omaha.main.app`` or ``app.css``.  The full end-to-end pipeline
(``generate_report`` + ``cli.main``) lives in
``tests/audit_integration/test_report_pipeline.py``.

Tests in this file use a 12-row fixture set; assertions match
specific HTML substrings paired with a label so a failure points at
the missing piece without dumping the whole report.
"""

from __future__ import annotations

import pytest

from omaha.audit.css_parser import TokenInventoryRow
from omaha.audit.inventory import InteractiveStateRow
from omaha.audit.report import render_report

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------


def _make_sample_rows() -> list[InteractiveStateRow]:
    """Build a small inventory set for the report tests."""
    return [
        InteractiveStateRow(
            template="dashboard.html",
            selector="button.import-btn-primary",
            element_snippet="<button>Importar CSV</button>",
            state="default",
            fg="#ffffff",
            bg="#0a66c2",
            ratio=7.5,
            status="Passa",
            hidden_by_default=False,
        ),
        InteractiveStateRow(
            template="dashboard.html",
            selector="button.import-btn-primary",
            element_snippet="<button>Importar CSV</button>",
            state="hover",
            fg="#ffffff",
            bg="#0b70d6",
            ratio=7.0,
            status="Passa",
            hidden_by_default=False,
        ),
        InteractiveStateRow(
            template="login.html",
            selector="button",
            element_snippet="<button>Entrar</button>",
            state="default",
            fg="#000000",
            bg="#cccccc",
            ratio=3.2,
            status="Falha",
            hidden_by_default=False,
        ),
    ]


def _make_token_rows() -> list[TokenInventoryRow]:
    """Build a small token set for the report tests."""
    return [
        TokenInventoryRow(
            token="--ink",
            computed_value="oklch(0.20 0.01 60)",
            adjacent_background="oklch(0.975 0.003 60)",
            ratio=15.5,
            status="Passa",
        ),
        TokenInventoryRow(
            token="--accent",
            computed_value="oklch(0.42 0.09 150)",
            adjacent_background="#ffffff",
            ratio=4.2,
            status="Falha",
        ),
    ]


@pytest.fixture(scope="module")
def report_html() -> str:
    """A rendered report with both inventory and token data."""
    return render_report(
        _make_sample_rows(),
        _make_token_rows(),
        "13/06/2026 14:00 UTC",
    )


# ---------------------------------------------------------------------------
# render_report — substring sweep
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "substring,label",
    [
        ("Inventário de contraste — Omaha", "title"),
        ("Elementos interativos", "summary card — interactive elements"),
        ("Tokens de cor", "summary card — color tokens"),
        ("Falhas WCAG AA", "summary card — AA failures"),
        ('lang="pt-BR"', "Portuguese lang attribute"),
        ('id="page-', "TOC anchor id"),
        ('<a href="#page-', "TOC anchor link"),
        ("dashboard.html", "per-page section: dashboard"),
        ("login.html", "per-page section: login"),
        ("Inventário de tokens CSS", "token inventory section"),
        ("badge--pass", "pass badge class"),
        ("badge--fail", "fail badge class"),
    ],
)
def test_render_report_contains_substring(report_html: str, substring: str, label: str) -> None:
    """render_report emits each expected structural substring (label-tagged)."""
    assert substring in report_html, f"missing {label!r}: {substring!r}"


def test_render_report_contains_timestamp(report_html: str) -> None:
    """render_report embeds the generation_time string verbatim."""
    assert "13/06/2026 14:00 UTC" in report_html


def test_render_report_is_self_contained(report_html: str) -> None:
    """No external stylesheet or script references; inline <style> present."""
    assert '<link rel="stylesheet"' not in report_html
    assert "<script src=" not in report_html
    assert "<style>" in report_html.lower()


def test_render_report_no_failures_shows_empty_state() -> None:
    """When every row passes, the report shows the documented empty-state copy."""
    rows = [
        InteractiveStateRow(
            template="test.html",
            selector="button.ok",
            element_snippet="<button>OK</button>",
            state="default",
            fg="#fff",
            bg="#000",
            ratio=21.0,
            status="Passa",
            hidden_by_default=False,
        )
    ]
    html = render_report(rows, [], "13/06/2026 14:00 UTC")
    assert "Nenhuma falha de contraste encontrada" in html
    assert "Todos os pares de cores auditados" in html


# ---------------------------------------------------------------------------
# CLI _parse_args
# ---------------------------------------------------------------------------


def test_parse_args_defaults() -> None:
    """``_parse_args([])`` returns the documented default paths."""
    from omaha.audit.cli import _parse_args

    args = _parse_args([])
    assert args.css == "src/omaha/static/app.css"
    assert args.templates_dir == "src/omaha/templates"
    assert args.output == "reports/contrast_audit.html"


@pytest.mark.parametrize(
    "argv,expected_css,expected_templates,expected_output",
    [
        (
            ["--css", "custom.css"],
            "custom.css",
            "src/omaha/templates",
            "reports/contrast_audit.html",
        ),
        (
            ["--css", "x.css", "--templates-dir", "t/", "--output", "o.html"],
            "x.css",
            "t/",
            "o.html",
        ),
        (
            ["--templates-dir", "alt/templates"],
            "src/omaha/static/app.css",
            "alt/templates",
            "reports/contrast_audit.html",
        ),
    ],
)
def test_parse_args_custom_values(
    argv: list[str],
    expected_css: str,
    expected_templates: str,
    expected_output: str,
) -> None:
    """``_parse_args`` honours each documented flag independently."""
    from omaha.audit.cli import _parse_args

    args = _parse_args(argv)
    assert args.css == expected_css
    assert args.templates_dir == expected_templates
    assert args.output == expected_output
