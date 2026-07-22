## 1. Fix HTML template test (1 failure)

- [ ] 1.1 Update `tests/test_pages_routes.py:658` — change expected from `formatPctRounded(classCurrentPct)` to `formatPctRounded(classCurrentPct, 1)`

## 2. Fix CSV parsing tests (4 failures)

- [ ] 2.1 Update `tests/test_real_csv_flow.py:230` — change `Decimal("1")` to `Decimal("0")` (qty for "Conta corrente em dólar Avenue" is `0E-8` in seed CSV, parsed as `Decimal("0")`)

- [ ] 2.2 Update `_ASSIGNMENTS` dict (line 190-203) — add 6th entry: `{"broker_ticker": "Conta corrente em dólar Avenue", "class_name": "Renda Variavel"}` and update comment from "5 zero-qty rows" to "6 zero-qty rows"

- [ ] 2.3 Update `remaining` list in `test_preview_real_csv_changes_after_adding_assets` (line 519-525) — add `("Renda Variavel", "Conta corrente em dólar Avenue")` and update comment from "remaining 5 assets" to "remaining 6 assets"

## 3. Verification

- [ ] 3.1 Run `uv run task test-integration` and confirm all 5 previously-failing tests pass
