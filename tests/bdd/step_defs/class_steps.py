"""Class CRUD BDD steps — snapshot form + inline add actions.

Two creation flows covered:

1. Snapshot create via ``/classes`` (the editor at
   ``[data-testid="class-editor"]`` with ``class-editor-add`` /
   ``class-editor-save`` / ``class-editor-name`` /
   ``class-editor-pct`` testids).
2. Inline add via the dashboard's ``+ Nova classe`` button
   (``new-class-plus-btn`` → ``new-class-form`` → ``save``).

The PATCH target actions (click + type + Enter on the class
section cell) live in :mod:`tests.bdd.step_defs.common_steps`
because they share the click / type / press shape with the
per-asset PATCH flow. This module owns the
:class-crate-specific` clicks + the unique ``alocação salva da
classe`` assertion that no other module covers.

Read-side assertions (section count, section text, etc.) live
in :mod:`tests.bdd.step_defs.dashboard_steps`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd import parsers, then, when

if TYPE_CHECKING:
    from playwright.sync_api import Page


# ─────────────────────────────────────────────────────────────────────
# When — snapshot editor (/classes page)
# ─────────────────────────────────────────────────────────────────────


@when(parsers.parse("abro o editor de classes"))
def open_class_editor(page: Page, live_url: str):
    page.goto(f"{live_url}/classes")
    page.wait_for_selector('[data-testid="class-editor"]', state="visible", timeout=5000)


@when(parsers.parse('clico em "Adicionar classe"'))
def click_add_class_row(page: Page):
    page.locator('[data-testid="class-editor-add"]').click()


@when(parsers.parse('preencho o campo "Nome da classe" da linha {idx:d} com "{name}"'))
def fill_class_row_name(page: Page, idx: int, name: str):
    rows = page.locator('[data-testid="class-editor"] tbody tr')
    rows.nth(idx).locator('[data-testid="class-editor-name"]').fill(name)


@when(parsers.parse('preencho o campo "Alocação alvo" da linha {idx:d} com "{pct}"'))
def fill_class_row_pct(page: Page, idx: int, pct: str):
    rows = page.locator('[data-testid="class-editor"] tbody tr')
    rows.nth(idx).locator('[data-testid="class-editor-pct"]').fill(pct)


@when(parsers.parse('clico em "Salvar classes"'))
def click_save_classes(page: Page):
    page.locator('[data-testid="class-editor-save"]').click()
    page.wait_for_load_state("networkidle", timeout=10000)


# ─────────────────────────────────────────────────────────────────────
# When — inline add (dashboard "+ Nova classe" button)
# ─────────────────────────────────────────────────────────────────────


@when(parsers.parse('preencho o campo "Nome da classe" com "{name}"'))
def fill_inline_class_name(page: Page, name: str):
    page.locator('[data-testid="new-class-name-input"]').fill(name)


@when(parsers.parse('preencho o campo "Alocação alvo" com "{pct}"'))
def fill_inline_class_pct(page: Page, pct: str):
    page.locator('[data-testid="new-class-pct-input"]').fill(pct)


@when(parsers.parse('clico em "Salvar"'))
def click_save_inline(page: Page):
    page.locator('[data-testid="new-class-form-save"]').click()
    page.wait_for_load_state("networkidle", timeout=10000)


# ─────────────────────────────────────────────────────────────────────
# Then — class-specific stored-value assertion
# ─────────────────────────────────────────────────────────────────────


@then(parsers.parse('a alocação salva da classe "{name}" é "{text}"'))
def class_target_pct_saved(page: Page, name: str, text: str):
    section = page.locator(
        f'[data-testid="class-summary-row"]:has([data-testid="class-section-name"]:text-is("{name}"))'
    )
    pct = section.first.locator('[data-testid="class-target-pct-view"]').inner_text()
    assert text in pct, f"esperava {text!r} na seção {name!r}, vi {pct!r}"
