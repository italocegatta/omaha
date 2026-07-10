## Context

Suite audit shows red surface in BDD and e2e browser/workflow tests. The failure mix suggests stale assertions plus some genuine regressions in the visible navigation/import flows.

## Goals / Non-Goals

**Goals:**
- Restore suite signal on canonical regression families.
- Correct smallest wrong side: code, test, or spec.
- Keep change isolated to test-health and contract alignment.

**Non-Goals:**
- New features.
- UI redesign.
- Runtime architecture changes.
- Broad refactors outside failing paths.

## Decisions

- Fix failures in dependency order: shared fixtures and glue first, then family-specific assertions, then focused verification.
- Treat specs as source of truth when tests contradict them; only change specs when the current contract is actually wrong.
- Prefer narrow edits over generalized test rewrites so the root cause stays visible.

## Risks / Trade-offs

- Multiple unrelated failures can hide each other -> address shared fixtures before per-test churn.
- A stale test may look like a product bug -> compare against owning spec before touching runtime code.
- Browser-flow fixes may require selector or wait updates -> keep those changes local to failing scenario.

## Migration Plan

1. Reproduce and classify failing families.
2. Fix shared glue or fixture issues first.
3. Repair stale expectations or runtime regressions per family.
4. Re-run focused suites, then full suite.
5. Update spec text only when the contract changed.

## Open Questions

- Which failures are pure test drift versus real regressions?
- Do any failures require spec clarification before code changes?
