## Why

Suite has 864 tests across 86 files, but no systematic audit proves each test guards real system behavior. Some tests verify imports, function existence, or output format without exercising functional contracts. Others are near-duplicates or parametrize-only-sentinel blocks that pass even if the function under test is deleted. T25 audits the full suite to ensure every surviving test has a written justification linking it to one of four retention criteria.

## What Changes

- **Inventory**: catalog all 864 tests with file, function name, parametrize count, and marker classification.
- **Audit**: apply four retention criteria to each test:
  1. Exercita caminho de erro ou edge case.
  2. Testa integração entre módulos.
  3. Valida contrato de spec.
  4. Protege regressão conhecida.
- **Action**: tests that match zero criteria are removed. Tests that are near-duplicates collapse into parametrize. Tests that only assert `isinstance`, `import`, or sentinel-only parametrize blocks are rewritten as behavioral tests or removed.
- **Justification manifest**: `tests/AUDIT.md` lists every surviving test with its retention category.

## Capabilities

### New Capabilities
- `test-suite-audit`: contract for the audit manifest, retention criteria, and justification format.

### Modified Capabilities
- `unit-test-effectiveness`: tighten requirements from T21's initial pass — add retention-criteria gate and justification-manifest requirement.
- `test-suite-quality`: add audit-manifest reference and forbid un-justified tests after T25.

## Impact

- `tests/` — primary target. Removals, rewrites, and parametrize collapses across ~86 files.
- `tests/AUDIT.md` — new manifest file listing every surviving test with justification.
- `openspec/specs/unit-test-effectiveness/spec.md` — delta spec adding retention-criteria gate.
- `openspec/specs/test-suite-quality/spec.md` — delta spec adding audit-manifest reference.
- `openspec/specs/test-suite-audit/spec.md` — new spec for the audit manifest contract.
- Coverage and mutation baselines may shift; re-baseline after audit.
