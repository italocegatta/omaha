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


# bdd-step-def-aliases (spec): alias chain consulted by ``click_button``
# before its default ``button:has-text`` / ``[data-testid]`` / ``a:has-text``
# candidates. Anchors the resolution on a stable testid when an F-slice
# re-organises an affordance and the Gherkin label drifts from the
# visible button text. Keys are the legacy Gherkin labels; values are
# ordered tuples of CSS selectors tried in sequence (first visible match
# wins). Each entry carries an inline comment naming the F-slice that
# introduced the drift so PR review sees the rationale.
STEP_CLICK_ALIASES: dict[str, tuple[str, ...]] = {
    # F02 moved the create-class button out of the removed sidebar.
    # Post-F02 the trigger is
    # ``[data-testid="empty-state-create-class"]`` with visible
    # text "Nova Classe" (no leading "+"). The second tuple
    # entry is the in-modal "Salvar" submit
    # (``[data-testid="new-class-modal-submit"]``), listed as a
    # safety net for any future step that walks past the trigger
    # with the modal already open.
    "+ Nova classe": (
        '[data-testid="empty-state-create-class"]',
        '[data-testid="new-class-modal-submit"]',
    ),
    # F02 symmetric preventive entry for the add-asset button
    # (``[data-testid="dashboard-add-asset-open"]`` with visible
    # text "Novo ativo"). No step call in the current BDD suite
    # trips this fallback, but the chain stays symmetric so a
    # future F-slice that re-routes the trigger does not silently
    # break the suite.
    "+ Novo ativo": ('[data-testid="dashboard-add-asset-open"]',),
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
    # Alias chain (spec ``bdd-step-def-aliases``): if the Gherkin
    # label has an explicit mapping, try those selectors first.
    # First visible match wins; the default candidate sequence is
    # the fallback (never replaced).
    alias_candidates: list[str] = list(STEP_CLICK_ALIASES.get(label, ()))
    for sel in alias_candidates:
        loc = page.locator(sel)
        if loc.count() == 0:
            continue
        try:
            loc.first.wait_for(state="visible", timeout=5000)
            loc.first.click()
            return
        except Exception:
            visible = loc.locator("visible=true")
            if visible.count() > 0:
                visible.first.click()
                return
            continue
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
# dashboard-inline-edit-friction: single-click auto-focus steps.
# These deliberately do NOT call ``focus()`` + select-all + delete
# after the click — the dashboard's inline editor now auto-focuses
# + pre-selects on the same click. Any further focus call would
# mask a regression in the auto-focus path.
# ─────────────────────────────────────────────────────────────────────


@when(parsers.parse('clico na pill "Alvo" da classe "{class_name}" com um único clique'))
def click_class_target_pill_once(page: Page, class_name: str):
    section = page.locator(
        f'[data-testid="class-summary-row"]:has('
        f'[data-testid="class-section-name"]:text-is("{class_name}"))'
    )
    section.first.wait_for(state="visible", timeout=5000)
    section.first.locator('[data-testid="class-target-pct-view"]').first.click()
    section.first.locator('[data-testid="class-inline-edit-input"]').wait_for(
        state="visible", timeout=5000
    )


@when(parsers.parse('clico no campo alvo % classe do ativo "{ticker}" com um único clique'))
def click_asset_class_cell_once(page: Page, ticker: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has('
        f'[data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    row.first.wait_for(state="visible", timeout=5000)
    row.first.locator('[data-testid="asset-target-pct-class"]').click()
    row.first.locator('[data-testid="asset-inline-edit-input"]').wait_for(
        state="visible", timeout=5000
    )


@when(parsers.parse('clico no campo alvo % total do ativo "{ticker}" com um único clique'))
def click_asset_total_cell_once(page: Page, ticker: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has('
        f'[data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    row.first.wait_for(state="visible", timeout=5000)
    row.first.locator('[data-testid="asset-target-pct-total"]').click()
    row.first.locator('[data-testid="asset-target-pct-total-edit-input"]').wait_for(
        state="visible", timeout=5000
    )


@when('limpo o input e pressiono "Enter"')
def clear_input_and_press_enter(page: Page):
    page.wait_for_function(
        "() => document.activeElement?.tagName === 'INPUT' "
        "&& document.activeElement?.type === 'number'",
        timeout=3000,
    )
    active = page.locator(":focus")
    active.fill("")
    page.keyboard.press("Enter")
    # Wait for the inline editor to close — that's the post-PATCH
    # signal that Alpine has updated the model. The assertion
    # step's filter(has_text=...) needs the re-rendered DOM, so
    # blocking here keeps Playwright from racing the response.
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"class-inline-edit-input\"]:focus') "
        "&& !document.querySelector('[data-testid=\"asset-inline-edit-input\"]:focus')",
        timeout=5000,
    )


@when("limpo o input e tiro o foco")
def clear_input_and_blur(page: Page):
    page.wait_for_function(
        "() => document.activeElement?.tagName === 'INPUT' "
        "&& document.activeElement?.type === 'number'",
        timeout=3000,
    )
    active = page.locator(":focus")
    active.fill("")
    page.locator("body").click(position={"x": 5, "y": 5})
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"class-inline-edit-input\"]:focus') "
        "&& !document.querySelector('[data-testid=\"asset-inline-edit-input\"]:focus')",
        timeout=5000,
    )


@then(parsers.parse('o input "{testid}" da classe "{class_name}" está focado'))
def class_input_is_focused(page: Page, testid: str, class_name: str):
    section = page.locator(
        f'[data-testid="class-summary-row"]:has('
        f'[data-testid="class-section-name"]:text-is("{class_name}"))'
    )
    section.first.wait_for(state="visible", timeout=5000)
    input_loc = section.first.locator(f'[data-testid="{testid}"]')
    input_loc.wait_for(state="visible", timeout=5000)
    is_focused = input_loc.evaluate("el => el === document.activeElement")
    assert is_focused, f"esperava {testid!r} da classe {class_name!r} focado"


@then(parsers.parse('o input "{testid}" da classe "{class_name}" tem o valor pré-selecionado'))
def class_input_value_selected(page: Page, testid: str, class_name: str):
    """Assert the inline input's value is pre-selected.

    ``<input type="number">`` returns ``null`` for ``selectionStart``
    / ``selectionEnd`` in Chrome / Firefox (numeric inputs don't
    expose a textual selection range), so we cannot measure the
    selection length directly. Instead we type a single character
    and assert the resulting value is just that character — proving
    the keystroke replaced the pre-selected value rather than
    appending to it.
    """
    section = page.locator(
        f'[data-testid="class-summary-row"]:has('
        f'[data-testid="class-section-name"]:text-is("{class_name}"))'
    )
    section.first.wait_for(state="visible", timeout=5000)
    input_loc = section.first.locator(f'[data-testid="{testid}"]')
    input_loc.wait_for(state="visible", timeout=5000)
    pre_value = input_loc.evaluate("el => el.value")
    input_loc.focus()
    # Press a single key. If the value was selected, this REPLACES
    # the value (resulting in just "9"). If not selected, it APPENDS
    # (resulting in "<pre_value>9"). Escape cancels so we don't
    # actually commit any change.
    page.keyboard.press("9")
    post_value = input_loc.evaluate("el => el.value")
    page.keyboard.press("Escape")
    assert post_value == "9", (
        f"esperava valor pré-selecionado em {testid!r} da classe {class_name!r}: "
        f"pre={pre_value!r}, após digitar 9 ficou {post_value!r} (deveria ser só '9')"
    )


@then(parsers.parse('o input "{testid}" do ativo "{ticker}" está focado'))
def asset_input_is_focused(page: Page, testid: str, ticker: str):
    row = page.locator(
        f'[data-testid="dashboard-asset-row"]:has('
        f'[data-testid="asset-row-name-text"]:text-is("{ticker}"))'
    )
    row.first.wait_for(state="visible", timeout=5000)
    input_loc = row.first.locator(f'[data-testid="{testid}"]')
    input_loc.wait_for(state="visible", timeout=5000)
    is_focused = input_loc.evaluate("el => el === document.activeElement")
    assert is_focused, f"esperava {testid!r} do ativo {ticker!r} focado"


# ─────────────────────────────────────────────────────────────────────
# Then — assertions
# ─────────────────────────────────────────────────────────────────────


@then(parsers.re(r'(que )?estou na página "(?P<path>[^"]+)"'))
def on_page(page: Page, path: str):
    page.wait_for_url(re.compile(re.escape(path) + r"$"), timeout=5000)


@then(parsers.parse('o dashboard mostra o nome do perfil "{name}"'))
def dashboard_shows_profile_name(page: Page, name: str):
    """Assert the patrimonio page renders the named profile in the header chip.

    F02: the sidebar wordmark was removed along with the sidebar
    itself (F02 D7 — ``dashboard-sidebar`` spec deprecated). The
    profile identity now lives in the header chip
    (``[data-testid="profile-switcher"]``) which renders the
    active profile name as the selected option. The chip is the
    stable hook — it carries the profile name verbatim.
    """
    chip = page.locator('[data-testid="profile-switcher"]')
    chip.wait_for(state="visible", timeout=5000)
    chip_text = chip.inner_text()
    assert name in chip_text, (
        f"esperava perfil {name!r} em [data-testid=profile-switcher], vi {chip_text!r}"
    )


@then(parsers.parse('o dashboard mostra as classes de "{name}"'))
def dashboard_shows_other_profile_classes(page: Page, name: str):
    """Assert the patrimonio shows the named profile's classes (cross-profile).

    F02: same hook as ``dashboard_shows_profile_name`` — the
    header chip renders the active profile name as the selected
    option, so switching profiles via the chip lands on a
    patrimonio that shows the matching profile's classes.
    """
    chip = page.locator('[data-testid="profile-switcher"]')
    chip.wait_for(state="visible", timeout=5000)
    chip_text = chip.inner_text()
    assert name in chip_text, (
        f"esperava perfil {name!r} em [data-testid=profile-switcher], vi {chip_text!r}"
    )


@then("o dashboard mostra a mensagem de estado vazio")
def dashboard_shows_empty_state(page: Page):
    empty = page.locator('[data-testid="empty-state-onboarding"]')
    empty.wait_for(state="visible", timeout=5000)


@then("a página mostra a nota de somente leitura")
def page_shows_read_only_note(page: Page):
    """F01 household mode: the dashboard renders the
    ``patrimonio-read-only-note`` element when ``?view=household``
    is active. The note is the visible signal that the operator is
    looking at the household aggregate (a sum of every viewer-owned
    profile) and not the per-profile view.
    """
    note = page.locator('[data-testid="patrimonio-read-only-note"]')
    note.wait_for(state="visible", timeout=5000)


@then(parsers.parse('a página mostra a mensagem de erro "{text}"'))
def page_shows_error(page: Page, text: str):
    locator = page.locator(
        f'[data-testid="login-error"]:has-text("{text}"), .error:has-text("{text}")'
    )
    locator.first.wait_for(state="visible", timeout=5000)


@then("não estou na página /profiles")
def not_on_profiles_page(page: Page):
    assert not page.url.endswith("/profiles"), f"URL inesperada: {page.url}"
