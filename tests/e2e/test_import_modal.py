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
EMPTY_FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "tiny_empty.csv"


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
    # Clear any stale rows first so this helper is deterministic even if
    # prior state leaked into test DB.
    page.evaluate(
        """async () => {
            const r = await fetch('/classes', { method: 'POST', body: new FormData() });
            if (!r.ok && r.status !== 303) {
                throw new Error('POST /classes clear ' + r.status + ': ' + await r.text());
            }
        }"""
    )
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

        # ------------------------------------------------------------------
        # Step 2: Wait for review (commit button visible = step 2 loaded)
        # ------------------------------------------------------------------
        page.wait_for_selector(SELECTORS["import_commit_btn"], state="visible", timeout=15000)
        page.wait_for_selector(SELECTORS["import_unmatched_table"], state="visible", timeout=5000)
        assert (
            page.locator('[data-testid="import-modal-overlay"] .modal-title').inner_text()
            == "Revisar posições"
        )

        section_headers = page.locator(".import-review-section h3")
        section_text = section_headers.all_inner_texts()
        assert any(text.startswith("Novos") and "5" in text for text in section_text)
        assert any(text.startswith("Alterados") and "43" in text for text in section_text)
        assert not any(text.startswith("Inalterados") for text in section_text)
        assert page.locator(SELECTORS["import_existing_row"]).count() == 43
        changed_trigger = (
            page.locator(SELECTORS["import_existing_row"])
            .first.locator(".import-diff-trigger")
            .first
        )
        assert changed_trigger.count() == 1
        disclosure = changed_trigger.locator("xpath=following-sibling::span")
        incoming_text = changed_trigger.inner_text()
        changed_trigger.hover()
        assert disclosure.is_visible()
        assert disclosure.evaluate("el => getComputedStyle(el).position") == "absolute"
        assert disclosure.inner_text() == "Não havia posição"
        assert "?" not in disclosure.inner_text()
        assert "Recebido" not in disclosure.inner_text()
        assert "Anterior" not in disclosure.inner_text()
        changed_trigger.focus()
        assert disclosure.is_visible()
        assert disclosure.inner_text() == "Não havia posição"
        assert changed_trigger.inner_text() == incoming_text
        assert (
            page.locator(".modal-panel--wide").evaluate("el => getComputedStyle(el).maxWidth")
            == "1200px"
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

        assert _re.match(r"^R\$[\s\xa0][\d.]+$", first_unmatched_total), (
            f"Total atual not in R$ X.XXX format (0 decimals): {first_unmatched_total!r}"
        )

        # Preço médio (renamed from "P. Médio") cell uses currency format with 0 decimals.
        first_unmatched_price = unmatched_rows.nth(0).locator("td").nth(2).inner_text().strip()
        assert first_unmatched_price.startswith("R$"), (
            f"expected Preço médio cell to start with R$, got {first_unmatched_price!r}"
        )
        assert _re.match(r"^R\$[\s\xa0][\d.]+$", first_unmatched_price), (
            f"Preço médio not in R$ X.XXX format: {first_unmatched_price!r}"
        )

        # ------------------------------------------------------------------
        # Selecting a class keeps class color formatting without a redundant swatch.
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
        # Find XPLG11 through its hidden assignment key, not input order:
        # F65 sorts rendered triage groups on the server.
        xplg_row = page.locator(SELECTORS["import_unmatched_row"]).filter(
            has=page.locator('input[type="hidden"][value="XPLG11"]')
        )
        xplg_cell = xplg_row.locator(SELECTORS["import_class_cell_assignment"])
        acoes_idx: int = page.evaluate(
            f"() => Alpine.store('importModal').assetClasses.findIndex(c => c.id === {acoes_id})"
        )
        # The <td> must carry the modifier class for the Acoes index
        # (e.g. import-class-cell--cls-1) — the visual color is now
        # applied via a fixed CSS rule keyed by class index, not via
        # inline :style (see investigate-import-class-color change).
        cell_class = xplg_cell.get_attribute("class") or ""
        expected_modifier = f"import-class-cell--cls-{acoes_idx}"
        assert expected_modifier in cell_class, (
            f"expected {expected_modifier!r} in XPLG11 cell class, got {cell_class!r}"
        )
        assert xplg_cell.locator(SELECTORS["import_class_swatch"]).count() == 0

        # The cell itself must carry a tinted background reflecting the class color.
        cell_bg = xplg_cell.evaluate("el => getComputedStyle(el).backgroundColor")
        assert cell_bg != "transparent", f"expected tinted cell background, got {cell_bg!r}"

        # The <select> itself must also be tinted — the user-visible "field"
        # is the select, not just the surrounding <td>. Without this assertion
        # the select stays white (background: #fff from app.css) and the user
        # can't see the class color at all.
        select_bg = xplg_cell.locator("select").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        select_style = xplg_cell.locator("select").get_attribute("style") or ""
        assert acoes_color in select_style, (
            f"expected class color {acoes_color!r} in select style, got {select_style!r}"
        )
        assert select_bg != "transparent", f"expected tinted select background, got {select_bg!r}"
        for trade_label in xplg_row.locator(".import-trade-toggle").all():
            trade_style = trade_label.evaluate(
                """el => {
                    const cs = getComputedStyle(el);
                    return {
                        background: cs.backgroundColor, border: cs.borderStyle, color: cs.color
                    };
                }"""
            )
            assert trade_style["background"] in {"rgba(0, 0, 0, 0)", "transparent"}
            assert trade_style["border"] == "none"
            assert trade_style["color"] not in {"rgba(0, 0, 0, 0)", "transparent"}

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

    def test_changed_money_disclosure_is_formatted_overlay(self, page: Page, live_url: str) -> None:
        """Prior money is only value text, formatted, and non-flow on hover/focus."""
        _login_and_select_italo(page, live_url)
        page.evaluate(
            """() => Alpine.store('importModal').openPreview({
                preview_id: 'money-review',
                auto_matched: [{
                    broker_ticker: 'FUND11', name: 'Fundo', qty: '10', avg_price: '100',
                    current_price: '120', invested: '100000', current_value: '3250.00',
                    asset_id: 1, asset_class_id: null, buy_enabled: true,
                    sell_enabled: true, currency_code: 'BRL'
                }],
                unmatched: [], asset_classes: [],
                triage: {
                    new: [], unchanged: [], absent: [],
                    changed: [{
                        broker_ticker: 'FUND11', name: 'Fundo', qty: '10', avg_price: '100',
                        current_price: '120', invested: '100000', current_value: '3250.00',
                        asset_id: 1, asset_class_id: null, buy_enabled: true,
                        sell_enabled: true, currency_code: 'BRL', state: 'changed',
                        changed_fields: [{
                            id: 'total_current', field: 'total_current', label: 'Total atual',
                            unit: 'R$', sign: 'negative', incoming: '3250.00',
                            incoming_value: '3250.00', incoming_display: 'R$ 3.250',
                            previous: '116615.5300', previous_value: '116615.5300',
                            previous_display: 'R$ 116.616'
                        }]
                    }]
                }
            })"""
        )
        page.wait_for_selector('[data-testid="import-existing-row"]', state="visible", timeout=5000)
        trigger = (
            page.locator('[data-testid="import-existing-row"] td')
            .nth(3)
            .locator(".import-diff-trigger")
        )
        assert trigger.inner_text().replace("\xa0", " ") == "R$ 3.250"
        disclosure = trigger.locator("xpath=following-sibling::span")
        trigger.hover()
        assert disclosure.inner_text().replace("\xa0", " ") == "R$ 116.616"
        assert "," not in disclosure.inner_text()
        assert "Recebido" not in disclosure.inner_text()
        assert "Anterior" not in disclosure.inner_text()
        trigger.focus()
        assert disclosure.is_visible()
        assert disclosure.inner_text().replace("\xa0", " ") == "R$ 116.616"
        assert disclosure.evaluate("el => getComputedStyle(el).position") == "absolute"
        clearance = disclosure.evaluate(
            """el => {
                const disclosureRect = el.getBoundingClientRect();
                const tableWrapRect = el.closest('.import-review-table-wrap')
                    .getBoundingClientRect();
                const panelRect = el.closest('.modal-panel').getBoundingClientRect();
                return {
                    disclosureTop: disclosureRect.top,
                    disclosureBottom: disclosureRect.bottom,
                    tableWrapTop: tableWrapRect.top,
                    tableWrapBottom: tableWrapRect.bottom,
                    panelTop: panelRect.top,
                    panelBottom: panelRect.bottom,
                };
            }"""
        )
        assert clearance["disclosureTop"] >= clearance["tableWrapTop"]
        assert clearance["disclosureBottom"] <= clearance["tableWrapBottom"]
        assert clearance["disclosureTop"] >= clearance["panelTop"]
        assert clearance["disclosureBottom"] <= clearance["panelBottom"]

    def test_absent_section_is_read_only_and_excluded_from_confirmation(
        self, page: Page, live_url: str
    ) -> None:
        """Ausentes is visible, profile review only, and absent from commit wire data."""
        _login_and_select_italo(page, live_url)
        result: dict[str, object] = page.evaluate(
            """async () => {
                const store = Alpine.store('importModal');
                store.openPreview({
                    preview_id: 'absent-review',
                    auto_matched: [{
                        broker_ticker: 'IN3', name: 'Entrada', qty: '1',
                        avg_price: '2', current_price: '3', invested: '2',
                        current_value: '3', asset_id: 1, asset_class_id: 1,
                        buy_enabled: true, sell_enabled: true, currency_code: 'BRL'
                    }],
                    unmatched: [],
                    asset_classes: [{id: 1, name: 'Ações', color: 'red'}],
                    triage: {
                        new: [],
                        changed: [],
                        unchanged: [],
                        absent: [{
                            broker_ticker: 'OUT3', name: 'Fora', qty: '4',
                            avg_price: '5', current_price: '6', invested: '20',
                            current_value: '24', asset_id: 2,
                            asset_class_id: 1, asset_class_name: 'Ações',
                            buy_enabled: true, sell_enabled: false,
                            currency_code: 'BRL', state: 'absent',
                            changed_fields: [], read_only: true, committable: false
                        }]
                    }
                });
                await new Promise(resolve => setTimeout(resolve, 0));
                const originalFetch = window.fetch;
                let payload = null;
                window.fetch = (url, options) => {
                    payload = JSON.parse(options.body);
                    return Promise.resolve({
                        ok: false,
                        json: () => Promise.resolve({detail: 'blocked'})
                    });
                };
                try {
                    store.commit();
                    await new Promise(resolve => setTimeout(resolve, 0));
                    return {
                        assignments: Object.keys(store.assignments),
                        payload,
                    };
                } finally {
                    window.fetch = originalFetch;
                }
            }"""
        )
        page.wait_for_selector('[data-testid="import-absent-row"]', state="visible", timeout=5000)
        assert page.locator('[data-testid="import-absent-row"]').count() == 1
        absent_row = page.locator('[data-testid="import-absent-row"]')
        assert absent_row.locator("select").count() == 0
        assert absent_row.locator('input[type="checkbox"]').count() == 0
        assert absent_row.locator('input[type="hidden"]').count() == 0
        assert absent_row.locator(".import-class-swatch").count() == 0
        assert result == {
            "assignments": ["IN3"],
            "payload": {
                "preview_id": "absent-review",
                "assignments": [
                    {
                        "broker_ticker": "IN3",
                        "class_id": 1,
                        "asset_name": "Entrada",
                        "buy_enabled": True,
                        "sell_enabled": True,
                        "currency_code": "BRL",
                    }
                ],
            },
        }

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

    def test_failed_upload_clears_file_input(self, page: Page, live_url: str) -> None:
        """An upload failure leaves input ready to select same file again."""
        _login_and_select_italo(page, live_url)
        page.click(SELECTORS["dashboard_import_btn"])
        page.wait_for_selector(SELECTORS["import_modal_overlay"], state="visible", timeout=5000)

        page.set_input_files(SELECTORS["import_file_input"], str(EMPTY_FIXTURE_PATH))
        page.wait_for_selector(SELECTORS["import_upload_error"], state="visible", timeout=15000)

        assert page.locator(SELECTORS["import_file_input"]).input_value() == ""

    def test_newer_file_selection_ignores_stale_preview_response(
        self, page: Page, live_url: str
    ) -> None:
        """Late preview for an older file cannot replace newer selection."""
        _login_and_select_italo(page, live_url)

        result: dict[str, object] = page.evaluate(
            """async () => {
                const store = Alpine.store('importModal');
                const originalFetch = window.fetch;
                const requests = [];
                const preview = (id) => ({
                    preview_id: id,
                    auto_matched: [],
                    unmatched: [],
                    asset_classes: [],
                });
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                window.fetch = () => new Promise(resolve => requests.push(resolve));

                try {
                    store.openModal();
                    store.selectFile(new File(['old'], 'old.csv', {type: 'text/csv'}));
                    await sleep(175);
                    store.selectFile(new File(['new'], 'new.csv', {type: 'text/csv'}));
                    await sleep(175);
                    if (requests.length !== 2) {
                        throw new Error('expected two preview requests, got ' + requests.length);
                    }

                    requests[0]({ok: true, json: () => Promise.resolve(preview('old'))});
                    await sleep(0);
                    const afterOld = {
                        step: store.step,
                        previewId: store.previewId,
                        fileName: store.file && store.file.name,
                    };

                    requests[1]({ok: true, json: () => Promise.resolve(preview('new'))});
                    await sleep(0);
                    await sleep(0);
                    return {
                        afterOld,
                        step: store.step,
                        previewId: store.previewId,
                        fileName: store.file && store.file.name,
                    };
                } finally {
                    window.fetch = originalFetch;
                }
            }"""
        )

        assert result["afterOld"] == {"step": 1, "previewId": None, "fileName": "new.csv"}
        assert result["step"] == 2
        assert result["previewId"] == "new"
        assert result["fileName"] == "new.csv"

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
        assert page.locator(".import-class-swatch").count() == 0
