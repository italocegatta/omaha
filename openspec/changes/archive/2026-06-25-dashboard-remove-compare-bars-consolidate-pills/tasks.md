## 1. Alpine logic updates

- [x] 1.1 Add `classCurrentStatus` getter to the `classSection` Alpine component in `src/omaha/templates/dashboard.html` (after the existing `classDelta` getter at line 941). Returns `'ok'` when `Math.abs(this.classCurrentPct - this.classTargetPct) <= 0.01`, else `'off'`.
- [x] 1.2 Drop the `if (this.editingAssetId === null) return '';` guard from the `classDeltaMessage` getter (line 950) so the Sobra/Falta pill renders in steady state, not only during inline asset edit. Keep the `Math.abs(delta) <= 0.01` guard as the sole condition for hiding the pill.

## 2. Template restructure

- [x] 2.1 Rewrite the `.class-section-header` block (`src/omaha/templates/dashboard.html:107-142`) to render the inline pill layout: chevron, colour swatch, class name, three pills (`Alvo`, `Atual`, delta), × button. Replace the `.class-section-stats` vertical stack (lines 117-141) with a horizontal pill row. Preserve `data-testid="class-target-pct-view"` on the `Alvo` pill, `data-testid="class-current-pct"` on the `Atual` pill, and `data-testid="class-delta-badge"` on the delta pill.
- [x] 2.2 Bind the `Atual` pill modifier class with `:class="'pct-current-pill--' + classCurrentStatus"` so the green/red status colour reflects the live deviation.
- [x] 2.3 Remove the `<div class="compare-bar" data-testid="class-compare-bar">` block (`src/omaha/templates/dashboard.html:170-177`).
- [x] 2.4 Remove the `<tr class="asset-group-header" data-testid="asset-group-header">` row from the asset table (`src/omaha/templates/dashboard.html:199-211`), including its inner `<span data-testid="asset-group-header-alert">` element.
- [x] 2.5 Remove the `<tr>` wrapping `<div class="asset-progress-bar" data-testid="asset-progress-bar">` from each asset row's per-row `<tbody>` (`src/omaha/templates/dashboard.html:300-306`).
- [x] 2.6 Drop the `--i` inline style on each `<tr data-testid="dashboard-asset-row">` (`src/omaha/templates/dashboard.html:215` — currently `:style="'--i:' + idx"`) since no CSS rule consumes it after the progress bar is gone.

## 3. CSS cleanup and additions

- [x] 3.1 Remove the colour-cycling rules that target the compare bar fill (`.dashboard-distribution .class-section:nth-of-type(6n+N) .compare-bar-current-fill` at `src/omaha/static/app.css:79-105`).
- [x] 3.2 Remove the `.compare-bar`, `.compare-bar-track`, `.compare-bar-fill`, `.compare-bar-target-fill`, `.compare-bar-current-fill` blocks (`src/omaha/static/app.css:858-868`).
- [x] 3.3 Remove the `.asset-progress-bar` and `.asset-progress-fill` blocks (`src/omaha/static/app.css:893-897`).
- [x] 3.4 Remove the `@keyframes fill-bar` and `@keyframes fill-asset` blocks plus the staggered delay rule that uses `--i` (`src/omaha/static/app.css:905-926`).
- [x] 3.5 Remove the dead `.pct-target--view`, `.pct-target--edit`, and `.class-delta-badge` / `--short` / `--long` blocks (`src/omaha/static/app.css:1217-1252`) — the legacy class-section-stats markup that consumed them is gone.
- [x] 3.6 Add the new pill styles: `.pct-target-pill` (dashed neutral border, click affordance), `.pct-current-pill--ok` (green tint, `--alert-ok`), `.pct-current-pill--off` (red tint, `--alert-danger`), `.pct-delta-pill--short` (red `--negative` for "Falta"), `.pct-delta-pill--long` (green `--accent` for "Sobra"). Sit these next to the existing `.class-inline-edit-input` rule for proximity.
- [x] 3.7 Rewrite `.class-section-delete-btn` (`src/omaha/static/app.css:1471-1495`) so the × is `color: var(--negative)` always, with a visible 1px border in `color-mix(in srgb, var(--negative) 30%, transparent)`, and a soft background `color-mix(in srgb, var(--negative) 6%, var(--surface))`. Hover state darkens both border and background.

## 4. Test updates

- [x] 4.1 Update `tests/test_pages_routes.py:343-345` (which currently asserts `class-target-pct-view`, `class-current-pct`, `class-compare-bar` are in the body) — keep the first two, invert the third to `assert ... not in body`.
- [x] 4.2 Update `tests/test_pages_routes.py:353` (asserts `asset-progress-bar` in body) — invert to `not in body`.
- [x] 4.3 Update `tests/test_pages_routes.py:369` (asserts `class-delta-badge` in body) — the test-id stays in the DOM but only when the per-class sum is off. Either seed the test fixture with an off-sum class (preferred — already in place for the portfolio sticky alert), or make the assertion conditional on the seeded data.
- [x] 4.4 Update `tests/test_pages_routes.py:385-386` (asserts `compare-bar-target-fill` and `compare-bar-current-fill` in body) — invert both to `not in body`.
- [x] 4.5 Update `tests/e2e/test_user_journey_rebalance.py` — remove `class_compare_bar` and `asset_progress_bar` from the `S05_SELECTORS` dict (lines 71, 78), remove the "Compare-bar target widths render as 60%/30%/10%" assertion block (lines 214-236), and remove the "Progress bar width is a positive percentage" assertion block (lines 281-297).
- [x] 4.6 Update `tests/e2e/test_user_journey_rebalance.py` — in the per-class section loop (lines 187-212), drop the `class_compare_bar` count assertion. Add an assertion that the `Alvo`, `Atual`, and delta pills are present in the section header.
- [x] 4.7 Update `tests/e2e/test_asset_table.py:39` — remove `asset_group_header_alert` from the selectors dict and any assertions that consume it.
- [x] 4.8 Verify `tests/e2e/test_inline_edit.py:81` — the `class_delta_badge` selector already points at `data-testid="class-delta-badge"`. Since the test-id is preserved, no change is needed unless the assertion relied on the previous "only-during-inline-edit" visibility rule. If so, relax to "visible in steady state when class is off".
- [x] 4.9 Verify `tests/bdd/step_defs/target_steps.py:36` and `tests/bdd/step_defs/common_steps.py:178,182` — both reference `data-testid="class-target-pct-view"`. The test-id is preserved on the new `Alvo` pill, so no change is needed.

## 5. Verification

- [x] 5.1 Run `uv run task lint` (ruff + prek) and fix any formatting / lint regressions.
- [x] 5.2 Run `uv run task test-unit` and confirm no regression.
- [x] 5.3 Run `uv run task test-integration` and confirm the updated `tests/test_pages_routes.py` assertions flip cleanly.
- [x] 5.4 Run `uv run task test-e2e` and confirm the S05 journey passes with the dropped selectors and added pill assertions.
- [x] 5.5 Run `uv run task test-bdd` and confirm the BDD scenarios using `class-target-pct-view` still pass.
- [x] 5.6 Run `uv run task db-reset` to bring the dev DB to the populated default state (Italo: 6 classes + 48 assets + 47 positions).
- [x] 5.7 Run `uv run task serve`, open `http://192.168.1.6:8000` from a client on the LAN, and verify visually: no compare bars, no per-asset progress bars, no `asset-group-header` row, three pills inline in each class section header (`Alvo` dashed / `Atual` green or red / delta when off), × button visibly red in steady state, Sobra/Falta pill present whenever a class sum deviates from 100%.
