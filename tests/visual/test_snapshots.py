"""Committed visual baselines for key Omaha pages and states."""

from __future__ import annotations

from pathlib import Path

from .conftest import (
    assert_structural_content,
    compare_or_update_screenshot,
    login_as_italo,
)

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "sample_broker.csv"


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


def test_assets_table_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    assert_structural_content(
        visual_page,
        '[data-testid="asset-table"]',
        '[data-testid="dashboard-asset-row"]',
        text="R$",
    )
    compare_or_update_screenshot(visual_page, "assets", visual_viewport)


def test_classes_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    assert_structural_content(
        visual_page,
        '[data-testid="class-summary"]',
        '[data-testid="class-summary-row"]',
        '[data-testid="class-section-name"]',
        text="Alvo",
    )
    compare_or_update_screenshot(visual_page, "classes", visual_viewport)


def test_rebalance_form_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/rebalanceamento")
    assert_structural_content(
        visual_page,
        '[data-testid="rebalance-form"]',
        '[data-testid="rebalance-placeholder"]',
        text="Pronto para rebalancear",
    )
    compare_or_update_screenshot(visual_page, "rebalance-form", visual_viewport)


def test_rebalance_plan_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/rebalanceamento")
    visual_page.fill('[data-testid="rebalance-contribution-input"]', "5000")
    visual_page.evaluate(
        "() => document.querySelector('[data-testid=\"rebalance-form\"]').submit()"
    )
    assert_structural_content(
        visual_page,
        '[data-testid="rebalance-plan"]',
        '[data-testid="rebalance-stat-grid"]',
        '[data-testid="rebalance-asset-table"]',
        text="Política aplicada",
    )
    visual_page.wait_for_function(
        "() => document.querySelectorAll('[data-testid^=\"rebalance-asset-row-\"]').length > 0"
    )
    compare_or_update_screenshot(visual_page, "rebalance-plan", visual_viewport)


def test_import_form_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    visual_page.click('[data-testid="dashboard-import-btn"]')
    assert_structural_content(
        visual_page,
        '[data-testid="import-modal-overlay"]',
        '[data-testid="import-file-input"]',
        '[data-testid="import-upload-btn"]',
        text="Importar CSV",
    )
    compare_or_update_screenshot(visual_page, "import-form", visual_viewport)


def test_import_review_snapshot(visual_page, live_url_visual: str, visual_viewport) -> None:
    login_as_italo(visual_page, live_url_visual)
    visual_page.goto(f"{live_url_visual}/patrimonio")
    visual_page.click('[data-testid="dashboard-import-btn"]')
    visual_page.set_input_files('[data-testid="import-file-input"]', str(FIXTURE_PATH))
    visual_page.wait_for_timeout(200)
    visual_page.evaluate("Alpine.store('importModal').uploadFile()")
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
