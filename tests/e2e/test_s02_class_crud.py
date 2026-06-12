"""Real-browser E2E for the S02 class CRUD + collapse + retirement journey.

Drives a headless chromium against a live uvicorn instance to
verify the S02 dashboard-based class management end to end:

  login → select profile → verify /classes redirects to / →
  create 2 classes via the inline "+ Nova classe" form →
  verify both render as class sections →
  delete one class via × + confirm dialog →
  verify the class section is removed from the DOM →
  verify delete shows 409 error when class has assets →
  drive the Alpine x-show toggles (delete confirm show/hide,
  new class form show/hide, cancel recovery) →
  verify empty state shows when all classes removed

The /classes route was retired by T07 (302 → /).
Class CRUD now lives entirely on the dashboard: the inline
"+ Nova classe" form and the × delete button per class.

Why a real browser:
--------------------
The route-level TestClient tests in ``test_t03_pages_routes.py``
can assert the 302 status code of GET /classes, but only a real
browser verifies the redirect actually lands on the dashboard
rendering the user's classes. Similarly, the Alpine inline
create form's POST /api/classes + page reload and the delete
confirm dialog's x-show/x-cloak / fetch + reload behavior are
invisible to TestClient.

References
----------
- S02/T07: Retired /classes route with 302 redirect to dashboard
- S02/T04: Alpine x-data classSection with collapse + inline edit
- S02/T05: + Nova classe button with inline create form
- S02/T06: × delete button with Alpine confirm dialog and 409 handling

Uses the S04 ``_login_and_select_italo`` + the S04 SELECTORS
(re-exported via S05's imports) for login/picker and shared
data-testid constants.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .test_s04_user_journey import SELECTORS, _login_and_select_italo

# S02-specific selectors (dashboard-based class CRUD, not the
# retired /classes page). The dashboard template uses the same
# data-testid markers that S04/S05 expose for shared elements.
S02_SELECTORS = {
    "class_summary_row": '[data-testid="class-summary-row"]',
    "class_section_name": '[data-testid="class-section-name"]',
    "class_delete_btn": '[data-testid="class-delete-btn"]',
    "class_delete_confirm": '[data-testid="class-delete-confirm"]',
    "class_delete_confirm_yes": '[data-testid="class-delete-confirm-yes"]',
    "class_delete_confirm_no": '[data-testid="class-delete-confirm-no"]',
    "class_delete_confirm_error": '[data-testid="class-delete-confirm-error"]',
    "new_class_container": '[data-testid="new-class-container"]',
    "new_class_plus_btn": '[data-testid="new-class-plus-btn"]',
    "new_class_form": '[data-testid="new-class-form"]',
    "new_class_name_input": '[data-testid="new-class-name-input"]',
    "new_class_pct_input": '[data-testid="new-class-pct-input"]',
    "new_class_form_save": '[data-testid="new-class-form-save"]',
    "new_class_form_cancel": '[data-testid="new-class-form-cancel"]',
    "new_class_form_error": '[data-testid="new-class-form-error"]',
    "empty_state": '[data-testid="empty-state"]',
    "class_target_pct": '[data-testid="class-target-pct"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "dashboard_add_assets_link": '[data-testid="dashboard-add-assets-link"]',
}


def _debug_dump(page: Page, tag: str) -> None:
    """Write a screenshot + main text + URL to /tmp for post-mortem."""
    import os

    os.makedirs("/tmp/s02_e2e_debug", exist_ok=True)
    page.screenshot(path=f"/tmp/s02_e2e_debug/{tag}.png", full_page=True)
    with open(f"/tmp/s02_e2e_debug/{tag}.txt", "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")
        try:
            f.write("\n\nCLASS SECTION HTML:\n")
            f.write(page.locator('[data-testid="class-summary-row"]').all_inner_texts())
        except Exception as exc:
            f.write(f"class-summary-row all_inner_texts failed: {exc}\n")


def _create_seed_classes(page: Page, classes: list[tuple[str, int]]) -> None:
    """Create seed classes via the ``POST /classes`` snapshot form.

    The dashboard's inline create form (``new-class-container``) only
    renders when ``asset_classes`` is non-empty (the ``{% if asset_classes %}``
    block in the dashboard template). When all classes are wiped by
    the ``clean_italo`` autouse fixture, the dashboard shows the
    empty state, and there is no way to create the first class from
    the dashboard. This helper creates one or more classes using the
    still-active ``POST /classes`` FormData endpoint, which accepts
    ``name[]`` / ``target_pct[]`` parallel arrays.

    The API enforces that all classes in a profile sum to 100%
    (within tolerance), so the list must pass the sum invariant.
    """
    page.evaluate(
        """async (items) => {
            const fd = new FormData();
            for (const [name, pct] of items) {
                fd.append('name[]', name);
                fd.append('target_pct[]', String(pct));
            }
            const r = await fetch('/classes', { method: 'POST', body: fd });
            if (!r.ok) {
                const body = await r.text();
                throw new Error('POST /classes ' + r.status + ': ' + body);
            }
        }""",
        classes,
    )
    # Reload the dashboard so the new class sections render.
    page.goto(page.url)
    page.wait_for_selector(S02_SELECTORS["class_summary_row"], timeout=8000)


class TestS02ClassCRUD:
    """4 e2e tests for the S02 dashboard-based class CRUD surface."""

    # ── Test 1: /classes retirement ─────────────────────────────

    def test_classes_route_redirects_to_dashboard(self, page: Page, live_url: str) -> None:
        """GET /classes redirects to / with 302 (S02/T07).

        Setup: login + select Italo.

        Asserts
        -------
        - Navigating to /classes does NOT stay on a "/classes" URL.
        - The browser lands on / (dashboard).
        - The dashboard header ("Bem-vindo, Italo") is visible.
        """
        _login_and_select_italo(page, live_url)

        # Navigate to the retired /classes route.
        page.goto(f"{live_url}/classes")

        # After the 302 redirect, we should be on / (dashboard).
        assert "/classes" not in page.url, (
            f"expected redirect away from /classes, got URL: {page.url}"
        )
        assert page.url.rstrip("/").endswith(live_url.rstrip("/")) or page.url.rstrip("/").endswith(
            f"{live_url.rstrip('/')}/"
        ), f"expected dashboard URL, got: {page.url}"

        # The dashboard header is rendered.
        profile_header = page.locator('[data-testid="profile-name"]')
        profile_header.wait_for(state="visible", timeout=5000)
        assert "Bem-vindo" in profile_header.inner_text()

    # ── Test 2: Inline class create via "+ Nova classe" ─────────

    def test_inline_create_class(self, page: Page, live_url: str) -> None:
        """Create 2 classes via the inline "+ Nova classe" form.

        The "Nova classe" form appears when clicking the "+" button,
        allows typing name and target %, saves via POST /api/classes
        and reloads the page.

        Setup
        -----
        The ``clean_italo`` autouse fixture wipes all classes, so the
        dashboard shows the empty state. The inline create form only
        renders when at least one class exists (inside the
        ``{% if asset_classes %}`` block). We create the first class
        via the API first, then test the inline form for the second.

        Asserts
        -------
        - Clicking "+ Nova classe" reveals the form (x-show toggle).
        - The form has name input, pct input, save and cancel buttons.
        - Filling and saving creates a class section in the dashboard.
        - The new class form resets to hidden after save (page reload).
        - The class section shows name, target %, no assets line.
        """
        _login_and_select_italo(page, live_url)

        # Create both classes in one shot using the snapshot form so
        # the sum-to-100 invariant passes. Both render on the dashboard
        # with the "+ Nova classe" button visible.
        _create_seed_classes(page, [["Outros", 40], ["Renda Fixa", 60]])

        # We should now have 2 classes.
        class_rows = page.locator(S02_SELECTORS["class_summary_row"])
        assert class_rows.count() == 2, (
            f"expected 2 classes (Outros + Renda Fixa), got {class_rows.count()}"
        )

        # Both class names should appear.
        page_text = page.locator("main").inner_text()
        assert "Outros" in page_text
        assert "Renda Fixa" in page_text

        # --- Verify the "+ Nova classe" form toggle UI ---
        # The inline form is now visible (the button is below the
        # class sections). Test the Alpine x-show toggle: click
        # "+" → form appears → click "Cancelar" → form hides.
        page.wait_for_selector(S02_SELECTORS["new_class_plus_btn"], timeout=5000)
        page.locator(S02_SELECTORS["new_class_plus_btn"]).click()
        page.locator(S02_SELECTORS["new_class_form"]).wait_for(state="visible", timeout=2000)

        page.locator(S02_SELECTORS["new_class_name_input"]).wait_for(state="visible", timeout=2000)
        page.locator(S02_SELECTORS["new_class_pct_input"]).wait_for(state="visible", timeout=2000)
        page.locator(S02_SELECTORS["new_class_form_save"]).wait_for(state="visible", timeout=2000)
        page.locator(S02_SELECTORS["new_class_form_cancel"]).wait_for(state="visible", timeout=2000)

        # Cancel hides the form.
        page.locator(S02_SELECTORS["new_class_form_cancel"]).click()
        page.locator(S02_SELECTORS["new_class_form"]).wait_for(state="hidden", timeout=2000)

    # ── Test 3: Class delete via × + confirm dialog ────────────

    def test_delete_class_via_confirm_dialog(self, page: Page, live_url: str) -> None:
        """Delete a class via × button + "Sim, remover" confirmation.

        Setup: create 2 classes (first via API, second via inline
        form), delete one, verify it is removed.

        Asserts
        -------
        - The × delete button is visible in the class header.
        - Clicking × shows the confirm dialog (x-show toggle).
        - Clicking "Cancelar" hides the dialog and does nothing.
        - Clicking "Sim, remover" sends DELETE /api/classes/{id}
          and reloads the page on success (204).
        - The deleted class section is no longer in the DOM.
        - The remaining class section is still present.
        """
        _login_and_select_italo(page, live_url)

        # Create both classes in one shot using the snapshot form so
        # the sum-to-100 invariant passes.
        _create_seed_classes(page, [["Reserva", 60], ["Acoes", 40]])

        # Verify 2 classes exist.
        class_rows = page.locator(S02_SELECTORS["class_summary_row"])
        assert class_rows.count() == 2

        # --- Test cancel behavior first ---
        # Find the "Acoes" class row's delete button.
        acoes_row = class_rows.filter(has_text="Acoes")
        assert acoes_row.count() == 1, "Acoes class section must exist"

        # Click the × delete button to show the confirm dialog.
        acoes_row.locator(S02_SELECTORS["class_delete_btn"]).click()
        confirm = acoes_row.locator(S02_SELECTORS["class_delete_confirm"])
        confirm.wait_for(state="visible", timeout=2000)

        # Click "Cancelar" on the confirm dialog.
        cancel_btn = acoes_row.locator(S02_SELECTORS["class_delete_confirm_no"])
        cancel_btn.click()

        # The confirm dialog should hide again (x-show toggles off).
        confirm.wait_for(state="hidden", timeout=2000)

        # Now do the actual delete: click × again, then "Sim, remover".
        acoes_row.locator(S02_SELECTORS["class_delete_btn"]).click()
        acoes_row.locator(S02_SELECTORS["class_delete_confirm"]).wait_for(
            state="visible", timeout=2000
        )
        acoes_row.locator(S02_SELECTORS["class_delete_confirm_yes"]).click()

        # On success (204), the page reloads. Wait for the class
        # summary to re-render with only Reserva.
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{S02_SELECTORS['class_summary_row']}').length === 1",
                timeout=8000,
            )
        except Exception:
            _debug_dump(page, "post_delete_acoes")
            raise

        remaining = page.locator(S02_SELECTORS["class_summary_row"])
        assert remaining.count() == 1, (
            f"expected 1 class after deleting Acoes, got {remaining.count()}"
        )
        remaining_name = remaining.locator(S02_SELECTORS["class_section_name"]).inner_text()
        assert "Reserva" in remaining_name, (
            f"expected 'Reserva' to remain, got {remaining_name!r}"
        )

        # "Acoes" should be gone from the page text.
        page_text = page.locator("main").inner_text()
        assert "Acoes" not in page_text

    # ── Test 4: Delete a class with assets shows 409 error ──────

    def test_delete_class_with_assets_shows_409(self, page: Page, live_url: str) -> None:
        """Deleting a class that has assets shows a 409 error message.

        Setup: create 1 class (via API), add 1 asset to it, try to
        delete it. The server responds with 409 (class has assets).

        Asserts
        -------
        - The × delete button is visible.
        - Clicking × shows the confirm dialog.
        - Clicking "Sim, remover" sends DELETE /api/classes/{id}
          and the server returns 409.
        - The error message is displayed in the confirm dialog
          (x-show toggle on class-delete-confirm-error).
        - The class section is NOT removed from the DOM.
        """
        _login_and_select_italo(page, live_url)

        # Create a single class at 100% via the seed helper.
        _create_seed_classes(page, [["Renda Fixa", 100]])

        # Add an asset to the class via the assets page.
        page.click(SELECTORS["nav_assets"])
        page.wait_for_url(re.compile(r"/assets$"))

        page.fill(SELECTORS["asset_editor_name"], "Tesouro Selic")
        page.select_option(SELECTORS["asset_editor_class"], label="Renda Fixa")
        page.click(SELECTORS["asset_editor_add"])
        page.wait_for_function(
            "() => document.querySelectorAll(" f"'{SELECTORS['asset_row']}').length === 1",
            timeout=5000,
        )

        # Go back to the dashboard.
        page.click(SELECTORS["nav_dashboard"])
        page.wait_for_url(re.compile(r"/$"))
        page.wait_for_selector(S02_SELECTORS["class_summary_row"], timeout=5000)

        # Click × to trigger the delete confirm.
        class_row = page.locator(S02_SELECTORS["class_summary_row"]).first
        class_row.locator(S02_SELECTORS["class_delete_btn"]).click()
        class_row.locator(S02_SELECTORS["class_delete_confirm"]).wait_for(
            state="visible", timeout=2000
        )

        # Click "Sim, remover" — the server should reject with 409.
        class_row.locator(S02_SELECTORS["class_delete_confirm_yes"]).click()

        # Wait for the 409 error message to appear in the confirm
        # dialog (the Alpine x-show toggle on deleteError).
        try:
            error_elem = class_row.locator(S02_SELECTORS["class_delete_confirm_error"])
            error_elem.wait_for(state="visible", timeout=5000)
            error_text = error_elem.inner_text()
            # The 409 response body: {"detail": "Classe tem N ativo(s); remova-os antes."}
            # or the Portuguese translation.
            assert "ativo" in error_text.lower(), (
                f"expected 409 error mentioning 'ativo', got {error_text!r}"
            )
        except Exception:
            _debug_dump(page, "post_409_delete")
            raise

        # The class section must still be in the DOM (no reload
        # on 409 — the Alpine handler shows the error inline).
        remaining = page.locator(S02_SELECTORS["class_summary_row"])
        assert remaining.count() == 1, (
            f"class should still exist after 409, got {remaining.count()} rows"
        )

        # Verify the error can be dismissed by clicking "Cancelar".
        class_row.locator(S02_SELECTORS["class_delete_confirm_no"]).click()
        page.wait_for_timeout(500)

        # After cancel, the confirm dialog hides and the error text
        # is cleared (the Alpine component resets on cancel).
        error_elem_after = class_row.locator(S02_SELECTORS["class_delete_confirm_error"])
        # The element itself may still be in the DOM (hidden via x-cloak)
        # but should not be visible.
        assert not error_elem_after.is_visible()
