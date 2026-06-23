"""Dashboard state BDD steps — read-only assertions on rendered DOM.

These steps are the read side of the BDD suite: they look up
DOM state via ``data-testid`` markers and assert on the rendered
text. They are deliberately idempotent — they wait for the
element to be visible before reading, so a flaky Alpine
``x-effect`` timing does not produce a false negative.

The dashboard's per-class and per-asset count assertions live
here too — they are derived state, not directly written by the
user, so they fit ``Then`` better than ``Given`` even when used
in the middle of a scenario.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd import parsers, then

if TYPE_CHECKING:
    from playwright.sync_api import Page


@then(parsers.parse("o dashboard mostra {count:d} seções de classe"))
def dashboard_class_section_count(page: Page, count: int):
    page.wait_for_selector('[data-testid="class-summary-row"]', state="visible", timeout=5000)
    actual = page.locator('[data-testid="class-summary-row"]').count()
    assert actual == count, f"esperava {count} seções, vi {actual}"


@then(parsers.parse("o dashboard mostra {count:d} linhas de ativos"))
def dashboard_asset_row_count(page: Page, count: int):
    page.wait_for_selector('[data-testid="dashboard-asset-row"]', state="visible", timeout=5000)
    actual = page.locator('[data-testid="dashboard-asset-row"]').count()
    assert actual == count, f"esperava {count} linhas de ativos, vi {actual}"


@then(parsers.parse('a seção "{name}" mostra "{text}"'))
def section_text(page: Page, name: str, text: str):
    section = page.locator(
        f'[data-testid="class-summary-row"]:has([data-testid="class-section-name"]:text-is("{name}"))'
    )
    section.first.wait_for(state="visible", timeout=5000)
    # Wait for the section text to actually contain the expected value.
    # Some flows (PATCH / inline edit) are async — the DOM updates
    # only after the fetch resolves and Alpine re-renders, so a
    # plain read immediately after the action would race the
    # response and produce a false negative.
    section.first.filter(has_text=text).wait_for(state="visible", timeout=10000)
    inner = section.first.inner_text()
    assert text in inner, f"esperava {text!r} na seção {name!r}, vi {inner!r}"


@then(parsers.parse('a seção "{name}" contém {count:d} ativos'))
def section_contains_assets(page: Page, name: str, count: int):
    rows = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-class"]:text-is("{name}"))'
    )
    actual = rows.count()
    assert actual == count, f"esperava {count} ativos em {name!r}, vi {actual}"
