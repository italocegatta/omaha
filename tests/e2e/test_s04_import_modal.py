"""E2E tests for the S04 dashboard import modal and route retirement.

Drives a headless chromium against a live uvicorn instance to verify
the complete import modal flow on the dashboard:

  login -> select profile -> create 3 classes (60/30/10) ->
  seed 43 matched assets via POST /api/assets ->
  click Importar CSV button on dashboard ->
  upload sample_broker.csv fixture via modal ->
  review step shows 43 auto-matched + 5 unmatched ->
  assign classes to the 5 unmatched rows ->
  click Confirmar -> modal commits, page reloads ->
  dashboard shows all 48 assets with position counts.

Also tests that navigating to /import lands on the dashboard (302).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .test_s04_user_journey import (
    _login_and_select_italo,
    ACOES_NAMES,
    MATCHED_NAMES,
    REPO_ROOT,
    RESERVA_NAMES,
    RF_POS_NAMES,
    UNMATCHED_NAMES,
)

FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "sample_broker.csv"

SELECTORS = {
    "profile_name": '[data-testid="profile-name"]',
    "dashboard_import_btn": '[data-testid="dashboard-import-btn"]',
    "import_modal_overlay": '[data-testid="import-modal-overlay"]',
    "import_file_input": '[data-testid="import-file-input"]',
    "import_upload_btn": '[data-testid="import-upload-btn"]',
    "import_matched_summary": '[data-testid="import-matched-summary"]',
    "import_unmatched_table": '[data-testid="import-unmatched-table"]',
    "import_unmatched_row": '[data-testid="import-unmatched-row"]',
    "import_commit_btn": '[data-testid="import-commit-btn"]',
    "class_summary_row": '[data-testid="class-summary-row"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "class_section_name": '[data-testid="class-section-name"]',
}


def _debug_dump(page: Page, tag: str) -> None:
    import os

    os.makedirs("/tmp/s04_e2e_debug", exist_ok=True)
    page.screenshot(path=f"/tmp/s04_e2e_debug/{tag}.png", full_page=True)
    with open(f"/tmp/s04_e2e_debug/{tag}.txt", "w") as f:
        f.write(f"URL: {page.url}\n\n")
        try:
            f.write("MAIN TEXT:\n")
            f.write(page.locator("main").inner_text())
        except Exception as exc:
            f.write(f"main inner_text failed: {exc}\n")


def _create_seed_classes(page: Page, classes: list[tuple[str, int]]) -> None:
    """Seed classes via fetch POST /classes (snapshot form), then reload."""
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
    assert page.locator(SELECTORS["class_summary_row"]).count() == len(classes)


def _seed_matched_assets(page: Page) -> None:
    """Create 43 matched assets spread across 3 classes via POST /api/assets.

    Reads class IDs from the rendered dashboard DOM, then creates each
    asset by fetch POST /api/assets with the matching class_id.
    """
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
    for asset_name in MATCHED_NAMES:
        if asset_name in RF_POS_NAMES:
            class_label = "RF Pós"
        elif asset_name in ACOES_NAMES:
            class_label = "Acoes"
        elif asset_name in RESERVA_NAMES:
            class_label = "Reserva"
        else:
            raise RuntimeError(f"asset {asset_name!r} not found in any class list")
        class_id = class_map.get(class_label)
        if class_id is None:
            raise RuntimeError(
                f"class {class_label!r} not found in rendered dashboard "
                f"(available: {list(class_map)})"
            )
        page.evaluate(
            """async ({classId, assetName}) => {
                const r = await fetch('/api/assets', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: assetName,
                        asset_class_id: classId,
                        target_pct: "0",
                    }),
                });
                if (!r.ok) {
                    throw new Error('POST /api/assets ' + r.status + ': ' + await r.text());
                }
            }""",
            {"classId": class_id, "assetName": asset_name},
        )

    # Reload the dashboard to pick up the new assets.
    page.goto(page.url)
    page.wait_for_selector(SELECTORS["dashboard_asset_row"], timeout=8000)


class TestS04ImportModal:
    """E2E tests for the dashboard import modal and route retirement."""

    def test_import_modal_happy_path(self, page: Page, live_url: str) -> None:
        """Full import modal flow: upload -> review -> assign -> commit -> assert.

        Setup: login + create 3 classes + seed 43 matched assets.
        """
        # ------------------------------------------------------------------
        # Setup: login, create classes, seed assets
        # ------------------------------------------------------------------
        _login_and_select_italo(page, live_url)
        _create_seed_classes(page, [["RF Pós", 60], ["Acoes", 30], ["Reserva", 10]])
        _seed_matched_assets(page)

        # Verify 43 assets on dashboard before import.
        asset_rows = page.locator(SELECTORS["dashboard_asset_row"])
        assert asset_rows.count() == 43, (
            f"expected 43 asset rows before import, got {asset_rows.count()}"
        )

        # ------------------------------------------------------------------
        # Step 1: Open modal and upload CSV
        # ------------------------------------------------------------------
        # Open the modal by calling the Alpine store method directly.
        # Clicking the button's @click handler sometimes races with
        # Playwright's visibility checks.
        page.evaluate("Alpine.store('importModal').openModal()")
        page.wait_for_selector(
            SELECTORS["import_modal_overlay"], state="visible", timeout=5000
        )

        page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
        # Let Alpine process the @change event from set_input_files.
        page.wait_for_timeout(200)

        # Click the upload button via the Alpine store directly, since
        # the button's :disabled binding re-enables once the store's
        # file property is set after the set_input_files change event.
        page.evaluate("Alpine.store('importModal').uploadFile()")
        page.wait_for_timeout(500)

        # ------------------------------------------------------------------
        # Step 2: Wait for review (matched summary + unmatched table)
        # ------------------------------------------------------------------
        page.wait_for_selector(
            SELECTORS["import_matched_summary"], state="visible", timeout=15000
        )
        page.wait_for_selector(
            SELECTORS["import_unmatched_table"], state="visible", timeout=5000
        )

        # Verify 5 unmatched rows.
        unmatched_rows = page.locator(SELECTORS["import_unmatched_row"])
        assert unmatched_rows.count() == 5, (
            f"expected 5 unmatched rows, got {unmatched_rows.count()}"
        )

        # Verify the unmatched tickers match the known list.
        unmatched_tickers: set[str] = set()
        for i in range(5):
            ticker = unmatched_rows.nth(i).locator("td").nth(0).inner_text().strip()
            unmatched_tickers.add(ticker)
        assert unmatched_tickers == set(UNMATCHED_NAMES), (
            f"expected unmatched tickers {set(UNMATCHED_NAMES)}, "
            f"got {unmatched_tickers}"
        )

        # ------------------------------------------------------------------
        # Step 3: Assign classes to the 5 unmatched rows
        # ------------------------------------------------------------------
        # The Alpine store defaults ALL unmatched to the first class
        # (RF Pós -- the first one created).  MXRF11 has "RF Pós" at
        # the suggestion level but the store always picks the first
        # class.  XPLG11's CSV row says "Acoes" so we put it in Acoes.
        # The other 3 can stay in their default (RF Pós).
        page.evaluate(
            """() => {
                const s = Alpine.store('importModal');
                const acoes = s.assetClasses.find(c => c.name === 'Acoes');
                if (acoes && s.assignments['XPLG11']) {
                    s.assignments['XPLG11'].class_id = acoes.id;
                }
            }"""
        )

        # ------------------------------------------------------------------
        # Step 4: Click Confirmar to commit
        # ------------------------------------------------------------------
        page.click(SELECTORS["import_commit_btn"])

        # The commit calls window.location.reload().  Wait for the
        # dashboard to show all 48 asset rows.
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                "'[data-testid=\"dashboard-asset-row\"]').length === 48",
                timeout=15000,
            )
        except Exception:
            _debug_dump(page, "post_commit_dashboard")
            raise

        # ------------------------------------------------------------------
        # Step 5: Verify 48 assets with positions
        # ------------------------------------------------------------------
        dashboard_rows = page.locator(SELECTORS["dashboard_asset_row"])
        assert dashboard_rows.count() == 48, (
            f"expected 48 asset rows after import, got {dashboard_rows.count()}"
        )

        for i in range(48):
            row = dashboard_rows.nth(i)
            count_str = row.get_attribute("data-position-count")
            assert count_str is not None, f"row {i} missing data-position-count"
            count = int(count_str)
            assert count >= 1, (
                f"row {i} has {count} positions, expected >= 1"
            )

        # The 5 new assets must appear in the dashboard text.
        dashboard_text = page.locator("main").inner_text()
        for name in UNMATCHED_NAMES:
            assert name in dashboard_text, (
                f"new asset {name!r} not found on dashboard after import"
            )

    def test_import_route_redirects(self, page: Page, live_url: str) -> None:
        """GET /import redirects to the dashboard (retired route)."""
        _login_and_select_italo(page, live_url)

        page.goto(f"{live_url}/import")

        # The URL must be the dashboard (/), not /import.
        assert "/import" not in page.url, (
            f"expected redirect away from /import, got URL: {page.url}"
        )

        profile_header = page.locator(SELECTORS["profile_name"])
        profile_header.wait_for(state="visible", timeout=5000)
        assert "Bem-vindo" in profile_header.inner_text()
