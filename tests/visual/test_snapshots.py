"""Committed visual baselines for key Omaha pages and states."""

from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import (
    assert_structural_content,
    compare_or_update_screenshot,
    login_as_italo,
)

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "sample_broker.csv"

T32_PRUNED_REASON = (
    "T32 owner-prioritized selective pruning: case remains versioned and auditable; "
    "standard blocking visual lane retains canonical replacement coverage."
)
T32_PRUNED = pytest.mark.t32_pruned(reason=T32_PRUNED_REASON)


def test_login_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    visual_page.goto(f"{live_url_visual}/login")
    assert_structural_content(
        visual_page,
        'input[name="username"]',
        'input[name="password"]',
        'button[type="submit"]',
        text="Entrar",
    )
    compare_or_update_screenshot(visual_page, "login", visual_viewport)


def test_patrimonio_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    assert_structural_content(
        visual_page,
        '[data-testid="patrimonio-portfolio-header"]',
        '[data-testid="class-summary-row"]',
        text="R$",
    )
    compare_or_update_screenshot(visual_page, "patrimonio", visual_viewport)


@T32_PRUNED
def test_assets_table_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    """Retained T32 desktop duplicate; canonical asset-table E2E owns contract."""
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    assert_structural_content(
        visual_page,
        '[data-testid="asset-table"]',
        '[data-testid="dashboard-asset-row"]',
        text="R$",
    )
    compare_or_update_screenshot(visual_page, "assets", visual_viewport)


@T32_PRUNED
def test_classes_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    """Retained T32 desktop duplicate; canonical class-section E2E owns contract."""
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    assert_structural_content(
        visual_page,
        '[data-testid="class-summary"]',
        '[data-testid="class-summary-row"]',
        '[data-testid="class-section-name"]',
    )
    compare_or_update_screenshot(visual_page, "classes", visual_viewport)


def test_rebalance_form_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/rebalanceamento")
    assert_structural_content(
        visual_page,
        '[data-testid="rebalance-form"]',
        '[data-testid="rebalance-plan"]',
    )
    # F52 — deterministic wait for the ECharts SVG renderer: every chart
    # container (if any) must have its <svg> attached before screenshot
    # (animation:false paints once; avoids capturing a half-rendered chart).
    visual_page.wait_for_function(
        """() => {
            const charts = document.querySelectorAll('[data-testid="rebalance-class-chart"]');
            if (!charts.length) return true;
            return [...charts].every((c) => c.querySelector('svg'));
        }""",
        timeout=10_000,
    )
    compare_or_update_screenshot(visual_page, "rebalance-form", visual_viewport)


def test_rebalance_plan_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/rebalanceamento")
    visual_page.fill('[data-testid="rebalance-contribution-input"]', "5000")
    visual_page.press('[data-testid="rebalance-contribution-input"]', "Enter")
    visual_page.wait_for_function(
        """() => {
            const el = document.querySelector('[data-testid="rebalance-plan-data"]');
            return el && JSON.parse(el.textContent).metrics.contribution === 5000;
        }""",
        timeout=10_000,
    )
    assert_structural_content(
        visual_page,
        '[data-testid="rebalance-plan"]',
        '[data-testid="rebalance-params-bar"]',
        '[data-testid="rebalance-asset-table"]',
        '[data-testid="rebalance-class-summary"]',
        '[data-testid="rebalance-class-bridge"]',
    )
    visual_page.wait_for_function(
        "() => document.querySelectorAll('[data-testid^=\"rebalance-asset-row-\"]').length > 0",
        timeout=10_000,
    )
    # F52 — wait for ECharts SVG charts to render before snapshotting.
    visual_page.wait_for_function(
        """() => {
            const charts = document.querySelectorAll('[data-testid="rebalance-class-chart"]');
            if (!charts.length) return true;
            return [...charts].every((c) => c.querySelector('svg'));
        }""",
        timeout=10_000,
    )
    visual_page.wait_for_timeout(400)
    compare_or_update_screenshot(visual_page, "rebalance-plan", visual_viewport)


def test_import_form_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    visual_page.click('[data-testid="dashboard-import-btn"]')
    assert_structural_content(
        visual_page,
        '[data-testid="import-modal-overlay"]',
        '[data-testid="import-file-input"]',
        text="Selecione um arquivo CSV",
    )
    compare_or_update_screenshot(visual_page, "import-form", visual_viewport)


def test_import_review_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    visual_page.click('[data-testid="dashboard-import-btn"]')
    visual_page.set_input_files('[data-testid="import-file-input"]', str(FIXTURE_PATH))
    visual_page.wait_for_selector(
        '[data-testid="import-commit-btn"]',
        state="visible",
        timeout=10_000,
    )
    assert_structural_content(
        visual_page,
        '[data-testid="import-commit-btn"]',
        '[data-testid="import-existing-table"]',
        '[data-testid="import-unmatched-table"]',
        text="Confirmar",
    )
    compare_or_update_screenshot(visual_page, "import-review", visual_viewport)


def test_rentabilidade_stub_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/rentabilidade")
    assert_structural_content(
        visual_page,
        '[data-testid="rentabilidade-stub"]',
        text="Em construção",
    )
    compare_or_update_screenshot(visual_page, "rentabilidade", visual_viewport)


def test_proventos_stub_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/proventos")
    assert_structural_content(
        visual_page,
        '[data-testid="proventos-stub"]',
        text="Em construção",
    )
    compare_or_update_screenshot(visual_page, "proventos", visual_viewport)
