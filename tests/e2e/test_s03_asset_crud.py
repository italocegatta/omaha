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

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .test_s04_user_journey import _login_and_select_italo

S03_SELECTORS = {
    "dashboard_add_asset_btn": '[data-testid="dashboard-add-asset-btn"]',
    "dashboard_add_asset_form": '[data-testid="dashboard-add-asset-form"]',
    "dashboard_add_asset_name_input": '[data-testid="dashboard-add-asset-name-input"]',
    "dashboard_add_asset_pct_input": '[data-testid="dashboard-add-asset-pct-input"]',
    "dashboard_add_asset_save": '[data-testid="dashboard-add-asset-save"]',
    "dashboard_add_asset_cancel": '[data-testid="dashboard-add-asset-cancel"]',
    "dashboard_add_asset_error": '[data-testid="dashboard-add-asset-error"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "dashboard_asset_delete_btn": '[data-testid="dashboard-asset-delete-btn"]',
    "dashboard_asset_delete_confirm": '[data-testid="dashboard-asset-delete-confirm"]',
    "dashboard_asset_delete_confirm_yes": '[data-testid="dashboard-asset-delete-confirm-yes"]',
    "dashboard_asset_delete_confirm_no": '[data-testid="dashboard-asset-delete-confirm-no"]',
    "dashboard_asset_delete_confirm_error": '[data-testid="dashboard-asset-delete-confirm-error"]',
    "class_summary_row": '[data-testid="class-summary-row"]',
    "asset_row_name": '[data-testid="asset-row-name"]',
}


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
    page.wait_for_selector(S03_SELECTORS["class_summary_row"], timeout=8000)


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
    page.wait_for_selector(S03_SELECTORS["dashboard_asset_row"], timeout=8000)


class TestS03AssetCRUD:
    """4 e2e tests for the S03 dashboard-based asset CRUD surface."""

    def test_assets_route_redirects_to_dashboard(
        self, page: Page, live_url: str
    ) -> None:
        """GET /assets redirects to / with 302 (S03/T05).

        Setup: login + select Italo.
        """
        _login_and_select_italo(page, live_url)

        page.goto(f"{live_url}/assets")

        assert (
            "/assets" not in page.url
        ), f"expected redirect away from /assets, got URL: {page.url}"
        profile_header = page.locator('[data-testid="profile-name"]')
        profile_header.wait_for(state="visible", timeout=5000)
        assert "Bem-vindo" in profile_header.inner_text()

    def test_add_asset_via_inline_form(self, page: Page, live_url: str) -> None:
        """Click + Ativo → fill form → save → asset row appears.

        Setup: login + select Italo; create 1 class via snapshot.
        """
        _login_and_select_italo(page, live_url)
        _create_seed_classes(page, [["Renda Fixa", 100]])

        class_section = page.locator(S03_SELECTORS["class_summary_row"]).first
        class_section.locator(S03_SELECTORS["dashboard_add_asset_btn"]).wait_for(
            state="visible", timeout=5000
        )
        class_section.locator(S03_SELECTORS["dashboard_add_asset_btn"]).click()
        class_section.locator(S03_SELECTORS["dashboard_add_asset_form"]).wait_for(
            state="visible", timeout=2000
        )
        class_section.locator(S03_SELECTORS["dashboard_add_asset_name_input"]).fill("PETR4")
        class_section.locator(S03_SELECTORS["dashboard_add_asset_pct_input"]).fill("0")
        class_section.locator(S03_SELECTORS["dashboard_add_asset_save"]).click()

        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{S03_SELECTORS['dashboard_asset_row']}').length === 1",
                timeout=8000,
            )
        except Exception:
            _debug_dump(page, "post_add_asset")
            raise

        rows = page.locator(S03_SELECTORS["dashboard_asset_row"])
        assert rows.count() == 1
        assert "PETR4" in rows.first.locator(S03_SELECTORS["asset_row_name"]).inner_text()

    def test_delete_asset_via_x_button(self, page: Page, live_url: str) -> None:
        """Click × on an asset row → confirm dialog → cancel hides it →
        click × again → confirm → row is removed.

        Setup: create 1 class with 1 asset via seed helpers.
        """
        _login_and_select_italo(page, live_url)
        _create_seed_classes(page, [["Renda Fixa", 100]])
        _create_seed_assets(page, [("Renda Fixa", "PETR4", 0)])

        asset_row = page.locator(S03_SELECTORS["dashboard_asset_row"]).first
        assert asset_row.count() == 1

        # First × click → confirm visible → cancel → confirm hidden.
        asset_row.locator(S03_SELECTORS["dashboard_asset_delete_btn"]).click()
        confirm = asset_row.locator(S03_SELECTORS["dashboard_asset_delete_confirm"])
        confirm.wait_for(state="visible", timeout=2000)
        asset_row.locator(S03_SELECTORS["dashboard_asset_delete_confirm_no"]).click()
        confirm.wait_for(state="hidden", timeout=2000)

        # Row still present after cancel.
        assert page.locator(S03_SELECTORS["dashboard_asset_row"]).count() == 1

        # Second × click → confirm visible → yes → row removed.
        asset_row.locator(S03_SELECTORS["dashboard_asset_delete_btn"]).click()
        confirm.wait_for(state="visible", timeout=2000)
        asset_row.locator(S03_SELECTORS["dashboard_asset_delete_confirm_yes"]).click()

        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{S03_SELECTORS['dashboard_asset_row']}').length === 0",
                timeout=8000,
            )
        except Exception:
            _debug_dump(page, "post_delete_asset")
            raise
        assert page.locator(S03_SELECTORS["dashboard_asset_row"]).count() == 0

    def test_full_asset_crud_journey(self, page: Page, live_url: str) -> None:
        """Add 2 assets via the inline form, delete the first, keep the second.

        Setup: login + select Italo; create 1 class; drive the inline
        form twice; delete the first asset; assert the second remains.
        """
        _login_and_select_italo(page, live_url)
        _create_seed_classes(page, [["Renda Fixa", 100]])

        # First inline add.
        section = page.locator(S03_SELECTORS["class_summary_row"]).first
        section.locator(S03_SELECTORS["dashboard_add_asset_btn"]).click()
        section.locator(S03_SELECTORS["dashboard_add_asset_form"]).wait_for(
            state="visible", timeout=2000
        )
        section.locator(S03_SELECTORS["dashboard_add_asset_name_input"]).fill("PETR4")
        section.locator(S03_SELECTORS["dashboard_add_asset_pct_input"]).fill("0")
        section.locator(S03_SELECTORS["dashboard_add_asset_save"]).click()

        page.wait_for_function(
            "() => document.querySelectorAll("
            f"'{S03_SELECTORS['dashboard_asset_row']}').length === 1",
            timeout=8000,
        )

        # Second inline add.
        section = page.locator(S03_SELECTORS["class_summary_row"]).first
        section.locator(S03_SELECTORS["dashboard_add_asset_btn"]).click()
        section.locator(S03_SELECTORS["dashboard_add_asset_form"]).wait_for(
            state="visible", timeout=2000
        )
        section.locator(S03_SELECTORS["dashboard_add_asset_name_input"]).fill("VALE3")
        section.locator(S03_SELECTORS["dashboard_add_asset_pct_input"]).fill("100")
        section.locator(S03_SELECTORS["dashboard_add_asset_save"]).click()

        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{S03_SELECTORS['dashboard_asset_row']}').length === 2",
                timeout=8000,
            )
        except Exception:
            _debug_dump(page, "post_add_two_assets")
            raise

        rows = page.locator(S03_SELECTORS["dashboard_asset_row"])
        assert rows.count() == 2

        # Delete the first row (PETR4 — display_order 0).
        first_row = rows.first
        first_row.locator(S03_SELECTORS["dashboard_asset_delete_btn"]).click()
        first_row.locator(S03_SELECTORS["dashboard_asset_delete_confirm"]).wait_for(
            state="visible", timeout=2000
        )
        first_row.locator(S03_SELECTORS["dashboard_asset_delete_confirm_yes"]).click()

        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{S03_SELECTORS['dashboard_asset_row']}').length === 1",
                timeout=8000,
            )
        except Exception:
            _debug_dump(page, "post_delete_first_asset")
            raise

        # Only VALE3 remains.
        remaining = page.locator(S03_SELECTORS["dashboard_asset_row"])
        assert remaining.count() == 1
        remaining_name = remaining.first.locator(S03_SELECTORS["asset_row_name"]).inner_text()
        assert "VALE3" in remaining_name, f"expected VALE3 to remain, got {remaining_name!r}"
        page_text = page.locator("main").inner_text()
        assert "PETR4" not in page_text, f"PETR4 should be gone, page text: {page_text!r}"
