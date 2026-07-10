## 1. Fix pre-push hook entry

- [x] 1.1 Edit `prek.toml` pre-push stage: replace the single `pytest` hook (lines 103-109) with two separate hooks:
  - `pytest-unit`: `entry = "uv run task test-unit"`, `priority = 4`
  - `pytest-integration`: `entry = "uv run task test-integration"`, `priority = 5`
- [x] 1.2 Preserve all other hook attributes: `language = "system"`, `pass_filenames = false`, `stages = ["pre-push"]`.
- [x] 1.3 Verify the existing comment on lines 106-107 remains legible and still applies (canonical non-browser gate).

## 2. Reinstall hooks and validate

- [x] 2.1 Run `uv run task prek-install` to re-register hooks in `.git/hooks/`.
- [x] 2.2 Validate `prek.toml` is valid TOML: `uv run prek run --hook-stage pre-push` or equivalent dry-run.
- [x] 2.3 Run `uv run task test-unit` to confirm unit test bucket still passes.
- [x] 2.4 Run `uv run task test-integration` to confirm integration test bucket still passes.

## 3. Gate integrity validation

- [x] 3.1 Verify `uv run task test-unit` fails fast before integration tests start (confirm priority ordering).
- [x] 3.2 Confirm `.github/workflows/ci.yml` requires no changes — CI jobs are already separate.
- [x] 3.3 Confirm `pyproject.toml` requires no changes — task definitions are already correct.

## 4. Archive preparation

- [x] 4.1 Verify no unrelated files changed (`git diff --stat` — only `prek.toml`).
- [x] 4.2 Run `openspec list --specs` to validate spec health gate.
- [x] 4.3 Update `openspec/roadmap.md` slice I03 status to `Applied`.
