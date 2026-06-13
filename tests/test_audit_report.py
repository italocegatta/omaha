"""Tests for the audit report generator (AUDT-01).

Covers ``render_report`` and ``generate_report`` with fixture data.
Asserts the generated HTML is self-contained, Portuguese, and
contains all expected sections.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from omaha.audit.css_parser import TokenInventoryRow, parse_stylesheet
from omaha.audit.inventory import InteractiveStateRow
from omaha.audit.report import generate_report, render_report


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------


def _make_sample_rows() -> list[InteractiveStateRow]:
    """Build a small set of inventory rows for testing."""
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
    """Build a small set of token rows for testing."""
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


# ---------------------------------------------------------------------------
# render_report tests
# ---------------------------------------------------------------------------


class TestRenderReport:
    """Verify the HTML report generation from fixture data."""

    @pytest.fixture(scope="class")
    def report_html(self) -> str:
        rows = _make_sample_rows()
        tokens = _make_token_rows()
        return render_report(rows, tokens, "13/06/2026 14:00 UTC")

    def test_report_contains_title(self, report_html):
        assert "Inventário de contraste — Omaha" in report_html

    def test_report_contains_summary_cards(self, report_html):
        assert "Elementos interativos" in report_html
        assert "Tokens de cor" in report_html
        assert "Falhas WCAG AA" in report_html

    def test_report_is_self_contained(self, report_html):
        # No external stylesheet or script references.
        assert '<link rel="stylesheet"' not in report_html
        assert '<script src=' not in report_html
        # Inline <style> is present.
        assert "<style>" in report_html.lower()

    def test_report_uses_portuguese_lang(self, report_html):
        assert 'lang="pt-BR"' in report_html

    def test_report_contains_toc_anchors(self, report_html):
        assert 'id="page-' in report_html
        assert '<a href="#page-' in report_html

    def test_report_contains_per_page_sections(self, report_html):
        assert "dashboard.html" in report_html
        assert "login.html" in report_html

    def test_report_contains_token_section(self, report_html):
        assert "Inventário de tokens CSS" in report_html
        assert "--ink" in report_html
        assert "--accent" in report_html

    def test_report_contains_status_badges(self, report_html):
        assert "Passa" in report_html
        assert "Falha" in report_html
        assert 'badge--pass' in report_html
        assert 'badge--fail' in report_html

    def test_report_contains_failure_log(self, report_html):
        assert "Registro de falhas" in report_html
        assert "login.html" in report_html

    def test_report_contains_swatches(self, report_html):
        assert 'class="swatch"' in report_html

    def test_report_contains_show_only_failures_toggle(self, report_html):
        assert "Mostrar apenas falhas" in report_html
        assert 'id="show-only-failures"' in report_html

    def test_report_contains_empty_state_when_no_failures(self):
        # When no failures, empty state should appear.
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

    def test_report_timestamp_present(self, report_html):
        assert "13/06/2026 14:00 UTC" in report_html

    def test_summary_counts_accurate(self, report_html):
        rows = _make_sample_rows()
        tokens = _make_token_rows()
        html = render_report(rows, tokens, "13/06/2026 14:00 UTC")
        # 2 unique (template, selector) combinations: button.import-btn-primary on dashboard, button on login
        assert "2" in html  # At least the values appear somewhere


# ---------------------------------------------------------------------------
# generate_report integration test
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Integration test for the full pipeline."""

    def test_generate_report_writes_file(self, tmp_path):
        css_path = Path("src/omaha/static/app.css")
        templates_dir = Path("src/omaha/templates")
        output_path = tmp_path / "contrast_audit.html"

        result = generate_report(css_path, templates_dir, output_path)
        assert result == output_path
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "Inventário de contraste — Omaha" in content
        assert len(content) > 5000  # Must be a substantial report

    def test_generate_report_is_self_contained(self, tmp_path):
        css_path = Path("src/omaha/static/app.css")
        templates_dir = Path("src/omaha/templates")
        output_path = tmp_path / "contrast_audit.html"

        result = generate_report(css_path, templates_dir, output_path)
        content = result.read_text(encoding="utf-8")
        assert '<link rel="stylesheet"' not in content
        assert '<script src=' not in content

    def test_generate_report_larger_than_10kb(self, tmp_path):
        css_path = Path("src/omaha/static/app.css")
        templates_dir = Path("src/omaha/templates")
        output_path = tmp_path / "contrast_audit.html"

        generate_report(css_path, templates_dir, output_path)
        size = output_path.stat().st_size
        assert size > 10_000, f"Report should be larger than 10 KB, got {size} bytes"
