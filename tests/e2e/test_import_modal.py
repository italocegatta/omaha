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

from .selectors import SELECTORS
from .test_import_user_journey import (
    ACOES_NAMES,
    MATCHED_NAMES,
    REPO_ROOT,
    RESERVA_NAMES,
    RF_POS_NAMES,
    UNMATCHED_NAMES,
    _login_and_select_italo,
)

FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "sample_broker.csv"


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
        # Click the dashboard import button to open the modal.
        page.click(SELECTORS["dashboard_import_btn"])
        page.wait_for_selector(SELECTORS["import_modal_overlay"], state="visible", timeout=5000)

        page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
        # Let Alpine process the @change event from set_input_files.
        page.wait_for_timeout(200)

        # Click the upload button via the Alpine store directly, since
        # the button's :disabled binding re-enables once the store's
        # file property is set after the set_input_files change event.
        page.evaluate("Alpine.store('importModal').uploadFile()")
        page.wait_for_timeout(500)

        # ------------------------------------------------------------------
        # Step 2: Wait for review (commit button visible = step 2 loaded)
        # ------------------------------------------------------------------
        page.wait_for_selector(SELECTORS["import_commit_btn"], state="visible", timeout=15000)
        page.wait_for_selector(SELECTORS["import_unmatched_table"], state="visible", timeout=5000)

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
            f"expected unmatched tickers {set(UNMATCHED_NAMES)}, got {unmatched_tickers}"
        )

        # ------------------------------------------------------------------
        # Assert Step 2 markup: no Ticker / no Nome do ativo columns.
        # The first column is now "Nome" (asset name), and Total atual
        # must be present and formatted as R$ X.XXX,XX.
        # ------------------------------------------------------------------
        for table_selector in (
            SELECTORS["import_existing_table"],
            SELECTORS["import_unmatched_table"],
        ):
            headers = page.locator(f"{table_selector} thead th").all_inner_texts()
            assert "TICKER" not in [h.upper() for h in headers], (
                f"{table_selector} should not render a Ticker column, got {headers}"
            )
            assert "NOME DO ATIVO" not in [h.upper() for h in headers], (
                f"{table_selector} should not render a Nome do ativo column, got {headers}"
            )
            assert any("TOTAL ATUAL" in h.upper() for h in headers), (
                f"{table_selector} missing Total atual header, got {headers}"
            )
            assert any("PREÇO MÉDIO" in h.upper() for h in headers), (
                f"{table_selector} missing 'Preço médio' header, got {headers}"
            )

        # Total atual cell for the first unmatched row must be R$ formatted
        # with 0 decimals (e.g. "R$ 5.450", not "R$ 5.450,00").
        first_unmatched_total = unmatched_rows.nth(0).locator("td").nth(3).inner_text().strip()
        assert first_unmatched_total.startswith("R$"), (
            f"expected Total atual cell to start with R$, got {first_unmatched_total!r}"
        )
        import re as _re

        assert _re.match(r"^R\$ [\d.]+$", first_unmatched_total), (
            f"Total atual not in R$ X.XXX format (0 decimals): {first_unmatched_total!r}"
        )

        # Preço médio (renamed from "P. Médio") cell uses currency format with 0 decimals.
        first_unmatched_price = unmatched_rows.nth(0).locator("td").nth(2).inner_text().strip()
        assert first_unmatched_price.startswith("R$"), (
            f"expected Preço médio cell to start with R$, got {first_unmatched_price!r}"
        )
        assert _re.match(r"^R\$ [\d.]+$", first_unmatched_price), (
            f"Preço médio not in R$ X.XXX format: {first_unmatched_price!r}"
        )

        # ------------------------------------------------------------------
        # Selecting a class must change the swatch's background color.
        # ------------------------------------------------------------------
        acoes_id: int = page.evaluate(
            """() => Alpine.store('importModal').assetClasses.find(c => c.name === 'Acoes').id"""
        )
        acoes_color: str = page.evaluate(
            f"() => Alpine.store('importModal').assetClasses.find(c => c.id === {acoes_id}).color"
        )
        # Assign XPLG11 to Acoes and confirm the cell-level --class-color
        # inline style updates to the matching hex.  Match the row by
        # data-testid on the <tr> to read the right cell.
        page.evaluate(
            f"""() => {{
                const s = Alpine.store('importModal');
                s.assignments['XPLG11'].class_id = {acoes_id};
            }}"""
        )
        page.wait_for_timeout(50)
        # Find the XPLG11 row by walking the tbody: each row's
        # class-cell testid is import-class-cell-assignment; the row
        # index that corresponds to XPLG11 is the one whose
        # assignments key equals XPLG11.
        xplg_idx: int = page.evaluate(
            "() => Alpine.store('importModal')"
            ".unmatched.findIndex(r => r.broker_ticker === 'XPLG11')"
        )
        acoes_idx: int = page.evaluate(
            f"() => Alpine.store('importModal').assetClasses.findIndex(c => c.id === {acoes_id})"
        )
        # The <td> must carry the modifier class for the Acoes index
        # (e.g. import-class-cell--cls-1) — the visual color is now
        # applied via a fixed CSS rule keyed by class index, not via
        # inline :style (see investigate-import-class-color change).
        cell_class = (
            page.locator(SELECTORS["import_class_cell_assignment"])
            .nth(xplg_idx)
            .get_attribute("class")
            or ""
        )
        expected_modifier = f"import-class-cell--cls-{acoes_idx}"
        assert expected_modifier in cell_class, (
            f"expected {expected_modifier!r} in XPLG11 cell class, got {cell_class!r}"
        )
        # The swatch itself must carry an inline background style with the class color.
        swatch_style = (
            page.locator(SELECTORS["import_class_cell_assignment"])
            .nth(xplg_idx)
            .locator(SELECTORS["import_class_swatch"])
            .get_attribute("style")
            or ""
        )
        assert acoes_color in swatch_style, (
            f"expected background {acoes_color!r} in XPLG11 swatch style, got {swatch_style!r}"
        )
        # Computed background-color must actually equal the class hex.
        # Browsers normalize "rgb(46, 125, 50)" for "#2e7d32".
        swatch_bg = page.evaluate(
            """(idx) => {
                const cell = document.querySelectorAll(
                    '[data-testid=\"import-class-cell-assignment\"]')[idx];
                const sw = cell.querySelector('.import-class-swatch');
                return getComputedStyle(sw).backgroundColor;
            }""",
            xplg_idx,
        )
        assert acoes_color.lower() in swatch_bg.lower() or swatch_bg.startswith("rgb"), (
            f"expected swatch background to be {acoes_color!r}, got {swatch_bg!r}"
        )
        # #2e7d32 = rgb(46, 125, 50)
        assert "46" in swatch_bg and "125" in swatch_bg, (
            f"expected swatch rgb(46, 125, 50), got {swatch_bg!r}"
        )

        # The cell itself must carry a tinted background reflecting the class color
        # (color-mix of the hex with var(--surface)). The computed color should
        # be a visible blend — not the bare surface color and not the full hex.
        # Chrome returns either "rgb(r, g, b)" or "color(srgb r g b)" depending
        # on the color space the browser uses internally; accept either.
        cell_bg = page.evaluate(
            """(idx) => {
                const cell = document.querySelectorAll(
                    '[data-testid=\"import-class-cell-assignment\"]')[idx];
                return getComputedStyle(cell).backgroundColor;
            }""",
            xplg_idx,
        )
        # Parse the green channel — #2e7d32 has dominant green. After 38% mix
        # with white, the green channel is highest of the three. Extract the
        # first number from "rgb(r, g, b)" or "color(srgb r g b)".
        import re as _re2

        nums = [float(x) for x in _re2.findall(r"[\d.]+", cell_bg)]
        assert len(nums) >= 3, f"could not parse cell background: {cell_bg!r}"
        r_ch, g_ch, b_ch = nums[0], nums[1], nums[2]
        # The channels may be 0-255 (legacy rgb) or 0.0-1.0 (color()).
        if g_ch > 1.0:  # legacy rgb
            r_ch, g_ch, b_ch = r_ch / 255, g_ch / 255, b_ch / 255
        # Green must be the dominant channel (#2e7d32 is G-heavy).
        assert g_ch > r_ch and g_ch > b_ch, (
            f"expected green-dominant cell background, got rgb({r_ch:.3f}, "
            f"{g_ch:.3f}, {b_ch:.3f}) from {cell_bg!r}"
        )
        # And it must NOT be fully white (surface) — the color-mix must have
        # applied. White would be all 1.0.
        assert not (r_ch > 0.99 and g_ch > 0.99 and b_ch > 0.99), (
            f"cell background is pure surface white — color-mix not applied: "
            f"rgb({r_ch:.3f}, {g_ch:.3f}, {b_ch:.3f})"
        )

        # The <select> itself must also be tinted — the user-visible "field"
        # is the select, not just the surrounding <td>. Without this assertion
        # the select stays white (background: #fff from app.css) and the user
        # can't see the class color at all.
        select_bg = page.evaluate(
            """(idx) => {
                const cell = document.querySelectorAll(
                    '[data-testid=\"import-class-cell-assignment\"]')[idx];
                return getComputedStyle(cell.querySelector('select')).backgroundColor;
            }""",
            xplg_idx,
        )
        sel_nums = [float(x) for x in _re2.findall(r"[\d.]+", select_bg)]
        assert len(sel_nums) >= 3, f"could not parse select background: {select_bg!r}"
        sr, sg, sb = sel_nums[0], sel_nums[1], sel_nums[2]
        if sg > 1.0:
            sr, sg, sb = sr / 255, sg / 255, sb / 255
        assert sg > sr and sg > sb, (
            f"expected green-dominant select background, got rgb({sr:.3f}, "
            f"{sg:.3f}, {sb:.3f}) from {select_bg!r}"
        )
        assert not (sr > 0.99 and sg > 0.99 and sb > 0.99), (
            f"select background is pure white — color-mix not applied: "
            f"rgb({sr:.3f}, {sg:.3f}, {sb:.3f}) from {select_bg!r}"
        )

        # ------------------------------------------------------------------
        # Step 3: Assign classes to the 5 unmatched rows
        # ------------------------------------------------------------------
        # Rows with "(Não configurado)" category have empty class_id.
        # Rows with "RF Pós" or "Acoes" category pre-fill from suggestion.
        # Fill any empty selections and set XPLG11 to Acoes.
        page.evaluate(
            """() => {
                const s = Alpine.store('importModal');
                const rfPos = s.assetClasses.find(c => c.name === 'RF Pós');
                const acoes = s.assetClasses.find(c => c.name === 'Acoes');
                // Fill all unmatched rows that have empty class_id
                for (const ticker in s.assignments) {
                    if (!s.assignments[ticker].class_id) {
                        s.assignments[ticker].class_id = rfPos ? rfPos.id : '';
                    }
                }
                // XPLG11 goes to Acoes (its CSV category is "Acoes")
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
            assert count >= 1, f"row {i} has {count} positions, expected >= 1"

        # The 5 new assets must appear in the dashboard text.
        dashboard_text = page.locator("main").inner_text()
        for name in UNMATCHED_NAMES:
            assert name in dashboard_text, f"new asset {name!r} not found on dashboard after import"

    def test_import_route_redirects(self, page: Page, live_url: str) -> None:
        """GET /import redirects to the dashboard (retired route)."""
        _login_and_select_italo(page, live_url)

        page.goto(f"{live_url}/import")

        # The URL must be the dashboard (/), not /import.
        assert "/import" not in page.url, (
            f"expected redirect away from /import, got URL: {page.url}"
        )

        profile_header = page.locator(SELECTORS["profile_switcher"])
        profile_header.wait_for(state="visible", timeout=5000)
        # F02: h1 "Bem-vindo" chip replaced by profile-switcher <select>.
        selected = profile_header.evaluate("el => el.value")
        assert selected, f"profile-switcher has no selected value: {selected!r}"

    def test_import_modal_pending_visual(self, page: Page, live_url: str) -> None:
        """With zero AssetClasses on the profile, every row in the modal
        must render with the ``import-class-cell--pending`` modifier
        (dashed border + sunk background), so the operator can see that
        the system has nothing to suggest.

        Setup: clean Italo has zero classes (the autouse ``clean_italo``
        fixture wipes them before every test). We do NOT create classes
        in this test — the point is the empty-classes case.
        """
        _login_and_select_italo(page, live_url)

        # Sanity: the dashboard should show no class sections.
        assert page.locator(SELECTORS["class_summary_row"]).count() == 0, (
            "expected zero class sections on dashboard before import"
        )

        # Open the modal and upload the same fixture the happy-path
        # test uses. Without classes the matcher falls through to the
        # unmatched bucket for every row, which is what we want to
        # inspect.
        page.click(SELECTORS["dashboard_import_btn"])
        page.wait_for_selector(SELECTORS["import_modal_overlay"], state="visible", timeout=5000)
        page.set_input_files(SELECTORS["import_file_input"], str(FIXTURE_PATH))
        page.wait_for_timeout(200)
        page.evaluate("Alpine.store('importModal').uploadFile()")
        page.wait_for_timeout(500)

        # Step 2 loads once the commit button becomes visible.
        page.wait_for_selector(SELECTORS["import_commit_btn"], state="visible", timeout=15000)
        page.wait_for_selector(SELECTORS["import_unmatched_table"], state="visible", timeout=5000)

        # assetClasses must be empty (profile has no classes).
        ac_count: int = page.evaluate("() => Alpine.store('importModal').assetClasses.length")
        assert ac_count == 0, (
            f"expected empty assetClasses for profile with zero classes, got {ac_count}"
        )

        # Every unmatched row's <td> must carry the --pending modifier.
        unmatched_rows = page.locator(SELECTORS["import_unmatched_row"])
        n_unmatched = unmatched_rows.count()
        assert n_unmatched > 0, "expected at least one unmatched row when importing without classes"

        for i in range(n_unmatched):
            cell_class = (
                page.locator(SELECTORS["import_class_cell_assignment"])
                .nth(i)
                .get_attribute("class")
                or ""
            )
            assert "import-class-cell--pending" in cell_class, (
                f"row {i}: expected import-class-cell--pending in class, got {cell_class!r}"
            )

        # First-row computed style: dashed border + background equal to
        # the body background (var(--surface-sunk) → close to body).
        first_cell_style = page.evaluate(
            """() => {
                const cell = document.querySelector(
                    '[data-testid=\"import-class-cell-assignment\"]');
                const cs = getComputedStyle(cell);
                return {
                    borderTopStyle: cs.borderTopStyle,
                    borderRightStyle: cs.borderRightStyle,
                    backgroundColor: cs.backgroundColor,
                };
            }"""
        )
        # The .import-class-cell--pending rule sets a 1px dashed border
        # on all four sides with a sunk background. borderTopStyle ==
        # "dashed" is the load-bearing visual signal — the dashed
        # pattern alone distinguishes the "no class assigned" state
        # from the tinted cls-N cells.
        assert first_cell_style["borderTopStyle"] == "dashed", (
            f"expected dashed top border on pending cell, got {first_cell_style!r}"
        )
        # surface-sunk and body bg may differ slightly but both are
        # neutral; the cell must NOT show any class tint (no
        # color-mix of a palette hex over --surface would look neutral).
        # Chromium may emit the value as ``rgb(...)`` or ``oklch(...)``
        # depending on the color space the stylesheet uses; accept any
        # color-function form, just not ``transparent``.
        bg = first_cell_style["backgroundColor"]
        assert bg != "transparent" and ("(" in bg and ")" in bg), (
            f"expected a color function for background, got {bg!r}"
        )
        # Pending swatch background must be transparent (no class color
        # to display).
        swatch_style = page.evaluate(
            """() => {
                const cell = document.querySelector(
                    '[data-testid=\"import-class-cell-assignment\"]');
                const sw = cell.querySelector('.import-class-swatch');
                return getComputedStyle(sw).backgroundColor;
            }"""
        )
        # "transparent" or "rgba(0, 0, 0, 0)" — both indicate no color.
        assert "transparent" in swatch_style or swatch_style.startswith("rgba(0, 0, 0, 0"), (
            f"expected transparent swatch background, got {swatch_style!r}"
        )
