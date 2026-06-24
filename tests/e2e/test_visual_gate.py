"""Visual gate test for S05 dashboard polish.

Captures a full-page screenshot of the dashboard with 3 classes
(one expanded with 2 assets, one with 1, one empty) and asserts
structural content is present BEFORE saving the screenshot.

The structural checks (class count, asset count, BRL formatting)
are the gate. The screenshot is the human-readable evidence —
pixel diffing against an M001 baseline is a future follow-up
(the baseline was not captured during M001).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .test_import_user_journey import (
    _login_and_select_italo,
)

SCREENSHOT_DIR = Path("/tmp/s05_e2e_screenshots")


def _create_seeded_classes(page: Page, live_url: str) -> None:
    """Create 3 classes with assets via direct fetch calls.

    Class 1: "Acoes BR" at 60%, with 2 assets (PETR4, VALE3).
    Class 2: "FIIs" at 30%, with 1 asset (HGLG11).
    Class 3: "Cripto" at 10%, empty (no assets).
    """
    # Class 1: Acoes BR 60%
    page.evaluate(
        """async () => {
            const r = await fetch('/api/classes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'Acoes BR', target_pct: 60 }),
            });
            return r.status;
        }"""
    )
    # Assets under class 1 (id=1)
    page.evaluate(
        """async () => {
            for (const name of ['PETR4', 'VALE3']) {
                await fetch('/api/assets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, asset_class_id: 1, target_pct: 50 }),
                });
            }
        }"""
    )

    # Class 2: FIIs 30% with 1 asset
    page.evaluate(
        """async () => {
            const r = await fetch('/api/classes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'FIIs', target_pct: 30 }),
            });
            const cls = await r.json();
            await fetch('/api/assets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'HGLG11', asset_class_id: cls.id, target_pct: 100 }),
            });
        }"""
    )

    # Class 3: Cripto 10% (empty, no assets)
    page.evaluate(
        """async () => {
            await fetch('/api/classes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'Cripto', target_pct: 10 }),
            });
        }"""
    )


class TestS05VisualGate:
    """Screenshot-based visual gate for S05 dashboard polish."""

    def test_capture_dashboard_polish_screenshot(self, page: Page, live_url: str) -> None:
        """Capture a full-page screenshot of the polished dashboard.

        The dashboard has 3 classes (one expanded with 2 assets, one
        with 1, one empty). Structural checks run BEFORE the screenshot
        is captured (class-summary-row count == 3, dashboard-asset-row
        count >= 1, BRL formatting present). The screenshot is saved to
        /tmp/s05_e2e_screenshots/s05_dashboard_polish.png for human
        review only — the file-size assertion is removed.
        """
        _login_and_select_italo(page, live_url)
        _create_seeded_classes(page, live_url)

        # Navigate to dashboard
        page.goto(live_url + "/")
        page.wait_for_selector('[data-testid="class-summary-row"]', timeout=5000)

        # asset-table-view 8.x / fix-asset-table-ui-bugs: class sections
        # default to expanded (isOpen: true on load); user can collapse
        # by clicking the header.
        page.wait_for_selector(
            '[data-testid="dashboard-asset-row"]',
            timeout=5000,
        )

        # ------------------------------------------------------------------
        # Structural pre-assertions (D4): the gate is the DOM, not the
        # file size. Run these BEFORE the screenshot so a regression in
        # class/asset rendering fails fast with a clear assertion.
        # ------------------------------------------------------------------
        class_rows = page.locator('[data-testid="class-summary-row"]')
        assert class_rows.count() == 3, f"expected 3 class-summary-row, got {class_rows.count()}"

        asset_rows = page.locator('[data-testid="dashboard-asset-row"]')
        assert asset_rows.count() >= 1, (
            f"expected >= 1 dashboard-asset-row, got {asset_rows.count()}"
        )

        main_text = page.locator("main").inner_text()
        assert "R$" in main_text, "expected BRL formatting (R$) in dashboard main text"

        # ------------------------------------------------------------------
        # Capture the screenshot AFTER the structural checks pass so the
        # human-readable artifact survives a green run.
        # ------------------------------------------------------------------
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOT_DIR / "s05_dashboard_polish.png"
        page.screenshot(path=str(screenshot_path), full_page=True)

        # The screenshot is human-readable evidence, not the gate. The
        # structural assertions above already proved the page renders;
        # the file just needs to exist.
        assert screenshot_path.exists(), f"Screenshot not created at {screenshot_path}"
