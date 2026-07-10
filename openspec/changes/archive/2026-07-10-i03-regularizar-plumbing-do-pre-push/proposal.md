## Why

`prek.toml` pre-push hook `pytest` uses `entry = "uv run task test-unit && uv run task test-integration"` with `language = "system"`. The `&&` shell operator is misparsed under the `system` hook — the command tokenizer passes the entire string as a single arg to the hook runner, breaking execution. Push currently blocked on parse failure, not on test or product behavior. `test-unit` and `test-integration` already pass individually.

## What Changes

- Split the combined `pytest` hook in `prek.toml` (pre-push stage) into two separate hooks: `pytest-unit` and `pytest-integration`, each with its own `entry` calling `uv run task test-unit` and `uv run task test-integration` respectively.
- Remove the single `pytest` hook entry that contained `&&`.
- Adjust task priority ordering in pre-push stage so unit tests run before integration tests.
- Ensure `pyproject.toml` task definitions for `test-unit` and `test-integration` remain unchanged — they are already correct.
- Ensure `.github/workflows/ci.yml` remains unchanged — CI already runs `test-unit` and `test-integration` as separate jobs.
- No product code, no spec changes, no test logic changes.

## Capabilities

### New Capabilities

*(none — no new capability introduced; this is a plumbing fix only)*

### Modified Capabilities

*(none — no spec-level behavior changes)*

## Impact

- **`prek.toml`**: Replace one `pytest` hook (`entry = "uv run task test-unit && uv run task test-integration"`, priority=4) with two hooks: `pytest-unit` (`entry = "uv run task test-unit"`, priority=4) and `pytest-integration` (`entry = "uv run task test-integration"`, priority=5). This ensures unit tests fail fast before integration tests run.
- **`pyproject.toml`**: No changes — `test-unit` and `test-integration` task definitions are already correct.
- **`.github/workflows/ci.yml`**: No changes — CI jobs are already separate and correct.
- **No spec files affected**: This is tooling plumbing only.
