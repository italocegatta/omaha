## Context

Current `prek.toml` pre-push stage has a single local `pytest` hook (lines 103-109):

```toml
[[repos]]
repo = "local"
hooks = [
    { id = "pytest", name = "pytest", entry = "uv run task test-unit && uv run task test-integration", language = "system", pass_filenames = false, stages = ["pre-push"], priority = 4 },
]
```

`prek`'s `system` hook runner does not parse shell operators (`&&`). The entire string `uv run task test-unit && uv run task test-integration` is passed as a single argument to a subprocess, causing execution to fail. This blocks all `git push` operations for the repo.

The test tasks themselves (`test-unit`, `test-integration`) are defined in `pyproject.toml` and work correctly when run individually:
- `test-unit`: `uv run pytest -m unit` — 346 passing tests
- `test-integration`: `uv run pytest -m integration --ignore=tests/audit_integration` — 108 passing tests

Existing hooks in `prek.toml` already demonstrate the correct single-command pattern for `system` hooks (e.g., `pytest-unit` in pre-commit stage at line 55 uses `entry = "uv run task test-unit"` with no `&&`).

CI jobs in `.github/workflows/ci.yml` already run `test-unit` and `test-integration` as separate job steps (lines 68-69, 102-103). No change needed there.

## Goals / Non-Goals

**Goals:**
- Fix pre-push hook so `task test-unit` and `task test-integration` both execute correctly on `git push`.
- Run unit tests before integration tests in pre-push (fail-fast ordering).
- Keep the full gate intact — no test bucket removed, no threshold relaxed.
- Preserve the existing `pre-commit` stage `pytest-unit` hook unchanged.

**Non-Goals:**
- No product code changes.
- No test logic changes.
- No `.github/workflows/ci.yml` changes (CI is already correct).
- No `pyproject.toml` task definition changes (task definitions are already correct).
- No spec changes.
- No lint drift cleanup (deferred to I04).
- No change to `pre-commit` stage hooks.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Fix approach | Replace single `pytest` hook with two separate `system` hooks | `prek` system hooks cannot parse `&&`. Two hooks is the canonical pattern — pre-commit stage already uses it (line 55). |
| Hook naming | `pytest-unit` (priority=4) and `pytest-integration` (priority=5) | Consistent with existing `pytest-unit` in pre-commit stage. Priority ordering ensures unit tests fail fast before slower integration tests. |
| Keep CI unchanged | Yes — no edit to `.github/workflows/ci.yml` | CI already runs unit and integration in separate jobs. No `&&` issue there. |
| Keep taskipy definitions | Yes — no edit to `pyproject.toml` | `task test-unit` and `task test-integration` work correctly individually. The bug is in how `prek` invokes them, not in the tasks themselves. |
| Skip delta spec | No spec files affected | Pure tooling/plumbing change. No capability contract changes. |

## Risks / Trade-offs

- **[Low risk] Hook ordering broken after split** — priority=4 for unit, priority=5 for integration. If `prek` runs hooks with equal priority in arbitrary order, unit might not gate integration. Mitigation: explicitly different priorities ensure `prek` sorts by priority (lower = earlier).
- **[Low risk] Two hooks means two `uv` cold-start invocations** — acceptable. Test suite overhead (~1-2s per `uv run`) is negligible vs push duration (~30-60s). The pre-commit `pytest-unit` hook already uses same pattern.
- **[Low risk] Existing `prek` cache or hook binary stale** — after editing `prek.toml`, user must run `uv run task prek-install` to re-register hooks in `.git/hooks/`. This is already documented in `task prek-install` help text.
