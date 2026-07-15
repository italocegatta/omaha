## Context

The test suite has 864 tests across 86 files. No systematic audit proves each test guards real system behavior. Previous T21 pass handled marker classification and duplicate stubs, but did not verify that each test exercises a behavioral contract. Some tests assert `isinstance`, function existence, or sentinel-only parametrize blocks that pass even if the function under test is deleted.

Retention criteria (from roadmap Notes):
1. Exercita caminho de erro ou edge case.
2. Testa integração entre módulos.
3. Valida contrato de spec.
4. Protege regressão conhecida.

## Goals / Non-Goals

**Goals:**
- Inventory all 864 tests with file, function name, parametrize count, and marker.
- Classify each test against the four retention criteria.
- Remove tests matching zero criteria.
- Collapse near-duplicates into parametrize.
- Rewrite import-only / isinstance / sentinel-only tests as behavioral tests or remove.
- Produce `tests/AUDIT.md` manifest listing every surviving test with justification.

**Non-Goals:**
- Increase mutation kill rate (T26 handles `policy.py`).
- Change marker classification (T24 already fixed mis-tagged files).
- Rewrite the entire suite from scratch.
- Touch e2e/Playwright or BDD test logic (only audit, not refactor harness).

## Decisions

### D1: Audit manifest format — `tests/AUDIT.md`

Each surviving test gets a one-line entry:

```
| test_file.py::test_name | retention_category | justification |
```

Categories: `error-path`, `integration`, `spec-contract`, `regression-guard`.

**Rationale**: Markdown table is human-readable, grep-friendly, and reviewable in PRs. CSV or JSON would be harder to diff.

### D2: Three-phase execution

- **Phase 1 — Inventory**: `pytest --collect-only` + script to generate initial manifest skeleton with all test names.
- **Phase 2 — Audit**: manual/agent review of each test against criteria. Mark `keep` (with category) or `remove`.
- **Phase 3 — Action**: execute removals, rewrites, parametrize collapses. Update manifest.

**Rationale**: separating inventory from action prevents accidental removal of tests that need rewriting instead.

### D3: Parametrize collapse rule

Two or more tests that differ only by input/expected and share the same retention category collapse into one `@pytest.mark.parametrize` test. The collapsed test MUST keep every input/expected pair from the originals.

**Rationale**: existing spec (`unit-test-effectiveness`) already mandates this. T25 enforces it at audit time.

### D4: Sentinel-only parametrize blocks → rewrite or remove

A parametrize block whose every expected value is `None` (or equivalent sentinel) is a false-positive bait: if the function under test were deleted, every case would still pass. These MUST include at least one positive case or be removed.

**Rationale**: `test-suite-quality` spec already forbids this pattern. T25 catches remaining instances.

### D5: Scope boundary — audit, not refactor

T25 does NOT:
- Change production code (except removing dead test helpers if they're only used by removed tests).
- Reorganize test directory structure.
- Touch e2e Playwright harness or BDD step definitions (audit only, remove if justified).

## Risks / Trade-offs

- **Risk**: removing a test that guarded a subtle regression → **Mitigation**: retention category `regression-guard` requires written justification naming the regression.
- **Risk**: audit manifest drifts from actual tests after future changes → **Mitigation**: spec requires `tests/AUDIT.md` update in same slice that adds/removes tests.
- **Risk**: phase 2 (audit) is labor-intensive for 864 tests → **Mitigation**: agent-driven review with structured output; human spot-check on borderline cases.
