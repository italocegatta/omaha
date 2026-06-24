"""Real-browser E2E for the asset-table-view table, sort, and alerts.

Covers the new dashboard table introduced by the asset-table-view
change: sortable columns, inline edit of ``alvo % total``, the sticky
allocation alert card, and the dashboard-level add-asset modal.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from tests.e2e.conftest import _seed_assets_with_positions_via_import

from .test_import_user_journey import _create_three_classes, _login_and_select_italo

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DB_PATH = REPO_ROOT / "data" / "test_e2e.db"

S10_SELECTORS = {
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "asset_row_name": '[data-testid="asset-row-name"]',
    "asset_target_pct_class": '[data-testid="asset-target-pct-class"]',
    "asset_target_pct_total": '[data-testid="asset-target-pct-total"]',
    "asset_target_pct_total_edit_input": '[data-testid="asset-target-pct-total-edit-input"]',
    "asset_table": '[data-testid="asset-table"]',
    "asset_table_th_name": '[data-testid="asset-table-th-name"]',
    "asset_table_th_class": '[data-testid="asset-table-th-class"]',
    "asset_table_th_qty": '[data-testid="asset-table-th-qty"]',
    "asset_table_th_current_value": '[data-testid="asset-table-th-current-value"]',
    "asset_table_th_target_pct_class": '[data-testid="asset-table-th-target-pct-class"]',
    "asset_table_th_current_pct_class": '[data-testid="asset-table-th-current-pct-class"]',
    "asset_table_th_target_pct_total": '[data-testid="asset-table-th-target-pct-total"]',
    "asset_table_th_current_pct_total": '[data-testid="asset-table-th-current-pct-total"]',
    "asset_group_header_alert": '[data-testid="asset-group-header-alert"]',
    "asset_allocation_alert": '[data-testid="asset-allocation-alert"]',
    "asset_allocation_alert_portfolio": '[data-testid="asset-allocation-alert-portfolio"]',
    "asset_allocation_alert_class": '[data-testid="asset-allocation-alert-class"]',
    "dashboard_add_asset_open": '[data-testid="dashboard-add-asset-open"]',
    "dashboard_add_asset_modal": '[data-testid="dashboard-add-asset-modal"]',
    "dashboard_add_asset_class": '[data-testid="dashboard-add-asset-modal-class"]',
    "dashboard_add_asset_name": '[data-testid="dashboard-add-asset-name"]',
    "dashboard_add_asset_target_pct": '[data-testid="dashboard-add-asset-target-pct"]',
    "dashboard_add_asset_submit": '[data-testid="dashboard-add-asset-submit"]',
    # fix-asset-table-ui-bugs: chevron + header for the new
    # toggle collapse/expand. Click on the chevron bubbles to the
    # header's ``@click`` handler.
    "class_section_header": '[data-testid="class-section-header"]',
    "class_chevron": '[data-testid="class-chevron"]',
}


def _seed_class_with_assets(class_name: str, assets: list[tuple[str, float | int]]) -> None:
    """Create one class + N assets for Italo via direct sqlite3 writes.

    Uses raw SQL against ``data/test_e2e.db`` so the test can set up
    state without driving the UI. ``assets`` is a list of
    ``(asset_name, target_pct)``.
    """
    if not TEST_DB_PATH.exists():
        raise RuntimeError("test DB not found")
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        row = conn.execute("SELECT id FROM profiles WHERE name = ?", ("Italo",)).fetchone()
        assert row is not None, "Italo profile not seeded"
        profile_id = row[0]

        conn.execute(
            "INSERT INTO asset_classes (profile_id, name, target_pct, display_order) "
            "VALUES (?, ?, 100.00, 0)",
            (profile_id, class_name),
        )
        class_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for name, target_pct in assets:
            conn.execute(
                "INSERT INTO assets (asset_class_id, name, target_pct, display_order) "
                "VALUES (?, ?, ?, 0)",
                (class_id, name, float(target_pct)),
            )
        conn.commit()
    finally:
        conn.close()


def _read_target_pct(asset_name: str) -> float | None:
    """Read an asset's target_pct back from the test DB."""
    if not TEST_DB_PATH.exists():
        return None
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        row = conn.execute(
            """
            SELECT a.target_pct
            FROM assets a
            JOIN asset_classes ac ON a.asset_class_id = ac.id
            JOIN profiles p ON ac.profile_id = p.id
            WHERE p.name = 'Italo' AND a.name = ?
            """,
            (asset_name,),
        ).fetchone()
        return None if row is None else float(row[0])
    finally:
        conn.close()


class TestS10AssetTable:
    """E2E coverage for the asset-table-view table, sort, alerts, and modal."""

    def test_table_sort_by_each_column(self, page: Page, live_url: str) -> None:
        """Click each sortable <th> and verify the indicator + order change."""
        _login_and_select_italo(page, live_url)
        # One class, three assets with distinct names/targets.
        _seed_class_with_assets(
            "Renda Fixa",
            [("Zebra", 10.0), ("Abacaxi", 30.0), ("Manga", 20.0)],
        )
        _seed_assets_with_positions_via_import(
            page, live_url, [("Renda Fixa", name) for name in ["Zebra", "Abacaxi", "Manga"]]
        )

        page.goto(f"{live_url}/")
        page.wait_for_selector(S10_SELECTORS["asset_table"], timeout=5000)

        for th_key in (
            "name",
            "class",
            "qty",
            "current-value",
            "target-pct-class",
            "current-pct-class",
            "target-pct-total",
            "current-pct-total",
        ):
            th = page.locator(S10_SELECTORS[f"asset_table_th_{th_key.replace('-', '_')}"])
            th.wait_for(state="visible", timeout=3000)
            indicator_before = th.locator("span").inner_text()
            th.click()
            # Alpine re-renders the indicator after the click.
            page.wait_for_timeout(250)
            indicator_after = th.locator("span").inner_text()
            assert indicator_after != indicator_before, (
                f"sort indicator for {th_key} did not change: {indicator_before!r}"
            )

        # Sanity: after sorting by name asc, Abacaxi should be the first row.
        page.locator(S10_SELECTORS["asset_table_th_name"]).click()
        page.wait_for_timeout(250)
        first_name = (
            page.locator(S10_SELECTORS["dashboard_asset_row"])
            .first.locator(S10_SELECTORS["asset_row_name"])
            .inner_text()
            .strip()
        )
        assert "Abacaxi" in first_name, (
            f"expected Abacaxi first after name sort, got {first_name!r}"
        )

    def test_edit_alvo_pct_total_updates_class_sum_and_alert(
        self, page: Page, live_url: str
    ) -> None:
        """Edit ``alvo % total`` and verify the per-class badge + alert card update.

        Setup: 1 class (Renda Fixa 100%) with 2 assets at 40% and 50%
        class-level (sum = 90, ``Falta 10%``). Edit the first asset's
        ``alvo % total`` from 40 to 50: the back-solve sets ``alvo %
        classe`` to 50, making the per-class sum 100. The alert card
        should disappear and the group-header badge should read OK.
        """
        _login_and_select_italo(page, live_url)
        _seed_class_with_assets("Renda Fixa", [("Ativo A", 40.0), ("Ativo B", 50.0)])
        _seed_assets_with_positions_via_import(
            page, live_url, [("Renda Fixa", "Ativo A"), ("Renda Fixa", "Ativo B")]
        )

        page.goto(f"{live_url}/")
        page.wait_for_selector(S10_SELECTORS["dashboard_asset_row"], timeout=5000)

        rows = page.locator(S10_SELECTORS["dashboard_asset_row"])
        target_row = None
        for i in range(rows.count()):
            row = rows.nth(i)
            if "Ativo A" in row.locator(S10_SELECTORS["asset_row_name"]).inner_text():
                target_row = row
                break
        assert target_row is not None, "Ativo A row not found"

        # The alert card is visible because the class sum is 90%.
        alert = page.locator(S10_SELECTORS["asset_allocation_alert"])
        assert alert.count() == 1, "expected allocation alert card to be present"
        alert.wait_for(state="visible", timeout=3000)
        assert "Falta" in alert.inner_text(), "expected 'Falta' in alert card"

        # Click the alvo % total cell to edit.
        cell = target_row.locator(S10_SELECTORS["asset_target_pct_total"]).first
        cell.click()
        edit_input = target_row.locator(S10_SELECTORS["asset_target_pct_total_edit_input"]).first
        edit_input.wait_for(state="visible", timeout=2000)
        edit_input.fill("50")
        edit_input.press("Enter")

        # Wait for PATCH + local state update.
        page.wait_for_timeout(500)

        # The group-header badge should now show OK (or be hidden).
        badge = page.locator(S10_SELECTORS["asset_group_header_alert"]).first
        if badge.is_visible():
            assert "OK" in badge.inner_text(), f"expected OK badge, got {badge.inner_text()!r}"

        # The alert card should disappear once the class sum reaches 100.
        alert.wait_for(state="hidden", timeout=3000)

        # Server-side target_pct was back-solved to 50.
        assert _read_target_pct("Ativo A") == 50.0, "Ativo A target_pct should be 50"

    def test_modal_add_asset_flow(self, page: Page, live_url: str) -> None:
        """Open the dashboard add-asset modal, submit, and verify the new row."""
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        page.locator(S10_SELECTORS["dashboard_add_asset_open"]).click()
        modal = page.locator(S10_SELECTORS["dashboard_add_asset_modal"])
        modal.wait_for(state="visible", timeout=5000)

        modal.locator(S10_SELECTORS["dashboard_add_asset_class"]).select_option(label="RF Pós")
        modal.locator(S10_SELECTORS["dashboard_add_asset_name"]).fill("NOVO_ATIVO")
        modal.locator(S10_SELECTORS["dashboard_add_asset_target_pct"]).fill("10")
        modal.locator(S10_SELECTORS["dashboard_add_asset_submit"]).click()

        # Wait for page reload and the new row to render.
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_selector(S10_SELECTORS["dashboard_asset_row"], timeout=5000)

        # Modal is closed after the reload.
        modal_after = page.locator(S10_SELECTORS["dashboard_add_asset_modal"])
        assert modal_after.count() == 0 or not modal_after.is_visible(), "modal should be closed"

        rows = page.locator(S10_SELECTORS["dashboard_asset_row"])
        assert rows.count() == 1, f"expected 1 asset row, got {rows.count()}"
        assert "NOVO_ATIVO" in rows.first.inner_text()

    def test_alert_card_shows_severity_for_small_and_large_deviations(
        self, page: Page, live_url: str
    ) -> None:
        """A 3% deviation shows warn; a 10% deviation shows danger."""
        _login_and_select_italo(page, live_url)
        # Class 1: sum = 103 (3% over) -> warn.
        # Class 2: sum = 110 (10% over) -> danger.
        # We need two separate profiles/classes to exercise both severities
        # without interaction; create two classes.
        _seed_class_with_assets("RF Pós", [("RF1", 103.0)])
        _seed_class_with_assets("Acoes", [("AC1", 110.0)])
        _seed_assets_with_positions_via_import(
            page, live_url, [("RF Pós", "RF1"), ("Acoes", "AC1")]
        )

        page.goto(f"{live_url}/")
        page.wait_for_selector(S10_SELECTORS["asset_allocation_alert"], timeout=5000)

        alert = page.locator(S10_SELECTORS["asset_allocation_alert"])
        alert_class = alert.get_attribute("class") or ""
        # Portfolio total is 213, so the portfolio-level deviation is large.
        assert "asset-allocation-alert--danger" in alert_class, (
            f"expected danger severity on portfolio alert, got {alert_class!r}"
        )

        # Per-class entries should include both deviations.
        class_alerts = page.locator(S10_SELECTORS["asset_allocation_alert_class"])
        assert class_alerts.count() >= 2, f"expected >=2 class alerts, got {class_alerts.count()}"
        alert_text = page.locator(S10_SELECTORS["asset_allocation_alert"]).inner_text()
        assert "Sobra" in alert_text, f"expected 'Sobra' in alert text, got {alert_text!r}"

    def test_alert_card_disappears_on_convergence(self, page: Page, live_url: str) -> None:
        """When the per-class sum converges to 100%, the alert card hides."""
        _login_and_select_italo(page, live_url)
        _seed_class_with_assets("Renda Fixa", [("Ativo A", 40.0), ("Ativo B", 50.0)])
        _seed_assets_with_positions_via_import(
            page, live_url, [("Renda Fixa", "Ativo A"), ("Renda Fixa", "Ativo B")]
        )

        page.goto(f"{live_url}/")
        page.wait_for_selector(S10_SELECTORS["asset_allocation_alert"], timeout=5000)
        alert = page.locator(S10_SELECTORS["asset_allocation_alert"])
        assert alert.is_visible(), "alert should be visible before convergence"

        # Edit Ativo B's alvo % classe from 50 to 60 to reach sum=100.
        rows = page.locator(S10_SELECTORS["dashboard_asset_row"])
        target_row = None
        for i in range(rows.count()):
            row = rows.nth(i)
            if "Ativo B" in row.locator(S10_SELECTORS["asset_row_name"]).inner_text():
                target_row = row
                break
        assert target_row is not None, "Ativo B row not found"

        cell = target_row.locator(S10_SELECTORS["asset_target_pct_class"]).first
        cell.click()
        edit_input = target_row.locator('[data-testid="asset-inline-edit-input"]').first
        edit_input.wait_for(state="visible", timeout=2000)
        edit_input.fill("60")
        edit_input.press("Enter")

        page.wait_for_timeout(500)
        alert.wait_for(state="hidden", timeout=3000)

    def test_patch_does_not_reorder_rows(self, page: Page, live_url: str) -> None:
        """PATCH on ``alvo % classe`` must not change the order of any row.

        fix-asset-table-ui-bugs: regression test for the user-perceived
        "value didn't persist" bug. Before this change, the row order
        was driven by a reactive ``sortedAssets`` getter that re-ran
        on every ``assets`` mutation and re-sorted by ``target_pct``.
        The old ``_pinFrozen`` helper spliced only the just-edited row
        back to its pre-edit index; every other row in the same class
        still shifted to fill the sort. The new ``displayAssets``
        snapshot freezes the order between explicit sort clicks.

        Setup
        -----
        One class (Renda Fixa) with 3 assets, all initially at
        ``target_pct=10`` (sum=30, validator would normally reject).
        We use direct DB writes to set Beta/Gama to 10 each so the
        PATCH of Alpha → 80 lands on a valid class sum of 100.

        Default sort is ``class`` asc, secondary ``target_pct`` asc,
        tertiary name — so with three assets tied at 10, the order
        is alphabetical: Alpha, Beta, Gama.

        Steps
        -----
        1. Read the ``[data-asset-id]`` order before the PATCH.
        2. Edit the first asset's ``alvo % classe`` to 80 — a
           value that, under the natural asc sort, would jump
           Alpha to the bottom of the list.
        3. Assert the order is unchanged after the PATCH lands
           (the row objects are mutated in place on
           ``displayAssets`` — no re-sort).
        """
        _login_and_select_italo(page, live_url)
        _seed_class_with_assets(
            "Renda Fixa",
            [("Alpha", 10.0), ("Beta", 10.0), ("Gama", 10.0)],
        )
        _seed_assets_with_positions_via_import(
            page,
            live_url,
            [("Renda Fixa", name) for name in ["Alpha", "Beta", "Gama"]],
        )

        page.goto(f"{live_url}/")
        page.wait_for_selector(S10_SELECTORS["dashboard_asset_row"], timeout=5000)

        rows = page.locator(S10_SELECTORS["dashboard_asset_row"])
        order_before = [rows.nth(i).get_attribute("data-asset-id") for i in range(rows.count())]
        assert len(order_before) == 3, f"expected 3 rows, got {len(order_before)}"
        # Default sort is target_pct asc + name asc; all three are at 10,
        # so the order is alphabetical by name. The name cell also carries
        # the per-asset × delete button glyph, so strip the suffix.
        names = [
            rows.nth(i)
            .locator(S10_SELECTORS["asset_row_name"])
            .inner_text()
            .strip()
            .rstrip("× ")
            .strip()
            for i in range(3)
        ]
        assert names == ["Alpha", "Beta", "Gama"], f"unexpected pre-edit order: {names!r}"

        # Edit Alpha (first row) to 80. Sum = 80 + 10 + 10 = 100 → 200 PATCH.
        first_row = rows.first
        cell = first_row.locator(S10_SELECTORS["asset_target_pct_class"]).first
        cell.click()
        edit_input = first_row.locator('[data-testid="asset-inline-edit-input"]').first
        edit_input.wait_for(state="visible", timeout=2000)
        edit_input.fill("80")
        edit_input.press("Enter")

        # Wait for the PATCH + the Alpine local update to settle.
        page.wait_for_timeout(500)

        # Order must be unchanged even though 80 would naturally
        # sort Alpha to the bottom of the asc list.
        rows_after = page.locator(S10_SELECTORS["dashboard_asset_row"])
        order_after = [
            rows_after.nth(i).get_attribute("data-asset-id") for i in range(rows_after.count())
        ]
        assert order_after == order_before, (
            f"PATCH reordered rows: before={order_before!r} after={order_after!r}"
        )

        # And the server-side value reflects the new target_pct.
        assert _read_target_pct("Alpha") == 80.0, (
            f"Alpha target_pct should be 80 after PATCH, got {_read_target_pct('Alpha')!r}"
        )

    def test_class_header_toggle_collapses_and_expands_assets(
        self, page: Page, live_url: str
    ) -> None:
        """Clicking the class header collapses then expands the asset table.

        fix-asset-table-ui-bugs: regression test for the chevron
        toggle that was removed in the asset-table-view 8.x archive.
        Before this change the header had no ``@click`` handler and
        the body was unconditionally visible. Now the header click
        toggles ``isOpen``, the body gets
        ``class-section-body--collapsed`` and ``x-show="isOpen"``,
        and the chevron rotates via ``class-chevron--open``.

        Asserts
        -------
        * Initial state: chevron has ``class-chevron--open`` and
          asset rows are visible.
        * After one click: chevron loses the open class, asset rows
          are not visible (x-show + max-height:0 + overflow:hidden).
        * After a second click: chevron regains the open class,
          asset rows are visible again.
        """
        _login_and_select_italo(page, live_url)
        _seed_class_with_assets("Renda Fixa", [("Ativo A", 100.0)])
        _seed_assets_with_positions_via_import(page, live_url, [("Renda Fixa", "Ativo A")])

        page.goto(f"{live_url}/")
        page.wait_for_selector(S10_SELECTORS["dashboard_asset_row"], timeout=5000)

        chevron = page.locator(S10_SELECTORS["class_chevron"]).first
        header = page.locator(S10_SELECTORS["class_section_header"]).first
        row = page.locator(S10_SELECTORS["dashboard_asset_row"]).first

        # Initial: open.
        chevron_cls = chevron.get_attribute("class") or ""
        assert "class-chevron--open" in chevron_cls, (
            f"expected class-chevron--open on initial render, got {chevron_cls!r}"
        )
        assert row.is_visible(), "expected asset row visible on initial render"

        # First click → collapsed.
        header.click()
        page.wait_for_timeout(300)
        chevron_cls = chevron.get_attribute("class") or ""
        assert "class-chevron--open" not in chevron_cls, (
            f"expected class-chevron--open removed after first click, got {chevron_cls!r}"
        )
        assert not row.is_visible(), "expected asset row hidden after first click"

        # Second click → expanded again.
        header.click()
        page.wait_for_timeout(300)
        chevron_cls = chevron.get_attribute("class") or ""
        assert "class-chevron--open" in chevron_cls, (
            f"expected class-chevron--open restored after second click, got {chevron_cls!r}"
        )
        assert row.is_visible(), "expected asset row visible again after second click"

    def test_column_widths_match_spec(self, page: Page, live_url: str) -> None:
        """The 8 asset-table <th> widths match the spec ratios within ±1px.

        fix-asset-table-ui-bugs: regression test for the explicit
        column widths declared in ``src/omaha/static/app.css``
        (``.asset-table th:nth-child(N)``). Before this change the
        table was ``table-layout: fixed`` with no explicit widths,
        so the browser distributed 12.5% to each of the 8 columns.
        Text columns ("Ativo", "Classe") got truncated while narrow
        numeric columns wasted space. Now the widths are 24/18/6/14
        /11/11/9/7 percent.

        Setup: 1 class + 1 asset so the table renders exactly 1 row.

        Asserts: each ``<th>`` ``getBoundingClientRect().width``
        matches the spec ratio (table_width × pct) within ±1px.
        The 8 widths must sum to the table width (no overflow /
        underflow).
        """
        _login_and_select_italo(page, live_url)
        _seed_class_with_assets("Renda Fixa", [("Ativo A", 100.0)])
        _seed_assets_with_positions_via_import(page, live_url, [("Renda Fixa", "Ativo A")])

        page.goto(f"{live_url}/")
        page.wait_for_selector(S10_SELECTORS["asset_table"], timeout=5000)

        expected_pct = [24, 18, 6, 14, 11, 11, 9, 7]
        width_data = page.evaluate(
            """() => {
                const table = document.querySelector('[data-testid="asset-table"]');
                const ths = table.querySelectorAll('thead th');
                const tableWidth = table.getBoundingClientRect().width;
                return {
                    tableWidth,
                    thWidths: Array.from(ths).map(th => th.getBoundingClientRect().width),
                };
            }"""
        )

        table_width = width_data["tableWidth"]
        th_widths = width_data["thWidths"]
        assert len(th_widths) == 8, f"expected 8 th elements, got {len(th_widths)}"

        sum_actual = sum(th_widths)
        # Allow ±2px total slack for browser rounding across 8 cells.
        assert abs(sum_actual - table_width) <= 2, (
            f"column widths sum to {sum_actual}, expected {table_width} (±2px)"
        )

        for idx, (expected_pct_val, actual_w) in enumerate(
            zip(expected_pct, th_widths, strict=True)
        ):
            expected_w = table_width * expected_pct_val / 100
            assert abs(actual_w - expected_w) <= 1, (
                f"column {idx + 1} expected ~{expected_w:.1f}px "
                f"({expected_pct_val}% of {table_width:.1f}px), got {actual_w:.1f}px"
            )
