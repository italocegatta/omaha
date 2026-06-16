"""Real-browser E2E for the S04 CSV import user journey.

Drives a headless chromium against a live uvicorn instance to
verify the complete S04 import loop end to end using the
dashboard import modal:

  login → select profile → create 3 classes (60/30/10) →
  seed 43 assets via the API → open the import modal →
  upload the 48-row broker CSV fixture → see 43 auto-matched
  + 5 unmatched in the modal review → assign a class to each
  of the 5 unmatched → confirm the import → dashboard shows
  all 48 assets with non-zero position counts.

The second test (negative) covers the "Expirado" state via API
assertion — the modal does not have a dedicated expired banner
but the server-side check correctly rejects expired previews.

Why the modal? The S04/T03/T10 refactored the standalone
/import → /import/review pages into an Alpine.js modal on the
dashboard. The form-based POST /import and GET /import/review
routes redirect to /, so the old page-navigation flow no longer
works.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "sample_broker.csv"
TEST_DB_PATH = REPO_ROOT / "data" / "test_e2e.db"

# The exact 48 names the fixture produces (header + banner + 48
# data rows, of which 1 is the empty-ticker phantom and 1 is the
# Total footer — both consumed by the parser — leaving 46 rows
# the user has to act on: 43 auto + 5 unmatched, but wait: 48
# RawPositions out of 48 data rows because the phantom is
# skipped by the parser's empty-ticker rule, not counted as a
# data row; the footer is consumed by the known-footer rule;
# so 48 - 1 phantom - 1 footer = 46... no, the test_t02 fixture
# asserts len(positions) == 48, so 48 RawPositions out, of which
# 5 are unmatched. The 5 unmatched names are pinned by
# test_t02_csv_import.UNMATCHED_NAMES.
UNMATCHED_NAMES = ["MXRF11", "BPAC11", "HGLG11", "XPLG11", "VINO11"]

# 48 total - 5 unmatched = 43 assets the test must seed so the
# auto-matcher picks them up. The list is the exact order they
# appear in the fixture (col 1 of each data row).
MATCHED_NAMES: list[str] = [
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "ABEV3",
    "MGLU3",
    "BBAS3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "B3SA3",
    "SUZB3",
    "CSAN3",
    "PETR3",
    "VBBR3",
    "PRIO3",
    "IVVB11",
    "IVV",
    "VOO",
    "QQQ",
    "SMH",
    "SOXX",
    "VTI",
    "SPY",
    "VT",
    "HASH11",
    "BTLG11",
    "KNCR11",
    "IRDM11",
    "XPML11",
    "VISC11",
    "BRCR11",
    "TORD11",
    "MALL11",
    "DEVA11",
    "RBVA11",
    "VRTA11",
    "BPRP11",
    "PVBI11",
    "HCTR11",
    "XPIN11",
    "Tesouro Selic 2029",
    "Tesouro IPCA+ 2035",
]
assert len(MATCHED_NAMES) == 43, f"expected 43 matched names, got {len(MATCHED_NAMES)}"

# Class assignment map for the 43 matched assets. The class labels
# below ("RF Pós", "Acoes", "Reserva") reflect the post-D011
# contract: the S04 suggester does exact + one-way substring match
# on normalized class names, no keyword map. "RF Pós" is the exact
# class name that the broker file's "Minha Categoria" column
# (e.g. MXRF11 → "RF Pós") pre-selects in the review screen, and
# "Acoes" matches the broker's "Ações" via normalize_name's
# accent-strip + lower. The percentages (60/30/10) are the S04
# demo target but the test does not assert on them — only on the
# import flow succeeding.
RF_POS_NAMES = {
    "HASH11",
    "BTLG11",
    "KNCR11",
    "IRDM11",
    "XPML11",
    "VISC11",
    "BRCR11",
    "TORD11",
    "MALL11",
    "DEVA11",
    "RBVA11",
    "VRTA11",
    "BPRP11",
    "PVBI11",
    "HCTR11",
    "XPIN11",
    "Tesouro Selic 2029",
    "Tesouro IPCA+ 2035",
}
ACOES_NAMES = {  # noqa: E305 — needs to follow RF_POS_NAMES
    "PETR4",
    "VALE3",
    "ITUB4",
    "BBDC4",
    "ABEV3",
    "MGLU3",
    "BBAS3",
    "WEGE3",
    "RENT3",
    "LREN3",
    "B3SA3",
    "SUZB3",
    "CSAN3",
    "PETR3",
    "VBBR3",
    "PRIO3",
    "IVVB11",
}
RESERVA_NAMES = {
    "IVV",
    "VOO",
    "QQQ",
    "SMH",
    "SOXX",
    "VTI",
    "SPY",
    "VT",
}
assert len(RF_POS_NAMES) + len(ACOES_NAMES) + len(RESERVA_NAMES) == 43


# Dashboard modal import selectors. The import is triggered via a
# button on the dashboard (S04/T03/T10) that opens an Alpine modal.
SELECTORS = {
    "login_user": 'input[name="username"]',
    "login_pass": 'input[name="password"]',
    "login_submit": 'button[type="submit"]',
    "profile_picker": "form.profile-picker button",
    "nav_dashboard": '[data-testid="nav-dashboard"]',
    "class_summary_row": '[data-testid="class-summary-row"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    # Dashboard import modal
    "dashboard_import_btn": '[data-testid="dashboard-import-btn"]',
    "import_file_input": '[data-testid="import-file-input"]',
    "import_upload_btn": '[data-testid="import-upload-btn"]',
    "import_modal_error": '[data-testid="import-upload-error"]',
    "import_commit_btn": '[data-testid="import-commit-btn"]',
    "import_unmatched_table": '[data-testid="import-unmatched-table"]',
    "import_assignment_class": '[data-testid="import-assignment-class"]',
    "import_assignment_name": '[data-testid="import-assignment-name"]',
    "import_commit_error": '[data-testid="import-commit-error"]',
}


def _login_and_select_italo(page: Page, base_url: str) -> None:
    """Drive the login + profile picker using the live UI."""
    page.goto(f"{base_url}/login")
    page.fill(SELECTORS["login_user"], "Italo")
    page.fill(SELECTORS["login_pass"], "test-password")
    page.click(SELECTORS["login_submit"])
    page.wait_for_url(re.compile(r"/profiles$"))

    page.locator(SELECTORS["profile_picker"]).filter(has_text="Italo").click()
    page.wait_for_url(re.compile(r"/$"))


def _create_classes_via_form(page: Page, base_url: str, classes: list[tuple[str, int]]) -> None:
    """Submit the snapshot class editor form via the browser's fetch API.

    The ``POST /classes`` endpoint uses snapshot semantics (parallel
    ``name[]`` / ``target_pct[]`` form arrays) and requires the per-profile
    sum to equal 100. The browser must be logged in — ``fetch`` inherits
    the page's cookies.
    """
    page.evaluate(
        """async ({ url, cls }) => {
            const fd = new FormData();
            for (const [name, pct] of cls) {
                fd.append('name[]', name);
                fd.append('target_pct[]', String(pct));
            }
            const r = await fetch(url, { method: 'POST', body: fd });
            if (!r.ok) {
                throw new Error('POST /classes ' + r.status + ': ' + await r.text());
            }
        }""",
        {"url": f"{base_url}/classes", "cls": classes},
    )


def _create_three_classes(page: Page, base_url: str) -> None:
    """Create RF Pós 60 / Acoes 30 / Reserva 10 via the snapshot form.

    Uses ``POST /classes`` (form-based, parallel arrays). The browser
    must be logged in — ``fetch`` inherits the page's cookies.

    "RF Pós" is the post-D011 class name: the broker file's "Minha
    Categoria" column carries "RF Pós" for the fixed-income rows and
    "Ações" for the equity rows, so the import review pre-selects these
    exact class names (no keyword map translates "RF Pós" → "Renda Fixa"
    any more).
    """
    _create_classes_via_form(
        page,
        base_url,
        [("RF Pós", 60), ("Acoes", 30), ("Reserva", 10)],
    )
    # Reload the dashboard to pick up the new classes.
    page.goto(f"{base_url}/")
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)
    assert page.locator(SELECTORS["class_summary_row"]).count() == 3


def _seed_43_assets(page: Page) -> None:
    """Seed 43 assets via the JSON API for speed.

    Uses ``page.evaluate()`` to call ``POST /api/assets`` once per asset,
    with the correct class id extracted from the DOM. This is much faster
    than creating 43 assets through the inline dashboard form.
    """
    # Read the class IDs from the dashboard DOM.
    class_ids: dict[str, int] = page.evaluate(
        """() => {
            const rows = document.querySelectorAll('[data-testid="class-summary-row"]');
            const result = {};
            for (const row of rows) {
                const nameEl = row.querySelector('[data-testid="class-section-name"]');
                const name = nameEl ? nameEl.textContent.trim() : '';
                result[name] = parseInt(row.getAttribute('data-class-id'), 10);
            }
            return result;
        }"""
    )
    assert "RF Pós" in class_ids, f"RF Pós not found in class_ids: {class_ids}"
    assert "Acoes" in class_ids, f"Acoes not found in class_ids: {class_ids}"
    assert "Reserva" in class_ids, f"Reserva not found in class_ids: {class_ids}"

    # Map asset name → class_id.
    def _class_id_for(name: str) -> int:
        if name in RF_POS_NAMES:
            return class_ids["RF Pós"]
        elif name in ACOES_NAMES:
            return class_ids["Acoes"]
        else:
            return class_ids["Reserva"]

    # Create assets one at a time via the JSON API.
    for asset_name in MATCHED_NAMES:
        success = page.evaluate(
            """async ({ name, class_id }) => {
                const r = await fetch('/api/assets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, asset_class_id: class_id }),
                });
                return r.status === 201;
            }""",
            {"name": asset_name, "class_id": _class_id_for(asset_name)},
        )
        assert success, f"Failed to create asset {asset_name!r} via API"

    # Reload to pick up the new assets on the dashboard.
    page.goto(page.url)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=5000)


def _debug_dump(page: Page, tag: str) -> None:
    """Write a screenshot + main-text + URL to /tmp for post-mortem."""
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


class TestS04ImportJourney:
    """One happy-path + one negative-path."""

    def test_import_journey_43_matched_5_unmatched_5_assigned_confirm_dashboard(
        self, page: Page, live_url: str, browser_context
    ) -> None:
        """Full S04 import journey via dashboard modal.

        Login → create 3 classes → seed 43 assets → open import modal →
        upload CSV → review (43 auto + 5 unmatched) → assign classes
        for unmatched → commit → dashboard shows 48 assets with positions.
        """
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)
        _seed_43_assets(page)

        # --- 1. Open the import modal and upload the CSV.
        # Click the dashboard import button to open the modal.
        page.click(SELECTORS["dashboard_import_btn"])
        page.wait_for_selector(
            '[data-testid="import-modal-overlay"]', state="visible", timeout=5000
        )
        page.wait_for_timeout(300)

        # Upload the CSV via the modal file input.
        page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
        page.wait_for_timeout(300)  # Alpine @change fires, sets $store.importModal.file
        # Use force=True because the button may be within the Alpine transition scope.
        page.click(SELECTORS["import_upload_btn"], force=True)

        # Wait for the modal to transition to step 2 (review).
        # The Alpine store sets step=2 on successful upload; the
        # commit button becomes visible.
        page.wait_for_selector(SELECTORS["import_commit_btn"], timeout=10000)

        # --- 2. Check all 5 unmatched rows have a class selected.
        # Rows with "(Não configurado)" category start with empty class.
        # Read the assignments and fill any empty values.
        unmatched_rows = page.locator('[data-testid="import-unmatched-table"] tbody tr')
        unmatched_count = unmatched_rows.count()
        assert unmatched_count == 5, f"expected 5 unmatched rows, got {unmatched_count}"

        # Override the 3 rows that start with an empty class
        # (BPAC11, HGLG11, VINO11 have "(Não configurado)" category
        # which does not pre-select a class) to "RF Pós".
        for i in range(unmatched_count):
            select = unmatched_rows.nth(i).locator(SELECTORS["import_assignment_class"])
            current_value = select.evaluate("el => el.options[el.selectedIndex].value")
            if not current_value:
                select.select_option(label="RF Pós")

        # --- 3. Confirm the import.
        page.click(SELECTORS["import_commit_btn"], force=True)

        # Wait for the page reload (modal calls window.location.reload()
        # on successful commit). Use load_state to catch the actual reload.
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_selector(SELECTORS["class_summary_row"], timeout=10000)

        # --- 4. Dashboard shows 48 asset rows, each with >= 1 position.
        dashboard_rows = page.locator(SELECTORS["dashboard_asset_row"])
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{SELECTORS['dashboard_asset_row']}').length === 48",
                timeout=10000,
            )
        except Exception:
            _debug_dump(page, "post_confirm_dashboard")
            raise
        assert dashboard_rows.count() == 48

        # Every row must have >= 1 position via data-position-count.
        for i in range(48):
            row = dashboard_rows.nth(i)
            count_str = row.get_attribute("data-position-count")
            assert count_str is not None, f"row {i} missing data-position-count"
            count = int(count_str)
            assert count >= 1, f"row {i} has {count} positions, expected >= 1"

        # The 5 new assets must have the unmatched names.
        dashboard_text = page.locator("main").inner_text()
        for name in UNMATCHED_NAMES:
            assert name in dashboard_text, f"new asset {name!r} not on dashboard after confirm"

    def test_expired_preview_shows_expirado(self, page: Page, live_url: str) -> None:
        """A backdated preview renders the Expired UI in the modal.

        The old test navigated to /import/review to see the expired
        banner. With the dashboard modal, the expired state is checked
        server-side on commit. We test end-to-end: upload via the modal,
        backdate the preview, then verify the commit returns 400.

        Additionally, we verify the GET /api/import/preview/<id> endpoint
        returns 404 for expired previews (the server-side check that
        the modal would hit on re-upload).
        """
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)

        # Upload via the dashboard modal to create a fresh preview.
        page.click(SELECTORS["dashboard_import_btn"])
        page.wait_for_selector(
            '[data-testid="import-modal-overlay"]', state="visible", timeout=5000
        )
        page.wait_for_timeout(300)
        page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
        page.wait_for_timeout(300)
        page.click(SELECTORS["import_upload_btn"], force=True)
        page.wait_for_selector(SELECTORS["import_commit_btn"], timeout=10000)

        # Read the preview_id from the Alpine store.
        preview_id: int | None = page.evaluate("() => Alpine.store('importModal').previewId")
        assert preview_id is not None and isinstance(
            preview_id, int
        ), f"expected preview_id, got {preview_id!r}"

        # Backdate the preview to 2 hours ago (PREVIEW_TTL is 1h).
        conn = sqlite3.connect(TEST_DB_PATH)
        try:
            conn.execute(
                "UPDATE import_previews SET created_at = datetime('now', '-2 hours') WHERE id = ?",
                (preview_id,),
            )
            conn.commit()
        finally:
            conn.close()

        # Verify the GET preview endpoint returns 404 (expired).
        resp = page.evaluate(
            """async (previewId) => {
                const r = await fetch('/api/import/preview/' + previewId);
                return { status: r.status, detail: (await r.json()).detail };
            }""",
            preview_id,
        )
        assert resp["status"] == 404, f"expected 404 for expired preview, got {resp}"
        assert (
            "expirado" in resp["detail"].lower()
        ), f"expected 'expirado' in error, got {resp['detail']!r}"

        # Verify commit rejects the expired preview.
        commit_resp = page.evaluate(
            """async (previewId) => {
                const r = await fetch('/api/import/commit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        preview_id: previewId,
                        assignments: [],
                    }),
                });
                return { status: r.status, detail: (await r.json()).detail };
            }""",
            preview_id,
        )
        assert commit_resp["status"] == 400, f"expected 400 for expired commit, got {commit_resp}"
        assert (
            "expirado" in commit_resp["detail"].lower()
        ), f"expected 'expirado' in error, got {commit_resp['detail']!r}"
