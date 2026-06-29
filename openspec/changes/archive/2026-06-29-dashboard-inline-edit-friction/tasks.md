## 1. Auto-focus + empty-to-zero on the class header editor

- [x] 1.1 In `src/omaha/templates/dashboard.html` add `x-ref="classPctInput"`
      to the `<input type="number">` inside
      `data-testid="class-inline-edit-input"`.
- [x] 1.2 In the matching `startEditClassPct()` factory method
      (~`:1121`), after `this.editClassPctValue = String(...)`, append a
      `this.$nextTick(() => { this.$refs.classPctInput.focus();
      this.$refs.classPctInput.select(); })` call.
- [x] 1.3 In `commitEditClassPct()` (~`:1131`), coerce
      `self.editClassPctValue` to `"0"` when the trimmed string is
      empty before building the PATCH body.

## 2. Auto-focus + empty-to-zero on the per-asset `alvo % classe` editor

- [x] 2.1 Add `x-ref="classPctInput"` to the `<input type="number">`
      inside `data-testid="asset-inline-edit-input"`. *(ref name
      deviated to `assetClassPctInput` — both inputs share the same
      `classSection` Alpine scope and identical ref names would
      collide; `totalPctInput` already distinct.)*
- [x] 2.2 In `startEdit()` (~`:1184`), after
      `this.editingValue = String(asset.target_pct)`, append the
      `$nextTick` focus + select pair.
- [x] 2.3 In `commitEdit()` (~`:1214`), coerce empty
      `self.editingValue` to `"0"` before PATCH.

## 3. Auto-focus + empty-to-zero on the per-asset `alvo % total` editor

- [x] 3.1 Add `x-ref="totalPctInput"` to the `<input type="number">`
      inside `data-testid="asset-target-pct-total-edit-input"`.
- [x] 3.2 In `startEditTotal()` (~`:1194`), after
      `this.editingTotalValue = String(asset.target_pct_total)`,
      append the `$nextTick` focus + select pair.
- [x] 3.3 In `commitEditTotal()` (~`:1282`), coerce empty
      `self.editingTotalValue` to `"0"` before the back-solve
      (the derived `new_target_pct` from a `0` total is `0`,
      which is in range, so no extra range guard needed).

## 4. Spinner suppression CSS

- [x] 4.1 In `src/omaha/static/app.css`, append the WebKit / Blink and
      Firefox suppression rules to the existing
      `.asset-inline-edit-input` and `.class-inline-edit-input`
      block (around `:1072` / `:1259`). Do not touch any other
      `<input type="number">` rule.

## 5. BDD scenarios

- [x] 5.1 Open `tests/bdd/feature/dashboard_inline_editing.feature`
      (or its actual filename — list with
      `ls tests/bdd/feature/` first) and add scenarios matching the
      new requirements in
      `openspec/changes/dashboard-inline-edit-friction/specs/dashboard-inline-editing/spec.md`:
      "Single click on the class target pill focuses the input",
      "Single click on the per-asset alvo % classe cell focuses the
      input", "Single click on the per-asset alvo % total cell
      focuses the input", "Clearing the class target and pressing
      Enter saves zero", "Clearing the per-asset alvo % classe and
      pressing Enter saves zero", "Clearing the per-asset alvo %
      total and pressing Enter saves zero", "Blurring an empty class
      input saves zero". *(filename is `tests/bdd/features/...`,
      not `tests/bdd/feature/` — verified via glob.)*
- [x] 5.2 Open `tests/bdd/step_defs/common_steps.py` and add new
      step definitions (or extend `click_class_field` /
      `click_asset_field`) so a single `Locator.click()` on the pill
      is followed directly by `Locator.fill(...)` (no second
      `focus()` call). Keep the existing step behavior backward
      compatible for callers that explicitly want focus first.
- [x] 5.3 Add a Playwright assertion (or extend an existing one) that
      `data-testid="*-inline-edit-input"` and
      `data-testid="*-total-edit-input"` have no rendered
      `::-webkit-inner-spin-button` pseudo-element visible. If the
      project lacks a CSS pseudo-element check pattern, skip this
      step (the spinner absence is enforced by the CSS rule itself
      and verified visually during delivery). *(skipped per the
      spec — project has no CSS pseudo-element assertion pattern;
      CSS rule enforces the absence; visual verification at
      delivery time.)*

## 6. Delivery gate

- [x] 6.1 `uv run task check` — lint + unit tests green.
- [x] 6.2 `uv run task test-bdd` — all BDD scenarios green
      (including the new ones).
- [x] 6.3 Run the **`refresh-for-test` skill** — restarts uvicorn,
      runs `uv run task db-reset`, smokes `/healthz`, verifies the
      seeded class names render, and reports the LAN URL plus DB
      row counts in the final message.
