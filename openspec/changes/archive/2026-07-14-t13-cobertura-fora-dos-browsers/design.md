## Context

The test suite has two execution lanes:

- **Fast lane**: unit (17s) + integration (219s). These are pure Python tests using httpx TestClient and SQLAlchemy — no browser.
- **Browser lane**: e2e (195s, Playwright), BDD (198s, pytest-bdd + real Chromium), visual (82s, Playwright visual regression).

Currently, `pyproject.toml` `[tool.pytest.ini_options] addopts` carries `--cov=src/omaha --cov-report=xml:reports/coverage.xml` globally, which means every pytest invocation — including browser-heavy lanes — pays the coverage instrumentation cost and generates XML. CI already separates lanes correctly: the `coverage` job runs after `test-unit` + `test-integration` and uploads the XML; browser jobs run without coverage. But local dev inherits the global addopts, so `task test-e2e` and `task test-bdd` silently run with coverage.

`task test-visual` already has an explicit `--no-cov` override in its taskipy command (line 217 of pyproject.toml). The e2e and bdd tasks do not.

## Goals / Non-Goals

**Goals:**
- Remove coverage instrumentation from browser-heavy lanes (e2e, bdd, visual) in local dev.
- Keep coverage reporting in the fast lane (unit + integration) via explicit flags.
- Make `task coverage` the single canonical command that produces `reports/coverage.xml`.
- Align local dev behavior with CI semantics.

**Non-Goals:**
- Changing test behavior, adding/removing tests, or modifying test assertions.
- Changing CI workflow (already correct).
- Adding coverage thresholds (`--cov-fail-under`) — that's a separate slice.
- Parallelizing any test lane.

## Decisions

### Decision 1: Move coverage flags from global addopts to per-task commands

**Choice:** Remove `--cov` and `--cov-report` from `[tool.pytest.ini_options] addopts`. Add them explicitly to `task test-unit`, `task test-integration`, and `task coverage` taskipy commands.

**Rationale:** Global addopts is a blunt instrument — it applies to every pytest invocation including ad-hoc `pytest tests/some_file.py`. Moving coverage to the task layer makes intent explicit: you get coverage when you ask for it (`task test-unit`, `task coverage`), not as a side effect.

**Alternatives considered:**
- Add `--no-cov` to `test-e2e` and `test-bdd` (like `test-visual` already has). Rejected: this is the inverse approach — keeping the global flag and suppressing it per-task. It's fragile: any new task must remember to add `--no-cov`. Moving coverage to explicit tasks is cleaner.
- Use a pytest plugin to conditionally enable coverage. Rejected: overengineered for a config change.

### Decision 2: Preserve `task coverage` as the canonical coverage producer

**Choice:** `task coverage` keeps its current behavior: `pytest -m 'unit or integration' --ignore=tests/audit_integration --cov=src/omaha --cov-report=term-missing --cov-report=xml:reports/coverage.xml`.

**Rationale:** This task is already the only intended producer of `reports/coverage.xml`. No change needed — it already has the explicit flags. After removing the global addopts, it becomes the *only* command that produces coverage XML, which is the desired state.

### Decision 3: Add `--no-cov` safety net to browser tasks

**Choice:** Add `--no-cov` to `test-e2e`, `test-bdd`, and keep it on `test-visual`.

**Rationale:** Even though global addopts will no longer carry `--cov`, a developer might pass `--cov` via `PYTEST_ADDOPTS` env var or a local pytest.ini. The `--no-cov` flag is a defensive guard that ensures browser lanes never produce coverage regardless of environment. Low cost, high certainty.

## Risks / Trade-offs

- **Risk:** A downstream tool or script reads `reports/coverage.xml` after running `task test-e2e` and breaks when the file is missing. **Mitigation:** Checked — CI already doesn't upload coverage from e2e. The only canonical producer is `task coverage`. README and PERFORMANCE.md already document this separation.
- **Risk:** Developer runs `pytest` directly (not via task) and gets no coverage by default. **Mitigation:** This is actually desired behavior — direct pytest invocations are ad-hoc debugging, not coverage collection. The `task coverage` command is the documented path.
- **Trade-off:** Slightly more verbose taskipy commands (explicit `--cov` flags). Acceptable for the clarity gained.

## Migration Plan

1. Edit `pyproject.toml`: remove `--cov=src/omaha --cov-report=xml:reports/coverage.xml` from `addopts`.
2. Edit `pyproject.toml`: add `--cov=src/omaha --cov-report=xml:reports/coverage.xml` to `test-unit` and `test-integration` taskipy commands.
3. Edit `pyproject.toml`: add `--no-cov` to `test-e2e` and `test-bdd` taskipy commands.
4. Verify `task test-unit`, `task test-integration`, `task coverage` still produce coverage.
5. Verify `task test-e2e`, `task test-bdd`, `task test-visual` do NOT produce coverage XML.
6. Update `README.md` Tests section to clarify coverage is opt-in via `task coverage`.
7. Update `tests/PERFORMANCE.md` lane description if needed.

Rollback: revert pyproject.toml and README.md changes. No data migration needed.

## Open Questions

None. The change is configuration-only with clear scope.
