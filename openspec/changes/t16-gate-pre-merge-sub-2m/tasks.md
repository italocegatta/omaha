## 1. Add `gate-fast` taskipy task (`pyproject.toml`)

- [x] 1.1 Add `gate-fast` task: `{ cmd = "uv run prek run --all-files && uv run pytest -m unit --cov=src/omaha --cov-report=xml:reports/coverage.xml", help = "Pre-merge fast gate: lint + unit tests, target < 2 min wall-clock" }`
- [x] 1.2 Update `check` task help text: add "(deprecated — use gate-fast)" suffix
- [x] 1.3 Verify `task gate-fast` runs successfully and completes under 2 min

## 2. Document lane split in `tests/PERFORMANCE.md`

- [x] 2.1 Add "Gate definitions" section after existing "Lanes de execução" section
- [x] 2.2 Document `gate-fast`: command, what it runs, what it excludes, timing target (< 2 min), baseline (~30s)
- [x] 2.3 Document full suite (`task test`): command, what it runs, baseline (~10+ min)
- [x] 2.4 Document browser lanes: commands, Playwright requirement, "not part of fast gate"
- [x] 2.5 Update the "Commands" section to include `gate-fast` in the command list

## 3. Verification

- [x] 3.1 Run `task gate-fast` and record wall-clock time (must be < 120s)
- [x] 3.2 Run `task lint` to verify lint step works standalone
- [x] 3.3 Run `task test-unit` to verify unit step works standalone
- [x] 3.4 Verify `task check` still works (backward compat)
