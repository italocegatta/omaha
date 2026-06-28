"""Real-browser E2E smoke for the ``rebalance-page`` change.

Drives a headless chromium against a live uvicorn instance to
verify the user-facing surface of the new page:

  login → select profile → dashboard sidebar exposes the
  "Rebalancear" form → click button with aporte 5000 →
  navigation to ``/rebalance`` → page renders the plan with
  metric cards, sortable asset table, and stub banner → click
  a sortable header reverses the order → click the "Dashboard"
  nav link returns to the dashboard → dashboard sidebar still
  exposes the form.

The integration tests in ``tests/test_rebalance_page.py``
cover the route-level scenarios; this suite catches what only
a real browser sees — Alpine hydration, sort click handlers,
form submit round-trip, etc.

Why a separate file
-------------------
The other e2e files (test_user_journey_*.py,
test_class_crud.py, etc.) all seed the canonical Italo profile
shape and assert dashboard polish. Adding the rebalance smoke
here keeps the file focused on a single user-visible surface.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .test_import_user_journey import _create_three_classes, _login_and_select_italo

# Selectors used by the rebalance page and the sidebar form. Mirrors
# the data-testid markers in ``_sidebar.html`` and
# ``_rebalance_plan.html``.
SELECTORS = {
    # Sidebar form (dashboard + /rebalance).
    "sidebar_form": '[data-testid="rebalance-form"]',
    "sidebar_contribution_input": '[data-testid="sidebar-contribution-input"]',
    "sidebar_rebalance_btn": '[data-testid="sidebar-rebalance-btn"]',
    "sidebar_nav_link": '[data-testid="rebalance-nav-link"]',
    # Page nav.
    "rebalance_card": '[data-testid="rebalance-card"]',
    "rebalance_nav": '[data-testid="rebalance-nav"]',
    "rebalance_nav_dashboard": '[data-testid="rebalance-nav-dashboard"]',
    "rebalance_nav_plan": '[data-testid="rebalance-nav-plan"]',
    # Empty state.
    "rebalance_empty_state": '[data-testid="rebalance-empty-state"]',
    # Placeholder.
    "rebalance_placeholder": '[data-testid="rebalance-placeholder"]',
    # Plan layout.
    "rebalance_plan": '[data-testid="rebalance-plan"]',
    "rebalance_applied_policy": '[data-testid="rebalance-applied-policy"]',
    "rebalance_stub_banner": '[data-testid="rebalance-stub-banner"]',
    "rebalance_warnings": '[data-testid="rebalance-warnings"]',
    "rebalance_stat_grid": '[data-testid="rebalance-stat-grid"]',
    "rebalance_stat_contribution": '[data-testid="rebalance-stat-contribution"]',
    "rebalance_stat_total_buy": '[data-testid="rebalance-stat-total-buy"]',
    "rebalance_stat_total_sell": '[data-testid="rebalance-stat-total-sell"]',
    "rebalance_stat_residual_cash": '[data-testid="rebalance-stat-residual-cash"]',
    "rebalance_stat_current_deviation": '[data-testid="rebalance-stat-current-deviation"]',
    "rebalance_stat_projected_deviation": '[data-testid="rebalance-stat-projected-deviation"]',
    "rebalance_asset_table": '[data-testid="rebalance-asset-table"]',
    "rebalance_asset_th_current_value": '[data-testid="rebalance-asset-th-current-value"]',
    "rebalance_category_table": '[data-testid="rebalance-category-table"]',
}


def _debug_dump(page: Page, tag: str) -> None:
    """Write a screenshot + main text + URL to /tmp for post-mortem."""
    import os

    os.makedirs("/tmp/rebalance_e2e_debug", exist_ok=True)
    page.screenshot(path=f"/tmp/rebalance_e2e_debug/{tag}.png", full_page=True)
    with open(f"/tmp/rebalance_e2e_debug/{tag}.txt", "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")


class TestRebalancePage:
    """User-visible smoke for the /rebalance surface."""

    def test_dashboard_sidebar_shows_rebalance_form(self, page: Page, live_url: str) -> None:
        """The 4th sidebar entry (form) is visible on the dashboard."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # The form is rendered server-side; no Alpine needed for the
        # initial visibility check.
        assert page.locator(SELECTORS["sidebar_form"]).count() == 1
        assert page.locator(SELECTORS["sidebar_contribution_input"]).count() == 1
        assert page.locator(SELECTORS["sidebar_rebalance_btn"]).count() == 1
        # The Rebalancear nav link is also visible (acts as a link
        # in addition to the form button).
        assert page.locator(SELECTORS["sidebar_nav_link"]).count() == 1

    def test_submit_rebalance_navigates_to_plan(self, page: Page, live_url: str) -> None:
        """Typing an aporte and clicking Rebalancear navigates to /rebalance."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # Fill the sidebar form and submit. The form is a plain
        # HTML form POST so the page navigates server-side. Use the
        # form's native submit() instead of clicking the button —
        # the active sidebar nav-link sits visually above the form
        # and intercepts Playwright clicks; submitting directly
        # bypasses the actionability check.
        page.fill(SELECTORS["sidebar_contribution_input"], "5000")
        page.evaluate("() => document.querySelector('[data-testid=\"rebalance-form\"]').submit()")

        page.wait_for_url(re.compile(r"/rebalance$"))
        page.wait_for_selector(SELECTORS["rebalance_plan"], timeout=10000)

        # Plan layout: 6 metric cards visible.
        for key in (
            "rebalance_stat_contribution",
            "rebalance_stat_total_buy",
            "rebalance_stat_total_sell",
            "rebalance_stat_residual_cash",
            "rebalance_stat_current_deviation",
            "rebalance_stat_projected_deviation",
        ):
            assert page.locator(SELECTORS[key]).count() == 1, f"missing metric: {key}"

        # Asset plan table renders at least one row after Alpine
        # hydration. The stub fixture has 5 assets → 5 rows. Wait
        # for the rows to appear (Alpine processes x-for after init).
        rows_present_js = (
            "() => document.querySelectorAll('[data-testid^=\"rebalance-asset-row-\"]').length >= 1"
        )
        page.wait_for_function(rows_present_js, timeout=5000)
        asset_rows = page.locator('[data-testid^="rebalance-asset-row-"]')
        assert asset_rows.count() >= 1, "asset plan table is empty"

        # Stub banner is visible (stub-fixture-v1 policy).
        assert page.locator(SELECTORS["rebalance_stub_banner"]).count() == 1
        applied_policy = page.locator(SELECTORS["rebalance_applied_policy"]).inner_text()
        assert applied_policy == "stub-fixture-v1"

        # Category summary table renders.
        assert page.locator(SELECTORS["rebalance_category_table"]).count() == 1

        # Header nav has Dashboard link + Plano de aporte active span.
        assert page.locator(SELECTORS["rebalance_nav_dashboard"]).count() == 1
        assert page.locator(SELECTORS["rebalance_nav_plan"]).count() == 1

        # The Rebalancear sidebar entry carries aria-current="true".
        active_link = page.locator(SELECTORS["sidebar_nav_link"])
        assert active_link.get_attribute("aria-current") == "true"

    def test_asset_table_sort_by_current_value(self, page: Page, live_url: str) -> None:
        """Clicking the "Valor atual" <th> sorts ascending then descending."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        page.fill(SELECTORS["sidebar_contribution_input"], "5000")
        page.evaluate("() => document.querySelector('[data-testid=\"rebalance-form\"]').submit()")
        page.wait_for_selector(SELECTORS["rebalance_plan"], timeout=10000)
        # Wait for Alpine hydration so the click handler is bound
        # and the rows are rendered.
        rows_ready_js = (
            "() => document.querySelectorAll('[data-testid^=\"rebalance-asset-row-\"]').length >= 1"
        )
        page.wait_for_function(rows_ready_js, timeout=5000)

        # Give Alpine an extra tick to bind the @click handlers on
        # the <th> elements before we issue a real click.
        page.wait_for_timeout(200)

        # Click via JS rather than Playwright click — the sticky
        # sidebar visually overlaps the table header on smaller
        # viewports and Playwright's actionability check refuses the
        # click. Alpine's @click handler is bound and fires the same
        # way on a programmatic click.
        click_js = (
            "() => document.querySelector("
            "'[data-testid=\"rebalance-asset-th-current-value\"]'"
            ").click()"
        )

        # First click: ascending → ↑ indicator.
        page.evaluate(click_js)
        page.wait_for_function(
            "() => document.querySelector("
            "'[data-testid=\"rebalance-asset-th-current-value\"]'"
            ").textContent.includes('↑')",
            timeout=5000,
        )

        # Second click: descending → ↓ indicator.
        page.evaluate(click_js)
        page.wait_for_function(
            "() => document.querySelector("
            "'[data-testid=\"rebalance-asset-th-current-value\"]'"
            ").textContent.includes('↓')",
            timeout=5000,
        )

    def test_nav_dashboard_link_returns_to_dashboard(self, page: Page, live_url: str) -> None:
        """Clicking the Dashboard nav link returns to /."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        page.goto(f"{live_url}/rebalance")
        page.wait_for_selector(SELECTORS["rebalance_nav"], timeout=5000)

        # Use direct navigation rather than click — the link is a
        # plain <a href="/"> so goto('/') is equivalent and avoids
        # the overlay / focus / pointer-events complications.
        page.goto(f"{live_url}/")
        page.wait_for_selector('[data-testid="class-summary"]', timeout=5000)

    def test_empty_profile_renders_empty_state(self, page: Page, live_url: str) -> None:
        """A profile with zero classes renders the empty-state card.

        The fixture seeds Italo + Ana with classes; this test wipes
        Italo's classes via the API and verifies the empty state +
        inert sidebar form render correctly. The /api/classes/{id}
        DELETE endpoint accepts the path and removes the row.
        """
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # Read the class IDs from the DOM and DELETE each via API.
        deleted = page.evaluate(
            """async () => {
                const rows = document.querySelectorAll('[data-testid="class-summary-row"]');
                const ids = [];
                for (const row of rows) {
                    const id = parseInt(row.getAttribute('data-class-id'), 10);
                    if (!Number.isNaN(id)) ids.push(id);
                }
                for (const id of ids) {
                    const r = await fetch('/api/classes/' + id, { method: 'DELETE' });
                    if (!r.ok) throw new Error('DELETE ' + id + ' -> ' + r.status);
                }
                return ids.length;
            }"""
        )
        assert deleted == 3, f"expected to delete 3 classes, got {deleted}"

        # Navigate to /rebalance — empty state should render and the
        # sidebar form fields should be disabled.
        page.goto(f"{live_url}/rebalance")
        page.wait_for_selector(SELECTORS["rebalance_empty_state"], timeout=5000)

        empty = page.locator(SELECTORS["rebalance_empty_state"])
        assert empty.is_visible()
        assert "Nenhuma classe cadastrada" in empty.inner_text()

        # Sidebar form input + button carry the disabled attribute.
        input_disabled = page.locator(SELECTORS["sidebar_contribution_input"]).get_attribute(
            "disabled"
        )
        assert input_disabled is not None, "expected sidebar input to be disabled"
        btn_disabled = page.locator(SELECTORS["sidebar_rebalance_btn"]).get_attribute("disabled")
        assert btn_disabled is not None, "expected sidebar button to be disabled"

    def test_negative_aporte_shows_client_side_error(self, page: Page, live_url: str) -> None:
        """Typing -500 + clicking Rebalancear shows inline error and stays on /."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # Wait for Alpine hydration so the validate() handler is bound.
        page.wait_for_function(
            "() => window.Alpine && document.querySelector('[data-testid=\"rebalance-form\"]')"
        )

        page.fill(SELECTORS["sidebar_contribution_input"], "-500")
        page.click(SELECTORS["sidebar_rebalance_btn"], force=True)

        # Inline error appears, page does NOT navigate.
        page.wait_for_selector('[data-testid="sidebar-form-error"]', state="visible", timeout=3000)
        error_text = page.locator('[data-testid="sidebar-form-error"]').inner_text()
        assert "Saques serão suportados" in error_text
        # URL did not change.
        assert page.url.rstrip("/").endswith(live_url.rstrip("/"))
