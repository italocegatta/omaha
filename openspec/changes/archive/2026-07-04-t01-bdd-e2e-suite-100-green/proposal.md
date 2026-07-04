## Why

The e2e + BDD suite has been red since F02 (commit `8f268fd`, 2026-07-03)
introduced structural UI changes that the tests never tracked:

- The legacy `<h1 class="profile-name" data-testid="profile-name">` chip
  was replaced by a `<select>` inside `form.profile-switcher` (spec
  `header-profile-switcher`, Requirement "The dashboard h1
  profile-name element is removed"). Four e2e tests still wait on the
  removed `data-testid="profile-name"`.
- The top-nav `Patrimônio` link now points to `/patrimonio` (was `/`).
  One e2e test asserts the legacy regex `/$` and never reaches.
- `.patrimonio-page` widened to `max-width: 1800px` with `width:
  calc(100% - 2rem)` to use wide screens. Five pixel-alignment tests
  measured columns against hard-coded thresholds that the new
  container violates.
- One click handler bug from F02 — `<section class="patrimonio-actions">`
  lacked an Alpine `x-data` ancestor, so `Importar CSV` / `Novo ativo`
  / `Nova classe` were silently dead. That fix already landed in
  commit `1755dd0`; this slice recovers the tests that depended on the
  dead handlers.

The accumulated debt is exactly the scope of slice T01 in
`openspec/roadmap.md`. Without this work, every CI run reports 12 red
tests for reasons unrelated to current code behavior.

## What Changes

- **Update e2e test selectors.** Replace `[data-testid="profile-name"]`
  with the current `[data-testid="profile-switcher"]` (the `<select>`
  on the header chip) in the four files that gate on
  `/classes → /dashboard`, `/assets → /dashboard`,
  `/import → /dashboard`, and the import journey redirect.
- **Update URL expectation.** The top-nav test in
  `tests/e2e/test_rebalance_page.py::test_top_nav_patrimonio_link_returns_to_dashboard`
  changes its `wait_for_url` from `/$` to `/patrimonio$`.
- **Re-measure alignment thresholds.** For the four
  `class_section_alignment` tests and the
  `test_column_widths_match_spec` test, re-record the post-widening
  pixel baselines and update the assertions. The threshold of 1.0 px
  remains; only the baselines move.
- **Add a regression test** that asserts
  `[data-testid="patrimonio-actions"]` carries an `x-data` attribute,
  so the F02 regression cannot reappear silently.

No production behavior changes. No spec delta files beyond
`header-profile-switcher` (the test selectors are already aligned with
this spec — tests are wrong, not the spec).

## Capabilities

### New Capabilities
- `e2e-selector-pinning`: Lock the e2e suite to a documented
  selector inventory keyed by `data-testid` / `aria-*` / role, so
  future UI changes surface as a failing selector rather than a
  hidden test rot. Centralizes the per-test
  `S0X_SELECTORS` dicts into a single importable map plus a
  `test_all_selectors_resolve` smoke that walks the inventory
  against a live dashboard and confirms each one resolves.

### Modified Capabilities
- `header-profile-switcher`: No requirement changes. The existing
  requirement "The dashboard h1 profile-name element is removed"
  is correct — the tests are wrong. No delta spec needed; only
  test code changes.

## Impact

- **Tests only.** No `src/omaha/` changes (the production fix already
  landed in commit `1755dd0`).
- **Five files modified:**
  `tests/e2e/test_class_crud.py`, `tests/e2e/test_asset_crud.py`,
  `tests/e2e/test_import_modal.py`, `tests/e2e/test_full_journey.py`,
  `tests/e2e/test_rebalance_page.py`,
  `tests/e2e/test_class_section_alignment.py`,
  `tests/e2e/test_asset_table.py`.
- **One new file:** `tests/e2e/selectors.py` (central selector map)
  plus `tests/e2e/test_selector_inventory.py` (smoke).
- **No DB / migration impact.** No UI behavior impact.
- **Risk:** Low. All assertions are post-F02 expectations; the change
  makes tests align with current code rather than the other way
  around.