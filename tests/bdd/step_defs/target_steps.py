"""Target PATCH BDD steps — per-class and per-asset target PATCH.

Two PATCH endpoints exercised:

* ``PATCH /api/classes/{id}`` — updates ``asset_classes.target_pct``
  (the per-class-of-portfolio target).
* ``PATCH /api/assets/{id}`` — updates ``assets.target_pct``
  (the per-asset-of-class target).

The click / type / press actions live in
:mod:`tests.bdd.step_defs.common_steps` so the same step text
clicks both class and asset cells. This module owns the
*assertions* on stored values + the derived portfolio % display.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd import parsers, then

if TYPE_CHECKING:
    from playwright.sync_api import Page


@then(parsers.parse('a alocação salva da classe "{name}" é "{text}"'))
def class_saved_target(page: Page, name: str, text: str):
    section = page.locator(
        f'[data-testid="class-summary-row"]:has([data-testid="class-section-name"]:text-is("{name}"))'
    )
    pct = section.first.locator('[data-testid="class-target-pct-view"]').inner_text()
    assert text in pct, f"esperava {text!r} na seção {name!r}, vi {pct!r}"


@then(parsers.parse('a alocação salva do ativo "{ticker}" é "{text}"'))
def asset_saved_class_target(page: Page, ticker: str, text: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    cell = row.first.locator('[data-testid="asset-target-pct-class"]')
    inner = cell.inner_text()
    assert text in inner, f"esperava {text!r} no ativo {ticker!r}, vi {inner!r}"


@then(parsers.parse('o derivado "{ticker}" na carteira é "{text}"'))
def derived_pct_total(page: Page, ticker: str, text: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    cell = row.first.locator('[data-testid="asset-current-pct-total"]')
    inner = cell.inner_text()
    assert text in inner, f"esperava derivado {text!r} para {ticker!r}, vi {inner!r}"
