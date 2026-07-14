## 1. pyproject.toml — remove global coverage from addopts

- [x] 1.1 Remove `--cov=src/omaha --cov-report=xml:reports/coverage.xml` from `[tool.pytest.ini_options] addopts`, keeping `-q --ignore=tests/e2e/_disabled`
- [x] 1.2 Verify `addopts` still contains the non-coverage flags (`-q`, `--ignore=tests/e2e/_disabled`)

## 2. pyproject.toml — add explicit coverage flags to fast-lane tasks

- [x] 2.1 Add `--cov=src/omaha --cov-report=xml:reports/coverage.xml` to `test-unit` taskipy command
- [x] 2.2 Add `--cov=src/omaha --cov-report=xml:reports/coverage.xml` to `test-integration` taskipy command
- [x] 2.3 Verify `coverage` task already has `--cov-report=term-missing --cov-report=xml:reports/coverage.xml` (no change needed)

## 3. pyproject.toml — add --no-cov to browser-lane tasks

- [x] 3.1 Add `--no-cov` to `test-e2e` taskipy command
- [x] 3.2 Add `--no-cov` to `test-bdd` taskipy command
- [x] 3.3 Verify `test-visual` already has `--no-cov` (no change needed)

## 4. Validation

- [x] 4.1 Run `uv run task test-unit` — confirm coverage output appears and `reports/coverage.xml` is written
- [x] 4.2 Run `uv run task test-e2e` — confirm no coverage output and no `reports/coverage.xml` written
- [x] 4.3 Run `uv run task test-bdd` — confirm no coverage output and no `reports/coverage.xml` written
- [x] 4.4 Run `uv run task test-visual` — confirm no coverage output (already has --no-cov)
- [x] 4.5 Run `uv run task coverage` — confirm term-missing + XML produced as before

## 5. Documentation

- [x] 5.1 Update `README.md` Tests section to clarify coverage is opt-in via `task coverage` and browser lanes run without it
- [x] 5.2 Update `tests/PERFORMANCE.md` lane description if coverage references need updating
