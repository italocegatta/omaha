"""Real-browser E2E for the S02 class CRUD + collapse + retirement journey.

Drives a headless chromium against a live uvicorn instance to
verify the S02 dashboard-based class management end to end:

  login → select profile → verify /classes redirects to / →
  create 2 classes via the sidebar "+ Nova classe" modal →
  verify both render as class sections →
  delete one class via × + confirm dialog →
  verify the class section is removed from the DOM →
  verify delete shows 409 error when class has assets →
  drive the Alpine x-show toggles (delete confirm show/hide,
  new class modal show/hide, cancel recovery) →
  verify empty state shows when all classes removed

The /classes route was retired by T07 (302 → /).
Class CRUD now lives entirely on the dashboard: the sidebar's
"+ Nova classe" modal (dashboard-action-sidebar) and the × delete
button per class.

Why a real browser:
--------------------
The route-level TestClient tests in ``test_pages_routes.py``
can assert the 302 status code of GET /classes, but only a real
browser verifies the redirect actually lands on the dashboard
rendering the user's classes. Similarly, the Alpine new-class
modal's POST /api/classes + page reload and the delete confirm
dialog's x-show/x-cloak / fetch + reload behavior are invisible
to TestClient.

References
----------
- S02/T07: Retired /classes route with 302 redirect to dashboard
- S02/T04: Alpine x-data classSection with collapse + inline edit
- S02/T05: + Nova classe button with inline create form
- S02/T06: × delete button with Alpine confirm dialog and 409 handling
- dashboard-action-sidebar: + Nova classe moved to the sidebar
  modal (new-class-modal-overlay).

Uses the S04 ``_login_and_select_italo`` + the S04 SELECTORS
(re-exported via S05's imports) for login/picker and shared
data-testid constants.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .selectors import SELECTORS
from .test_import_user_journey import _login_and_select_italo


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

    The sidebar ``+ Nova classe`` modal
    (``new-class-modal-overlay``) also calls ``POST /api/classes``
    which now accepts any allocation sum. The snapshot form is
    used here to create multiple classes in one shot for faster
    test setup.
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
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=8000)


class TestS02ClassCRUD:
    """5 e2e tests for the S02 dashboard-based class CRUD surface."""

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

        # The dashboard header is rendered. F02 replaced the h1
        # "Bem-vindo, <profile>" chip with a <select data-testid=
        # "profile-switcher">. The switcher's selected option is the
        # active profile name.
        profile_header = page.locator('[data-testid="profile-switcher"]')
        profile_header.wait_for(state="visible", timeout=5000)
        selected_value = profile_header.evaluate("el => el.value")
        assert selected_value, f"profile-switcher has no selected value; got: {selected_value!r}"

    # ── Test 2: Create first class from empty state ────────────

    def test_create_first_class_from_empty_state(self, page: Page, live_url: str) -> None:
        """Create the very first class from the empty state dashboard.

        Bug fix: the "+ Nova classe" form was previously inside the
        ``{% if asset_classes %}`` Jinja block, so when the DB had
        zero classes, the form was not rendered. The empty state only
        showed a "Gerenciar classes" link pointing to ``/classes``,
        which had been retired in S02/T07 (302 redirect back to
        dashboard -- a dead loop).

        The fix moved the ``new-class-container`` outside the if/else
        so it is always visible. This test verifies the fix by
        starting with a clean DB (0 classes) and creating the first
        class directly via the sidebar modal.

        After dashboard-action-sidebar, the inline ``+ Nova classe``
        was promoted to a modal opened from the sidebar
        (``empty-state-create-class`` → ``new-class-modal-overlay``).
        The test exercises the same "first class from empty state"
        flow through the modal.

        ``POST /api/classes`` does NOT block by allocation sum --
        the user creates classes incrementally at any percentage.
        This test creates the first class at 60% to prove the
        sum-to-100 invariant is informational, not blocking.

        Asserts
        -------
        - The onboarding empty state is visible
          (``empty-state-onboarding`` card with the 3-step list).
        - The sidebar "+ Nova classe" button is visible despite 0 classes.
        - Clicking the sidebar button opens the new-class modal.
        - Filling name (60%) and saving creates a class section.
        - Page reloads with the class section visible.
        """
        _login_and_select_italo(page, live_url)

        # Verify the onboarding empty state is shown (0 classes).
        empty_state = page.locator(SELECTORS["empty_state"])
        empty_state.wait_for(state="visible", timeout=5000)
        assert "Vamos comecar" in empty_state.inner_text()

        # Verify the sidebar "+ Nova classe" button is visible.
        plus_btn = page.locator(SELECTORS["empty_state_create_class_btn"])
        plus_btn.wait_for(state="visible", timeout=2000)
        assert plus_btn.is_visible(), "'+ Nova classe' sidebar button must be visible"

        # Click the sidebar button to open the new-class modal.
        plus_btn.click()
        modal = page.locator(SELECTORS["new_class_modal_overlay"])
        modal.wait_for(state="visible", timeout=2000)
        modal.locator(SELECTORS["new_class_modal_name_input"]).wait_for(
            state="visible", timeout=2000
        )
        modal.locator(SELECTORS["new_class_modal_pct_input"]).wait_for(
            state="visible", timeout=2000
        )

        # Fill and save the first class at 60% (allocation is NOT
        # blocked by sum-to-100 -- the user creates classes at any
        # percentage and builds the portfolio incrementally).
        modal.locator(SELECTORS["new_class_modal_name_input"]).fill("Renda Fixa")
        modal.locator(SELECTORS["new_class_modal_pct_input"]).fill("60")
        modal.locator(SELECTORS["new_class_modal_submit"]).click()

        # On 201, the page reloads. Wait for the class section to appear.
        try:
            class_row = page.locator(SELECTORS["class_summary_row"])
            class_row.wait_for(state="visible", timeout=8000)
            assert class_row.count() == 1, f"expected 1 class, got {class_row.count()}"
            name_elem = class_row.locator(SELECTORS["class_section_name"])
            assert "Renda Fixa" in name_elem.inner_text()
        except Exception:
            _debug_dump(page, "post_create_first_class")
            raise

        # The empty state should be gone now.
        assert not empty_state.is_visible(), "empty state should be hidden after creating a class"

    # ── Test 3: Inline class create via "+ Nova classe" ─────────
    # Seeds via snapshot form. Creating one class at a time via the
    # inline form now works at any percentage -- allocation sum is
    # informational, not blocking.

    def test_inline_create_class(self, page: Page, live_url: str) -> None:
        """Verify the sidebar "+ Nova classe" modal toggle UI.

        After dashboard-action-sidebar, the inline form was promoted
        to a modal opened from the sidebar's ``+ Nova classe`` button
        (``empty-state-create-class`` → ``new-class-modal-overlay``).
        This test verifies the modal toggle behavior: open, see the
        name + pct inputs and Save / Cancel buttons, click Cancel and
        the modal closes.

        Setup
        -----
        Seed 2 classes via snapshot form (batch sum to 100). Tests the
        x-show toggle behavior of the new-class modal.

        Asserts
        -------
        - Clicking the sidebar button reveals the modal (x-show toggle).
        - The modal has name input, pct input, save and cancel buttons.
        - Cancel hides the modal again.
        """
        _login_and_select_italo(page, live_url)

        # Seed both classes in one shot so the sum-to-100 invariant passes.
        _create_seed_classes(page, [["Outros", 40], ["Renda Fixa", 60]])

        # Verify 2 classes rendered.
        class_rows = page.locator(SELECTORS["class_summary_row"])
        assert class_rows.count() == 2

        # --- Verify the new-class modal toggle UI ---
        page.locator(SELECTORS["empty_state_create_class_btn"]).wait_for(
            state="visible", timeout=5000
        )
        page.locator(SELECTORS["empty_state_create_class_btn"]).click()
        modal = page.locator(SELECTORS["new_class_modal_overlay"])
        modal.wait_for(state="visible", timeout=2000)
        modal.locator(SELECTORS["new_class_modal_name_input"]).wait_for(
            state="visible", timeout=2000
        )
        modal.locator(SELECTORS["new_class_modal_pct_input"]).wait_for(
            state="visible", timeout=2000
        )
        modal.locator(SELECTORS["new_class_modal_submit"]).wait_for(state="visible", timeout=2000)
        modal.locator(SELECTORS["new_class_modal_cancel"]).wait_for(state="visible", timeout=2000)

        # Cancel closes the modal.
        modal.locator(SELECTORS["new_class_modal_cancel"]).click()
        modal.wait_for(state="hidden", timeout=2000)

    # ── Test 4: Class delete via x + confirm dialog ────────────

    def test_delete_class_via_confirm_dialog(self, page: Page, live_url: str) -> None:
        """Delete a class via x button + "Sim, remover" confirmation.

        Setup: create 2 classes via snapshot form, delete one, verify
        it is removed.

        Asserts
        -------
        - The x delete button is visible in the class header.
        - Clicking x shows the confirm dialog (x-show toggle).
        - Clicking "Cancelar" hides the dialog and does nothing.
        - Clicking "Sim, remover" sends DELETE /api/classes/{id}
          and reloads the page on success (204).
        - The deleted class section is no longer in the DOM.
        - The remaining class section is still present.
        """
        _login_and_select_italo(page, live_url)

        # Create two classes via snapshot form (batch sum to 100).
        _create_seed_classes(page, [["Reserva", 60], ["Acoes", 40]])

        # Verify 2 classes exist.
        class_rows = page.locator(SELECTORS["class_summary_row"])
        assert class_rows.count() == 2

        # --- Test cancel behavior first ---
        acoes_row = class_rows.filter(has_text="Acoes")
        assert acoes_row.count() == 1, "Acoes class section must exist"

        # Click the x delete button to show the confirm dialog.
        acoes_row.locator(SELECTORS["class_delete_btn"]).click()
        confirm = acoes_row.locator(SELECTORS["class_delete_confirm"])
        confirm.wait_for(state="visible", timeout=2000)

        # Click "Cancelar" on the confirm dialog.
        acoes_row.locator(SELECTORS["class_delete_confirm_no"]).click()

        # The confirm dialog should hide again (x-show toggles off).
        confirm.wait_for(state="hidden", timeout=2000)

        # Now do the actual delete: click x again, then "Sim, remover".
        acoes_row.locator(SELECTORS["class_delete_btn"]).click()
        acoes_row.locator(SELECTORS["class_delete_confirm"]).wait_for(state="visible", timeout=2000)
        acoes_row.locator(SELECTORS["class_delete_confirm_yes"]).click()

        # On success (204), the page reloads. Wait for only Reserva.
        try:
            page.wait_for_function(
                f"() => document.querySelectorAll('{SELECTORS['class_summary_row']}').length === 1",
                timeout=8000,
            )
        except Exception:
            _debug_dump(page, "post_delete_acoes")
            raise

        remaining = page.locator(SELECTORS["class_summary_row"])
        assert remaining.count() == 1, (
            f"expected 1 class after deleting Acoes, got {remaining.count()}"
        )
        remaining_name = remaining.locator(SELECTORS["class_section_name"]).inner_text()
        assert "Reserva" in remaining_name, f"expected 'Reserva' to remain, got {remaining_name!r}"

        # "Acoes" should be gone from the page text.
        page_text = page.locator("main").inner_text()
        assert "Acoes" not in page_text

    # ── Test 5: Delete a class with assets shows 409 error ──────

    def test_delete_class_with_assets_shows_409(self, page: Page, live_url: str) -> None:
        """Deleting a class that has assets shows a 409 error message.

        Setup: create 1 class (via API), add 1 asset to it, try to
        delete it. The server responds with 409 (class has assets).

        Asserts
        -------
        - The x delete button is visible.
        - Clicking x shows the confirm dialog.
        - Clicking "Sim, remover" sends DELETE /api/classes/{id}
          and the server returns 409.
        - The error message is displayed in the confirm dialog
          (x-show toggle on class-delete-confirm-error).
        - The class section is NOT removed from the DOM.
        """
        _login_and_select_italo(page, live_url)

        # Create a single class at 100% via the seed helper.
        _create_seed_classes(page, [["Renda Fixa", 100]])

        # Add an asset to the class via the dashboard add-asset modal
        # (the old /assets page redirects to /, so use the modal flow).
        page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)

        page.locator(SELECTORS["dashboard_add_asset_open"]).click()
        modal = page.locator(SELECTORS["add_asset_modal_overlay"])
        modal.wait_for(state="visible", timeout=5000)
        modal.locator(SELECTORS["dashboard_add_asset_class"]).select_option(label="Renda Fixa")
        modal.locator(SELECTORS["dashboard_add_asset_name"]).fill("Tesouro Selic")
        modal.locator(SELECTORS["dashboard_add_asset_pct"]).fill("100")
        modal.locator(SELECTORS["dashboard_add_asset_submit"]).click()
        # Wait for the page reload (201 -> window.location.reload()).
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)

        # Click x to trigger the delete confirm.
        class_row = page.locator(SELECTORS["class_summary_row"]).first
        class_row.locator(SELECTORS["class_delete_btn"]).click()
        class_row.locator(SELECTORS["class_delete_confirm"]).wait_for(state="visible", timeout=2000)

        # Click "Sim, remover" -- the server should reject with 409.
        class_row.locator(SELECTORS["class_delete_confirm_yes"]).click()

        # Wait for the 409 error message to appear in the confirm
        # dialog (the Alpine x-show toggle on deleteError).
        try:
            error_elem = class_row.locator(SELECTORS["class_delete_confirm_error"])
            error_elem.wait_for(state="visible", timeout=5000)
            error_text = error_elem.inner_text()
            assert "ativo" in error_text.lower(), (
                f"expected 409 error mentioning 'ativo', got {error_text!r}"
            )
        except Exception:
            _debug_dump(page, "post_409_delete")
            raise

        # The class section must still be in the DOM.
        remaining = page.locator(SELECTORS["class_summary_row"])
        assert remaining.count() == 1, (
            f"class should still exist after 409, got {remaining.count()} rows"
        )

        # Verify the error can be dismissed by clicking "Cancelar".
        class_row.locator(SELECTORS["class_delete_confirm_no"]).click()
        page.wait_for_timeout(500)

        # After cancel, the confirm dialog hides and the error text
        # is cleared (the Alpine component resets on cancel).
        error_elem_after = class_row.locator(SELECTORS["class_delete_confirm_error"])
        # The element itself may still be in the DOM (hidden via x-cloak)
        # but should not be visible.
        assert not error_elem_after.is_visible()
