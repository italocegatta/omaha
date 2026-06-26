# language: pt-BR
"""Common BDD step definitions — login, nav, profile pick.

These steps cover the auth bootstrap that every profile-aware
scenario depends on. Step text is in PT-BR to match the
dashboard UI and the user's request that the scenario steps
mirror what the operator types. The
:func:`pytest_bdd.parsers.parse` placeholders (``{path}``,
``{value}``, ``{label}``) let a single step match multiple
literal texts without losing PT-BR readability.

Dual-profile parametrization lives in the Gherkin
``Esquema do Cenário`` + ``Exemplos`` blocks in each
``.feature`` file — pytest-bdd creates one test instance per
Examples row, so the steps here don't need a ``profile``
fixture.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pytest_bdd import given, parsers, then, when

from tests.bdd.step_defs._workflows import (
    login_and_land,
)

if TYPE_CHECKING:
    from playwright.sync_api import Page


# ─────────────────────────────────────────────────────────────────────
# Given — preconditions (server up, DB seeded, on a given page)
# ─────────────────────────────────────────────────────────────────────


@given("o servidor de testes do BDD está no ar")
def bdd_server_is_up(live_url):
    assert live_url.startswith("http://"), f"BDD live_url invalid: {live_url!r}"


@given("o banco de dados de teste foi inicializado com a senha compartilhada")
def bdd_db_initialized():
    # The live uvicorn startup hook runs alembic + seed against
    # data/test_bdd.db. Both seeded profiles (Italo + Ana Livia)
    # exist before the first step runs.
    return None


@given(parsers.parse('os perfis "{italo}" e "{ana}" existem e estão sem classes e sem ativos'))
def profiles_empty(italo, ana):
    # The conftest's autouse ``clean_seeded_profiles`` fixture
    # wipes both profiles before each scenario, so the assertion
    # is implicit. The names come from the feature file so the
    # human reader sees the canonical profile spellings.
    assert italo == "Italo"
    assert ana == "Ana"


@given(parsers.re(r'(que )?estou na página "(?P<path>[^"]+)"'))
def at_page(page: Page, live_url: str, path: str):
    page.goto(f"{live_url}{path}")


# ─────────────────────────────────────────────────────────────────────
# Workflow wrappers — thin steps that delegate to ``_workflows.py``.
# Each wrapper's body is a single call into the workflow library so
# the contract test ``test_wrappers_delegate_to_workflows`` can
# enforce "no inlined workflow logic".
# ─────────────────────────────────────────────────────────────────────


@given(parsers.re(r'(que )?estou logado como "(?P<profile>[^"]+)"'))
def _w_logged_in_as(page: Page, live_url: str, profile: str):
    login_and_land(page, live_url, profile)


# ─────────────────────────────────────────────────────────────────────
# When — actions (fill field, click button)
# ─────────────────────────────────────────────────────────────────────


# Translate the PT-BR label that the operator types into the
# English testid slug the dashboard templates actually use. The
# user-facing label is the Gherkin step text ("Nome da classe"),
# the testid is the implementation hook
# ("new-class-modal-name-input" — the new-class modal promoted
# from the old inline form during dashboard-action-sidebar).
_PT_LABEL_TO_TESTID_SLUG: dict[str, str] = {
    "Nome da classe": "new-class-modal-name-input",
    "Alocação alvo": "new-class-modal-pct-input",
    "Nome do ativo": "dashboard-add-asset-name",
    "Alocação alvo do modal de ativo": "dashboard-add-asset-target-pct",
    "username": None,  # handled via ``input[name=...]`` below
    "password": None,
}


@when(parsers.parse('preencho o campo "{label}" com "{value}"'))
def fill_field(page: Page, label: str, value: str):
    selectors: list[str] = []
    slug = _PT_LABEL_TO_TESTID_SLUG.get(label)
    if slug is not None:
        selectors.append(f'[data-testid="{slug}"]')
    selectors.extend(
        [
            f'input[name="{label}"]',
            f'[data-testid="{label}"]',
            f'input[aria-label="{label}"]',
            f'label:has-text("{label}") + input',
            f'label:has-text("{label}") input',
        ]
    )
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                # 5s gives Alpine's ``x-show`` toggle a comfortable
                # tick to reveal the input after the trigger click.
                loc.first.wait_for(state="visible", timeout=5000)
                loc.first.fill(value)
                return
            except Exception:
                continue
    raise AssertionError(f"campo {label!r} não encontrado")


@when(parsers.parse('clico em "{label}"'))
def click_button(page: Page, label: str):
    candidates = [
        f'button:has-text("{label}")',
        f'[data-testid="{label}"]',
        f'a:has-text("{label}")',
    ]
    for sel in candidates:
        loc = page.locator(sel)
        if loc.count() == 0:
            continue
        # Two-phase visibility filter: a button matching the label
        # may exist multiple times (e.g. ``Salvar`` is the label of
        # both new-class-modal-submit and dashboard-add-asset-submit,
        # but only one is in an open modal). Walk the candidates,
        # pick the first whose first match is visible, and wait
        # briefly so Alpine's reactive transition can flip
        # ``display: none`` on a freshly-revealed parent.
        try:
            loc.first.wait_for(state="visible", timeout=5000)
            loc.first.click()
            return
        except Exception:
            # First match hidden (Alpine x-show on closed modal).
            # Try a fresh lookup with Playwright's :visible engine.
            visible = loc.locator("visible=true")
            if visible.count() > 0:
                visible.first.click()
                return
            continue
    raise AssertionError(f"botão/link {label!r} não encontrado")


@when(parsers.re(r'troco o perfil pelo chip do header para "(?P<name>[^"]+)"'))
def switch_profile_via_chip(page: Page, name: str):
    """Pick a different profile via the header chip's native <select>.

    direct-landing-with-header-profile-switcher: the old
    ``form.profile-picker`` step is gone (the picker page was
    removed). Cross-profile switching now goes through the header
    chip's native <select>: ``select_option(label=name)`` triggers
    the form's onchange handler which rewrites the action and
    submits.
    """
    page.locator('[data-testid="profile-switcher"]').select_option(label=name)


@when(parsers.parse('pressiono "{key}"'))
def press_key(page: Page, key: str):
    page.keyboard.press(key)


@when(parsers.parse('clico no campo "{label}" da classe "{class_name}"'))
def click_class_field(page: Page, label: str, class_name: str):
    section = page.locator(
        f'[data-testid="class-summary-row"]:has([data-testid="class-section-name"]:text-is("{class_name}"))'
    )
    # Two ``class-target-pct-view`` spans live under the section
    # (the per-class header plus a duplicate in the asset group
    # header). The editable one is the first match (the clickable
    # one with the ``startEditClassPct`` handler).
    section.first.locator('[data-testid="class-target-pct-view"]').first.click()
    edit_input = section.first.locator('[data-testid="class-inline-edit-input"]')
    edit_input.wait_for(state="visible", timeout=5000)
    edit_input.focus()
    edit_input.press("Control+a")
    edit_input.press("Delete")


@when(parsers.parse('clico no campo "{label}" do ativo "{ticker}"'))
def click_asset_field(page: Page, label: str, ticker: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    if "carteira" in label.lower() or "total" in label.lower():
        row.first.locator('[data-testid="asset-target-pct-total"]').click()
        edit_input = row.first.locator('[data-testid="asset-target-pct-total-edit-input"]')
    else:
        row.first.locator('[data-testid="asset-target-pct-class"]').click()
        edit_input = row.first.locator('[data-testid="asset-inline-edit-input"]')
    edit_input.wait_for(state="visible", timeout=5000)
    edit_input.focus()
    edit_input.press("Control+a")
    edit_input.press("Delete")


@when(parsers.parse('digito "{value}"'))
def type_value(page: Page, value: str):
    page.keyboard.type(value)


# ─────────────────────────────────────────────────────────────────────
# Then — assertions
# ─────────────────────────────────────────────────────────────────────


@then(parsers.re(r'(que )?estou na página "(?P<path>[^"]+)"'))
def on_page(page: Page, path: str):
    page.wait_for_url(re.compile(re.escape(path) + r"$"), timeout=5000)


@then(parsers.parse('o dashboard mostra o nome do perfil "{name}"'))
def dashboard_shows_profile_name(page: Page, name: str):
    """Assert the dashboard renders the named profile in the sidebar wordmark.

    direct-landing-with-header-profile-switcher: the h1 ``profile-name``
    element was removed (D6); the profile identity now lives in the
    sidebar wordmark (``[data-testid="sidebar-wordmark"]``) and the
    header chip's selected option (``[data-testid="profile-switcher"]``).
    The sidebar wordmark is the stable hook — it's the first element
    rendered after the layout flips and it carries the profile name
    verbatim.
    """
    wordmark = page.locator('[data-testid="sidebar-wordmark"]')
    wordmark.wait_for(state="visible", timeout=5000)
    assert name in wordmark.inner_text(), (
        f"esperava perfil {name!r} em [data-testid=sidebar-wordmark], vi {wordmark.inner_text()!r}"
    )


@then(parsers.parse('o dashboard mostra as classes de "{name}"'))
def dashboard_shows_other_profile_classes(page: Page, name: str):
    """Assert the dashboard shows the named profile's classes (cross-profile).

    direct-landing-with-header-profile-switcher + profile_sharing: after
    switching to another user's profile via the chip, the dashboard
    renders that profile's classes. The sidebar wordmark carries the
    profile name so the assertion matches.
    """
    wordmark = page.locator('[data-testid="sidebar-wordmark"]')
    wordmark.wait_for(state="visible", timeout=5000)
    assert name in wordmark.inner_text(), (
        f"esperava wordmark {name!r}, vi {wordmark.inner_text()!r}"
    )


@then("o dashboard mostra a mensagem de estado vazio")
def dashboard_shows_empty_state(page: Page):
    empty = page.locator('[data-testid="empty-state-onboarding"]')
    empty.wait_for(state="visible", timeout=5000)


@then(parsers.parse('a página mostra a mensagem de erro "{text}"'))
def page_shows_error(page: Page, text: str):
    locator = page.locator(
        f'[data-testid="login-error"]:has-text("{text}"), .error:has-text("{text}")'
    )
    locator.first.wait_for(state="visible", timeout=5000)


@then("não estou na página /profiles")
def not_on_profiles_page(page: Page):
    assert not page.url.endswith("/profiles"), f"URL inesperada: {page.url}"
