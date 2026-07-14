## Why

CI feedback loop is slow. `task test` runs the full suite (unit + integration + audit + e2e + bdd + visual) — wall-clock 10+ min on a good day. Developers waiting for merge feedback waste cycles. The existing `task check` (`lint && test-unit`) already runs in ~30s but is not formally defined as a pre-merge gate and lacks documentation about what it covers vs. what it skips.

Baseline (2026-07-13 rerun):

| Lane | Wall-clock |
|------|-----------|
| unit | 15.37s |
| integration | 190.12s |
| audit integration | 25.04s |
| e2e | 192.50s |
| bdd | 176.87s |
| visual | 55.36s |
| **lint (prek)** | ~15s (est.) |

Unit + lint ≈ 30s. Everything else is 190s+. The gap is clear: fast gate stays under 2 min, heavy lanes run async.

## What Changes

- Add `gate-fast` taskipy task: `lint` + `test-unit` in sequence, under 2 min wall-clock.
- Rename existing `check` to `gate-fast` (or add `gate-fast` as alias). `check` becomes deprecated alias pointing to `gate-fast`.
- Document lane split in `tests/PERFORMANCE.md`: fast gate vs. full suite vs. browser lanes.
- Update `tests/PERFORMANCE.md` with gate-fast definition and timing expectations.
- No changes to test infrastructure, markers, conftest, or test files themselves.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `dev-tasks`: add `gate-fast` task as the formal pre-merge gate command.

## Impact

- `pyproject.toml` — `[tool.taskipy.tasks]` block: add `gate-fast`, deprecate `check`.
- `tests/PERFORMANCE.md` — add "Gate definitions" section documenting fast gate, full suite, and browser lanes with timing expectations.
- No runtime code change. No test change. No template change. Pure ops/doc slice.

## Scope boundary

- Coverage reporting is out of scope (owned by T13).
- Integration test optimization is out of scope (future slice).
- pytest-xdist parallelization is out of scope (future slice).
- CI pipeline YAML changes are out of scope (this repo uses taskipy, not GitHub Actions directly).
