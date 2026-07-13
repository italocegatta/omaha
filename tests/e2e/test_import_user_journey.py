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

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

from tests.support.import_flow import (
    ACOES_NAMES,
    MATCHED_NAMES,
    RESERVA_NAMES,
    RF_POS_NAMES,
    UNMATCHED_NAMES,
)
from tests.support.import_flow import (
    create_three_classes as _create_three_classes,
)
from tests.support.import_flow import (
    debug_dump as _debug_dump,
)
from tests.support.import_flow import (
    login_and_select_italo as _login_and_select_italo,
)
from tests.support.import_flow import (
    seed_43_assets as _seed_43_assets,
)

from .selectors import SELECTORS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "sample_broker.csv"

assert len(RF_POS_NAMES) + len(ACOES_NAMES) + len(RESERVA_NAMES) == 43
assert len(MATCHED_NAMES) == 43


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

        # File selection automatically advances the modal to step 2 (review).
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

        # Wait for dashboard re-render after import commit.
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

    def test_expired_preview_shows_expirado(self, page: Page, live_url_short_ttl: str) -> None:
        """A short-TTL preview expires while the modal is open.

        The old test navigated to /import/review to see the expired
        banner. With the dashboard modal, the expired state is checked
        server-side on commit. We test end-to-end: upload via the modal,
        wait for the 1-second TTL to expire, then verify the commit
        returns 400.

        Additionally, we verify the GET /api/import/preview/<id> endpoint
        returns 404 for expired previews (the server-side check that
        the modal would hit on re-upload).
        """
        _login_and_select_italo(page, live_url_short_ttl)
        _create_three_classes(page, live_url_short_ttl)

        # Upload via the dashboard modal to create a fresh preview.
        page.click(SELECTORS["dashboard_import_btn"])
        page.wait_for_selector(
            '[data-testid="import-modal-overlay"]', state="visible", timeout=5000
        )
        page.wait_for_timeout(300)
        page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
        page.wait_for_selector(SELECTORS["import_commit_btn"], timeout=10000)

        # Read the preview_id from the Alpine store.
        preview_id: int | None = page.evaluate("() => Alpine.store('importModal').previewId")
        assert preview_id is not None and isinstance(preview_id, int), (
            f"expected preview_id, got {preview_id!r}"
        )

        # PREVIEW_TTL is 1s in e2e (set in conftest._start_uvicorn via
        # the ``PREVIEW_TTL_SECONDS=1`` extra_env). The 1.5s margin
        # covers the upload + parse round-trip so the server's
        # ``now - created_at`` is comfortably past the 1s boundary on
        # the next request. The test relies on the e2e short_ttl
        # uvicorn binding a unique port (8767 — see
        # tests/test_e2e_port_uniqueness.py); a port collision with
        # the bdd suite's uvicorn (8766) would silently route the
        # GET to the wrong server with the default 1h TTL, and the
        # preview would never expire.
        page.wait_for_timeout(1500)

        # Verify the GET preview endpoint returns 404 (expired).
        resp = page.evaluate(
            """async (previewId) => {
                const r = await fetch('/api/import/preview/' + previewId);
                return { status: r.status, detail: (await r.json()).detail };
            }""",
            preview_id,
        )
        assert resp["status"] == 404, f"expected 404 for expired preview, got {resp}"
        assert "expirado" in resp["detail"].lower(), (
            f"expected 'expirado' in error, got {resp['detail']!r}"
        )

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
        assert "expirado" in commit_resp["detail"].lower(), (
            f"expected 'expirado' in error, got {commit_resp['detail']!r}"
        )
