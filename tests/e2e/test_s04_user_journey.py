"""Real-browser E2E for the S04 CSV import user journey.

Drives a headless chromium against a live uvicorn instance to
verify the complete S04 import loop end to end:

  login → select profile → create 3 classes (60/30/10) →
  add 43 assets spread across the 3 classes →
  upload the 48-row broker CSV fixture →
  see 43 auto-matched + 5 unmatched on the review screen →
  assign a class to each of the 5 unmatched →
  confirm the import →
  dashboard shows all 48 assets with non-zero position counts.

The second test (negative) covers the "Expirado" state by
backdating the preview row's created_at via a direct sqlite3
write so the review screen renders the expired banner.

This test exists because the route-level TestClient tests in
``test_t03_imports_routes.py`` bypass the rendered HTML. If the
import button were placed outside its ``<form>``, or the review
form's class select changed names, or the dashboard stopped
showing position counts, this test would catch it.

The 43 matched asset names are the exact strings the parser
emits in :mod:`omaha.csv_import` (col 1 of every non-unmatched
data row in ``tests/fixtures/sample_broker.csv``). The 5
unmatched are the names the S02/T02 test plan called out and
that the unit tests pin in :mod:`tests.test_t02_csv_import`.
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
    "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "MGLU3", "BBAS3",
    "WEGE3", "RENT3", "LREN3", "B3SA3", "SUZB3", "CSAN3", "PETR3",
    "VBBR3", "PRIO3", "IVVB11",
    "IVV", "VOO", "QQQ", "SMH", "SOXX", "VTI", "SPY", "VT",
    "HASH11", "BTLG11", "KNCR11", "IRDM11", "XPML11", "VISC11",
    "BRCR11", "TORD11", "MALL11", "DEVA11", "RBVA11", "VRTA11",
    "BPRP11", "PVBI11", "HCTR11", "XPIN11",
    "Tesouro Selic 2029", "Tesouro IPCA+ 2035",
]
assert len(MATCHED_NAMES) == 43, f"expected 43 matched names, got {len(MATCHED_NAMES)}"

# Class assignment map for the 43 matched assets. The percentages
# (60/30/10) are the S04 demo target but the test does not assert
# on them — only on the import flow succeeding.
RENDA_FIXA_NAMES = {
    "HASH11", "BTLG11", "KNCR11", "IRDM11", "XPML11", "VISC11",
    "BRCR11", "TORD11", "MALL11", "DEVA11", "RBVA11", "VRTA11",
    "BPRP11", "PVBI11", "HCTR11", "XPIN11",
    "Tesouro Selic 2029", "Tesouro IPCA+ 2035",
}
ACOES_NAMES = {
    "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "MGLU3", "BBAS3",
    "WEGE3", "RENT3", "LREN3", "B3SA3", "SUZB3", "CSAN3", "PETR3",
    "VBBR3", "PRIO3", "IVVB11",
}
RESERVA_NAMES = {
    "IVV", "VOO", "QQQ", "SMH", "SOXX", "VTI", "SPY", "VT",
}
assert len(RENDA_FIXA_NAMES) + len(ACOES_NAMES) + len(RESERVA_NAMES) == 43


SELECTORS = {
    "login_user": 'input[name="username"]',
    "login_pass": 'input[name="password"]',
    "login_submit": 'button[type="submit"]',
    "profile_picker": 'form.profile-picker button',
    "nav_dashboard": '[data-testid="nav-dashboard"]',
    "nav_classes": '[data-testid="nav-classes"]',
    "nav_assets": '[data-testid="nav-assets"]',
    "nav_import": '[data-testid="nav-import"]',
    "class_editor_name": '[data-testid="class-editor-name"]',
    "class_editor_pct": '[data-testid="class-editor-pct"]',
    "class_editor_add": '[data-testid="class-editor-add"]',
    "class_editor_save": '[data-testid="class-editor-save"]',
    "class_summary_row": '[data-testid="class-summary-row"]',
    "asset_editor_name": '[data-testid="asset-editor-name"]',
    "asset_editor_class": '[data-testid="asset-editor-class"]',
    "asset_editor_add": '[data-testid="asset-editor-add"]',
    "asset_row": '[data-testid="asset-row"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "import_form": '[data-testid="import-form"]',
    "import_file": '[data-testid="import-file"]',
    "import_submit": '[data-testid="import-submit"]',
    "import_error": '[data-testid="import-error"]',
    "import_review_form": '[data-testid="import-review-form"]',
    "import_review_auto_count": '[data-testid="import-review-auto-count"]',
    "import_review_unmatched_count": '[data-testid="import-review-unmatched-count"]',
    "import_review_auto_row": '[data-testid="import-review-auto-row"]',
    "import_review_unmatched_row": '[data-testid="import-review-unmatched-row"]',
    "import_review_class_select": '[data-testid="import-review-class-select"]',
    "import_review_name_input": '[data-testid="import-review-name-input"]',
    "import_review_confirm": '[data-testid="import-review-confirm"]',
    "import_review_expired": '[data-testid="import-review-expired"]',
    "position_count": '[data-testid="import-position-count"]',
}


def _login_and_select_italo(page: Page, base_url: str) -> None:
    """Drive the login + profile picker using the live UI."""
    page.goto(f"{base_url}/login")
    page.fill(SELECTORS["login_user"], "family")
    page.fill(SELECTORS["login_pass"], "test-password")
    page.click(SELECTORS["login_submit"])
    page.wait_for_url(re.compile(r"/profiles$"))

    page.locator(SELECTORS["profile_picker"]).filter(has_text="Italo").click()
    page.wait_for_url(re.compile(r"/$"))


def _create_three_classes(page: Page) -> None:
    """Create Renda Fixa 60 / Acoes 30 / Reserva 10 via the Alpine class editor."""
    page.click(SELECTORS["nav_classes"])
    page.wait_for_url(re.compile(r"/classes$"))
    # Editor seeds 1 empty row on init; addRow twice to reach 3.
    page.click(SELECTORS["class_editor_add"])
    page.click(SELECTORS["class_editor_add"])
    name_inputs = page.locator(SELECTORS["class_editor_name"])
    pct_inputs = page.locator(SELECTORS["class_editor_pct"])
    name_inputs.nth(0).fill("Renda Fixa")
    pct_inputs.nth(0).fill("60")
    name_inputs.nth(1).fill("Acoes")
    pct_inputs.nth(1).fill("30")
    name_inputs.nth(2).fill("Reserva")
    pct_inputs.nth(2).fill("10")
    page.wait_for_function(
        f"() => !document.querySelector('{SELECTORS['class_editor_save']}').disabled",
        timeout=3000,
    )
    page.click(SELECTORS["class_editor_save"])
    page.wait_for_url(re.compile(r"/$"))
    assert page.locator(SELECTORS["class_summary_row"]).count() == 3


def _seed_43_assets(page: Page) -> None:
    """Add the 43 names that match the broker fixture, one per asset."""
    page.click(SELECTORS["nav_assets"])
    page.wait_for_url(re.compile(r"/assets$"))

    for i, asset_name in enumerate(MATCHED_NAMES):
        if asset_name in RENDA_FIXA_NAMES:
            class_label = "Renda Fixa"
        elif asset_name in ACOES_NAMES:
            class_label = "Acoes"
        else:
            class_label = "Reserva"
        page.fill(SELECTORS["asset_editor_name"], asset_name)
        page.select_option(SELECTORS["asset_editor_class"], label=class_label)
        page.click(SELECTORS["asset_editor_add"])
        # Wait for the row count to increment before continuing.
        try:
            page.wait_for_function(
                f"() => document.querySelectorAll('{SELECTORS['asset_row']}').length === {i + 1}",
                timeout=5000,
            )
        except Exception:
            _debug_dump(page, f"asset_iter_{i}_{asset_name}")
            raise

    assert page.locator(SELECTORS["asset_row"]).count() == 43


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
        self, page: Page, live_url: str
    ) -> None:
        """Full S04 user journey: classes → 43 assets → upload → review →
        assign 5 unmatched → confirm → dashboard shows 48 assets each with
        at least 1 position.

        The matcher contract (43 auto + 5 unmatched) is pinned in
        ``test_t02_csv_import.test_match_positions_43_5_split``. This
        test asserts the same split is visible on the rendered review
        screen AND the confirm flow commits one position per row.
        """
        _login_and_select_italo(page, live_url)
        _create_three_classes(page)
        _seed_43_assets(page)

        # --- 1. Upload the broker CSV via the live /import form.
        page.click(SELECTORS["nav_import"])
        page.wait_for_url(re.compile(r"/import$"))
        page.set_input_files(SELECTORS["import_file"], str(FIXTURE_PATH))
        page.click(SELECTORS["import_submit"])
        page.wait_for_url(re.compile(r"/import/review$"))

        # --- 2. Review screen shows 43 auto + 5 unmatched.
        auto_count_text = page.locator(SELECTORS["import_review_auto_count"]).inner_text()
        unmatched_count_text = page.locator(
            SELECTORS["import_review_unmatched_count"]
        ).inner_text()
        assert "43" in auto_count_text, f"expected 43 auto, got {auto_count_text!r}"
        assert "5" in unmatched_count_text, (
            f"expected 5 unmatched, got {unmatched_count_text!r}"
        )

        # Spot-check the auto and unmatched row counts in the DOM.
        assert page.locator(SELECTORS["import_review_auto_row"]).count() == 43
        assert page.locator(SELECTORS["import_review_unmatched_row"]).count() == 5

        # The 5 unmatched names match the T02 unit-test contract.
        unmatched_names = {
            page.locator(SELECTORS["import_review_unmatched_row"]).nth(i).locator(
                "td"
            ).nth(0).inner_text()
            for i in range(5)
        }
        for expected in UNMATCHED_NAMES:
            assert any(expected in text for text in unmatched_names), (
                f"missing unmatched {expected!r} in {unmatched_names!r}"
            )

        # --- 3. Assign a class to each of the 5 unmatched rows.
        # Use the first available class ("Renda Fixa") for all 5
        # to keep the test simple — the import route's only class
        # contract is "belongs to this profile".
        for i in range(5):
            select = page.locator(SELECTORS["import_review_class_select"]).nth(i)
            select.select_option(label="Renda Fixa")

        # --- 4. Confirm the import.
        page.click(SELECTORS["import_review_confirm"])
        page.wait_for_url(re.compile(r"/$"))

        # --- 5. Dashboard shows 48 asset rows (43 pre-seeded + 5 created),
        # each with at least 1 position.
        dashboard_rows = page.locator(SELECTORS["dashboard_asset_row"])
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{SELECTORS['dashboard_asset_row']}').length === 48",
                timeout=5000,
            )
        except Exception:
            _debug_dump(page, "post_confirm_dashboard")
            raise
        assert dashboard_rows.count() == 48

        # Every row must show >= 1 position. The data-position-count
        # attribute (added in the T04 dashboard change) is the
        # machine-readable form of the count.
        for i in range(48):
            row = dashboard_rows.nth(i)
            count = int(row.locator(SELECTORS["position_count"]).get_attribute(
                "data-position-count"
            ))
            assert count >= 1, f"row {i} has {count} positions, expected >= 1"

        # The 5 new assets must have the unmatched names. They were
        # all created in "Renda Fixa" (the class we picked for them).
        dashboard_text = page.locator("main").inner_text()
        for name in UNMATCHED_NAMES:
            assert name in dashboard_text, (
                f"new asset {name!r} not on dashboard after confirm"
            )

    def test_expired_preview_shows_expirado(
        self, page: Page, live_url: str
    ) -> None:
        """A preview whose created_at is older than PREVIEW_TTL renders
        the Expirado state on /import/review.

        We don't wait 1 hour: the test backdates the preview row via
        a direct sqlite3 write. The ``clean_italo`` autouse fixture
        wipes classes before the test; we re-create them so the
        /import POST succeeds (the route requires an active profile
        with no class constraint, but the seed function on the
        e2e conftest wipes everything).
        """
        _login_and_select_italo(page, live_url)
        _create_three_classes(page)

        # Upload to create a fresh preview.
        page.click(SELECTORS["nav_import"])
        page.wait_for_url(re.compile(r"/import$"))
        page.set_input_files(SELECTORS["import_file"], str(FIXTURE_PATH))
        page.click(SELECTORS["import_submit"])
        page.wait_for_url(re.compile(r"/import/review$"))

        # Backdate the preview to 2 hours ago (PREVIEW_TTL is 1h).
        # Connect to the test DB the e2e conftest started.
        conn = sqlite3.connect(TEST_DB_PATH)
        try:
            conn.execute(
                "UPDATE import_previews SET created_at = datetime('now', '-2 hours')"
            )
            conn.commit()
        finally:
            conn.close()

        # Reload the review page — it should now show Expirado.
        page.goto(f"{live_url}/import/review")
        # The Expirado state replaces the form; the form is gone and
        # the import-review-expired banner is rendered.
        assert page.locator(SELECTORS["import_review_expired"]).count() == 1
        assert page.locator(SELECTORS["import_review_form"]).count() == 0
        expired_text = page.locator(SELECTORS["import_review_expired"]).inner_text()
        assert "Expirado" in expired_text or "expirado" in expired_text.lower()
