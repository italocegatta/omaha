## Context

T03 introduced mutation testing for `rebalance/solver.py` + `rebalance/validation.py` (771 LOC combined). Baseline from 2026-07-06: 869 mutants, 556 killed, 301 survived, 12 no_tests → 64.9% killed share. Wall-clock: ~3 min.

The remaining critical rebalance files add ~2200 LOC:
- `engine.py` (211 LOC) — CVXPY solver orchestration, constraint assembly
- `policy.py` (665 LOC) — threshold gating, buy/sell decision logic
- `postprocessing.py` (619 LOC) — result formatting, deviation computation
- `builders.py` (402 LOC) — plan row construction, quantity calculation
- `glue.py` (240 LOC) — route-to-engine data bridge
- `constants.py` (79 LOC) — shared constants, column definitions

These files have unit test coverage via 7 test files (~2900 LOC) but zero mutation testing. Mutations in `policy.py` threshold logic or `engine.py` constraint assembly could survive undetected.

Existing test files that exercise the new scope:
- `test_rebalance_builders.py` (502 LOC)
- `test_rebalance_engine_glue.py` (196 LOC)
- `test_rebalance_engine_regression.py` (289 LOC)
- `test_rebalance_glue.py` (559 LOC)
- `test_rebalance_page.py` (728 LOC) — integration, may not run in mutmut
- `test_rebalance_policy.py` (126 LOC)
- `test_rebalance_postprocessing.py` (210 LOC)
- `test_rebalance_route.py` (525 LOC) — integration, may not run in mutmut
- `test_rebalance_schemas.py` (307 LOC)
- `test_rebalance_table_poc.py` (293 LOC)

## Goals / Non-Goals

**Goals:**
- Expand `only_mutate` to cover all 8 critical rebalance files
- Add corresponding test files to `pytest_add_cli_args_test_selection` so mutants in new files are exercised
- Keep total wall-clock under 20 minutes via mutmut parallelism
- Produce a new `.mutmut-baseline` reflecting the expanded scope
- Update the `rebalance-mutation-testing` spec to document the broader scope

**Non-Goals:**
- Promoting mutation score to a CI gate (T20 scope)
- Adding new tests — existing tests already cover the new files
- Changing mutation testing infrastructure (`task mutation`, `task mutation-report`, `task mutation-baseline` interfaces stay identical)
- Mutating non-rebalance modules (`routes/`, `models/`, `templates/`)

## Decisions

### D-T19.1 — Parallelism via `mutmut --num-workers`

**Choice:** Add `num_workers` key to `[tool.mutmut]` in `pyproject.toml`.

**Rationale:** mutmut3 supports `--num-workers N` for parallel mutant evaluation. On a 4-core machine, `num_workers = 3` (leave 1 core for system) should cut wall-clock from ~18 min (serial) to ~6-8 min. The project already has `pytest-xdist` in dev deps, so parallel test execution within each mutant is also possible but riskier (DB contention). Mutant-level parallelism is safer — each mutant runs its own pytest invocation.

**Alternatives considered:**
- *pytest-xdist inside each mutant:* More complex, risk of DB state leakage between parallel test workers within a single mutant. Deferred.
- *CI-only mutation:* Defeats local dev feedback loop. Rejected.
- *No parallelism:* 2500+ mutants × ~0.4s/test = ~17 min. Acceptable but close to the 20 min ceiling. Parallelism provides headroom.

### D-T19.2 — Scope via `only_mutate` list (not directory glob)

**Choice:** Enumerate files explicitly in `only_mutate`.

**Rationale:** Explicit list matches T03 convention and prevents accidentally mutating non-critical files (`market_prices.py`, `quotes_adapter.py`, `schemas.py`, `models.py`). These files have different risk profiles and test patterns. Adding them later is a separate decision.

### D-T19.3 — Test selection expansion

**Choice:** Add all unit test files for newly covered modules to `pytest_add_cli_args_test_selection`.

**Rationale:** mutmut3 uses `pytest_add_cli_args_test_selection` to scope which tests run per mutant. Currently only 6 test files are listed. Adding the builder, glue, engine, policy, postprocessing, schemas, and table_poc test files ensures mutants in the new source files are actually exercised. Integration-heavy tests (`test_rebalance_page.py`, `test_rebalance_route.py`) are excluded — they hit DB/HTTP and would slow each mutant invocation significantly.

### D-T19.4 — Baseline regeneration strategy

**Choice:** Delete `mutants/` directory before the expanded run, then run `task mutation-baseline`.

**Rationale:** mutmut3 caches by source path. Adding new files to `only_mutate` doesn't invalidate the cache for existing files, but the `.meta` files for newly added source paths won't exist until a fresh run. A clean run ensures the baseline reflects all 8 files consistently.

## Risks / Trade-offs

- **[Risk] Wall-clock exceeds 20 min** → Mitigation: `num_workers = 3` provides ~3x speedup. If still too slow, reduce scope to 6 files (drop `constants.py` and `glue.py` — lower risk). Monitor first run.

- **[Risk] Survived mutants in new files reveal test gaps** → Mitigation: Expected. T19 is infrastructure (expand scope), not test improvement. Survived mutants become input for future T-slices that add targeted tests.

- **[Risk] Integration tests excluded from mutation** → Mitigation: `test_rebalance_page.py` and `test_rebalance_route.py` are integration-heavy. Including them would add ~2s per mutant (DB setup). They can be added in a follow-up if unit coverage proves insufficient.

- **[Risk] mutmut3 parallelism instability** → Mitigation: mutmut3 `--num-workers` is battle-tested in the project's CI (pytest-xdist). If crashes occur, fall back to `num_workers = 1` (serial).
