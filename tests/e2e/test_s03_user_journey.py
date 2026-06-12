"""Real-browser E2E for the S03 user journey.

Drives a headless chromium against a live uvicorn instance to
verify the complete S03 user loop end to end:

  login → select profile → create 3 classes → add 3 assets →
  delete 1 asset → verify dashboard distribution

This test exists because the route-level TestClient tests in
``test_t03_assets_e2e.py`` bypass the rendered HTML. The
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


SELECTORS = {
    "login_user": 'input[name="username"]',
    "login_pass": 'input[name="password"]',
    "login_submit": 'button[type="submit"]',
    "profile_picker": "form.profile-picker button",
    "nav_dashboard": '[data-testid="nav-dashboard"]',
    "nav_assets": '[data-testid="nav-assets"]',
    "class_summary_row": '[data-testid="class-summary-row"]',
    "asset_editor_name": '[data-testid="asset-editor-name"]',
    "asset_editor_class": '[data-testid="asset-editor-class"]',
    "asset_editor_add": '[data-testid="asset-editor-add"]',
    "asset_row": '[data-testid="asset-row"]',
    "asset_row_delete": '[data-testid="asset-row-delete"]',
    "dashboard_class_section": '[data-testid="dashboard-class-section"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
}


def _login_and_select_italo(page: Page, base_url: str) -> None:
    """Drive the login + profile picker using the live UI."""
    page.goto(f"{base_url}/login")
    page.fill(SELECTORS["login_user"], "family")
    page.fill(SELECTORS["login_pass"], "test-password")
    page.click(SELECTORS["login_submit"])
    page.wait_for_url(re.compile(r"/profiles$"))

    # The picker renders one button per profile, in display_order.
    # The seed creates Italo first, Ana Livia second.
    page.locator(SELECTORS["profile_picker"]).filter(has_text="Italo").click()
    page.wait_for_url(re.compile(r"/$"))


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


class TestS03UserJourney:
    """One class per test scenario so failures are isolated."""

    def test_login_select_profile_renders_dashboard(self, page: Page, live_url: str) -> None:
        """Smoke: login + select Italo lands on a dashboard with no classes yet."""
        _login_and_select_italo(page, live_url)

        # The nav is rendered and points to the right places.
        assert page.locator(SELECTORS["nav_dashboard"]).count() == 1
        assert page.locator(SELECTORS["nav_assets"]).count() == 1

        # No classes yet → empty state on the dashboard.
        page.wait_for_selector('[data-testid="empty-state"]', timeout=5000)
        assert page.locator(SELECTORS["class_summary_row"]).count() == 0

    def test_full_crud_journey_classes_assets_delete(self, page: Page, live_url: str) -> None:
        """Full S03 user journey: 3 classes, 3 assets, delete 1, verify dashboard.

        This is the regression test for the delete-button-outside-form
        bug. If the formaction button is not associated with a <form>
        (the original bug), clicking the "x" does nothing and the
        test fails on the post-delete row count.
        """
        _login_and_select_italo(page, live_url)

        # --- 1. Create 3 classes summing to 100 via the snapshot form.
        # The /classes page was retired in S02/T07 — class CRUD goes
        # through the snapshot POST /classes (parallel form arrays)
        # or the REST API. We use fetch() + FormData from the browser
        # context since the page is already logged in.
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

        # Reload the dashboard to pick up the new classes.
        page.goto(f"{live_url}/")
        page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)
        assert page.locator(SELECTORS["class_summary_row"]).count() == 3

        # --- 2. Add 3 assets, one per class.
        page.click(SELECTORS["nav_assets"])
        page.wait_for_url(re.compile(r"/assets$"))

        for i, (class_name, asset_name) in enumerate(
            (
                ("Renda Fixa", "Tesouro Selic"),
                ("Acoes", "PETR4"),
                ("Reserva", "IVVB11"),
            )
        ):
            page.fill(SELECTORS["asset_editor_name"], asset_name)
            page.select_option(SELECTORS["asset_editor_class"], label=class_name)
            page.click(SELECTORS["asset_editor_add"])
            # Wait for the asset to appear in the rendered list
            # (the editor re-renders, the POST/303 round-trip is
            # server-bound). i+1 because the iteration index
            # starts at 0.
            try:
                page.wait_for_function(
                    "() => document.querySelectorAll("
                    f"'{SELECTORS['asset_row']}').length === {i + 1}",
                    timeout=5000,
                )
            except Exception:
                _debug_dump(page, f"asset_iter_{i}_{class_name}_{asset_name}")
                raise

        assert page.locator(SELECTORS["asset_row"]).count() == 3

        # --- 3. Delete the second asset (PETR4 / Acoes).
        # Locate the row whose name is "PETR4" and click its delete.
        petr4_row = page.locator(SELECTORS["asset_row"]).filter(has_text="PETR4")
        assert petr4_row.count() == 1, "PETR4 row should exist before delete"
        petr4_row.locator(SELECTORS["asset_row_delete"]).click()

        # The formaction routes the POST to /assets/{id}/delete;
        # a 303 redirects back to /assets. Wait for the row count
        # to drop. The form is INSIDE the page, so the click
        # actually fires — this is the regression assertion.
        try:
            page.wait_for_function(
                f"() => document.querySelectorAll('{SELECTORS['asset_row']}').length === 2",
                timeout=5000,
            )
        except Exception:
            _debug_dump(page, "post_delete")
            raise
        assert page.locator(SELECTORS["asset_row"]).count() == 2
        # The remaining 2 are Tesouro Selic and IVVB11 (no PETR4).
        page_text = page.locator(".asset-editor").inner_text()
        assert "PETR4" not in page_text

        # --- 4. Verify the dashboard shows 3 class sections, 2 assets.
        page.click(SELECTORS["nav_dashboard"])
        page.wait_for_url(re.compile(r"/$"))

        sections = page.locator(SELECTORS["dashboard_class_section"])
        assert sections.count() == 3

        asset_rows = page.locator(SELECTORS["dashboard_asset_row"])
        assert asset_rows.count() == 2
        dashboard_text = page.locator("main").inner_text()
        assert "Tesouro Selic" in dashboard_text
        assert "IVVB11" in dashboard_text
        assert "PETR4" not in dashboard_text
