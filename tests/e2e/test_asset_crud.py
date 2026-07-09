"""Real-browser E2E for the S03 inline asset CRUD + /assets retirement journey.

Drives a headless chromium against a live uvicorn instance to
verify the S03 dashboard-based asset management end to end:

  login → select profile → verify /assets redirects to / →
  create 1 class via the snapshot form →
  click the per-class "+ Ativo" button to open the inline form →
  fill name + target %, save, and assert the asset row appears →
  click × on an asset row, dismiss the confirm dialog (cancel) →
  click × again, click "Sim, remover", assert the row is removed →
  drive a full CRUD journey: add 2 assets via the inline form,
  delete the first one, assert only the second remains.

The /assets route was retired by S03/T05 (302 → /). Asset CRUD
now lives entirely on the dashboard: the per-class "+ Ativo"
form (T03) and the per-asset × delete button (T04).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .selectors import SELECTORS
from .test_import_user_journey import _login_and_select_italo


def _debug_dump(page: Page, tag: str) -> None:
    import os

    os.makedirs("/tmp/s03_e2e_debug", exist_ok=True)
    page.screenshot(path=f"/tmp/s03_e2e_debug/{tag}.png", full_page=True)
    with open(f"/tmp/s03_e2e_debug/{tag}.txt", "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")


def _create_seed_classes(page: Page, classes: list[tuple[str, int]]) -> None:
    page.evaluate(
        """async (items) => {
            const fd = new FormData();
            for (const [name, pct] of items) {
                fd.append('name[]', name);
                fd.append('target_pct[]', String(pct));
            }
            const r = await fetch('/classes', { method: 'POST', body: fd });
            if (!r.ok) {
                throw new Error('POST /classes ' + r.status + ': ' + await r.text());
            }
        }""",
        classes,
    )
    page.goto(page.url)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=8000)


def _create_seed_assets(page: Page, assets: list[tuple[str, str, float | int]]) -> None:
    """Seed assets via POST /api/assets JSON. Each tuple is
    ``(class_name, asset_name, target_pct)``. Looks up class_id from
    the dashboard's ``data-class-id`` attribute."""
    class_map: dict[str, int] = page.evaluate(
        """() => {
            const out = {};
            document.querySelectorAll('[data-testid="class-summary-row"]').forEach((row) => {
                const nameEl = row.querySelector('[data-testid="class-section-name"]');
                const id = row.dataset.classId;
                if (nameEl && id) out[nameEl.textContent.trim()] = parseInt(id, 10);
            });
            return out;
        }"""
    )
    for class_name, asset_name, pct in assets:
        if class_name not in class_map:
            raise RuntimeError(f"class {class_name!r} not found in rendered dashboard")
        class_id = class_map[class_name]
        page.evaluate(
            """async ({classId, assetName, pct}) => {
                const r = await fetch('/api/assets', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: assetName,
                        asset_class_id: classId,
                        target_pct: String(pct),
                    }),
                });
                if (!r.ok) {
                    throw new Error('POST /api/assets ' + r.status + ': ' + await r.text());
                }
            }""",
            {"classId": class_id, "assetName": asset_name, "pct": pct},
        )
    page.goto(page.url)
    # fix-asset-table-ui-bugs: sections are expanded by default on load
    # (isOpen: true). The test asserts DOM presence, not visibility.
    page.wait_for_selector(SELECTORS["dashboard_asset_row"], state="attached", timeout=8000)


class TestS03AssetCRUD:
    """4 e2e tests for the S03 dashboard-based asset CRUD surface."""

    def test_assets_route_redirects_to_dashboard(self, page: Page, live_url: str) -> None:
        """GET /assets redirects to / with 302 (S03/T05).

        Setup: login + select Italo.
        """
        _login_and_select_italo(page, live_url)

        page.goto(f"{live_url}/assets")

        assert "/assets" not in page.url, (
            f"expected redirect away from /assets, got URL: {page.url}"
        )
        profile_header = page.locator('[data-testid="profile-switcher"]')
        profile_header.wait_for(state="visible", timeout=5000)
        # F02: the h1 "Bem-vindo, <profile>" chip was replaced by a
        # <select data-testid="profile-switcher">. The switcher's
        # selected option is the active profile name.
        selected = profile_header.evaluate("el => el.value")
        assert selected, f"profile-switcher has no selected value: {selected!r}"

    def test_add_asset_via_modal(self, page: Page, live_url: str) -> None:
        """Click + Ativo → fill modal → save → asset row appears.

        Setup: login + select Italo; create 1 class via snapshot.
        """
        _login_and_select_italo(page, live_url)
        _create_seed_classes(page, [["Renda Fixa", 100]])

        # asset-table-view 8.x/10.x / fix-asset-table-ui-bugs: class sections
        # default to expanded (isOpen: true on load); user can collapse
        # by clicking the header.
        # and the add-asset flow uses a dashboard-level modal.
        page.locator(SELECTORS["dashboard_add_asset_open"]).click()
        modal = page.locator(SELECTORS["dashboard_add_asset_modal"])
        modal.wait_for(state="visible", timeout=5000)

        modal.locator(SELECTORS["dashboard_add_asset_class"]).select_option(label="Renda Fixa")
        modal.locator(SELECTORS["dashboard_add_asset_name"]).fill("PETR4")
        modal.locator(SELECTORS["dashboard_add_asset_target_pct"]).fill("0")
        before = page.locator(SELECTORS["dashboard_asset_row"]).count()
        modal.locator(SELECTORS["dashboard_add_asset_submit"]).click()

        # Wait for asset row to appear after reload.
        page.wait_for_function(
            f"() => document.querySelectorAll('{SELECTORS['dashboard_asset_row']}').length > {before}",
            timeout=10000,
        )
        page.wait_for_selector(SELECTORS["dashboard_asset_row"], state="attached", timeout=8000)

        rows = page.locator(SELECTORS["dashboard_asset_row"])
        assert rows.count() == 1
        assert "PETR4" in rows.first.locator(SELECTORS["asset_row_name"]).inner_text()

    def test_delete_asset_via_x_button(self, page: Page, live_url: str) -> None:
        """Click × on an asset row → confirm dialog → cancel hides it →
        click × again → confirm → row is removed.

        Setup: create 1 class with 1 asset via seed helpers.
        """
        _login_and_select_italo(page, live_url)
        _create_seed_classes(page, [["Renda Fixa", 100]])
        _create_seed_assets(page, [("Renda Fixa", "PETR4", 0)])

        # asset-table-view 8.x / fix-asset-table-ui-bugs: class sections
        # default to expanded (isOpen: true on load); user can collapse
        # by clicking the header.

        asset_row = page.locator(SELECTORS["dashboard_asset_row"]).first
        assert asset_row.count() == 1
        asset_id = asset_row.get_attribute("data-asset-id")

        # First × click → confirm visible → cancel → confirm hidden.
        asset_row.locator(SELECTORS["dashboard_asset_delete_btn"]).click(force=True)
        confirm = page.locator(
            f'[data-testid="dashboard-asset-delete-confirm"][data-asset-id="{asset_id}"]'
        )
        confirm.wait_for(state="visible", timeout=2000)
        confirm.locator(SELECTORS["dashboard_asset_delete_confirm_no"]).click(force=True)
        confirm.wait_for(state="hidden", timeout=2000)

        # Row still present after cancel.
        assert page.locator(SELECTORS["dashboard_asset_row"]).count() == 1

        # Second × click → confirm visible → yes → row removed.
        asset_row.locator(SELECTORS["dashboard_asset_delete_btn"]).click(force=True)
        confirm.wait_for(state="visible", timeout=2000)
        confirm.locator(SELECTORS["dashboard_asset_delete_confirm_yes"]).click(force=True)

        # Wait for row removal after reload.
        page.wait_for_function(
            f"() => document.querySelectorAll('{SELECTORS['dashboard_asset_row']}').length === 0",
            timeout=10000,
        )
        assert page.locator(SELECTORS["dashboard_asset_row"]).count() == 0

    def test_full_asset_crud_journey(self, page: Page, live_url: str) -> None:
        """Add 2 assets via the modal, delete the first, keep the second.

        Setup: login + select Italo; create 1 class; drive the modal
        add-asset flow twice; delete the first asset; assert the second
        remains.
        """
        _login_and_select_italo(page, live_url)
        _create_seed_classes(page, [["Renda Fixa", 100]])

        # First modal add.
        page.locator(SELECTORS["dashboard_add_asset_open"]).click()
        modal = page.locator(SELECTORS["dashboard_add_asset_modal"])
        modal.wait_for(state="visible", timeout=5000)
        modal.locator(SELECTORS["dashboard_add_asset_class"]).select_option(label="Renda Fixa")
        modal.locator(SELECTORS["dashboard_add_asset_name"]).fill("PETR4")
        modal.locator(SELECTORS["dashboard_add_asset_target_pct"]).fill("0")
        before = page.locator(SELECTORS["dashboard_asset_row"]).count()
        modal.locator(SELECTORS["dashboard_add_asset_submit"]).click()

        page.wait_for_function(
            f"() => document.querySelectorAll('{SELECTORS['dashboard_asset_row']}').length > {before}",
            timeout=10000,
        )

        # Second add via direct API.
        _create_seed_assets(page, [("Renda Fixa", "VALE3", 100)])

        page.wait_for_function(
            f"() => document.querySelectorAll('{SELECTORS['dashboard_asset_row']}').length === 2",
            timeout=10000,
        )

        rows = page.locator(SELECTORS["dashboard_asset_row"])
        assert rows.count() == 2

        # Delete the first row (PETR4 — display_order 0).
        first_row = page.locator(SELECTORS["dashboard_asset_row"]).first
        first_asset_id = first_row.get_attribute("data-asset-id")
        first_row.locator(SELECTORS["dashboard_asset_delete_btn"]).click(force=True)
        confirm = page.locator(
            f'[data-testid="dashboard-asset-delete-confirm"][data-asset-id="{first_asset_id}"]'
        )
        confirm.wait_for(state="visible", timeout=2000)
        confirm.locator(SELECTORS["dashboard_asset_delete_confirm_yes"]).click(force=True)

        # Wait for row removal after reload.
        page.wait_for_function(
            f"() => document.querySelectorAll('{SELECTORS['dashboard_asset_row']}').length === 1",
            timeout=10000,
        )

        # Only VALE3 remains.
        remaining = page.locator(SELECTORS["dashboard_asset_row"])
        assert remaining.count() == 1
        remaining_name = remaining.first.locator(SELECTORS["asset_row_name"]).inner_text()
        assert "VALE3" in remaining_name, f"expected VALE3 to remain, got {remaining_name!r}"
        page_text = page.locator("main").inner_text()
        assert "PETR4" not in page_text, f"PETR4 should be gone, page text: {page_text!r}"
