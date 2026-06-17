## Why

The current `prek.toml` is minimal — only file-sanity hooks, ruff, and `detect-private-key`. Every hook runs on `pre-commit` (default stage), so mutating hooks like `ruff --fix` and `end-of-file-fixer` churn the index on every WIP commit, and there is no test gate before commit or push. A reference configuration from another project demonstrates a stage-split design (fast checks on pre-commit, mutating/slow checks on pre-push) with a pytest gate, a type-check gate, secret scanning, lockfile sync, and conventional-commit validation. This change ports that design to omaha, scoped to the hooks that provide clear value given the project's tech stack (FastAPI, SQLAlchemy 2, Jinja2, Alpine.js) and codebase size.

Pre-existing lint and type errors (171 ruff errors on v0.6.9, 26 real pyright errors at basic mode) are intentionally **not** fixed in this change. The new hooks that would fail on the current codebase are marked `continue-on-error: true` so the infrastructure lands cleanly; a follow-up change addresses the cleanup.

## What Changes

- Restructure `prek.toml` into a stage-split layout: fast checks on `pre-commit`, mutating and slow checks on `pre-push`, message-format validation on `commit-msg`.
- Add new hooks: `check-merge-conflict`, `check-json`, `validate-pyproject`, `gitleaks`, `uv-lock`, `commitizen`, `commitizen-branch`, `pyright`.
- Move existing mutating hooks (`ruff-format`, `ruff --fix`, `trailing-whitespace`, `end-of-file-fixer`) from `pre-commit` to `pre-push` so WIP commits do not churn the index.
- Add two `local` pytest gates: `pytest-unit` on `pre-commit` (runs `pytest -m unit`, ~1.2s) and `pytest` on `pre-push` (runs the full suite, ~142s).
- Mark `ruff`, `ruff-format`, and `pyright` with `continue-on-error: true` to avoid blocking the 197 pre-existing issues; these hooks run, report failures, and pass through. A follow-up change fixes the issues and removes the `continue-on-error` flags.
- Bump `ruff-pre-commit` from `v0.6.9` to `v0.14.3` to match the reference pin.
- Add `[tool.pyright]` to `pyproject.toml` with `typeCheckingMode = "basic"`, `pythonVersion = "3.12"`, `include = ["src/omaha"]`, `venvPath = "."`, `venv = ".venv"`.
- Add a `prek-install` taskipy shortcut (`uv run prek install`) so the hook installation step is documented in the dev workflow.
- Update `AGENTS.md` test-marker rule entry is **not** required — the existing `_INTEGRATION_PREFIXES` allow-list in `tests/conftest.py` already covers the suite.

## Capabilities

### New Capabilities

- `prek-hooks`: Defines the project's pre-commit / pre-push / commit-msg hook set, their stage assignment, and their fail mode (blocking vs. `continue-on-error`).

### Modified Capabilities

- `dev-tasks`: Add a `prek-install` taskipy shortcut that runs `uv run prek install` to populate `.git/hooks/`. Existing tasks (`install`, `lint`, `format`, `check`) are not changed.

## Impact

- **`prek.toml`**: grows from 46 to ~80 lines. New repos: `astral-sh/uv-pre-commit`, `commitizen-tools/commitizen`, `gitleaks/gitleaks`, `abravalheri/validate-pyproject`, `RobertCraigie/pyright-python`, plus one `local` repo with two hooks.
- **`pyproject.toml`**: adds a `[tool.pyright]` section (~10 lines). No other sections change.
- **Taskipy**: adds one task (`prek-install`).
- **CI**: no CI config exists today. The prek hooks assume a working `.venv` populated by `uv sync`; documentation in the change will note this prerequisite for any future CI pipeline.
- **Push latency**: every `git push` adds ~142s for the full pytest run. Commits are unaffected.
- **Commit latency**: every `git commit` adds ~1.2s for the unit pytest run.
- **Git hooks**: requires `uv run prek install` to be run once after the change lands. The taskipy shortcut `task prek-install` documents and automates this.
- **No new runtime dependencies** — pyright, gitleaks, commitizen, and ruff are fetched by the prek hooks themselves; pyright's `additional_dependencies` lists FastAPI, SQLAlchemy, pydantic, and pytest so type resolution works in the hook's isolated venv.
