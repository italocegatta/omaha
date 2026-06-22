## 1. Server: remove sum gate from asset routes

- [x] 1.1 In `src/omaha/routes/assets.py`, drop the `validate_target_pct_sum` call on `POST /api/assets` (around line 294). Keep the per-row range check (0-100). Commit, refresh, return 201.
- [x] 1.2 In `src/omaha/routes/assets.py`, drop the `validate_target_pct_sum` call on `PATCH /api/assets/{id}` (around line 390). Keep the per-row range check. Commit and return 200 unconditionally.
- [x] 1.3 Confirm `omaha.validators.validate_target_pct_sum` is still imported and unchanged — the new alert UI calls it as a formatter, not a gate.

## 2. Server tests: invert 422 → 200

- [x] 2.1 In `tests/test_t99_assets_patch.py`, invert `test_patch_asset_invalid_sum_returns_422` to assert 200 + row mutated on disk + per-class sum exceeding 100. Update any sibling tests that pinned the rejection.
- [x] 2.2 In `tests/test_t03_assets_e2e.py` (and any other route-level tests), search for assertions on 422 from `/api/assets/*` and invert to 201/200 + state assertions.
- [x] 2.3 In `tests/test_t01_asset_target.py`, leave the pure validator tests untouched — the helper is still used as a formatter.

## 3. Frontend: extend `classSum` Alpine store to track per-class deltas

- [x] 3.1 In `src/omaha/templates/dashboard.html`, extend the `classSum` store with a `classDeltas` map keyed by class id, each value carrying `{delta, message, severity}`. Add `register(id, pct)`, `update(id, pct)`, and a `_recalc()` that recomputes per-class and portfolio sums in one pass.
- [x] 3.2 Severity assignment: `abs(delta) <= 0.01` → `'ok'`, `0.01 < abs(delta) <= 5` → `'warn'`, `abs(delta) > 5` → `'danger'`. Export the helper as a pure function on the store for reuse.
- [x] 3.3 Make each `classSection` Alpine component register its `classId` + `classTargetPct` on `init` and update on every successful PATCH (asset or class).

## 4. Frontend: build the asset table HTML

- [x] 4.1 Replace the `<ul class="dashboard-asset-list">` in `dashboard.html` with a `<table class="asset-table">` carrying a `<thead>` with the columns: Ativo, Classe, Qtd, Valor, Alvo % classe, Atual % classe, Alvo % total, Atual % total. Each `<th>` gets `data-testid="asset-table-th-{column}"` and a sort indicator `<span data-testid="asset-table-sort-{column}">`.
- [x] 4.2 Render one `<tr class="asset-group-header" data-testid="asset-group-header">` per class above its assets, carrying the color swatch, name, target %, current %, and the per-class alert badge (`data-testid="asset-group-header-alert"`).
- [x] 4.3 Render one `<tr data-testid="dashboard-asset-row">` per asset with the cell testids preserved (D11 of `design.md`).
- [x] 4.4 Remove the per-class `+ Ativo` button + form. Remove the chevron toggle. Remove the `class-section-body--collapsed` CSS hook.

## 5. Frontend: CSS for the table

- [x] 5.1 In `src/omaha/static/app.css`, add `.asset-table` rules: full-width, fixed layout, sticky `<thead>`, zebra rows, group-header row with colored left border and bold weight.
- [x] 5.2 Add severity color tokens (`--alert-ok`, `--alert-warn`, `--alert-danger`) and apply them to `.asset-allocation-alert` and `.asset-group-header-alert` via class modifiers.
- [x] 5.3 Style the editable cells with hover affordance and an `--editing` modifier for the input state.

## 6. Frontend: sort logic in `assetTable` Alpine component

- [x] 6.1 Add an `assetTable` Alpine component (sibling to `classSection`) that owns `sortKey` (`'class'` default), `sortDir` (`'asc'` default), and a `sortedAssets` computed getter that groups by class and sorts each group by the active key.
- [x] 6.2 Wire each `<th>` `@click` to toggle `sortDir` or set `sortKey` per the two-state rule. Update the sort indicator glyph accordingly.
- [x] 6.3 Wrap the table in `x-data="assetTable()"` and move the per-class iteration off the `classSection` scope to the new top-level scope (the class bands stay in the same row order as the active profile's classes).

## 7. Frontend: inline edit of `alvo % total`

- [x] 7.1 Add a new editable cell for `alvo % total` per row. Click opens an input with `data-testid="asset-target-pct-total-edit-input"`, commit button (`data-testid="asset-target-pct-total-edit-commit"`), cancel button (`data-testid="asset-target-pct-total-edit-cancel"`), and a confirm hint describing the contained effect.
- [x] 7.2 On commit, compute `new_target_pct = total * 100 / classTargetPct` and PATCH to `/api/assets/{id}`. On 200, update the local `target_pct` and `target_pct_total` fields, recompute the per-class sum, update the alert card and the per-class badge via the `classSum` store.
- [x] 7.3 Enforce mutual exclusion with the `alvo % classe` edit cell (only one cell per row in edit mode at a time).

## 8. Frontend: default expanded + stay expanded

- [x] 8.1 Set `isOpen: true` (was `false`) on the `classSection` Alpine component. Remove the chevron markup and its `x-show`/`x-cloak` references.
- [x] 8.2 In `commitEdit` and `commitEditClassPct`, append `self.isOpen = true;` after a successful PATCH so the class group stays open post-edit.
- [x] 8.3 Remove the `class-section-body--collapsed` modifier and its CSS rule.

## 9. Frontend: sticky alert card + per-class badge

- [x] 9.1 Add the sticky alert card markup above the table (inside the "Ativos" section) with `data-testid="asset-allocation-alert"`. The card shows the portfolio total at `data-testid="asset-allocation-alert-portfolio"` and a list of deviating classes at `data-testid="asset-allocation-alert-class"`.
- [x] 9.2 Make the card `position: sticky; top: 0;` and apply severity class modifiers (`.asset-allocation-alert--ok | --warn | --danger`) based on the portfolio delta.
- [x] 9.3 Render or remove the per-class badge on each group header reactively from the `classSum` store's `classDeltas` map.
- [x] 9.4 Hide the card from the DOM when the portfolio delta is within 0.01 of 100% (use `x-show` with the inverse condition, or a conditional `<template>`).

## 10. Frontend: dashboard-level add-asset modal

- [x] 10.1 Add a single `+ Ativo` button above the table with `data-testid="dashboard-add-asset-open"`.
- [x] 10.2 Add a modal component (over the table, behind a backdrop) with `data-testid="dashboard-add-asset-modal"`, a class `<select>` (using the established `x-init $nextTick` + `x-effect` pattern for dynamic options), name input, target_pct input, submit and cancel buttons.
- [x] 10.3 Wire the modal to POST `/api/assets`. On 201, reload the page. On 409/422, surface the error inline. Off-100 sums are accepted (per task 1).

## 11. Test updates for new testids

- [x] 11.1 In `tests/test_t03_pages_routes.py`, update the dashboard testid assertions: drop `data-testid="asset-pct-grid"` (replaced by per-cell layout), drop `data-testid="class-chevron"`, drop `data-testid="class-summary-total"` (moved to alert card), add `data-testid="asset-table"`, `data-testid="asset-group-header"`, `data-testid="asset-allocation-alert"`, `data-testid="dashboard-add-asset-open"`.
- [x] 11.2 In `tests/e2e/test_s01_inline_edit.py`, `test_s03_asset_crud.py`, `test_s03_user_journey.py`, `test_s05_user_journey.py`, `test_s06_full_journey.py`: replace `data-testid="dashboard-add-asset-btn"` clicks with the modal flow. Replace any chevron toggles with the always-visible assumption. Add the new sort and edit-%-total scenarios.
- [x] 11.3 Add new e2e tests covering: (a) table sort by each column, (b) edit `alvo % total` back-solves `alvo % classe`, (c) alert card appears with the right severity for small and large deviations, (d) alert card disappears on convergence, (e) modal add-asset flow.

## 12. Final verification

- [x] 12.1 Run `uv run task lint` and resolve any format / lint regressions.
- [x] 12.2 Run `uv run task test-unit` and confirm all unit tests pass.
- [x] 12.3 Run `uv run task test-integration` and confirm the inverted server tests + updated route tests pass.
- [x] 12.4 Run `uv run task test-e2e` and confirm the new e2e scenarios pass against the dev server bound to `0.0.0.0:8000`.
- [ ] 12.5 Manual smoke: open the dashboard at `http://192.168.1.7:8000`, edit an asset to push the class sum to 110%, confirm the alert card shows "Sobra 10%" in danger color and the per-class badge mirrors. Edit another asset in the same class to bring the sum back to 100%, confirm the card disappears. Edit `alvo % total` on a row, confirm the `alvo % classe` updates via the back-solve and the per-class sum reflects the new value.
