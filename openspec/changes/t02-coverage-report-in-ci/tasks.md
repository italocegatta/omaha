## 1. Coverage configuration in pyproject.toml

- [x] 1.1 Add `[tool.coverage.run]` block with `source = ["src/omaha"]` to `pyproject.toml`
- [x] 1.2 Add `[tool.coverage.report]` block with `exclude_lines` for `pragma: no cover`, `if __name__ == "__main__":`, `raise NotImplementedError`, `if TYPE_CHECKING:`
- [x] 1.3 Add `addopts = "--cov=src/omaha --cov-report=xml:reports/coverage.xml"` to existing `[tool.pytest.ini_options]` block (do NOT remove existing `markers` / `addopts` content — extend only)
- [x] 1.4 Verify `task coverage` still produces term-missing + XML output locally (`uv run task coverage` then `ls reports/`)
- [x] 1.5 Verify `pytest --cov=src/omaha` (without `task coverage`) also produces XML (proves `addopts` global works)

## 2. .gitignore update

- [x] 2.1 Add `reports/coverage.xml` to `.gitignore` (preserve the existing `coverage/` entry — distinct entry for the new artifact path)
- [x] 2.2 Confirm `reports/` directory is committed empty (the spec says "directory exists" — check git status shows `?? reports/` or that it's tracked-but-empty; if untracked-empty, add a `.gitkeep` or leave untracked) — **resolved**: `reports/` already tracked with `.gitkeep` + `contrast_audit.html` committed; no action needed.

## 3. Workflow file creation

- [x] 3.1 Create `.github/workflows/ci.yml` with `name: ci`, triggers `push` (branches: `[main]`) + `pull_request` (branches: `[main]`)
- [x] 3.2 Add single job `lint` running `ruff check src tests alembic` + `ruff format --check src tests alembic` on `ubuntu-latest` with Python 3.12 (from `.python-version`) + `actions/setup-python@v5` with `cache: "uv"`
- [x] 3.3 Add job `test-unit` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-unit`
- [x] 3.4 Add job `test-integration` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-integration` with `timeout-minutes: 15`
- [x] 3.5 Add job `test-bdd` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-bdd` with `timeout-minutes: 15`
- [x] 3.6 Add job `coverage` (needs: test-unit, test-integration) running `mkdir -p reports` then `uv run pytest -m "unit or integration" -q --ignore=tests/e2e/_disabled` (addopts provides `--cov` flags) then `actions/upload-artifact@v4` with name `coverage-report` and path `reports/coverage.xml`

## 4. Local verification

- [x] 4.1 Run `uv run task test-unit` locally — **271 passed / 2 skipped** (matches R04 baseline)
- [x] 4.2 Run `uv run task test-integration` locally — **369 passed / 2 skipped** (matches R02/R03/R04 baseline)
- [x] 4.3 Run `uv run task test-bdd` locally — **51 passed** (matches T05 baseline)
- [x] 4.4 Run `uv run task coverage` locally — **640 passed / 4 skipped / 92% line coverage**, `reports/coverage.xml` is Cobertura-compatible (`<coverage version=... line-rate="0.9163" ...>` + `<package name=...>` + `<class filename=...>` structure)
- [x] 4.5 Run `uv run pytest tests/test_seed.py::test_seed_creates_user_and_profiles --cov=src/omaha` (single test) — XML written, no term-missing bloat
- [x] 4.6 Run `ruff check src tests alembic` + `ruff format --check src tests alembic` — both green (All checks passed / 156 files already formatted)

## 5. CI verification (BLOCKED — requires operator + GitHub Actions runner)

- [ ] 5.1 Push branch `feat/t02-coverage-report-in-ci` to origin — **blocked: requires operator (no `git push` in this sandbox)**
- [ ] 5.2 Open PR against `main` — **blocked: requires operator**
- [ ] 5.3 Confirm all 5 jobs pass in Actions tab (`lint`, `test-unit`, `test-integration`, `test-bdd`, `coverage`) — **blocked: requires Actions runner**
- [ ] 5.4 Download `coverage-report` artifact from the workflow run — validate `coverage.xml` has `<coverage line-rate=` and `<package name=...>` structure (Cobertura-compatible) — **blocked: requires Actions runner**
- [ ] 5.5 Confirm workflow run time is < 10 min (cache hit + parallel lint/unit/integration) — **blocked: requires Actions runner**

## 6. Roadmap + spec sync

- [x] 6.1 Update `openspec/roadmap.md` slice T02 block `Progress` — set `Proposed: done 2026-07-06`, link to `openspec/changes/t02-coverage-report-in-ci/` — done in propose phase
- [x] 6.2 Verify `openspec validate t02-coverage-report-in-ci --json` returns `valid: true` — confirmed
- [x] 6.3 Verify `openspec list --specs` shows new capability `ci-coverage-pipeline` — confirmed (41 total / 0 errors / new spec pending archive)