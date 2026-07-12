"""Real-browser E2E smoke for the ``rebalance-page`` change.

Drives a headless chromium against a live uvicorn instance to
verify the user-facing surface of the new page:

  login → select profile → dashboard sidebar exposes the
        rebalance form → Enter with aporte 5000 →
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
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from tests.e2e.conftest import (
    _seed_assets_with_positions_via_import,
    _set_asset_target_pcts_via_db,
)

from .selectors import SELECTORS
from .test_import_user_journey import _create_three_classes, _login_and_select_italo


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


def _disable_quotes_for_rebalance_fixture() -> None:
    """Keep synthetic E2E tickers off external quote lookup."""
    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "test_e2e.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("UPDATE asset_classes SET quote_kind = 'none'")
        connection.commit()


class TestRebalancePage:
    """User-visible smoke for the /rebalanceamento surface (F02)."""

    def test_patrimonio_shows_in_body_action_buttons(self, page: Page, live_url: str) -> None:
        """The action buttons live at the top of /patrimonio (F02 D5)."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # The patrimonio action row is rendered server-side.
        assert page.locator('[data-testid="patrimonio-actions"]').count() == 1
        assert page.locator('[data-testid="dashboard-import-btn"]').count() == 1
        assert page.locator('[data-testid="dashboard-add-asset-open"]').count() == 1
        assert page.locator('[data-testid="empty-state-create-class"]').count() == 1

    def test_patrimonio_actions_has_alpine_scope(self, page: Page, live_url: str) -> None:
        """Regression: ``patrimonio-actions`` carries ``x-data`` and
        each button toggles its modal store.

        The F02 commit ``1755dd0`` restored the missing ``x-data``
        on this section; this test guards against silent
        re-regression by locking in (a) the attribute presence and
        (b) the click-to-store wiring for each of the three action
        buttons.
        """
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)
        page.goto(f"{live_url}/patrimonio")
        page.wait_for_selector(SELECTORS["patrimonio_actions"], timeout=5000)

        actions = page.locator(SELECTORS["patrimonio_actions"])
        x_data = actions.first.get_attribute("x-data")
        # Alpine allows `x-data` with an empty value (it just
        # initialises an empty component scope). The contract is
        # attribute presence, not expression body.
        assert x_data is not None, (
            "patrimonio-actions is missing its x-data attribute; "
            "Alpine click handlers will be inert (F02 regression)."
        )

        # Drive each of the three buttons via direct DOM dispatch on
        # the matching testid. This bypasses any modal overlay that
        # is currently open from a previous iteration (the F02
        # regression was specifically about handler binding, not
        # about the open-overlay gesture).
        for selector, store_name in (
            (SELECTORS["dashboard_import_btn"], "importModal"),
            (SELECTORS["dashboard_add_asset_open"], "addAssetModal"),
            (SELECTORS["empty_state_create_class"], "newClassModal"),
        ):
            # Reset every store to closed before each click.
            for store in ("importModal", "addAssetModal", "newClassModal"):
                page.evaluate(
                    """(name) => {
                        const s = Alpine.store(name);
                        if (s && typeof s.closeModal === 'function') s.closeModal();
                        else if (s) s.open = false;
                    }""",
                    store,
                )
            # Direct dispatch — equivalent to a real user click but
            # bypasses overlay intercepts from other open modals.
            page.evaluate(
                """(selector) => {
                    const el = document.querySelector(selector);
                    if (!el) throw new Error('selector not found: ' + selector);
                    el.click();
                }""",
                selector,
            )
            opened = page.evaluate("(name) => Alpine.store(name).open === true", store_name)
            assert opened, (
                f"{selector} click did not flip {store_name}.open to True; "
                "Alpine scope likely broken on patrimonio-actions."
            )

    def test_top_nav_highlights_patrimonio(self, page: Page, live_url: str) -> None:
        """``/patrimonio`` highlights the Patrimônio tab."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # Tab nav is visible on /patrimonio
        assert page.locator('[data-testid="app-tab-nav"]').count() == 1
        # The patrimonio tab is active (aria-current="true")
        active = page.locator('[data-testid="app-tab-btn-patrimonio"][aria-current="true"]')
        assert active.count() == 1

    def test_editing_contribution_refreshes_plan_automatically(
        self, page: Page, live_url: str
    ) -> None:
        """Typing stays local; Enter refreshes server-rendered plan."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)
        # Rebalance needs positions (not just assets). Seed via the
        # import-modal helper so each asset has at least one position
        # and the plan can compute buy/sell rows.
        _seed_assets_with_positions_via_import(
            page,
            live_url,
            [
                ("RF Pós", "REBAL_A"),
                ("Acoes", "REBAL_B"),
                ("Reserva", "REBAL_C"),
            ],
            positions={
                "REBAL_A": (100.0, 100.0),
                "REBAL_B": (100.0, 100.0),
                "REBAL_C": (100.0, 100.0),
            },
        )
        # CSV import leaves target_pct=0 on every asset. The CVXPY
        # engine rejects that state ("Os pesos-alvo dos ativos devem
        # somar 100%"); patch each asset's target_pct directly so the
        # per-class sum equals 100 and the plan renders.
        _set_asset_target_pcts_via_db(
            {"REBAL_A": 100.0, "REBAL_B": 100.0, "REBAL_C": 100.0},
        )

        # The user navigates to /rebalanceamento via the top nav.
        page.click(SELECTORS["app_tab_btn_rebalanceamento"])
        page.wait_for_url(re.compile(r"/rebalanceamento$"))
        page.wait_for_selector(SELECTORS["rebalance_form"], timeout=5000)

        # Typing does not run solver. Enter preserves normal form-submit semantics.
        post_requests: list[str] = []
        page.on(
            "request",
            lambda request: (
                post_requests.append(request.url)
                if request.method == "POST" and request.url.endswith("/rebalanceamento")
                else None
            ),
        )
        contribution = page.locator(SELECTORS["rebalance_contribution_input"])
        contribution.fill("5000")
        page.wait_for_timeout(500)
        assert post_requests == []
        contribution.press("Enter")
        page.wait_for_function(
            """() => {
                const el = document.querySelector('[data-testid="rebalance-plan-data"]');
                return el && JSON.parse(el.textContent).metrics.contribution === 5000;
            }""",
            timeout=10000,
        )

        # Plan layout controls remain visible after submission.
        for key in (
            "rebalance_stat_contribution",
            "rebalance_stat_total_buy",
            "rebalance_stat_total_sell",
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

        assert page.locator(SELECTORS["rebalance_class_summary"]).count() == 1

    def test_asset_table_poc_parity_interactions(self, page: Page, live_url: str) -> None:
        """POC-format table sorts and filters hydrated Alpine rows."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)
        _disable_quotes_for_rebalance_fixture()
        _seed_assets_with_positions_via_import(
            page,
            live_url,
            [
                ("RF Pós", "SORT_A"),
                ("Acoes", "SORT_B"),
                ("Reserva", "SORT_C"),
            ],
            positions={
                "SORT_A": (1.0, 100.0),
                "SORT_B": (1.0, 200.0),
                "SORT_C": (1.0, 300.0),
            },
        )
        # CSV import leaves target_pct=0; CVXPY rejects that. Patch
        # each asset's target_pct so the per-class sum equals 100.
        _set_asset_target_pcts_via_db(
            {"SORT_A": 100.0, "SORT_B": 100.0, "SORT_C": 100.0},
        )

        # Navigate via the top nav, then submit input with Enter.
        page.click(SELECTORS["app_tab_btn_rebalanceamento"])
        page.wait_for_url(re.compile(r"/rebalanceamento$"))
        try:
            page.wait_for_selector(SELECTORS["rebalance_form"], timeout=5000)
        except Exception:
            _debug_dump(page, "rebalance-form-missing")
            raise

        contribution = page.locator(SELECTORS["rebalance_contribution_input"])
        contribution.fill("5000")
        contribution.press("Enter")
        page.wait_for_function(
            """() => {
                const el = document.querySelector('[data-testid="rebalance-plan-data"]');
                return el && JSON.parse(el.textContent).metrics.contribution === 5000;
            }""",
            timeout=10000,
        )
        # Wait for Alpine hydration so the click handler is bound
        # and the rows are rendered.
        rows_ready_js = (
            "() => document.querySelectorAll('[data-testid^=\"rebalance-asset-row-\"]').length >= 1"
        )
        page.wait_for_function(rows_ready_js, timeout=5000)

        # Give Alpine an extra tick to bind the @click handlers on
        # the <th> elements before we issue a real click.
        page.wait_for_timeout(200)

        click_js = (
            "() => document.querySelector("
            "'[data-testid=\"rebalance-asset-th-current-value\"]'"
            ").click()"
        )

        # First click: ascending → ▲ indicator and numeric order.
        page.evaluate(click_js)
        page.wait_for_function(
            "() => document.querySelector("
            "'[data-testid=\"rebalance-asset-th-current-value\"]'"
            ").textContent.includes('▲')",
            timeout=5000,
        )
        ascending_values = page.evaluate(
            """() => Alpine.$data(document.querySelector('[data-testid="rebalance-plan"]'))
              .filteredRows.map((row) => Number(row.current_value))"""
        )
        assert ascending_values == sorted(ascending_values)

        # Second click: descending → ▼ indicator and reversed numeric order.
        page.evaluate(click_js)
        page.wait_for_function(
            "() => document.querySelector("
            "'[data-testid=\"rebalance-asset-th-current-value\"]'"
            ").textContent.includes('▼')",
            timeout=5000,
        )
        descending_values = page.evaluate(
            """() => Alpine.$data(document.querySelector('[data-testid="rebalance-plan"]'))
              .filteredRows.map((row) => Number(row.current_value))"""
        )
        assert descending_values == sorted(descending_values, reverse=True)

        # Header enum filter updates declarative table rows.
        row_count = page.locator('[data-testid^="rebalance-asset-row-"]').count()
        category_filter = page.locator(
            '[data-testid="rebalance-header-filter-category_name-trigger"]'
        )
        category_filter.click()
        category_panel = page.locator(
            '[data-testid="rebalance-asset-th-category"] .rebalance-filter-panel'
        )
        page.wait_for_selector(
            '[data-testid="rebalance-asset-th-category"] .rebalance-filter-panel', timeout=5000
        )
        category_panel.locator('input[type="checkbox"]').nth(1).check()
        row_sel = '[data-testid^="rebalance-asset-row-"]'
        page.wait_for_function(
            f"() => document.querySelectorAll('{row_sel}').length > 0"
            f" && document.querySelectorAll('{row_sel}').length < {row_count}",
            timeout=5000,
        )

        page.locator('[data-testid="rebalance-header-clear-category_name-trigger"]').click()
        page.wait_for_function(
            f"() => document.querySelectorAll('{row_sel}').length === {row_count}",
            timeout=5000,
        )

    def test_top_nav_patrimonio_link_returns_to_dashboard(self, page: Page, live_url: str) -> None:
        """Clicking the Patrimonio top-nav tab returns to /."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        page.goto(f"{live_url}/rebalanceamento")
        page.wait_for_selector(SELECTORS["rebalance_form"], timeout=5000)

        # Click the Patrimonio tab via JS to bypass any layout overlap.
        page.evaluate(
            "() => document.querySelector('[data-testid=\"app-tab-btn-patrimonio\"]').click()"
        )
        page.wait_for_url(re.compile(r"/patrimonio$"))
        page.wait_for_selector('[data-testid="class-summary"]', timeout=5000)

    def test_empty_profile_renders_empty_state(self, page: Page, live_url: str) -> None:
        """A profile with zero classes renders the empty-state card.

        F02: the in-body form (no longer in a sidebar slot) carries
        the ``disabled`` attribute when the profile has zero
        classes. The delete classes via API to land in the empty
        state and verify the form is inert + the empty-state card
        is visible.
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

        # Navigate to /rebalanceamento — empty state should render and the
        # in-body form fields should be disabled.
        page.goto(f"{live_url}/rebalanceamento")
        page.wait_for_selector(SELECTORS["rebalance_empty_state"], timeout=5000)

        empty = page.locator(SELECTORS["rebalance_empty_state"])
        assert empty.is_visible()
        assert "Nenhuma classe cadastrada" in empty.inner_text()

        # In-body form input remains inert and has no manual submit button.
        input_disabled = page.locator(SELECTORS["rebalance_contribution_input"]).get_attribute(
            "disabled"
        )
        assert input_disabled is not None, "expected aporte input to be disabled"
        assert page.locator('[data-testid="rebalance-submit-btn"]').count() == 0

    def test_negative_aporte_shows_client_side_error(self, page: Page, live_url: str) -> None:
        """Typing negative aporte shows inline error without a recalculation."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # Navigate to /rebalanceamento via the top nav.
        page.click(SELECTORS["app_tab_btn_rebalanceamento"])
        page.wait_for_url(re.compile(r"/rebalanceamento$"))

        # Wait for Alpine hydration so the validate() handler is bound.
        page.wait_for_function(
            "() => window.Alpine && document.querySelector('[data-testid=\"rebalance-form\"]')"
        )

        contribution = page.locator(SELECTORS["rebalance_contribution_input"])
        post_requests: list[str] = []
        page.on(
            "request",
            lambda request: (
                post_requests.append(request.url)
                if request.method == "POST" and request.url.endswith("/rebalanceamento")
                else None
            ),
        )
        contribution.fill("-500")

        # Feedback appears during input. Negative edits do not run the solver.
        page.wait_for_selector(
            '[data-testid="rebalance-form-error"]', state="visible", timeout=3000
        )
        error_text = page.locator('[data-testid="rebalance-form-error"]').inner_text()
        assert "Saques serão suportados" in error_text
        page.wait_for_timeout(500)
        assert post_requests == []
        # URL did not change.
        assert page.url.rstrip("/").endswith((live_url + "/rebalanceamento").rstrip("/"))

    def test_legacy_rebalance_url_returns_404(self, page: Page, live_url: str) -> None:
        """``GET /rebalance`` returns HTTP 404 after F02 (D1)."""
        response = page.goto(f"{live_url}/rebalance")
        assert response is not None
        assert response.status == 404

    def test_stub_pages_render_placeholder(self, page: Page, live_url: str) -> None:
        """``/rentabilidade`` and ``/proventos`` render the F02 stub."""
        _login_and_select_italo(page, live_url)

        page.goto(f"{live_url}/rentabilidade")
        page.wait_for_selector('[data-testid="rentabilidade-stub"]', timeout=5000)
        assert "Em construção" in page.locator("main").inner_text()

        page.goto(f"{live_url}/proventos")
        page.wait_for_selector('[data-testid="proventos-stub"]', timeout=5000)
        assert "Em construção" in page.locator("main").inner_text()
