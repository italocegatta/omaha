## 1. Coverage configuration in pyproject.toml

- [ ] 1.1 Add `[tool.coverage.run]` block with `source = ["src/omaha"]` to `pyproject.toml`
- [ ] 1.2 Add `[tool.coverage.report]` block with `exclude_lines` for `pragma: no cover`, `if __name__ == "__main__":`, `raise NotImplementedError`, `if TYPE_CHECKING:`
- [ ] 1.3 Add `addopts = "--cov=src/omaha --cov-report=xml:reports/coverage.xml"` to existing `[tool.pytest.ini_options]` block (do NOT remove existing `markers` / `addopts` content — extend only)
- [ ] 1.4 Verify `task coverage` still produces term-missing + XML output locally (`uv run task coverage` then `ls reports/`)
- [ ] 1.5 Verify `pytest --cov=src/omaha` (without `task coverage`) also produces XML (proves `addopts` global works)

## 2. .gitignore update

- [ ] 2.1 Add `reports/coverage.xml` to `.gitignore` (preserve the existing `coverage/` entry — distinct entry for the new artifact path)
- [ ] 2.2 Confirm `reports/` directory is committed empty (the spec says "directory exists" — check git status shows `?? reports/` or that it's tracked-but-empty; if untracked-empty, add a `.gitkeep` or leave untracked)

## 3. Workflow file creation

- [ ] 3.1 Create `.github/workflows/ci.yml` with `name: ci`, triggers `push` (branches: `[main]`) + `pull_request` (branches: `[main]`)
- [ ] 3.2 Add single job `lint` running `ruff check src tests alembic` + `ruff format --check src tests alembic` on `ubuntu-latest` with Python 3.12 (from `.python-version`) + `actions/setup-python@v5` with `cache: "uv"`
- [ ] 3.3 Add job `test-unit` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-unit`
- [ ] 3.4 Add job `test-integration` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-integration` with `timeout-minutes: 15`
- [ ] 3.5 Add job `test-bdd` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-bdd` with `timeout-minutes: 15`
- [ ] 3.6 Add job `coverage` (needs: test-unit, test-integration) running `mkdir -p reports` then `uv run pytest --cov=src/omaha --cov-report=xml:reports/coverage.xml` then `actions/upload-artifact@v4` with name `coverage-report` and path `reports/coverage.xml`

## 4. Local verification

- [ ] 4.1 Run `uv run task test-unit` locally — confirm no regression vs pre-slice baseline (R04 archive: 271 pass / 2 skip)
- [ ] 4.2 Run `uv run task test-integration` locally — confirm no regression (R04 archive: 369 pass / 2 skip)
- [ ] 4.3 Run `uv run task test-bdd` locally — confirm no regression (T05 archive: 51 pass / 0 skip)
- [ ] 4.4 Run `uv run task coverage` locally — confirm `reports/coverage.xml` is created and is Cobertura-compatible (XML well-formed, contains `<coverage line-rate=...>`)
- [ ] 4.5 Run `uv run pytest --cov=src/omaha tests/test_x.py::test_one` (single test) — confirm XML is written and no term-missing bloat in output (or accept it per D-T02.5)
- [ ] 4.6 Run `ruff check src tests alembic` + `ruff format --check src tests alembic` — confirm green

## 5. CI verification

- [ ] 5.1 Push branch `feat/t02-coverage-report-in-ci` to origin
- [ ] 5.2 Open PR against `main`
- [ ] 5.3 Confirm all 5 jobs pass in Actions tab (`lint`, `test-unit`, `test-integration`, `test-bdd`, `coverage`)
- [ ] 5.4 Download `coverage-report` artifact from the workflow run — validate `coverage.xml` has `<coverage line-rate=` and `<package name=...>` structure (Cobertura-compatible)
- [ ] 5.5 Confirm workflow run time is < 10 min (cache hit + parallel lint/unit/integration)

## 6. Roadmap + spec sync

- [ ] 6.1 Update `openspec/roadmap.md` slice T02 block `Progress` — set `Proposed: done 2026-07-06`, link to `openspec/changes/t02-coverage-report-in-ci/`
- [ ] 6.2 Verify `openspec validate t02-coverage-report-in-ci --json` returns `valid: true`
- [ ] 6.3 Verify `openspec list --specs` shows new capability `ci-coverage-pipeline` with `requirements` count matching spec file