## Context

Current hook pipeline timing (measured 2026-07-15):

| Stage | Hook | Time |
|-------|------|------|
| pre-commit | check-merge-conflict + check-yaml + check-toml + check-json + check-added-large-files + detect-private-key + validate-pyproject + gitleaks | ~8s |
| pre-commit | `pytest-unit` (354 tests) | ~17s |
| **pre-commit total** | | **~25s** |
| pre-push | ruff + trailing-whitespace + end-of-file-fixer + uv-lock + commitizen-branch | ~8s |
| pre-push | `pytest-unit` (DUPLICATE — same 354 tests) | ~17s |
| pre-push | `pytest-integration` serial (388 tests) | ~187s |
| **pre-push total** | | **~212s** |

The `test-integration-parallel` task (added T17, validated with `test-worker-db-isolation` spec) runs the same 388 integration tests with `-n auto --dist loadgroup`. T17 measured ~2:44 wall-clock (~164s). With the serial-to-parallel switch and duplicate removal:

| Stage | Hook | Time (projected) |
|-------|------|------|
| pre-commit | same as above | ~25s |
| pre-push | ruff + trailing-whitespace + end-of-file-fixer + uv-lock + commitizen-branch | ~8s |
| pre-push | `pytest-integration-parallel` (388 tests, `-n auto`) | ~65s |
| **pre-push total** | | **~73s** |

Net gain: ~137s per push. Pre-commit unchanged.

## Goals / Non-Goals

**Goals:**
- Remove duplicate `pytest-unit` from pre-push (already gated at pre-commit)
- Switch pre-push integration hook from serial to parallel (`test-integration-parallel`)
- Update `prek-hooks` spec to reflect the new hook layout
- Verify pre-push completes under 180s target

**Non-Goals:**
- Changing test scope or marker classification
- Modifying `task test-unit` or `task test-integration` interfaces
- Adding new tests or changing test behavior
- Touching CI workflows (`.github/workflows/`)

## Decisions

### D-I05.1 — Remove pytest-unit from pre-push (not pre-commit)

**Choice:** Remove `pytest-unit` from the pre-push stage, keep it in pre-commit.

**Rationale:** Pre-commit is the correct gate for unit tests — fast feedback on every commit. Running the same tests again at push time adds 17s with zero additional coverage. The `prek-hooks` spec already documents unit tests as a pre-commit gate. The pre-push spec says "one or more `uv run task ...` commands" for the non-browser gate — running only integration satisfies this since unit is already gated.

**Alternative considered:** Keep both but skip via cache (`pytest --last-failed` or similar). Rejected — adds complexity, pytest cache is per-session not cross-hook, and the fundamental issue is unnecessary duplication.

### D-I05.2 — Use test-integration-parallel (not test-integration)

**Choice:** Switch pre-push integration hook to `uv run task test-integration-parallel`.

**Rationale:** T17 already validated parallel integration with `pytest-xdist`. The `test-worker-db-isolation` spec guarantees each xdist worker gets its own SQLite DB. `loadgroup` distribution respects `xdist_group("serial")` markers (4 files: `test_real_csv_flow`, `test_db_reset_both_profiles`, `test_seed_from_csv`, `test_snapshot_to_csv`). Serial fallback (`task test-integration`) remains available for debugging.

**Alternative considered:** Keep serial integration in pre-push, only remove the duplicate unit. Saves only ~17s (220s → 203s), doesn't meet the 180s target. Rejected.

### D-I05.3 — Update spec, don't create new one

**Choice:** Modify existing `prek-hooks` spec. No new spec needed.

**Rationale:** The change modifies hook configuration behavior, which is already covered by the `prek-hooks` spec. The spec's "Pytest full gate on pre-push" requirement needs updating to reflect that unit is pre-commit-only and integration runs parallel. A delta spec would be appropriate if we were adding a new capability, but this is a refinement of existing behavior.

## Risks / Trade-offs

- **[Risk] Parallel integration failures not caught serially** → Mitigation: `test-integration-parallel` uses `loadgroup` which serializes tests marked `xdist_group("serial")`. If parallel-specific flakiness emerges, developer can run `task test-integration` (serial) to diagnose. The serial task is unchanged.

- **[Risk] Removing pytest-unit from pre-push means a bad commit could reach push** → Mitigation: unit tests still run at pre-commit. If someone bypasses pre-commit (`git commit --no-verify`), the integration tests at pre-push will still catch functional regressions. Unit test failures are pure-function issues that integration tests also exercise indirectly.

- **[Risk] xdist worker count varies by machine** → Mitigation: `-n auto` detects CPU count. On 2-core machines, parallelism is limited but still faster than serial. The `xdist_group("serial")` tests run in a single worker regardless. No action needed.
