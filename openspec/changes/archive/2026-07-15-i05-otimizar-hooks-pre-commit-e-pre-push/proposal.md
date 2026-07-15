## Why

Pre-push hook takes ~220s: `pytest-unit` (17s, duplicate — already runs in pre-commit) + `pytest-integration` serial (187s). Developer blocks on push for 3.5+ minutes. Goal: commit < 60s, push < 180s.

Two levers:
1. `pytest-unit` runs in both pre-commit AND pre-push — same command, same tests, pure waste of 17s.
2. `task test-integration` runs serial (187s) while `task test-integration-parallel` exists with `-n auto --dist loadgroup` (T17 already validated ~2:44 wall-clock).

Removing the duplicate and switching to parallel saves ~137s per push, bringing pre-push from ~220s to ~83s.

## What Changes

- Remove `pytest-unit` local hook from pre-push stage in `prek.toml` (line 107). Unit tests remain gated at pre-commit — no coverage lost.
- Change `pytest-integration` hook entry from `uv run task test-integration` to `uv run task test-integration-parallel` in `prek.toml` (line 108).
- Update `prek-hooks` spec: pre-push pytest gate now runs integration-only (unit gated at pre-commit); hook uses parallel integration task.
- No production code changes. No test code changes. No new dependencies.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `prek-hooks`: pre-push pytest gate drops duplicate unit hook, switches integration to parallel task. Coverage contract unchanged — unit tests gated at pre-commit, integration tests gated at pre-push.

## Impact

- **Files modified:** `prek.toml` (2 lines: remove `pytest-unit` from pre-push, change `pytest-integration` entry).
- **Files modified:** `openspec/specs/prek-hooks/spec.md` (update pre-push gate requirement to reflect integration-only + parallel).
- **Timing:** pre-commit stays ~25s. Pre-push drops from ~220s to ~83s (ruff ~5s + integration-parallel ~65s + commitizen-branch ~3s + margin).
- **No breaking changes:** `task test-unit`, `task test-integration`, `task test-integration-parallel` interfaces unchanged.
- **Coverage preserved:** unit tests still run on every commit (pre-commit hook). Integration tests still run on every push (pre-push hook, now parallel).
- **Dependencies:** existing `pytest-xdist>=3.6` already in dev deps (added in T17).
