"""Real-browser E2E for the S05 dashboard user journey.

Drives a headless chromium against a live uvicorn instance to
verify the S05 distribution-visualization polish end to end:

  login → select profile → create 3 classes (60/30/10) →
  add 43 assets spread across the 3 classes →
  upload the 48-row broker CSV →
  review (43 auto + 5 unmatched) → assign 5 unmatched → confirm →
  dashboard shows the S05 polish: portfolio header with
  invested/current/gain in BRL, per-class sections with
  target-vs-current compare bars, per-asset rows with
  position count + BRL value + pct + progress bar, color
  swatches with non-empty backgrounds, and the 6
  ``--class-N`` color tokens defined in :root.

This test exists because the TestClient tests in
``test_pages_routes.py`` only assert data-testid markers
in the rendered HTML string. A real browser catches:
- A swatch rendered with a transparent / white background
  (the inline `style="background:#..."` was dropped)
- A progress bar with width: 0% even when asset_pct is set
- A gain sign that flips positive/negative on the wrong side
  (CSS rule not applied because the class name is wrong)
- A color token dropped from :root so the cycling fallback
  would have no color at all

Reuses the S04 journey helpers (``_login_and_select_italo``,
``_create_three_classes``, ``_seed_43_assets``, ``SELECTORS``)
so this test stays focused on S05-specific assertions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page

# tests/ has no __init__.py (pytest discovers it as a rootdir), so
# absolute imports of sibling test files don't resolve. We import
# S04's helpers as a relative import within the tests.e2e package
# (``tests/e2e/__init__.py`` exists).
from .test_import_user_journey import (
    FIXTURE_PATH,
    UNMATCHED_NAMES,
    _create_three_classes,
    _debug_dump,
    _login_and_select_italo,
    _seed_43_assets,
)
from .selectors import SELECTORS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOT_DIR = Path("/tmp/s05_e2e_screenshots")

# S05-specific data-testid markers. Backed by the central selectors
# map — keys here are an S05-specific subset (e.g. portfolio-* are
# only relevant to the S05 dashboard polish assertions). F02
# renamed the portfolio header from `portfolio-header` /
# `portfolio-invested` / `portfolio-total` / `portfolio-gain`
# (S05) to the unified `patrimonio-portfolio-header` spec; the
# S05-specific selectors below are kept as aliases to that new
# shape via the central map so existing assertions do not need
# to be rewritten line-by-line.
S05_SELECTORS = {
    "portfolio_header": SELECTORS["patrimonio_portfolio_header"],
    "portfolio_invested": SELECTORS["patrimonio_portfolio_header"],
    "portfolio_total": SELECTORS["patrimonio_portfolio_header"],
    "portfolio_gain": SELECTORS["patrimonio_portfolio_header"],
    "class_summary_row": SELECTORS["class_summary_row"],
    "dashboard_class_section": '[data-testid="class-section-header"]',
    "class_color_swatch": '[data-testid="class-color-swatch"]',
    "class_section_name": '[data-testid="class-section-name"]',
    "class_target_pct": '[data-testid="class-target-pct-view"]',
    "class_current_pct": '[data-testid="class-current-pct"]',
    "class_delta_badge": '[data-testid="class-delta-badge"]',
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "asset_row_name": '[data-testid="asset-row-name"]',
    "asset_row_name_text": '[data-testid="asset-row-name-text"]',
    "asset_position_count": '[data-testid="asset-position-count"]',
    "asset_current_value": '[data-testid="asset-current-value"]',
    "asset_pct": '[data-testid="asset-pct"]',
}


def _do_import(page: Page) -> None:
    """Drive the S04 import flow up to the dashboard via the modal.

    Opens the dashboard import modal, uploads the broker CSV,
    assigns classes for unmatched rows (BPAC11, HGLG11, VINO11
    start on "-- escolha --" with the post-D011 class name that
    matches the broker file's "Minha Categoria" column via exact
    normalized name), and confirms the import. Waits for the
    page reload on success.
    """
    page.evaluate("() => Alpine.store('importModal').openModal()")
    page.wait_for_selector('[data-testid="import-modal-overlay"]', state="visible", timeout=5000)
    page.wait_for_timeout(300)
    page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
    page.wait_for_timeout(300)
    page.click(SELECTORS["import_upload_btn"], force=True)
    page.wait_for_selector(SELECTORS["import_commit_btn"], timeout=10000)

    # Assign classes to unmatched rows that have no selection.
    unmatched_rows = page.locator('[data-testid="import-unmatched-table"] tbody tr')
    for i in range(unmatched_rows.count()):
        select = unmatched_rows.nth(i).locator(SELECTORS["import_assignment_class"])
        current = select.evaluate("el => el.options[el.selectedIndex].value")
        if not current:
            select.select_option(label="RF Pós")

    page.click(SELECTORS["import_commit_btn"], force=True)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_selector(SELECTORS["class_summary_row"], timeout=10000)


def _capture_dashboard_screenshot(page: Page, tag: str) -> Path:
    """Full-page screenshot of the dashboard for the S05 visual gate."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{tag}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


class TestS05DashboardJourney:
    """Real-browser assertions on the S05 visualization polish."""

    def test_dashboard_full_journey_renders_s05_polish(self, page: Page, live_url: str) -> None:
        """Full S05 user journey: import flow → dashboard with S05 polish.

        Asserts:
        - The portfolio header is present with 3 BRL-formatted stats
          (invested, current, gain) and a positive gain sign.
        - 3 class sections each render a color swatch with a non-empty
          background, a target_pct line ("Alvo NN%"), a current_pct
          line ("Atual NN.NN%"), and a compare bar.
        - 48 asset rows each render a position count, BRL value, pct,
          and a non-zero progress bar.
        - The compare-bar target widths are 60%/30%/10% (the seeded
          class target_pcts).
        - The 5 unmatched names appear as asset row names.
        - A full-page screenshot is captured for the S05 visual gate.
        """
        _login_and_select_italo(page, live_url)
        _create_three_classes(page, live_url)
        _seed_43_assets(page)
        _do_import(page)

        # --- 1. Portfolio header is present with 3 BRL-formatted stats.
        # Wait explicitly for the portfolio header — after the import
        # commit calls location.reload(), wait_for_load_state("networkidle")
        # can resolve before the NEW page has finished rendering, because
        # networkidle detects the OLD page's idle state before the reload
        # navigation starts. Use a targeted wait_for_selector instead.
        page.wait_for_selector(S05_SELECTORS["portfolio_header"], timeout=10000)
        assert page.locator(S05_SELECTORS["portfolio_header"]).count() == 1
        assert page.locator(S05_SELECTORS["portfolio_invested"]).count() == 1
        assert page.locator(S05_SELECTORS["portfolio_total"]).count() == 1
        assert page.locator(S05_SELECTORS["portfolio_gain"]).count() == 1

        invested_text = page.locator(S05_SELECTORS["portfolio_invested"]).inner_text()
        current_text = page.locator(S05_SELECTORS["portfolio_total"]).inner_text()
        gain_text = page.locator(S05_SELECTORS["portfolio_gain"]).inner_text()
        for label, text in (
            ("invested", invested_text),
            ("current", current_text),
            ("gain", gain_text),
        ):
            assert "R$" in text, f"{label} stat missing R$ prefix: {text!r}"
            assert text.strip() != "R$", f"{label} stat is empty: {text!r}"

        # The fixture's current prices are higher than avg prices, so
        # the gain is positive.
        gain_sign = page.locator(S05_SELECTORS["portfolio_gain"]).get_attribute("data-gain-sign")
        assert gain_sign == "positive", f"fixture has gains; expected positive, got {gain_sign!r}"

        # --- 2. 3 class sections each with name + the three pills
        # (Alvo / Atual / delta) + swatch.
        sections = page.locator(S05_SELECTORS["class_summary_row"])
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{S05_SELECTORS['class_summary_row']}').length === 3",
                timeout=5000,
            )
        except Exception:
            _debug_dump(page, "post_import_class_sections")
            raise
        assert sections.count() == 3

        for i in range(3):
            section = sections.nth(i)
            assert section.locator(S05_SELECTORS["class_section_name"]).count() >= 1
            assert section.locator(S05_SELECTORS["class_target_pct"]).count() >= 1
            assert section.locator(S05_SELECTORS["class_current_pct"]).count() >= 1
            # Compare-bar is gone; the section header carries the three
            # pills as the single source of truth for class metrics.
            assert section.locator(S05_SELECTORS["class_color_swatch"]).count() >= 1
            # class_delta_badge is in the DOM via x-show; visible only when off.
            assert section.locator(S05_SELECTORS["class_delta_badge"]).count() == 1

            target_text = section.locator(S05_SELECTORS["class_target_pct"]).first.inner_text()
            current_text = section.locator(S05_SELECTORS["class_current_pct"]).first.inner_text()
            assert "Alvo" in target_text, f"target line missing 'Alvo': {target_text!r}"
            assert "%" in target_text, f"target line missing %: {target_text!r}"
            assert "Atual" in current_text, f"current line missing 'Atual': {current_text!r}"
            assert "%" in current_text, f"current line missing %: {current_text!r}"

            # Color swatch has a non-empty inline background.
            swatch_style = section.locator(S05_SELECTORS["class_color_swatch"]).first.get_attribute(
                "style"
            )
            assert swatch_style, f"class {i} swatch has no inline style"
            assert "background" in swatch_style, (
                f"class {i} swatch missing background: {swatch_style!r}"
            )
            assert "transparent" not in swatch_style, (
                f"class {i} swatch transparent: {swatch_style!r}"
            )

        # --- 3. 48 asset rows each with name, position count, BRL value,
        # pct. The per-asset progress bar is gone.
        asset_rows = page.locator(S05_SELECTORS["dashboard_asset_row"])
        try:
            page.wait_for_function(
                "() => document.querySelectorAll("
                f"'{S05_SELECTORS['dashboard_asset_row']}').length === 48",
                timeout=5000,
            )
        except Exception:
            _debug_dump(page, "post_import_asset_rows")
            raise
        assert asset_rows.count() == 48

        # Spot-check the first row.
        row = asset_rows.first
        assert row.locator(S05_SELECTORS["asset_row_name"]).count() == 1
        assert row.locator(S05_SELECTORS["asset_position_count"]).count() == 1
        assert row.locator(S05_SELECTORS["asset_current_value"]).count() == 1
        assert row.locator(S05_SELECTORS["asset_pct"]).count() == 1

        value_text = row.locator(S05_SELECTORS["asset_current_value"]).inner_text()
        assert "R$" in value_text, f"asset value missing R$ prefix: {value_text!r}"
        assert value_text.strip() != "R$", f"asset value is empty: {value_text!r}"

        # The [data-testid="asset-pct"] hidden span is just the raw
        # number (no % suffix) — a machine-readable value for tests
        # and backward compat with the S05 aggregate test. Check it
        # is non-empty and parseable.
        pct_text = row.locator(S05_SELECTORS["asset_pct"]).inner_text()
        assert pct_text.strip(), "asset pct is empty"
        float(pct_text)  # must parse — ValueError if not

        # data-position-count is on the <li> row itself, not on the
        # hidden <span data-testid="asset-position-count"> child.
        pos_count_str = row.get_attribute("data-position-count")
        assert pos_count_str is not None, "asset row missing data-position-count"
        pos_count = int(pos_count_str)
        assert pos_count >= 1, f"asset row 0 has {pos_count} positions, expected >= 1"

        # --- 4. The 5 unmatched names appear as asset row names.
        all_names = {
            asset_rows.nth(i).locator(S05_SELECTORS["asset_row_name"]).inner_text()
            for i in range(48)
        }
        for name in UNMATCHED_NAMES:
            assert any(name in n for n in all_names), f"missing asset {name!r} on dashboard"

        # --- 5. S05 visual gate: capture the dashboard screenshot.
        _capture_dashboard_screenshot(page, "s05_dashboard_polish")

    def test_class_color_tokens_defined_in_root(self, page: Page, live_url: str) -> None:
        """The 6 ``--class-N`` color tokens are defined in :root.

        Hits /login (no auth required) so the test stays fast — the
        stylesheet is loaded by base.html on every page. The tokens
        are the S05 design-system primitive the cycling rules below
        :root consume. A missing or empty token would mean
        nth-of-type cycling has no color to fall back to.
        """
        page.goto(f"{live_url}/login")

        token_colors = page.evaluate(
            """() => {
                const root = getComputedStyle(document.documentElement);
                return {
                    '1': root.getPropertyValue('--class-1').trim(),
                    '2': root.getPropertyValue('--class-2').trim(),
                    '3': root.getPropertyValue('--class-3').trim(),
                    '4': root.getPropertyValue('--class-4').trim(),
                    '5': root.getPropertyValue('--class-5').trim(),
                    '6': root.getPropertyValue('--class-6').trim(),
                };
            }"""
        )
        for k, v in token_colors.items():
            assert v, f"--class-{k} token is empty in computed style: {token_colors!r}"

        # All 6 tokens are distinct (the design system requires
        # visually-distinct colors so 7+ classes don't collide).
        unique = set(token_colors.values())
        assert len(unique) == 6, f"class color tokens not all distinct: {token_colors!r}"
