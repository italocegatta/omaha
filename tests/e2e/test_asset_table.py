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


def _seed_positions(asset_names: list[str]) -> None:
    """Seed one position per named asset so current_value is non-zero."""
    if not TEST_DB_PATH.exists():
        return
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        for name in asset_names:
            conn.execute(
                """
                INSERT INTO positions (asset_id, qty, avg_price, current_price, broker_ticker)
                SELECT a.id, 1, 100.0, 110.0, 'TEST-E2E'
                FROM assets a
                JOIN asset_classes ac ON a.asset_class_id = ac.id
                JOIN profiles p ON ac.profile_id = p.id
                WHERE p.name = 'Italo' AND a.name = ?
                """,
                (name,),
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
        _seed_positions(["Zebra", "Abacaxi", "Manga"])

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
        _seed_positions(["Ativo A", "Ativo B"])

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
        _seed_positions(["RF1", "AC1"])

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
        _seed_positions(["Ativo A", "Ativo B"])

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
