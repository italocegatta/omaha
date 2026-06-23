"""Asset CRUD BDD steps — manual dashboard add + per-class sum validation.

The dashboard's per-class "+ Ativo" button opens a modal
(``dashboard-add-asset-modal``) with class picker, name, and
target-pct inputs. Submitting calls ``POST /api/assets``; the
modal ``reload()``s the page on 201 and surfaces the inline
error (``dashboard-add-asset-error``) on 422.

The per-class sum validator (``validate_target_pct_sum``) is
exercised by attempting to set two assets whose target_pct sums
to a value other than 100 — the API returns 422 and neither
value is persisted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd import parsers, then, when

from tests.bdd.step_defs._workflows import (
    add_one_asset,
    create_four_assets,
)

if TYPE_CHECKING:
    from playwright.sync_api import Page


@when(parsers.parse('abro o formulário de ativo da classe "{class_name}"'))
def open_asset_form(page: Page, class_name: str):
    # Find the class section by name, then click its "+ Ativo"
    # button. The class section header has the button — we
    # locate it inside the matching ``class-summary-row``.
    section = page.locator(
        f'[data-testid="class-summary-row"]:has([data-testid="class-section-name"]:text-is("{class_name}"))'
    )
    section.first.locator('[data-testid="dashboard-add-asset-open"]').click()
    modal = page.locator('[data-testid="dashboard-add-asset-modal"]')
    modal.wait_for(state="visible", timeout=5000)


@when(parsers.parse('seleciono a classe "{class_name}" no modal de ativo'))
def select_asset_class(page: Page, class_name: str):
    select = page.locator('[data-testid="dashboard-add-asset-modal-class"]')
    select.select_option(label=class_name)


@when(parsers.parse('preencho o campo "Nome do ativo" com "{name}"'))
def fill_asset_name(page: Page, name: str):
    page.locator('[data-testid="dashboard-add-asset-name"]').fill(name)


@when(parsers.parse('preencho o campo "Alocação alvo" do modal de ativo com "{pct}"'))
def fill_asset_pct(page: Page, pct: str):
    page.locator('[data-testid="dashboard-add-asset-target-pct"]').fill(pct)


@when(parsers.parse('clico em "Adicionar ativo"'))
def click_add_asset(page: Page):
    page.locator('[data-testid="dashboard-add-asset-submit"]').click()
    page.wait_for_load_state("networkidle", timeout=10000)


@then(parsers.parse("o dashboard mostra {count:d} linhas de ativos"))
def dashboard_asset_row_count(page: Page, count: int):
    page.wait_for_selector('[data-testid="dashboard-asset-row"]', state="visible", timeout=5000)
    actual = page.locator('[data-testid="dashboard-asset-row"]').count()
    assert actual == count, f"esperava {count} linhas de ativos, vi {actual}"


@then(parsers.parse('a classe "{class_name}" contém {count:d} ativos'))
def class_contains_assets(page: Page, class_name: str, count: int):
    # The asset table groups rows by class — count rows whose
    # ``asset-row-class`` cell exactly matches ``class_name``.
    rows = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-class"]:text-is("{class_name}"))'
    )
    actual = rows.count()
    assert actual == count, f"esperava {count} ativos em {class_name!r}, vi {actual}"


@then(parsers.parse('o modal de ativo mostra a mensagem de erro "{text}"'))
def asset_modal_error(page: Page, text: str):
    err = page.locator('[data-testid="dashboard-add-asset-error"]')
    err.wait_for(state="visible", timeout=5000)
    inner = err.inner_text()
    assert text in inner, f"esperava erro {text!r}, vi {inner!r}"


# ─────────────────────────────────────────────────────────────────────
# Workflow wrappers — thin steps that delegate to ``_workflows.py``.
# ─────────────────────────────────────────────────────────────────────


@when(parsers.parse('adicionei o ativo "{ticker}" à classe "{cls}" com "{pct:d}%"'))
def _w_one_asset(page: Page, live_url: str, ticker: str, cls: str, pct: int):
    add_one_asset(page, live_url, cls, ticker, pct)


@when("adicionei 4 ativos com distribuição não-igual")
def _w_four_assets(page: Page, live_url: str):
    create_four_assets(page, live_url)
