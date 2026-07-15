## Why

Suite tem testes que não provam comportamento real: skips redundantes (cobertos por outros testes), duplicação óbvia (mesma pipeline rodada 2x), e asserts triviais em strings hardcoded. Cada teste que não mata mutant ou valida edge case é peso morto — aumenta tempo de suite, confunde manutenção, e dá falsa sensação de cobertura.

## What Changes

- **Remove 2 skipped tests** redundantes:
  - `test_rebalance_engine_glue.py::test_run_rebalance_negative_contribution_rejected` — coberto por `test_rebalance_validation.py::test_check_1_negative_contribution_rejected` + `test_rebalance_route.py::test_solver_validation_error_returns_400`
  - `test_rebalance_glue.py::test_default_solver_is_cvxpy` — coberto por `test_rebalance_engine_glue.py::test_cvxpy_solver_directly_returns_native_shape`

- **Merge 2 duplicate slow tests** em `test_audit_inventory.py`:
  - `test_inventory_for_patrimonio_produces_rows` (31s) + `test_inventory_rows_carry_template_field` (31s) → 1 teste que valida rows > 0 E template field em uma única chamada `inventory_for_page("patrimonio.html")`. Economiza ~31s.

- **Remove 2 trivial find_interactive tests** em `test_audit_inventory.py`:
  - `test_find_interactive_empty_html_returns_empty` — `assert find_interactive("") == []`
  - `test_find_interactive_no_interactive_elements_returns_empty` — `assert find_interactive("<div><p>Hello</p></div>") == []`
  - Ambos testam strings hardcoded, não código do sistema. Zero mutation kill value. `find_interactive` já é exercitado por `test_find_interactive_finds_tag` com templates reais.

- **No new capabilities or spec changes.** This is test hygiene only.

## Capabilities

### New Capabilities

None — test cleanup, no behavioral changes.

### Modified Capabilities

None — no spec-level behavior is changing.

## Impact

- **Files modified:** `tests/test_rebalance_engine_glue.py`, `tests/test_rebalance_glue.py`, `tests/test_audit_inventory.py`
- **Time saved:** ~31s from audit_inventory merge + removal of 2 trivial tests (negligible individually, but reduces noise)
- **Test count:** -5 tests (2 removed skips, 2 removed trivial, 1 merged duplicate) + 1 new merged test = net -4
- **No production code touched.** No seed files touched (PRD §4.3).
