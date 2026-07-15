## 1. Update prek.toml hook configuration

- [x] 1.1 Remove `pytest-unit` entry from the pre-push local hooks section in `prek.toml` (line 107: `{ id = "pytest-unit", name = "pytest-unit", entry = "uv run task test-unit", ... stages = ["pre-push"], priority = 4 }`)
- [x] 1.2 Change `pytest-integration` entry in pre-push from `entry = "uv run task test-integration"` to `entry = "uv run task test-integration-parallel"` (line 108)

## 2. Update prek-hooks spec

- [x] 2.1 Update the "Pytest full gate on pre-push" requirement in `openspec/specs/prek-hooks/spec.md` to state: unit tests are gated at pre-commit only; pre-push runs integration tests via `task test-integration-parallel`
- [x] 2.2 Update the "Pre-push delegates to canonical tasks" scenario to reflect the pre-push gate runs integration-only (unit gated at commit time)
- [x] 2.3 Update the "Pre-push pytest hook entry documents the dev-server carve-out" requirement comment to reference parallel integration

## 3. Verify timing and coverage

- [x] 3.1 Run `uv run task test-unit` and confirm 354 tests pass (~17s) — baseline for pre-commit
- [x] 3.2 Run `uv run task test-integration-parallel` and confirm all integration tests pass with parallel execution
- [x] 3.3 Verify `xdist_group("serial")` tests (4 files) are serialized correctly under `loadgroup`
- [x] 3.4 Measure pre-push wall-clock: ruff + integration-parallel + commitizen-branch — confirm < 180s

## 4. Update roadmap

- [x] 4.1 Move I05 from `Ready` to `Spec Proposed` with progress log entry in `openspec/roadmap.md`
