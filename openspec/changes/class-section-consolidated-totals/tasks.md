## 1. CSS variables + grid + colgroup (the alignment contract)

- [ ] 1.1 `src/omaha/static/app.css` — add `:root` block with the 8 `--col-*` CSS variables (`--col-ativo: 2.5fr`, `--col-classe: 1.5fr`, `--col-qtd: 0.6fr`, `--col-valor: 1.2fr`, `--col-alvo-classe: 1fr`, `--col-atual-classe: 1fr`, `--col-alvo-total: 1fr`, `--col-atual-total: 1fr`).
- [ ] 1.2 `src/omaha/static/app.css` — switch `.class-section-header` from `display: flex` to `display: grid` with `grid-template-columns: var(--col-ativo) var(--col-classe) var(--col-qtd) var(--col-valor) var(--col-alvo-classe) var(--col-atual-classe) var(--col-alvo-total) var(--col-atual-total)`. Keep `align-items: center; gap: 0.5rem; cursor: pointer; user-select: none;`.
- [ ] 1.3 `src/omaha/static/app.css` — add `.hdr-leading { grid-column: 1 / span 3; display: flex; align-items: center; gap: 0.6rem; }`, `.hdr-valor { grid-column: 4; text-align: right; font-variant-numeric: tabular-nums; font-weight: 500; }`, `.hdr-delta { grid-column: 5; justify-self: start; }`, `.hdr-alvo { grid-column: 7; justify-self: start; }`, `.hdr-atual { grid-column: 8; justify-self: start; }`.
- [ ] 1.4 `src/omaha/static/app.css` — `.asset-table` add `table-layout: fixed; width: 100%;`. `.asset-table td` add `overflow-wrap: break-word;`.
- [ ] 1.5 `src/omaha/static/app.css` — add `.asset-table col:nth-child(1) { width: var(--col-ativo); }` through `nth-child(8) { width: var(--col-atual-total); }` (8 selectors).
- [ ] 1.6 `src/omaha/static/app.css` — drop the legacy `.asset-table th:nth-child(N) { width: NN%; }` rules (the percentage table from `dashboard-inline-editing` "Column widths" requirement) — superseded by the `<colgroup>` widths. Also drop the legacy `.asset-table th { transition: width 200ms; }` rule — not reliably animatable on `<col>`-driven widths.

## 2. Template restructure (`dashboard.html`)

- [ ] 2.1 `src/omaha/templates/dashboard.html` — `class_data` blob (line ~102): add `"current_value": (c.current_value | float)` alongside the existing fields.
- [ ] 2.2 `src/omaha/templates/dashboard.html` — restructure `.class-section-header` (lines 107-140) into 5 sibling children: `.hdr-leading` (chevron + swatch + name + ×), `.hdr-valor`, `.hdr-delta`, `.hdr-alvo`, `.hdr-atual`. Move the × button inside `.hdr-leading` after the class name span.
- [ ] 2.3 `src/omaha/templates/dashboard.html` — add `<colgroup>` with 8 `<col class="col-N">` elements inside `<table class="asset-table">` (line 175), one per column, before the existing `<thead>`.
- [ ] 2.4 `src/omaha/templates/dashboard.html` — keep all existing `data-testid` attributes on the existing pills (`class-target-pct-view`, `class-current-pct`, `class-delta-badge`, `class-delete-btn`, etc.) unchanged. Add `data-testid="class-total-value"` on the new `.hdr-valor` span.

## 3. Alpine `classSection` factory

- [ ] 3.1 `src/omaha/templates/dashboard.html` — `classSection(initial)` factory: add `classCurrentValue: initial.current_value,` alongside the existing `classCurrentPct: initial.current_pct,`.
- [ ] 3.2 `src/omaha/templates/dashboard.html` — `classSection(initial)`: add `formatBRLCompact: function (value) { ... }` (BRL with `minimumFractionDigits: 0, maximumFractionDigits: 0`). Reuse `formatBRL` pattern but with 0 decimals.

## 4. Integration tests (TestClient)

- [ ] 4.1 `tests/test_pages_routes.py` — new scenario: `test_class_section_renders_consolidated_value` — for a class with assets summing to a known `current_value`, the rendered HTML at `data-testid="class-total-value"` contains the BRL string with no decimals (e.g. `R$ 9.389`).
- [ ] 4.2 `tests/test_pages_routes.py` — new scenario: `test_class_section_renders_em_dash_when_empty` — for a class with no assets, the rendered HTML at `data-testid="class-total-value"` contains `—` (NOT `R$ 0`).
- [ ] 4.3 `tests/test_pages_routes.py` — new scenario: `test_class_section_renders_pct_with_two_decimals_when_empty` — for a class with no assets, the rendered HTML at `data-testid="class-current-pct"` contains `Atual 0.00%`.
- [ ] 4.4 `tests/test_pages_routes.py` — new scenario: `test_class_section_delete_btn_precedes_stats` — in the rendered HTML, the `class-delete-btn` element comes BEFORE `class-total-value` in DOM order (inside `.class-section-header`).
- [ ] 4.5 `tests/test_pages_routes.py` — new scenario: `test_asset_table_has_colgroup` — the rendered HTML contains `<colgroup>` with exactly 8 `<col>` elements inside `<table class="asset-table">`.
- [ ] 4.6 `tests/test_pages_routes.py` — new scenario: `test_class_data_blob_exposes_current_value` — assert the classData JSON embedded in the Alpine `x-data='classSection(...)'` attribute carries `current_value` as a numeric field (not undefined).
- [ ] 4.7 `tests/test_pages_routes.py` — run `uv run task test-integration` — green.

## 5. E2E visual gate (Playwright)

- [ ] 5.1 `tests/e2e/test_visual_gate.py` (or new file `test_class_section_alignment.py`) — new scenario: `test_class_total_value_aligned_with_valor_th` — for each class section, assert `getBoundingClientRect().left` of `data-testid="class-total-value"` is within ±1px of `getBoundingClientRect().left` of `data-testid="asset-table-th-current-value"`.
- [ ] 5.2 Same file — new scenario: `test_class_alvo_pill_aligned_with_alvo_total_th` — assert alignment between `class-target-pct-view` and `asset-table-th-target-pct-total` (±1px).
- [ ] 5.3 Same file — new scenario: `test_class_atual_pill_aligned_with_atual_total_th` — assert alignment between `class-current-pct` and `asset-table-th-current-pct-total` (±1px).
- [ ] 5.4 Same file — new scenario: `test_class_delta_pill_aligned_with_alvo_classe_th` (when delta pill is rendered) — assert alignment between `class-delta-badge` and `asset-table-th-target-pct-class` (±1px).
- [ ] 5.5 Same file — new scenario: `test_class_total_value_visible_when_collapsed` — click class header to collapse; assert `class-total-value`, `class-current-pct`, `class-target-pct-view` are still visible while `<table class="asset-table">` is hidden (`class-section-body--collapsed` present).
- [ ] 5.6 Run `uv run task test-e2e` — green.

## 6. Visual + manual verification

- [ ] 6.1 `uv run task db-reset` — confirm DB has Italo + 6 classes + 48 assets + 47 positions.
- [ ] 6.2 `uv run task serve` — manual browser pass: login as Italo → land on `/` showing Italo's dashboard.
- [ ] 6.3 Manual browser pass: for each class section, the consolidated `Valor`, `Alvo`, `Atual` pills (and `Sobra/Falta` when off) align visually with the `Valor`, `Alvo % total`, `Atual % total` columns (and `Alvo % classe` column) of the asset table below.
- [ ] 6.4 Manual browser pass: collapse a class section — header (with all 5 cells) stays visible, asset table hides.
- [ ] 6.5 Manual browser pass: hover the × button — still red, still darkens on hover.
- [ ] 6.6 Manual browser pass: click `Alvo NN%` pill — inline editor opens (existing edit flow unchanged).
- [ ] 6.7 DevTools pass: change `--col-ativo` value in `:root` → both header and table re-align on next layout (sanity check the single-source-of-truth contract).
- [ ] 6.8 Mobile (resize browser <480px): header stacks gracefully; pills remain readable; × remains tappable.

## 7. Lint + check + delivery

- [ ] 7.1 `uv run task check` (lint + test-unit) — green.
- [ ] 7.2 `uv run task test-integration` — green.
- [ ] 7.3 `uv run task test-e2e` — green.
- [ ] 7.4 Run `refresh-for-test` skill (or `uv run task db-reset` + `uv run task serve` restart + `/healthz` smoke) before reporting done.
- [ ] 7.5 Report LAN URL + DB state to the user; confirm dashboard renders the new header layout and all alignment assertions hold.
