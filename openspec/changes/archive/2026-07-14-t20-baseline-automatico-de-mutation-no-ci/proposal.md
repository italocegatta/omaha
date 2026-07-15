## Why

Mutation testing (T03 → T19) now covers the full rebalance module (8 files, 3867 mutants, 94.5% killed). The baseline `.mutmut-baseline` is generated manually via `task mutation-baseline` after local runs. This creates a gap: if a developer merges code that silently drops mutation score, nobody notices until the next manual run. Automating baseline generation on merge to `main` closes this gap — the baseline stays current and regression in mutation score becomes visible immediately via `git diff`.

## What Changes

- Add a new GitHub Actions job `mutation-baseline` to `.github/workflows/ci.yml` that runs `task mutation` + `task mutation-baseline` post-merge on `main` only (not on PRs — cost too high).
- The job commits the updated `.mutmut-baseline` back to `main` automatically via `git` push.
- Add a taskipy task `mutation-ci` that chains `mutation` → `mutation-baseline` for single-command CI invocation.
- Update the `rebalance-mutation-testing` spec to document the CI automation requirement.
- No production code changes. No test changes.

## Capabilities

### New Capabilities

None — the capability `rebalance-mutation-testing` already exists.

### Modified Capabilities

- `rebalance-mutation-testing`: add requirement for automatic post-merge baseline generation in CI, including the workflow job structure, commit-back strategy, and failure handling.

## Impact

- **Files modified:** `.github/workflows/ci.yml` (new `mutation-baseline` job).
- **Files modified:** `pyproject.toml` (`[tool.taskipy.tasks]` — add `mutation-ci`).
- **Files modified:** `openspec/specs/rebalance-mutation-testing/spec.md` (new CI requirement).
- **Runtime:** `task mutation` takes 10-18 min; the CI job adds ~20 min to post-merge pipeline (runs once per merge, not per PR).
- **No breaking changes:** existing `task mutation`, `task mutation-report`, `task mutation-baseline` interfaces unchanged.
- **Dependencies:** existing `mutmut>=3.0,<4` already in dev dependencies. CI uses `actions/checkout` + `astral-sh/setup-uv` already present.
- **Security:** job needs `contents: write` permission to push the updated baseline commit.
