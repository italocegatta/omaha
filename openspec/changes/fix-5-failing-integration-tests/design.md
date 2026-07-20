## Context

Two commits introduced production behavior changes but their corresponding tests were not updated:

1. **F46** (`ab2e0aa`): Template `_patrimonio_class_section.html:148` changed `formatPctRounded(classCurrentPct)` → `formatPctRounded(classCurrentPct, 1)`. The test at `test_pages_routes.py:658-659` still asserts the old expression.

2. **CSV alignment** (`bcb68836`): Tests restructured to use `load_positions("italo")` from seed data. "Conta corrente em dólar Avenue" has `qty=0E-8` in `italo_positions.csv` (a non-tradeable position with explicit totals). The test incorrectly asserts `qty == Decimal("1")` and has incomplete `_ASSIGNMENTS`/`remaining` lists (5 entries vs 6 zero-qty rows).

## Goals / Non-Goals

**Goals:**
- Make all 5 failing integration tests pass by correcting assertions to match current production behavior.
- Zero changes to production code.

**Non-Goals:**
- Refactoring test structure or improving test coverage.
- Changing seed data or CSV fixtures.
- Fixing any other test failures.

## Decisions

1. **Fix tests, not code.** Both commits are intentional behavior changes (F46 decimal formatting, CSV workflow alignment). Tests must follow.

2. **Minimal assertion edits.** Each fix is a single-line or small-block change. No restructuring.

3. **"Conta corrente em dólar Avenue" maps to "Renda Variavel" class.** Per `_dashboard_class_for_asset()` logic (line 103-110): seed class "Internacional" is not in `{"RF Dinâmica", "RF Pós", "FII"}`, so it falls through to `return "Renda Variavel"`.

## Risks / Trade-offs

- **Risk:** Seed data could change again, breaking these tests. → Mitigation: tests read from canonical `data/seed/italo_positions.csv`; changes there are intentional and would require test updates anyway.
- **Risk:** Fixing only these 5 tests might mask other drift. → Mitigation: run full integration suite after fix to confirm.
