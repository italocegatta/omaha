## 1. Restructure prek.toml

- [x] 1.1 Bump `ruff-pre-commit` from `v0.6.9` to `v0.14.3` in prek.toml
- [x] 1.2 Add `exclude` pattern covering `.agents/.*`, `.gsd/.*`, `.opencode/.*`, `data/.*`, `backups/.*`, `certs/.*`
- [x] 1.3 Add `pre-commit` stage file-sanity hooks: `check-merge-conflict`, `check-json`, `validate-pyproject`, `gitleaks` (keep `check-yaml`, `check-toml`, `check-added-large-files`, `detect-private-key`)
- [x] 1.4 Add `pre-commit` stage local pytest hook: `id = "pytest-unit"`, `entry = "./.venv/bin/python -m pytest -m unit"`, `pass_filenames = false`, `types = ["python"]`, `priority = 4`
- [x] 1.5 Move `ruff-format`, `ruff --fix`, `trailing-whitespace`, `end-of-file-fixer` to `pre-push` stage with priorities 1, 2, 3, 3 respectively; mark `ruff-format` and `ruff --fix` with `continue-on-error = true`
- [x] 1.6 Add `pre-push` stage `uv-lock` hook from `astral-sh/uv-pre-commit` at rev `0.11.19`, priority 3
- [x] 1.7 Add `pre-push` stage local pytest hook: `id = "pytest"`, `entry = "./.venv/bin/python -m pytest"`, `pass_filenames = false`, `types = ["python"]`, priority 4
- [x] 1.8 Add `pre-push` stage `pyright` hook from `RobertCraigie/pyright-python` at rev `v1.1.391`, with `additional_dependencies = ["fastapi[standard]>=0.115", "sqlalchemy>=2.0", "pydantic>=2.7", "pydantic-settings>=2.4", "pytest>=8.3"]`, `always_run = true`, `continue-on-error = true`
- [x] 1.9 Add `pre-push` stage `commitizen-branch` hook from `commitizen-tools/commitizen` at rev `v4.8.0`
- [x] 1.10 Add `commit-msg` stage `commitizen` hook from `commitizen-tools/commitizen` at rev `v4.8.0`

## 2. Add pyright config to pyproject.toml

- [x] 2.1 Add `[tool.pyright]` section with `pythonVersion = "3.12"`, `typeCheckingMode = "basic"`, `include = ["src/omaha"]`, `exclude = ["**/alembic/*"]`, `venvPath = "."`, `venv = ".venv"`, `reportMissingImports = "error"`, `reportMissingTypeStubs = "none"`

## 3. Add prek-install taskipy shortcut

- [x] 3.1 Add `prek-install = { cmd = "uv run prek install", help = "Install prek git hooks into .git/hooks/" }` to `[tool.taskipy.tasks]`
- [x] 3.2 Update `[tool.taskipy.tasks]` lint entry if needed to reflect the new stage structure (currently `lint = { cmd = "uv run prek run --all-files" }` — no change needed since the command runs all stages regardless of stage config)

## 4. Verify

- [x] 4.1 Run `uv run prek validate-config` and confirm the config is valid
- [x] 4.2 Run `uv run prek run --all-files` and confirm: file-sanity hooks pass, pytest-unit passes, pytest (full) passes, ruff and pyright report failures (expected) but do not abort, gitleaks passes, validate-pyproject passes, uv-lock either passes or no-ops
- [x] 4.3 Run `uv run task prek-install` and confirm `.git/hooks/pre-commit`, `.git/hooks/pre-push`, `.git/hooks/commit-msg` are populated

**Note:** prek 0.4.4 does not support `continue-on-error` at hook level (ignored with warning). Ruff/pyright failures will block pre-push until the 197 pre-existing issues are fixed. This is a prek-version limitation, not a config bug.
- [x] 4.4 Run a no-op `git commit --allow-empty -m "test(prek): verify hooks"` and confirm: pre-commit hooks run and commit lands (confirmed - commit succeeded with staged prek.toml)
- [x] 4.5 Test pre-push stage manually via `prek run --all-files --stage pre-push` (confirmed: ruff/pyright fail as expected, pytest/uv-lock pass, commitizen-branch needs remote tracking branch)

## 5. Sync and archive

- [x] 5.1 Commit the change with a Conventional Commits message: `chore(prek): expand prek config with stage split, pytest gate, pyright, gitleaks, commitizen`

**Note:** prek 0.4.4 does not support `continue-on-error` at hook level. Ruff/pyright failures will block pre-push until pre-existing issues are resolved. Documentation/design note: a follow-up change should either fix the 197 issues or find a prek-compatible mechanism (e.g., entry wrapper) for non-blocking hooks.
- [ ] 5.2 After the change lands and the user has run the new hooks at least once, sync the spec deltas via `openspec sync-specs --change "expand-prek-hooks"` and archive the change
