## Why

Mutation testing (T03) covers only `solver.py` + `validation.py` (~771 LOC, 869 mutants, 64.9% killed). The remaining critical rebalance files — `engine.py`, `policy.py`, `postprocessing.py`, `builders.py`, `glue.py`, `constants.py` — add ~2200 LOC of optimization logic, threshold gating, and data transformation that currently have zero mutation coverage. Expanding the scope closes this blind spot before promoting mutation score to a gate (T20).

## What Changes

- Expand `only_mutate` in `[tool.mutmut]` (pyproject.toml) from 2 files to 8 files covering the full `rebalance/` module.
- Add `pytest_add_cli_args_test_selection` entries for test files that exercise the newly covered modules (`test_rebalance_builders.py`, `test_rebalance_engine_glue.py`, `test_rebalance_glue.py`, `test_rebalance_page.py`, `test_rebalance_route.py`, `test_rebalance_schemas.py`, `test_rebalance_table_poc.py`).
- Configure mutmut parallelism (`--num-workers`) to keep total wall-clock under 20 minutes with ~2500-3400 mutants.
- Update `.mutmut-baseline` after the expanded run completes.
- Update `rebalance-mutation-testing` spec to reflect the broader scope.
- No production code changes. No test code changes (existing tests already cover these files).

## Capabilities

### New Capabilities

None — the capability `rebalance-mutation-testing` already exists.

### Modified Capabilities

- `rebalance-mutation-testing`: expand scope from `solver.py` + `validation.py` to all critical rebalance module files (`engine.py`, `policy.py`, `postprocessing.py`, `builders.py`, `glue.py`, `constants.py`), add parallelism configuration for wall-clock control.

## Impact

- **Files modified:** `pyproject.toml` (`[tool.mutmut]` block only — `only_mutate`, `pytest_add_cli_args_test_selection`, possibly new `num_workers` key).
- **Files modified:** `openspec/specs/rebalance-mutation-testing/spec.md` (scope expansion).
- **Files regenerated:** `.mutmut-baseline` (new baseline after expanded run).
- **Runtime:** `task mutation` wall-clock increases from ~3 min (869 mutants) to estimated 10-18 min (2500-3400 mutants) depending on parallelism.
- **No breaking changes:** `task mutation`, `task mutation-report`, `task mutation-baseline` interfaces unchanged.
- **Dependencies:** existing `mutmut>=3.0,<4` and `pytest-xdist>=3.6` already in dev dependencies.
