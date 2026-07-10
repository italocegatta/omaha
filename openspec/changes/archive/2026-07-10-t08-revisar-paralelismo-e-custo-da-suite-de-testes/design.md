## Context

Current suite shape has three coupled problems. First, bucket ownership drifted: `tests/conftest.py`, task help text, `prek.toml`, and `.github/workflows/ci.yml` no longer describe the same families. Second, T07 found late-suite BDD flakes that reproduce only after many passes, which points at fixture/workflow/load behavior instead of a single browser assertion. Third, browser-backed suites still pay repeated launch/setup cost, especially in BDD and visual flows, so wall time is dominated by harness overhead before product regressions are even classified.

Known constraints from exploration stay binding here:

- no `pytest-xdist` today;
- BDD stays serial by contract unless repeated-run evidence proves a safe change;
- e2e and visual fixtures are valid targets for reuse review;
- large audit tests are cost centers that need explicit bucket ownership;
- scope is test harness and bucket architecture only.

## Goals / Non-Goals

**Goals:**
- Publish one canonical bucket map across markers, tasks, hooks, and CI.
- Reproduce and classify late-suite BDD flakes as harness behavior, then stabilize or document the risky edge.
- Reduce browser-backed suite cost only through safe fixture/resource reuse.
- Leave a written serial vs parallelizable vs too-risky decision record for heavy families.

**Non-Goals:**
- Product/browser regression fixes owned by T07, T09, T10, or T11.
- Screenshot baseline refreshes.
- CSV pipeline correctness work.
- Rebalance contract or schema fixes.
- Broad test deletion unless duplicate coverage is obvious and canonically covered already.

## Decisions

### D1. Canonical bucket map comes first; all entrypoints delegate to it

T08 will treat the marker allowlist in `tests/conftest.py` plus named `task` commands as the primary bucket definition. Hook entries and CI jobs should delegate to the same named buckets instead of maintaining separate raw pytest expressions. This keeps selection, help text, and operational docs in one place.

**Alternatives considered:**
- Keep raw pytest selectors in each surface: rejected; this is current drift source.
- Move all logic into CI only: rejected; local operators still need trustworthy buckets.

### D2. BDD remains serial; investigate cost before concurrency

BDD already has a serial contract in `tests/bdd/README.md`, and exploration found no xdist today. T08 will therefore investigate late-suite flake sources in serial mode first: repeated live-server startup, per-test browser launch, DB/profile wipe cost, and workflow waits. Parallel BDD is out unless repeated-run evidence shows fixture isolation can survive it.

**Alternatives considered:**
- Add xdist immediately: rejected; violates known contract and risks masking flake with more nondeterminism.
- Move BDD failures back into product slices now: rejected; T07 already showed harness symptoms cross scenario boundaries.

### D3. Reuse outer browser resources only where isolation stays function-scoped

Potential runtime wins are most likely in e2e and visual suites, where browser/server launch cost repeats often. T08 may reuse outer resources such as a browser process or server fixture, but each test must keep isolated page/context state unless repeated-run verification proves a wider scope safe. If a reuse idea conflicts with Playwright event-loop safety or leaks session state, the slice records it as too risky and stops there.

**Alternatives considered:**
- Leave all browser fixtures per-test: simplest, but preserves avoidable wall time.
- Reuse full page/context across tests: rejected; state leakage would trade speed for false greens.

### D4. Heavy families need explicit ownership, not silent omission

Large audit tests, BDD, e2e, and visual families each need an explicit home in tasks, hooks, and CI. T08 will not solve slowness by silently dropping a family from one gate. If a family stays out of a hook or bucket, the decision record must name where it runs and why.

**Alternatives considered:**
- Hide slow families behind undocumented ignores: rejected; creates green signal drift.
- Mass-delete slow tests: rejected; outside scope unless duplicate coverage is already canonical elsewhere.

## Risks / Trade-offs

- **BDD root cause may stay partially unresolved** → still ship explicit risky-bucket decision plus reproducible focused commands so T07 has clean handoff.
- **Fixture reuse can leak state** → keep contexts/pages function-scoped and use repeated-run verification before widening scope.
- **Bucket realignment can surprise operators** → align help text, hook comments, CI job names, and README in same slice.
- **Runtime wins may be modest** → even small wins matter if the suite contract becomes understandable and stable.

## Migration Plan

1. Inventory current bucket definitions and mismatches across conftest, tasks, hooks, and CI.
2. Reproduce late-suite BDD flake with task-driven repeated runs and classify dominant cost centers.
3. Apply safe harness-only changes for bucket alignment and fixture reuse.
4. Update operator-facing docs/comments with the decision matrix.
5. Re-run focused bucket commands, repeated BDD checks, and OpenSpec spec verification.

## Verification Plan

- `uv run task test-unit`
- `uv run task test-integration`
- `uv run task test-bdd -- -k <late-suite-slice>` repeated as needed for reproduction/stability proof
- `uv run task test-e2e`
- `uv run task test-visual`
- `openspec list --specs`

Focused selectors are allowed for repeated BDD investigation, but verification stays task-driven so bucket ownership is what gets tested.

## Open Questions

- Can e2e browser-process reuse return safely without reintroducing event-loop pollution?
- Does visual-suite cost fall enough with shared browser setup to justify extra fixture complexity?
- Should audit-heavy tests stay in `integration` or move to a dedicated named bucket with mirrored CI ownership?
