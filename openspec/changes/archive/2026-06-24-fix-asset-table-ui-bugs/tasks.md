## 1. Spec delta (this change's `specs/dashboard-inline-editing/spec.md`)

- [x] 1.1 Replace the existing "Seções colapsáveis" requirement with the
      new toggle-based requirement (chevron + `@click="isOpen = !isOpen"`
      + in-memory default-true)
- [x] 1.2 Add a new "Column widths" requirement under the asset table
      requirement, listing the 8 explicit widths and the `transition:
      width 200ms` rule

## 2. `src/omaha/templates/dashboard.html` — `classSection` factory

- [x] 2.1 Replace the `sortedAssets` getter with a `displayAssets`
      array initialised in `init()` from `assets.slice().sort(sortFn(...))`
- [x] 2.2 Update `sortBy(key)` to rebuild `displayAssets` (and to
      remain the only place that touches `sortKey` / `sortDir`)
- [x] 2.3 Refactor the sort comparator into a private helper
      `function sortFn(key, dir)` so `init()` and `sortBy()` share it
- [x] 2.4 Remove `_pinFrozen`, `frozenAssetId`, `frozenIndex` fields,
      and the pinning logic in `startEdit` / `startEditTotal` /
      `cancelEdit` / `cancelEditTotal`
- [x] 2.5 Update `commitEdit` and `commitEditTotal` (the 200-response
      blocks) to mutate `displayAssets[i].target_pct` and
      `target_pct_total` in place — no re-sort
- [x] 2.6 Update `commitEditClassPct` (the 200-response block) to
      recompute each asset's `target_pct_total` in place on
      `displayAssets` (was already done; just retarget the loop)
- [x] 2.7 Change the `<template x-for>` source from `sortedAssets` to
      `displayAssets`

## 3. `src/omaha/templates/dashboard.html` — header + body templates

- [x] 3.1 Add `@click="isOpen = !isOpen"` and
      `data-testid="class-section-header"` on the `<header
      class="class-section-header">` element
- [x] 3.2 Add a `<span class="class-chevron"
      data-testid="class-chevron" :class="{'class-chevron--open':
      isOpen}">▸</span>` as the first child of the header (after the
      `class-color-swatch` is fine; spec just says "in the header")
- [x] 3.3 Add `:class="{'class-section-body--collapsed': !isOpen}"`
      and `x-show="isOpen"` on the `<div class="class-section-body">`
      element (line ~146)

## 4. `src/omaha/static/app.css`

- [x] 4.1 Add `.class-section-body--collapsed { max-height: 0; opacity:
      0; }` to drive the existing transition
- [x] 4.2 Add `.class-chevron { display: inline-block; transition:
      transform 150ms ease-out; }` and `.class-chevron--open { transform:
      rotate(90deg); }`
- [x] 4.3 Add `.asset-table th { transition: width 200ms ease-out; }`
      (or extend the existing `.asset-table th` block)
- [x] 4.4 Add the 8 `.asset-table th:nth-child(N) { width: X%; }`
      declarations (Ativo 24, Classe 18, Qtd 6, Valor 14, Alvo%classe
      11, Atual%classe 11, Alvo%total 9, Atual%total 7) — sum = 100%
- [x] 4.5 Add `text-overflow: ellipsis; overflow: hidden;` to
      `.asset-table th` (defensive — protects against future long
      headers)

## 5. `tests/e2e/test_asset_table.py` — new E2E coverage

- [x] 5.1 Add selector constants for `class_section_header` and
      `class_chevron` to the `S10_SELECTORS` dict
- [x] 5.2 Add `test_patch_does_not_reorder_rows` that seeds one class
      with 3 assets at distinct `target_pct` (e.g. 10, 30, 50), reads
      the `[data-asset-id]` order before, edits the first asset's
      `alvo % classe` to a value that would sort it last (e.g. 80),
      and asserts the order is unchanged after PATCH
- [x] 5.3 Add `test_class_header_toggle_collapses_and_expands_assets`
      that seeds 1 class + 1 asset, clicks the class header, asserts
      `dashboard-asset-row` goes to `not visible`, clicks the header
      again, asserts it goes back to `visible`. Use the chevron's
      `class` attribute (`class-chevron--open` present / absent) as a
      second signal.
- [x] 5.4 Add `test_column_widths_match_spec` that seeds 1 class + 1
      asset, reads `getBoundingClientRect().width` of each `<th>`, and
      asserts the ratios match the spec within ±1px tolerance (24%,
      18%, 6%, 14%, 11%, 11%, 9%, 7%)

## 6. Stale comment cleanup in other E2E tests

- [x] 6.1 Update the comment "Sections collapse on reload (D016); rows
      exist but are not visible." in `tests/e2e/test_user_journey.py:168`
      to reflect the new behaviour: "Sections are expanded by default;
      rows are visible on load. The test asserts DOM presence, not
      visibility."
- [x] 6.2 Update the same stale comment in
      `tests/e2e/test_asset_crud.py:119` (same wording, same fix)
- [x] 6.3 Update the comments "asset-table-view 8.x: class sections
      are always visible." in `tests/e2e/test_visual_gate.py:108`,
      `test_user_journey.py:178`, `test_asset_crud.py:150/179`, and
      `test_inline_edit.py:317` to: "asset-table-view 8.x/fix-asset-table-ui-bugs:
      class sections default to expanded; user can collapse by clicking
      the header."

## 7. Spec alignment + archive

- [ ] 7.1 Run `uv run task lint` — ensure ruff passes on the touched
      files
- [ ] 7.2 Run `uv run task test-unit` — no unit regressions
- [ ] 7.3 Run `uv run task test-integration` — no integration regressions
- [ ] 7.4 Run `uv run task test-e2e` — the two new E2E tests pass
- [ ] 7.5 Archive the change: `openspec archive fix-asset-table-ui-bugs`
      (syncs the spec delta into `openspec/specs/dashboard-inline-editing/spec.md`)
