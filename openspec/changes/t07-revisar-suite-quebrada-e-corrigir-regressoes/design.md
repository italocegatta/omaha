## Context

Suite audit shows broad red surface across BDD, e2e, visual, CSV seed flow, and rebalance glue/schema tests. The failure mix suggests a combination of stale assertions, contract drift, and at least some genuine regressions.

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

- Fix failures in dependency order: shared fixtures and glue first, then family-specific assertions, then full-suite verification.
- Treat specs as source of truth when tests contradict them; only change specs when the current contract is actually wrong.
- Prefer narrow edits over generalized test rewrites so the root cause stays visible.

## Risks / Trade-offs

- Multiple unrelated failures can hide each other -> address shared fixtures before per-test churn.
- A stale test may look like a product bug -> compare against owning spec before touching runtime code.
- Visual or BDD fixes may require baseline/data updates -> keep those changes local to the failing scenario.

## Migration Plan

1. Reproduce and classify failing families.
2. Fix shared glue or fixture issues first.
3. Repair stale expectations or runtime regressions per family.
4. Re-run focused suites, then full suite.
5. Update spec text or visual baselines only when the contract changed.

## Open Questions

- Which failures are pure test drift versus real regressions?
- Do any failures require spec clarification before code changes?
