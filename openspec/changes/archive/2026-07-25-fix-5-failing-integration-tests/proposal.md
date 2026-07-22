## Why

Five integration tests fail because test assertions drifted from production code after two commits:
- `ab2e0aa` (F46: format Classe/Carteira columns with 1 decimal) changed template but not the HTML test.
- `bcb68836` (fix: align csv and bdd workflows) restructured CSV tests to use seed-data helpers but left stale assertions.

Tests are out of sync with code — not code bugs.

## What Changes

- Update 1 assertion in `tests/test_pages_routes.py` to match template `formatPctRounded(classCurrentPct, 1)`.
- Update 3 spots in `tests/test_real_csv_flow.py` to reflect that "Conta corrente em dólar Avenue" is a zero-qty unmatched ticker (qty=`0`, not `1`).

No production code changes. No spec changes. Test-only.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — no spec-level behavior changes; these are test assertion corrections only.

## Impact

- `tests/test_pages_routes.py` — 1 line change (assertion on `x-text` expression).
- `tests/test_real_csv_flow.py` — 3 changes:
  1. Line 230: `Decimal("1")` → `Decimal("0")` for qty assertion.
  2. `_ASSIGNMENTS` dict: add missing entry for "Conta corrente em dólar Avenue".
  3. `remaining` list in `test_preview_real_csv_changes_after_adding_assets`: add missing entry.
- Zero risk to production behavior.
