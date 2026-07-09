"""Import modal BDD steps — upload, review, commit.

The import modal (``import-modal-overlay``) is opened from the
dashboard's ``dashboard-import-btn``. The user picks a file
(``import-file-input``), clicks ``import-upload-btn``, and
then clicks ``import-commit-btn``. The matcher auto-assigns
each row to a class whose name matches the row's
``Minha Categoria`` cell — for the tiny fixture (4 rows from
``posicao_italo.csv``) the row categories are ``RF Pós`` and
``RF Dinâmica``, which match the dashboard classes one-for-one
(``pytest_bdd`` tier-1 exact match) so the modal shows zero
unmatched rows and the user just confirms.

A manual-assignment path is not exercised here because the
fixture categories are deliberately chosen to match the test
class names — the user wants the import flow to be a single
confirm step, not a per-row assignment.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest_bdd import parsers, then, when

if TYPE_CHECKING:
    from playwright.sync_api import Page


REPO_ROOT = Path(__file__).resolve().parents[3]
TINY_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "tiny_portfolio.csv"


@when(parsers.parse('abro o modal "Importar posições"'))
def open_import_modal(page: Page):
    page.locator('[data-testid="dashboard-import-btn"]').click()
    page.locator('[data-testid="import-modal-overlay"]').wait_for(state="visible", timeout=5000)


@when(parsers.parse('seleciono o arquivo "{filename}"'))
def select_import_file(page: Page, filename: str):
    # Resolve fixture name → path. The BDD suite knows about
    # ``tiny_portfolio.csv`` and ``empty.csv`` (header-only) by
    # convention; anything else resolves to
    # ``tests/fixtures/`` directly.
    fixture_name = filename.removesuffix(".csv")
    candidates = [
        REPO_ROOT / "tests" / "fixtures" / filename,
        REPO_ROOT / "tests" / "fixtures" / f"{fixture_name}_portfolio.csv",
        REPO_ROOT / "tests" / "fixtures" / f"{fixture_name}_empty.csv",
    ]
    for path in candidates:
        if path.exists():
            page.locator('[data-testid="import-file-input"]').set_input_files(str(path))
            return
    raise FileNotFoundError(f"fixture {filename!r} não encontrada em tests/fixtures/")


@when(parsers.parse('clico em "Enviar"'))
def click_upload(page: Page):
    page.locator('[data-testid="import-upload-btn"]').click()
    page.wait_for_selector('[data-testid="import-commit-btn"]', timeout=15000)


@when(parsers.parse('atribuo "{class_name}" ao ticker "{ticker}"'))
def assign_class_to_ticker(page: Page, class_name: str, ticker: str):
    # Find the unmatched row for ``ticker``, locate its
    # assignment select, and pick the option whose label matches
    # ``class_name``.
    row = page.locator(f'[data-testid="import-unmatched-row"]:has-text("{ticker}")')
    select = row.first.locator('[data-testid="import-assignment-class"]')
    select.select_option(label=class_name)


@when(parsers.parse('clico em "Confirmar importação"'))
def click_commit_import(page: Page):
    page.locator('[data-testid="import-commit-btn"]').click()
    page.wait_for_selector('[data-testid="class-summary-row"]', timeout=15000)


@then(parsers.parse("o modal mostra {count:d} linhas não correspondidas"))
def modal_unmatched_count(page: Page, count: int):
    # When count is 0 the unmatched section is x-show=hidden (rows
    # are auto-matched). When count > 0 each row is rendered with
    # [data-testid="import-unmatched-row"] — wait briefly for the
    # first one to appear before counting.
    if count > 0:
        page.wait_for_selector(
            '[data-testid="import-unmatched-row"]',
            state="visible",
            timeout=5000,
        )
    actual = page.locator('[data-testid="import-unmatched-row"]').count()
    assert actual == count, f"esperava {count} linhas unmatched, vi {actual}"


@then(parsers.parse('o modal mostra a mensagem de erro "{text}"'))
def modal_error(page: Page, text: str):
    err = page.locator('[data-testid="import-upload-error"], [data-testid="import-commit-error"]')
    err.first.wait_for(state="visible", timeout=5000)
    inner = err.first.inner_text()
    assert text in inner, f"esperava erro {text!r}, vi {inner!r}"
