## Context

The project uses `prek` (Rust-based pre-commit replacement) for git-hook automation. The current `prek.toml` (46 lines) defines seven hooks — all on the default `pre-commit` stage — covering file sanity (`trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`, `check-added-large-files`), ruff format + lint, and `detect-private-key`. There is no test gate, no type check, no secret scan, no lockfile sync, no commit-message validation.

A reference configuration from a sibling project (Python + uv + pytest + pyright + commitizen) demonstrates a stage-split design:

- `pre-commit` runs fast, non-mutating checks plus a pytest gate (~1s).
- `pre-push` runs mutating hooks (format, lint-fix, whitespace/EOF) plus slow checks (full pytest, pyright) plus commitizen-branch validation.
- `commit-msg` runs commitizen for message-format validation.

The reference also pins `ruff` to `v0.14.3` and uses `additional_dependencies` to give pyright access to project deps in its isolated venv. The current `prek.toml` pins `ruff` to `v0.6.9`.

A baseline measurement on the current codebase:

- Ruff v0.6.9 reports 171 errors (`E501: 123, SIM102: 25, F841: 7, SIM105: 7, B007: 5, SIM108: 4`).
- Ruff format would reformat 4 files.
- Pyright (basic mode, with `.venv` configured) reports 26 errors.
- `pytest -m unit` runs 121 tests in 1.19s.
- `pytest` (full) runs 335 tests in 142.06s.

## Goals / Non-Goals

**Goals:**

- Port the reference's stage-split design to omaha, keeping only hooks that provide clear value given the project's tech stack.
- Land the new hook infrastructure in a state that does not block existing WIP commits, by marking the hooks that would fail on the current codebase as `continue-on-error: true`.
- Add a pytest gate on both `pre-commit` (unit, fast) and `pre-push` (full) to satisfy the requirement "antes do push quero que todos os testes passem".
- Add pyright basic-mode type checking scoped to `src/omaha`.
- Add a `prek-install` taskipy shortcut for hook installation.

**Non-Goals:**

- Fixing the 171 ruff errors and 26 pyright errors. That work is a follow-up change.
- Adding codespell. The project's HTML templates under `src/omaha/templates/` contain Portuguese strings (`Selecione`, `Internacional`, `RF Pos`) that produce false positives.
- Adding pyright coverage of `tests/`. Tests use fixtures, mocks, and `monkeypatch` that are noisy in basic mode; their correctness is already covered by pytest.
- Adding CI configuration. The change documents the `.venv` prerequisite for any future CI pipeline but does not introduce one.
- Tightening pyright to `strict` or `standard` mode. `basic` is the level that matches the reference and produces actionable signal without exhaustive type annotations.

## Decisions

### Stage split: pre-commit / pre-push / commit-msg

**Decision:** Mutating hooks move from `pre-commit` to `pre-push`. Slow checks (full pytest, pyright) also go on `pre-push`. The pytest unit gate is the only test hook on `pre-commit`.

**Rationale:** The reference's rationale (paraphrased) — mutating hooks on `pre-commit` cause the index to churn on every WIP commit. A failed commit blocked by a mutating hook requires `git add` again. Pre-push mutating hooks run once, and a failed push means "format and re-push" without index churn.

**Alternatives considered:**

- Keep everything on `pre-commit` (status quo). Rejected: WIP commits churn the index, and there's no place for the full pytest gate that the user explicitly asked for.
- Put pytest full on `pre-commit` (the reference's choice for their 1-2s test suite). Rejected: omaha's full suite is 142s — too slow for commit-time blocking.

### Two pytest hooks, not one

**Decision:** `pytest-unit` on `pre-commit` runs `pytest -m unit`. `pytest` on `pre-push` runs `pytest` (full suite).

**Rationale:** The user asked for "antes do push quero que todos os testes passem" — that maps directly to a `pre-push` full gate. Adding a `pre-commit` unit gate is belt-and-suspenders: it catches unit regressions at commit time (fast) so the pre-push gate sees cleaner code.

**Alternatives considered:**

- `pre-commit` unit only (no pre-push). Rejected: doesn't satisfy the "antes do push" requirement.
- `pre-push` full only (no pre-commit unit). Rejected: slower feedback loop for unit regressions.

### Hardcoded `./.venv/bin/python` for pytest hooks

**Decision:** Local pytest hook entries use `./.venv/bin/python -m pytest` (with `-m unit` for the unit hook).

**Rationale:** Matches the reference. The project's `omaha` package is installed as editable in `.venv` via `[tool.hatch.build.targets.wheel]` + `[tool.uv] package = true`. The editable `.pth` file points at `src/`, so the venv's Python imports the working-tree source. Using `uv run pytest` would work equivalently but the reference documents a "stale-global-wheel trap" where the system Python imports a uv-tool-installed copy instead of the working tree. Explicit venv path removes that risk.

**Trade-off:** In CI, `.venv` must exist before the hook runs (`uv sync` first). The change does not introduce CI, but any future CI must `uv sync` before invoking prek.

### `continue-on-error: true` on ruff + pyright, not on file-sanity hooks

**Decision:** Only the hooks that fail on the current codebase get `continue-on-error: true`. The 171 ruff errors, the 4 format-only files, and the 26 pyright errors mean the ruff and pyright hooks would block every commit and push. The other hooks (`check-yaml`, `check-toml`, `check-json`, `check-merge-conflict`, `check-added-large-files`, `detect-private-key`, `gitleaks`, `validate-pyproject`, `uv-lock`, the pytest hooks) pass on the current codebase and stay blocking.

**Rationale:** Blocking hooks that pass = useful friction. Blocking hooks that fail constantly = ignored friction. The user explicitly chose "cleanup depois" — `continue-on-error` is the mechanism that lets the infrastructure land cleanly while preserving the visibility of the existing problems.

**Removal:** A follow-up change fixes the 197 issues and removes the three `continue-on-error: true` flags.

### Pyright basic mode, `include = ["src/omaha"]`, `venvPath = "."`, `venv = ".venv"`

**Decision:** Pyright runs in `basic` mode over `src/omaha` only, with the venv at `.venv`.

**Rationale:**

- `basic` mode matches the reference and catches missing imports, undefined variables, and obvious type mismatches without requiring exhaustive annotations.
- Excluding `tests/` avoids noise from fixtures and `monkeypatch`. The test suite is already gated by pytest.
- `venvPath = "."` + `venv = ".venv"` makes pyright resolve `import fastapi`, `import sqlalchemy`, etc., from the project's actual venv. Without this, every import reports `reportMissingImports` and the real type errors drown in config noise.

### Commitizen: `commit-msg` + `pre-push` branch check

**Decision:** Add `commitizen` (commit-msg stage) for message-format validation, and `commitizen-branch` (pre-push stage) for branch-name validation.

**Rationale:** The commit history already follows Conventional Commits (`fix(import-modal):`, `test(architecture):`, `docs(02):`...). The hooks codify the convention that's already in use. `commitizen-branch` is a soft check — it warns rather than blocks by default — so branches named `fix/import-modal` won't break the push.

**Trade-off:** The reference uses `commitizen-branch` without a `stages` attribute; it runs on both `pre-commit` and `pre-push` by default. This change pins it to `pre-push` only to avoid running it on every commit.

### gitleaks + detect-private-key both kept

**Decision:** Keep `detect-private-key` (current config) AND add `gitleaks`.

**Rationale:** `detect-private-key` runs in `builtin` (zero install, ~10ms) and catches PEM blocks. `gitleaks` (~100ms) catches PEM blocks plus broker credentials, API keys, and other secret patterns. Cost of running both is marginal. The alternative — drop `detect-private-key` in favor of `gitleaks` only — saves 10ms per commit in exchange for a single point of failure for secret detection.

### `uv-lock` on pre-push, after ruff hooks

**Decision:** `uv-lock` runs on `pre-push` with priority 3 (same as `trailing-whitespace` and `end-of-file-fixer`).

**Rationale:** Lockfile changes are a mutation, so they belong on pre-push. Priority 3 (alongside other pre-push mutating hooks) means it runs after `ruff-format` and `ruff --fix` but before the test/type-check gates — so the test suite runs against the updated lockfile if the lockfile changed.

## Risks / Trade-offs

- **[Risk]** `continue-on-error: true` on ruff and pyright makes them noisy (every commit shows a failed-hook line) but non-blocking. **Mitigation:** The noise is the intended signal — the user sees the existing problems on every commit. A follow-up change removes the flag once the issues are fixed.
- **[Risk]** Pre-push full pytest adds 142s to every `git push`. **Mitigation:** User explicitly chose this option. The cost is a known, bounded addition to push latency. If friction emerges, downgrade to pre-push unit-only in a follow-up.
- **[Risk]** Hardcoded `./.venv/bin/python` path in local hooks breaks in any environment where the venv lives elsewhere (e.g., Docker). **Mitigation:** No CI exists today. The Docker `Dockerfile` will need to `uv sync` before any prek invocation; this is documented in `Dockerfile` comments if/when CI is added.
- **[Risk]** Pyright `additional_dependencies` in the prek hook declares FastAPI, SQLAlchemy, pydantic, and pytest as type-resolution deps. If those versions drift from the actual `pyproject.toml` deps, type resolution can be subtly wrong. **Mitigation:** Use the floor version (`>=`) in `additional_dependencies` to match the project's actual constraints. Update both when bumping the hook.
- **[Risk]** gitleaks with default rules may produce false positives on `package-lock.json` (long SHA hashes that resemble tokens). **Mitigation:** Run `prek run --all-files` once after the change lands to see the baseline. If noisy, add a `.gitleaks.toml` with a `[[allowlists]]` entry for `package-lock.json`, `package.json`, and `uv.lock`.
- **[Risk]** `commitizen-branch` on pre-push may warn on branches named outside the `feat|fix|chore|...` pattern. **Mitigation:** By default, `commitizen-branch` reports a warning but does not fail. If it becomes friction, switch to the `commitizen-branch --strict` mode in a follow-up.

## Migration Plan

1. Apply the change: edit `prek.toml` and `pyproject.toml`, add the `prek-install` task.
2. Run `uv run prek run --all-files` to see the baseline. The ruff and pyright hooks will report failures (expected — `continue-on-error` is set). All other hooks should pass.
3. Run `uv run task prek-install` to populate `.git/hooks/`.
4. Commit the change. The pre-commit hook runs `pytest -m unit` (~1.2s) and reports ruff/pyright failures (non-blocking). The commit lands.
5. A follow-up change fixes the 197 ruff + pyright issues, removes the three `continue-on-error: true` flags, and the gates become fully blocking.

**Rollback:** Revert the change. The new hooks are additive; the only files modified are `prek.toml`, `pyproject.toml`, and (for the task) the `taskipy.tasks` section. The prek install step is reversible with `uv run prek uninstall`.

## Open Questions

- None remaining at design time. The `gitleaks` allowlist and `commitizen-branch` strictness are flagged as future-tuning items, not design-time decisions.
