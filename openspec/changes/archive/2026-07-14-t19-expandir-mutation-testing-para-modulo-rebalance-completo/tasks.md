## 1. Expand mutmut scope in pyproject.toml

- [x] 1.1 Add 6 new files to `only_mutate` in `[tool.mutmut]`: `engine.py`, `policy.py`, `postprocessing.py`, `builders.py`, `glue.py`, `constants.py`
- [x] 1.2 Add `num_workers = 3` to `[tool.mutmut]` for parallel mutant evaluation
- [x] 1.3 Add test files to `pytest_add_cli_args_test_selection`: `test_rebalance_builders.py`, `test_rebalance_engine_glue.py`, `test_rebalance_engine_regression.py`, `test_rebalance_glue.py`, `test_rebalance_policy.py`, `test_rebalance_postprocessing.py`, `test_rebalance_schemas.py`, `test_rebalance_table_poc.py`
- [x] 1.4 Update the `# Mutation testing` comment block above `[tool.mutmut]` to reflect the expanded scope and parallelism

## 2. Clean cache and run expanded mutation testing

- [x] 2.1 Delete `mutants/` directory to force a clean run with the new scope
- [x] 2.2 Run `task mutation` and verify it completes without errors (target: < 20 min wall-clock)
- [x] 2.3 Run `task mutation-report` and verify per-file `.meta` coverage includes all 8 source files

## 3. Capture new baseline

- [x] 3.1 Run `task mutation-baseline` to generate the updated `.mutmut-baseline`
- [x] 3.2 Verify `.mutmut-baseline` shows increased mutant count (expected: 2500-3400 total) and records `generated_at` timestamp

## 4. Update spec

- [x] 4.1 Sync the delta spec from `openspec/changes/t19-.../specs/rebalance-mutation-testing/spec.md` to `openspec/specs/rebalance-mutation-testing/spec.md` using `openspec-sync-specs`

## 5. Verify and update roadmap

- [x] 5.1 Run `openspec verify --change t19-expandir-mutation-testing-para-modulo-rebalance-completo` and resolve any issues
- [x] 5.2 Update roadmap: move T19 from `Ready` to `Spec Proposed` with progress log entry
