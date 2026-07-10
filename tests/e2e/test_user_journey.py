"""Real-browser E2E for the S03 user journey.

Drives a headless chromium against a live uvicorn instance to
verify the complete S03 user loop end to end:

  login → select profile → create 3 classes → add 3 assets via
  the dashboard inline "+ Ativo" form → delete 1 asset via the
  per-row confirm dialog → verify dashboard distribution

This test exists because the route-level TestClient tests in
``test_assets_e2e.py`` bypass the rendered HTML. The
``formaction``-based delete button bug that the user found in
production (delete button placed outside its ``<form>``) was
invisible to those tests; this one would catch it.

If a single step in this test fails, the fix almost certainly
involves a template/JS bug that route-level tests cannot see.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .selectors import SELECTORS


def _login_and_select_italo(page: Page, base_url: str) -> None:
    """Drive the direct-landing login flow.

    direct-landing-with-header-profile-switcher: ``POST /login``
    auto-binds ``active_profile_id`` to the logged-in user's first
    profile (by ``display_order``) and 303s to ``/``. There is no
    intermediate ``/profiles`` picker page — login lands directly on
    the dashboard.
    """
    page.goto(f"{base_url}/login", wait_until="commit", timeout=60000)
    page.locator('input[name="username"]').wait_for(state="visible", timeout=30000)
    page.evaluate(
        """async () => {
            const fd = new FormData();
            fd.append('username', 'Italo');
            fd.append('password', 'test-password');
            const r = await fetch('/login', { method: 'POST', body: fd });
            if (!r.ok && r.status !== 303) {
                throw new Error('POST /login ' + r.status);
            }
        }"""
    )
    page.goto(f"{base_url}/", wait_until="commit")
    page.wait_for_selector(SELECTORS["app_header_wordmark"], timeout=30000)


def _create_three_classes(page: Page, base_url: str) -> None:
    """Create 3 classes via the snapshot form (POST /classes)."""
    page.evaluate(
        """async () => {
            const fd = new FormData();
            for (const [name, pct] of [['Renda Fixa', 60], ['Acoes', 30], ['Reserva', 10]]) {
                fd.append('name[]', name);
                fd.append('target_pct[]', String(pct));
            }
            const r = await fetch('/classes', { method: 'POST', body: fd });
            if (!r.ok) throw new Error('POST /classes ' + r.status + ': ' + await r.text());
        }"""
    )
    page.goto(f"{base_url}/", wait_until="commit", timeout=60000)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=30000)
    assert page.locator(SELECTORS["class_summary_row"]).count() == 3


def _debug_dump(page: Page, tag: str) -> None:
    """Write a screenshot + main-text + URL to /tmp for post-mortem."""
    import os

    os.makedirs("/tmp/s03_e2e_debug", exist_ok=True)
    screenshot_path = f"/tmp/s03_e2e_debug/{tag}.png"
    page.screenshot(path=screenshot_path, full_page=True)
    text_path = f"/tmp/s03_e2e_debug/{tag}.txt"
    with open(text_path, "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")
        try:
            f.write("\n\nASSET ROWS HTML:\n")
            f.write(page.locator("main").inner_html())
        except Exception as exc:
            f.write(f"main inner_html failed: {exc}\n")


def _add_asset_via_dashboard(
    page: Page, base_url: str, class_name: str, asset_name: str, target_pct: str = "10"
) -> None:
    """Add an asset to a class via the dashboard add-asset modal.

    Opens the dashboard-level ``+ Ativo`` modal, selects the target
    class, fills the name and target % inputs, clicks Salvar, and
    waits for the page reload on success.
    """
    page.locator(SELECTORS["dashboard_add_asset_open"]).click()
    modal = page.locator(SELECTORS["dashboard_add_asset_modal"])
    modal.wait_for(state="visible", timeout=5000)

    modal.locator(SELECTORS["dashboard_add_asset_class"]).select_option(label=class_name)
    modal.locator(SELECTORS["dashboard_add_asset_name"]).fill(asset_name)
    modal.locator(SELECTORS["dashboard_add_asset_pct"]).fill(target_pct)

    # Click Salvar — this triggers a POST /api/assets and reloads on 201.
    with page.expect_response(re.compile(r".*/api/assets$"), timeout=30000) as resp_info:
        modal.locator(SELECTORS["dashboard_add_asset_submit"]).click()
    assert resp_info.value.status == 201

    page.goto(f"{base_url}/", wait_until="commit", timeout=60000)
    page.wait_for_selector(
        f"{SELECTORS['dashboard_asset_row']}:has({SELECTORS['asset_row_name_text']}:text-is(\"{asset_name}\"))",
        state="visible",
        timeout=30000,
    )


class TestS03UserJourney:
    """One class per test scenario so failures are isolated."""

    def test_login_select_profile_renders_dashboard(self, page: Page, live_url: str) -> None:
        """Smoke: login + select Italo lands on a dashboard with no classes yet."""
        _login_and_select_italo(page, live_url)

        # Header wordmark is rendered as the page's primary brand mark.
        assert page.locator(SELECTORS["app_header_wordmark"]).count() == 1
        assert page.locator(SELECTORS["app_header_wordmark"]).inner_text().strip() == "Omaha"

        # No classes yet → onboarding empty state on the dashboard
        # (3-step card introduced by dashboard-action-sidebar).
        page.wait_for_selector('[data-testid="empty-state-onboarding"]', timeout=5000)
        assert page.locator(SELECTORS["class_summary_row"]).count() == 0

    def test_full_crud_journey_classes_assets_delete(self, page: Page, live_url: str) -> None:
        """Full S03 user journey: 3 classes, 3 assets (inline), delete 1, verify dashboard.

        Uses the dashboard inline "+ Ativo" form for asset creation and
        the per-row confirm dialog for deletion — both added in S03/T03
        and S03/T04.
        """
        _login_and_select_italo(page, live_url)

        # --- 1. Create 3 classes summing to 100 via the snapshot form.
        _create_three_classes(page, live_url)

        # --- 2. Add 3 assets inline on the dashboard, one per class.
        # Assets are created with target_pct=0 because the per-class sum
        # validator requires all assets' target_pct in a class to total 100
        # — a single asset at 40% in an empty class would fail validation.
        # The test asserts the CRUD flow (add/delete/verify), not allocation
        # percentages, so 0% is fine for setup.
        _add_asset_via_dashboard(page, live_url, "Renda Fixa", "Tesouro Selic", "0")
        _add_asset_via_dashboard(page, live_url, "Acoes", "PETR4", "0")
        _add_asset_via_dashboard(page, live_url, "Reserva", "IVVB11", "0")

        # Verify all 3 assets appear on the dashboard.
        # fix-asset-table-ui-bugs: sections are expanded by default on load
        # (isOpen: true). The test asserts DOM presence, not visibility.
        # Wait for exactly 3 asset rows to avoid race between page rendering
        # and the count assertion (the 3rd inline save reload races with Alpine).
        page.wait_for_function(
            f"() => document.querySelectorAll('{SELECTORS['dashboard_asset_row']}').length === 3",
            timeout=8000,
        )
        asset_rows = page.locator(SELECTORS["dashboard_asset_row"])

        # --- 3. Delete the second asset (PETR4 in Acoes).
        # asset-table-view 8.x / fix-asset-table-ui-bugs: class sections
        # default to expanded (isOpen: true on load); user can collapse
        # by clicking the header.

        # Locate the row whose name is "PETR4" and click its delete button.
        petr4_row = asset_rows.filter(has_text="PETR4")
        assert petr4_row.count() == 1, "PETR4 row should exist before delete"
        petr4_asset_id = petr4_row.get_attribute("data-asset-id")
        petr4_row.locator(SELECTORS["dashboard_asset_delete_btn"]).click()
        page.wait_for_timeout(300)  # let Alpine x-show toggle the confirm dialog

        # Click the confirm button in the per-row delete dialog.
        confirm = page.locator(
            f'[data-testid="dashboard-asset-delete-confirm"][data-asset-id="{petr4_asset_id}"]'
        )
        confirm.locator(SELECTORS["dashboard_asset_delete_confirm_yes"]).click()

        # Wait for delete reload to settle on 2 remaining rows.
        page.wait_for_function(
            f"() => document.querySelectorAll('{SELECTORS['dashboard_asset_row']}').length === 2",
            timeout=10000,
        )
        page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)

        # --- 4. Verify dashboard shows 3 class sections, 2 assets.
        page.wait_for_timeout(300)
        sections = page.locator(SELECTORS["dashboard_class_section"])
        assert sections.count() == 3

        # The remaining assets are inside collapsed sections. Count via
        # DOM presence (not visibility).
        asset_rows = page.locator(SELECTORS["dashboard_asset_row"])
        assert asset_rows.count() == 2, f"expected 2 asset rows, got {asset_rows.count()}"
        dashboard_text = page.locator("main").inner_text()
        assert "Tesouro Selic" in dashboard_text
        assert "IVVB11" in dashboard_text
        assert "PETR4" not in dashboard_text
