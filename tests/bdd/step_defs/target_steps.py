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

import re
from typing import TYPE_CHECKING

from pytest_bdd import parsers, then

if TYPE_CHECKING:
    from playwright.sync_api import Page


def _normalize_pct_text(text: str) -> str:
    return re.sub(r"(\d+)\.0+%", r"\1%", text)


@then(parsers.parse('a alocação salva da classe "{name}" é "{text}"'))
def class_saved_target(page: Page, name: str, text: str):
    section = page.locator(
        f'[data-testid="class-summary-row"]:has([data-testid="class-section-name"]:text-is("{name}"))'
    )
    section.first.wait_for(state="visible", timeout=5000)
    expected = _normalize_pct_text(text)
    if text.startswith("Alvo "):
        expected = _normalize_pct_text(text.removeprefix("Alvo ").strip())
        inner = section.first.evaluate(
            r"""el => {
                const clone = el.cloneNode(true);
                clone.querySelectorAll('.icon, [class*="icon--"]').forEach(n => n.remove());
                return clone.innerText.replace(/\s+/g, ' ').trim();
            }""",
        )
        assert expected in _normalize_pct_text(inner), (
            f"esperava {text!r} na seção {name!r}, vi {inner!r}"
        )
        return

    page.wait_for_function(
        """({name, expected}) => {
            const rows = Array.from(document.querySelectorAll('[data-testid="class-summary-row"]'));
            return rows.some((row) => {
                const nameEl = row.querySelector('[data-testid="class-section-name"]');
                if (!nameEl || nameEl.textContent.trim() !== name) return false;
                const target = row.querySelector('[data-testid="class-target-pct-view"]');
                if (!target) return false;
                return target.innerText.replace(/(\\d+)\\.0+%/g, '$1%').includes(expected);
            });
        }""",
        arg={"name": name, "expected": expected},
        timeout=10000,
    )

    pct = section.first.locator('[data-testid="class-target-pct-view"]').first.inner_text()
    assert _normalize_pct_text(text) in _normalize_pct_text(pct), (
        f"esperava {text!r} na seção {name!r}, vi {pct!r}"
    )


@then(parsers.parse('a alocação salva do ativo "{ticker}" é "{text}"'))
def asset_saved_class_target(page: Page, ticker: str, text: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    cell = row.first.locator('[data-testid="asset-target-pct-total"]')
    cell.wait_for(state="visible", timeout=5000)
    # Wait for the *button* inside the cell to contain the expected
    # value. The edit-hint / edit-error spans sit in the same ``<td>``
    # so reading the cell's full text races the post-commit state;
    # the button alone is the source of truth once editing ends.
    button = cell.locator("button").first
    button.wait_for(state="visible", timeout=10000)
    expected = _normalize_pct_text(text)
    page.wait_for_function(
        """({ticker, expected}) => {
            const rows = Array.from(
                document.querySelectorAll('[data-testid="dashboard-asset-row"]')
            );
            return rows.some((row) => {
                const nameEl = row.querySelector('[data-testid="asset-row-name-text"]');
                if (!nameEl || nameEl.textContent.trim() !== ticker) return false;
                const button = row.querySelector('[data-testid="asset-target-pct-total"] button');
                if (!button) return false;
                return button.innerText.replace(/(\\d+)\\.0+%/g, '$1%').includes(expected);
            });
        }""",
        arg={"ticker": ticker, "expected": expected},
        timeout=10000,
    )
    inner_button = button.inner_text()
    assert _normalize_pct_text(text) in _normalize_pct_text(inner_button), (
        f"esperava {text!r} no botão do ativo {ticker!r}, vi {inner_button!r}"
    )


@then(parsers.parse('a alocação salva da célula alvo % classe do ativo "{ticker}" é "{text}"'))
def asset_class_cell_saved(page: Page, ticker: str, text: str):
    """Read the asset's ``alvo % classe`` cell (per-class target) — NOT
    the total cell. The existing ``asset_saved_class_target`` step
    reads the total cell, which is correct for "PATCH per-asset
    total reflects in dashboard" but wrong for assertions about
    edits to the class-level cell.
    """
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    cell = row.first.locator('[data-testid="asset-target-pct-class"]')
    cell.wait_for(state="visible", timeout=5000)
    button = cell.locator("button").first
    button.wait_for(state="visible", timeout=10000)
    expected = _normalize_pct_text(text)
    page.wait_for_function(
        """({ticker, expected}) => {
            const rows = Array.from(
                document.querySelectorAll('[data-testid="dashboard-asset-row"]')
            );
            return rows.some((row) => {
                const nameEl = row.querySelector('[data-testid="asset-row-name-text"]');
                if (!nameEl || nameEl.textContent.trim() !== ticker) return false;
                const button = row.querySelector('[data-testid="asset-target-pct-class"] button');
                if (!button) return false;
                return button.innerText.replace(/(\\d+)\\.0+%/g, '$1%').includes(expected);
            });
        }""",
        arg={"ticker": ticker, "expected": expected},
        timeout=10000,
    )
    inner = button.inner_text()
    assert _normalize_pct_text(text) in _normalize_pct_text(inner), (
        f"esperava {text!r} na célula alvo % classe do ativo {ticker!r}, vi {inner!r}"
    )


@then(parsers.parse('o derivado "{ticker}" na carteira é "{text}"'))
def derived_pct_total(page: Page, ticker: str, text: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    cell = row.first.locator('[data-testid="asset-target-pct-total"]')
    cell.wait_for(state="visible", timeout=5000)
    button = cell.locator("button").first
    button.wait_for(state="visible", timeout=10000)
    expected = _normalize_pct_text(text)
    page.wait_for_function(
        """({ticker, expected}) => {
            const rows = Array.from(
                document.querySelectorAll('[data-testid="dashboard-asset-row"]')
            );
            return rows.some((row) => {
                const nameEl = row.querySelector('[data-testid="asset-row-name-text"]');
                if (!nameEl || nameEl.textContent.trim() !== ticker) return false;
                const button = row.querySelector('[data-testid="asset-target-pct-total"] button');
                if (!button) return false;
                return button.innerText.replace(/(\\d+)\\.0+%/g, '$1%').includes(expected);
            });
        }""",
        arg={"ticker": ticker, "expected": expected},
        timeout=10000,
    )
    inner = button.inner_text()
    assert _normalize_pct_text(text) in _normalize_pct_text(inner), (
        f"esperava derivado {text!r} para {ticker!r}, vi {inner!r}"
    )
