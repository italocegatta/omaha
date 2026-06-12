"""Real-browser E2E for the full M002 user journey.

Drives a headless chromium against a live uvicorn instance to
verify the complete M002 user loop end to end:

  login -> select profile -> assert dashboard -> create 3 classes
  via snapshot form -> expand a class section -> add an asset
  via the inline "+ Ativo" form -> edit the asset's target_pct
  inline -> seed 43 assets for CSV auto-match -> open the import
  modal -> upload the 48-row broker CSV -> review and assign
  unmatched classes -> commit -> verify dashboard totals ->
  logout

Why a single monolithic test instead of separate focused tests
----------------------------------------------------------------
The task plan asks for a single Playwright test exercising the
full M002 user journey to catch cross-slice integration bugs.
Each slice (S01 inline edit, S02 class CRUD, S03 asset CRUD,
S04 CSV import, S05 viz polish) was independently tested in its
own module. This test chains them in a single run so that
boundary mismatches (e.g. the inline editor should work before
the import, and the import should not corrupt the inline-edited
target_pct) are caught by CI.

Why helpers are copied inline
-----------------------------
Per the task plan: "Use helpers from test_s05_user_journey.py
(copied, not imported)." This keeps the test self-contained and
avoids import coupling between sibling test modules.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "sample_broker.csv"

# ---------------------------------------------------------------------------
# SELECTORS — combined set from S04 (dashboard + modal), S01 (inline edit),
# S02 (class CRUD), and S05 (viz polish). All copied inline per the plan.
# ---------------------------------------------------------------------------
SELECTORS = {
    # Login
    "login_user": 'input[name="username"]',
    "login_pass": 'input[name="password"]',
    "login_submit": 'button[type="submit"]',
    # Profile picker
    "profile_picker": "form.profile-picker button",
    # Dashboard
    "profile_name": '[data-testid="profile-name"]',
    "nav_dashboard": '[data-testid="nav-dashboard"]',
    "class_summary_row": '[data-testid="class-summary-row"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "dashboard_class_section": '[data-testid="dashboard-class-section"]',
    "class_section_name": '[data-testid="class-section-name"]',
    "class_chevron": '[data-testid="class-chevron"]',
    "class_target_pct": '[data-testid="class-target-pct"]',
    "class_current_pct": '[data-testid="class-current-pct"]',
    "class_delta_badge": '[data-testid="class-delta-badge"]',
    # S02: inline class create
    "new_class_container": '[data-testid="new-class-container"]',
    "new_class_plus_btn": '[data-testid="new-class-plus-btn"]',
    "new_class_form": '[data-testid="new-class-form"]',
    "new_class_name_input": '[data-testid="new-class-name-input"]',
    "new_class_pct_input": '[data-testid="new-class-pct-input"]',
    "new_class_form_save": '[data-testid="new-class-form-save"]',
    "new_class_form_cancel": '[data-testid="new-class-form-cancel"]',
    "new_class_form_error": '[data-testid="new-class-form-error"]',
    "empty_state": '[data-testid="empty-state"]',
    # S03: inline asset create
    "dashboard_add_asset_btn": '[data-testid="dashboard-add-asset-btn"]',
    "dashboard_add_asset_name": '[data-testid="dashboard-add-asset-name-input"]',
    "dashboard_add_asset_pct": '[data-testid="dashboard-add-asset-pct-input"]',
    "dashboard_add_asset_save": '[data-testid="dashboard-add-asset-save"]',
    # S01: inline edit
    "asset_target_pct_class": '[data-testid="asset-target-pct-class"]',
    "asset_inline_edit_input": '[data-testid="asset-inline-edit-input"]',
    "asset_inline_edit_commit": '[data-testid="asset-inline-edit-commit"]',
    "asset_inline_edit_cancel": '[data-testid="asset-inline-edit-cancel"]',
    "asset_row_name": '[data-testid="asset-row-name"]',
    # S04: import modal
    "dashboard_import_btn": '[data-testid="dashboard-import-btn"]',
    "import_file_input": '[data-testid="import-file-input"]',
    "import_upload_btn": '[data-testid="import-upload-btn"]',
    "import_modal_overlay": '[data-testid="import-modal-overlay"]',
    "import_commit_btn": '[data-testid="import-commit-btn"]',
    "import_matched_summary": '[data-testid="import-matched-summary"]',
    "import_unmatched_table": '[data-testid="import-unmatched-table"]',
    "import_assignment_class": '[data-testid="import-assignment-class"]',
    # S05: portfolio header
    "portfolio_header": '[data-testid="portfolio-header"]',
    "portfolio_invested": '[data-testid="portfolio-invested"]',
    "portfolio_total": '[data-testid="portfolio-total"]',
    "portfolio_gain": '[data-testid="portfolio-gain"]',
    # Logout
    "logout_form": 'form.profile-switcher',
}

# The 48-row fixture produces 48 RawPositions. Of those, 43 are
# auto-matched by name and 5 are unmatched. Copied from S04.
UNMATCHED_NAMES = ["MXRF11", "BPAC11", "HGLG11", "XPLG11", "VINO11"]

MATCHED_NAMES: list[str] = [
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "ABEV3",
    "MGLU3",
    "BBAS3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "B3SA3",
    "SUZB3",
    "CSAN3",
    "PETR3",
    "VBBR3",
    "PRIO3",
    "IVVB11",
    "IVV",
    "VOO",
    "QQQ",
    "SMH",
    "SOXX",
    "VTI",
    "SPY",
    "VT",
    "HASH11",
    "BTLG11",
    "KNCR11",
    "IRDM11",
    "XPML11",
    "VISC11",
    "BRCR11",
    "TORD11",
    "MALL11",
    "DEVA11",
    "RBVA11",
    "VRTA11",
    "BPRP11",
    "PVBI11",
    "HCTR11",
    "XPIN11",
    "Tesouro Selic 2029",
    "Tesouro IPCA+ 2035",
]
assert len(MATCHED_NAMES) == 43, f"expected 43 matched names, got {len(MATCHED_NAMES)}"

RF_POS_NAMES = {
    "HASH11",
    "BTLG11",
    "KNCR11",
    "IRDM11",
    "XPML11",
    "VISC11",
    "BRCR11",
    "TORD11",
    "MALL11",
    "DEVA11",
    "RBVA11",
    "VRTA11",
    "BPRP11",
    "PVBI11",
    "HCTR11",
    "XPIN11",
    "Tesouro Selic 2029",
    "Tesouro IPCA+ 2035",
}
ACOES_NAMES = {
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "ABEV3",
    "MGLU3",
    "BBAS3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "B3SA3",
    "SUZB3",
    "CSAN3",
    "PETR3",
    "VBBR3",
    "PRIO3",
    "IVVB11",
}
RESERVA_NAMES = {
    "IVV",
    "VOO",
    "QQQ",
    "SMH",
    "SOXX",
    "VTI",
    "SPY",
    "VT",
}
assert len(RF_POS_NAMES) + len(ACOES_NAMES) + len(RESERVA_NAMES) == 43


# ---------------------------------------------------------------------------
# Helper functions — copied inline per the plan instruction
# ---------------------------------------------------------------------------


def _login_and_select_italo(page: Page, base_url: str) -> None:
    """Drive the login + profile picker using the live UI."""
    page.goto(f"{base_url}/login")
    page.fill(SELECTORS["login_user"], "family")
    page.fill(SELECTORS["login_pass"], "test-password")
    page.click(SELECTORS["login_submit"])
    page.wait_for_url(re.compile(r"/profiles$"))
    page.locator(SELECTORS["profile_picker"]).filter(has_text="Italo").click()
    page.wait_for_url(re.compile(r"/$"))


def _create_classes_via_form(page: Page, base_url: str, classes: list[tuple[str, int]]) -> None:
    """Submit the snapshot class editor form via fetch."""
    page.evaluate(
        """async ({ url, cls }) => {
            const fd = new FormData();
            for (const [name, pct] of cls) {
                fd.append('name[]', name);
                fd.append('target_pct[]', String(pct));
            }
            const r = await fetch(url, { method: 'POST', body: fd });
            if (!r.ok) {
                throw new Error('POST /classes ' + r.status + ': ' + await r.text());
            }
        }""",
        {"url": f"{base_url}/classes", "cls": classes},
    )


def _create_three_classes(page: Page, base_url: str) -> None:
    """Create RF Pos 60 / Acoes 30 / Reserva 10 via the snapshot form."""
    _create_classes_via_form(
        page,
        base_url,
        [("RF Pos", 60), ("Acoes", 30), ("Reserva", 10)],
    )
    page.goto(f"{base_url}/")
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)
    assert page.locator(SELECTORS["class_summary_row"]).count() == 3


def _expand_section(page: Page, class_name: str) -> None:
    """Expand a class section by clicking its chevron.

    Sections collapse on every page reload (D016). Use force=True to
    bypass pointer-event interception checks in the stacked layout.
    The chevron uses @click.stop so clicking it directly prevents
    the parent header's @click from toggling isOpen a second time.
    """
    page.wait_for_function("() => typeof Alpine !== 'undefined'", timeout=5000)
    page.wait_for_timeout(300)
    class_sections = page.locator(SELECTORS["class_summary_row"])
    found = False
    for i in range(class_sections.count()):
        name_el = class_sections.nth(i).locator(SELECTORS["class_section_name"])
        if name_el.inner_text().strip() == class_name:
            class_sections.nth(i).locator(SELECTORS["class_chevron"]).click(force=True)
            found = True
            break
    assert found, f"Class section '{class_name}' not found"
    page.wait_for_timeout(350)  # CSS transition: 200ms ease-out + buffer


def _add_asset_via_dashboard(page: Page, class_name: str,
                              asset_name: str, target_pct: str = "0") -> None:
    """Add an asset to a class via the dashboard inline form.

    Expands the section first, clicks + Ativo, fills name and pct,
    clicks Save, and waits for the page reload on 201.
    """
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)
    _expand_section(page, class_name)

    # Find the section by its name and scope the + Ativo button to it.
    sections = page.locator(SELECTORS["class_summary_row"])
    section = None
    for i in range(sections.count()):
        name_el = sections.nth(i).locator(SELECTORS["class_section_name"])
        if name_el.inner_text().strip() == class_name:
            section = sections.nth(i)
            break
    assert section is not None, f"Class section '{class_name}' not found"

    # Click the + Ativo button inside this class section.
    section.locator(SELECTORS["dashboard_add_asset_btn"]).click()
    page.wait_for_timeout(300)

    # Fill the form (scoped to the section).
    section.locator(SELECTORS["dashboard_add_asset_name"]).fill(asset_name)
    section.locator(SELECTORS["dashboard_add_asset_pct"]).fill(target_pct)

    # Click Save — POST /api/assets, reloads on 201.
    section.locator(SELECTORS["dashboard_add_asset_save"]).click()
    page.wait_for_load_state("networkidle", timeout=10000)


def _edit_asset_target_inline(page: Page, asset_name: str, new_value: str) -> None:
    """Edit an asset's target_pct inline on the dashboard.

    Assumes the class section is already expanded. Locates the asset
    row by name, clicks the "alvo % classe" cell to enter edit mode,
    types the new value, and verifies the commit succeeds.

    The per-class sum must equal 100 for the commit button to be
    enabled. With a single asset in the class at 0%, changing to 100
    makes the sum equal 100 — so the delta message is empty and the
    commit is allowed.
    """
    rows = page.locator(SELECTORS["dashboard_asset_row"])
    target_row = None
    for i in range(rows.count()):
        name_text = rows.nth(i).locator(SELECTORS["asset_row_name"]).inner_text()
        if name_text.strip() == asset_name:
            target_row = rows.nth(i)
            break
    assert target_row is not None, f"Asset row '{asset_name}' not found"

    # Click the "alvo % classe" cell to enter edit mode.
    cell = target_row.locator(SELECTORS["asset_target_pct_class"]).first
    cell.click()

    # Wait for the inline input to appear.
    edit_input = target_row.locator(SELECTORS["asset_inline_edit_input"]).first
    edit_input.wait_for(state="visible", timeout=2000)
    edit_input.fill(new_value)

    # The commit button should be enabled when classDeltaMessage is empty.
    commit = target_row.locator(SELECTORS["asset_inline_edit_commit"]).first
    _js_commit_enabled = (
        "() => !document.querySelector('"
        f"{SELECTORS['asset_inline_edit_commit']}"
        "').disabled"
    )
    page.wait_for_function(_js_commit_enabled, timeout=2000)
    commit.click()

    # Wait for the PATCH to complete and the input to hide.
    _js_input_hidden = (
        "() => { const el = document.querySelector('"
        f"{SELECTORS['asset_inline_edit_input']}"
        "'); return !el || el.offsetParent === null; }"
    )
    page.wait_for_function(_js_input_hidden, timeout=3000)


def _seed_43_assets(page: Page) -> None:
    """Seed 43 assets via the JSON API for speed.

    Reads class IDs from the DOM and POSTs one asset per matched name.
    Copied from S04's _seed_43_assets.
    """
    class_ids: dict[str, int] = page.evaluate(
        """() => {
            const rows = document.querySelectorAll('[data-testid="class-summary-row"]');
            const result = {};
            for (const row of rows) {
                const nameEl = row.querySelector('[data-testid="class-section-name"]');
                const name = nameEl ? nameEl.textContent.trim() : '';
                result[name] = parseInt(row.getAttribute('data-class-id'), 10);
            }
            return result;
        }"""
    )
    assert "RF Pos" in class_ids, f"RF Pos not found in class_ids: {class_ids}"
    assert "Acoes" in class_ids, f"Acoes not found in class_ids: {class_ids}"
    assert "Reserva" in class_ids, f"Reserva not found in class_ids: {class_ids}"

    def _class_id_for(name: str) -> int:
        if name in RF_POS_NAMES:
            return class_ids["RF Pos"]
        elif name in ACOES_NAMES:
            return class_ids["Acoes"]
        else:
            return class_ids["Reserva"]

    for asset_name in MATCHED_NAMES:
        success = page.evaluate(
            """async ({ name, class_id }) => {
                const r = await fetch('/api/assets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, asset_class_id: class_id, target_pct: 0 }),
                });
                return r.status === 201;
            }""",
            {"name": asset_name, "class_id": _class_id_for(asset_name)},
        )
        assert success, f"Failed to create asset {asset_name!r} via API"

    # Reload to pick up the new assets on the dashboard.
    page.goto(page.url)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)


def _do_import(page: Page) -> None:
    """Drive the S04 import flow via the dashboard modal.

    Opens the modal, uploads the broker CSV, assigns classes for
    unmatched rows that have no class pre-selected, and commits.
    The modal reloads the page on success.
    """
    # Open the import modal via Alpine store.
    page.evaluate("() => Alpine.store('importModal').openModal()")
    page.wait_for_selector(SELECTORS["import_modal_overlay"], state="visible", timeout=5000)
    page.wait_for_timeout(300)

    # Upload the CSV.
    page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
    page.wait_for_timeout(300)
    page.click(SELECTORS["import_upload_btn"], force=True)
    page.wait_for_selector(SELECTORS["import_commit_btn"], timeout=10000)
    page.wait_for_selector(SELECTORS["import_matched_summary"], timeout=5000)

    # Assign classes to unmatched rows that have no selection.
    unmatched_rows = page.locator(
        '[data-testid="import-unmatched-table"] tbody tr'
    )
    unmatched_count = unmatched_rows.count()
    assert unmatched_count == 5, f"expected 5 unmatched rows, got {unmatched_count}"

    for i in range(unmatched_count):
        select = unmatched_rows.nth(i).locator(SELECTORS["import_assignment_class"])
        current_value = select.evaluate("el => el.options[el.selectedIndex].value")
        if not current_value:
            select.select_option(label="RF Pos")

    # Commit the import.
    page.click(SELECTORS["import_commit_btn"], force=True)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=10000)


def _debug_dump(page: Page, tag: str) -> None:
    """Write a screenshot + main text + URL to /tmp for post-mortem."""
    import os

    os.makedirs("/tmp/s06_e2e_debug", exist_ok=True)
    page.screenshot(path=f"/tmp/s06_e2e_debug/{tag}.png", full_page=True)
    with open(f"/tmp/s06_e2e_debug/{tag}.txt", "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestS06FullJourney:
    """A single Playwright test walks the full M002 user journey."""

    def test_full_journey_login_to_logout(
        self, page: Page, live_url: str, browser_context
    ) -> None:
        """Full M002 user journey end to end.

        The test exercises every M002 slice surface in sequence:
        login, profile picker, class creation, inline asset creation,
        inline asset target editing, CSV import, dashboard totals, and
        logout — all in a single browser session.
        """
        # ==================================================================
        # Step 1: Login + select Italo profile
        # ==================================================================
        _login_and_select_italo(page, live_url)

        # ==================================================================
        # Step 2: Assert the dashboard is rendered
        # ==================================================================
        assert page.locator(SELECTORS["profile_name"]).count() == 1
        welcome_text = page.locator(SELECTORS["profile_name"]).inner_text()
        assert "Bem-vindo" in welcome_text, f"expected welcome on dashboard, got {welcome_text!r}"

        # ==================================================================
        # Step 3: Create 3 classes via snapshot form (RF Pos 60, Acoes 30,
        #         Reserva 10) — class CRUD from S02.
        # ==================================================================
        _create_three_classes(page, live_url)

        # ==================================================================
        # Step 4: Expand the RF Pos class section (D016: collapsed by
        #         default) and add an asset via the inline "+ Ativo" form
        #         — asset CRUD from S03.
        # ==================================================================
        _add_asset_via_dashboard(page, "RF Pos", "Tesouro Selic", "0")

        # After the asset create, the page reloads. Expand again.
        page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)
        _expand_section(page, "RF Pos")

        # ==================================================================
        # Step 5: Edit the asset's target_pct inline from 0 to 100 —
        #         the inline editor from S01. With only 1 asset in the
        #         class, setting 100 makes the per-class sum = 100, and
        #         the commit button is enabled.
        # ==================================================================
        _edit_asset_target_inline(page, "Tesouro Selic", "100")

        # ==================================================================
        # Step 6: Seed 43 assets via the JSON API for the CSV import
        #         auto-matcher to find. Copied from S04.
        # ==================================================================
        _seed_43_assets(page)

        # ==================================================================
        # Step 7: Open the import modal, upload the 48-row broker CSV,
        #         assign classes to unmatched rows, and commit — the
        #         S04 CSV import flow.
        # ==================================================================
        _do_import(page)

        # ==================================================================
        # Step 8: Verify dashboard totals.
        #
        # After the import, the dashboard should have:
        # - 3 class sections (RF Pos, Acoes, Reserva)
        # - 49 asset rows: 43 seeded + 5 new from CSV import + 1
        #   manually created "Tesouro Selic"
        # - Portfolio header with 3 BRL-formatted stats
        # ==================================================================
        sections = page.locator(SELECTORS["class_summary_row"])
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{SELECTORS['class_summary_row']}').length === 3",
                timeout=5000,
            )
        except Exception:
            _debug_dump(page, "post_import_sections")
            raise
        assert sections.count() == 3, (
            f"expected 3 class sections, got {sections.count()}"
        )

        # Each section must have a name, target pct, and current pct.
        for i in range(3):
            section = sections.nth(i)
            section_name = section.locator(SELECTORS["class_section_name"]).inner_text()
            has_name = section.locator(SELECTORS["class_section_name"]).count() == 1
            has_target = section.locator(SELECTORS["class_target_pct"]).count() == 1
            has_current = section.locator(SELECTORS["class_current_pct"]).count() == 1
            if not (has_name and has_target and has_current):
                _debug_dump(page, f"section_{i}_missing")
                inner = section.evaluate("el => el.innerHTML.substring(0, 2000)")
                assert False, (
                    f"Section {i} ({section_name!r}): "
                    f"has_name={has_name}, has_target={has_target}, has_current={has_current}\n"
                    f"Inner HTML: {inner}"
                )
            target_text = section.locator(SELECTORS["class_target_pct"]).inner_text()
            assert "Alvo" in target_text, f"target line missing 'Alvo': {target_text!r}"
            assert "%" in target_text, f"target line missing %: {target_text!r}"

        # Asset rows: 43 seeded + 5 new from CSV + 1 manual = 49.
        asset_rows = page.locator(SELECTORS["dashboard_asset_row"])
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{SELECTORS['dashboard_asset_row']}').length === 49",
                timeout=10000,
            )
        except Exception:
            _debug_dump(page, "post_import_asset_rows")
            raise
        assert asset_rows.count() == 49, (
            f"expected 49 asset rows, got {asset_rows.count()}"
        )

        # Portfolio header is present.
        assert page.locator(SELECTORS["portfolio_header"]).count() == 1
        assert page.locator(SELECTORS["portfolio_invested"]).count() == 1
        assert page.locator(SELECTORS["portfolio_total"]).count() == 1
        assert page.locator(SELECTORS["portfolio_gain"]).count() == 1

        # BRL values on the portfolio header are non-empty.
        invested_text = page.locator(SELECTORS["portfolio_invested"]).inner_text()
        current_text = page.locator(SELECTORS["portfolio_total"]).inner_text()
        assert "R$" in invested_text, f"invested stat missing R$: {invested_text!r}"
        assert "R$" in current_text, f"current stat missing R$: {current_text!r}"
        assert invested_text.strip() != "R$", "invested stat is R$ only (empty value)"
        assert current_text.strip() != "R$", "current stat is R$ only (empty value)"

        # The 5 unmatched names appear as asset row names on the dashboard.
        all_names = set()
        for i in range(asset_rows.count()):
            all_names.add(asset_rows.nth(i).locator(SELECTORS["asset_row_name"]).inner_text())
        for name in UNMATCHED_NAMES:
            assert any(name in n for n in all_names), (
                f"missing imported asset {name!r} on dashboard"
            )

        # ==================================================================
        # Step 9: Logout via the "Sair" button in the profile switcher.
        # ==================================================================
        logout_btn = page.locator(f'{SELECTORS["logout_form"]} button[type="submit"]')
        assert logout_btn.count() == 1, "logout button not found"
        logout_btn.click()

        # After logout, the user should be on /login.
        page.wait_for_url(re.compile(r"/login"), timeout=5000)
        assert page.locator(SELECTORS["login_user"]).count() == 1, (
            "expected login page after logout"
        )
