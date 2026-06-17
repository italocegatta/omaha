## Context

Seven tests fail on `uv run task test` — all pre-existing, none
introduced by `review-unit-tests-effectiveness` (verified via
`git stash`). The failures concentrate on the assets routes
(`/assets` and `/api/assets/{id}`) and on the e2e flows that
depend on them, so the blast radius is bounded to one module
(`src/omaha/routes/assets.py`) and the test files that exercise
it.

The proposal enumerates five plausible root causes. The design
goal here is to lay out a **decision procedure** that picks the
right fix once a developer has run each failing test under
`--tb=long -p no:cacheprovider` and compared the traceback
against the route decorator + handler body.

## Goals / Non-Goals

**Goals:**

- Reproduce each of the 7 failures with a full traceback and a
  side-by-side read of the route handler + the test helper.
- Land a minimal-surface fix per failure: smallest diff that
  resolves the divergence and locks it with a regression test
  at the cheapest layer.
- Avoid touching routes that the test suite does NOT exercise
  failures against (route-level regressions in unrelated
  modules are out of scope).
- Confirm the 7 failures resolve and no new tests break.

**Non-Goals:**

- Refactoring `routes/assets.py` for style, structure, or to
  satisfy a new design. The goal is to fix the divergence, not
  to redesign the module.
- Touching the audit tests, the marker infrastructure, or the
  conftest hook added by `review-unit-tests-effectiveness`.
- Adding coverage gates or new CI workflows.
- Renaming routes or handlers. The URL contract is what the
  tests pin; if a test expects `/api/assets/{id}` and the route
  is `/api/assets/{id}/target_pct`, the *helper URL* changes,
  not the route decorator.

## Decisions

### D1: Reproduce before deciding — no diff without traceback

The five plausible causes in the proposal map to five different
fix shapes. Picking the wrong one turns a 1-line fix into a 50-line
revert. The change explicitly mandates a **fresh reproduction
step** before any edit:

1. Run each failing test with `--tb=long -p no:cacheprovider`.
2. Read the response body printed by Starlette (the 404 may carry
   a `{"detail": ...}` that pins whether the route is matched and
   rejected at the ownership check vs. unmatched).
3. Diff the route decorator (`routes/assets.py:87` for GET,
   `:343` for PATCH) against the test helper's URL.
4. Diff the handler's return shape against the test's `assert
   body == {...}`.

Only after the divergence is localised do we pick an edit site.

### D2: Test fix vs. code fix — route the decision by *evidence*, not intent

The test names ("retire", "redirects_to_dashboard") and the
docstring on `test_s03_t05_assets_retire.py` ("The /assets page
was retired in S03/T05 — the dedicated editor is replaced by
inline asset management") suggest the spec was written *ahead* of
the implementation. The route at `routes/assets.py:87` still
renders the page, which is consistent with: spec written, code
never updated; or spec reverted, test not reverted; or the spec
was always aspirational.

**Default**: treat the route handler as the source of truth and
update the test, **unless** reproduction shows the test's
expected status code is what an upstream caller (e2e, dashboard
JS, Alpine component) actually depends on. The proposal names
this as a per-test decision because a route retirement is a
breaking change for callers, while a test edit is not.

### D3: Single regression test per fix

Where the fix is a code change (route edit), add or extend one
unit-level test that asserts the new behaviour at the route
boundary — `client.get(...)` / `client.patch(...)` with
`follow_redirects=False`, checking status + Location header / JSON
body. This locks the contract at the cheapest layer and replaces
the e2e cascades that were the only coverage.

Where the fix is a test edit, the existing test IS the regression
test — no new file needed.

### D4: Reproduce in two environments if possible

If CI has a separate runner, reproduce there too. The conftest's
session-scoped DB fixture plus the `_omaha_test_env` re-import
shuffle has historically masked fixtures that pass locally and
fail in CI (and vice versa). Reading both tracebacks side-by-side
catches environment-specific drift that a single reproduction
would miss.

## Risks / Trade-offs

- **R1**: We pick the wrong side of the test-vs-code decision
  and ship a test edit where the route really should change (or
  vice versa). → Mitigation: D1 + D2 mandate evidence-based
  routing. Cross-check the failing test's expected status against
  any caller that depends on the route (Alpine component,
  e2e spec, scripts/generate_contrast_audit.py uses
  `routes/classes.py` not assets, so this risk is bounded).

- **R2**: The 404 on PATCH comes from the ownership check at
  `routes/assets.py` rejecting the seeded asset because the
  session-scoped fixture cleared it between login and PATCH. →
  Mitigation: reproduction with `--tb=long` shows whether the
  asset exists in the response (`{"detail": "Asset X not found"}`)
  or whether the URL is unmatched (no body). These read
  differently and pin the cause.

- **R3**: The fix touches routes that have no other test
  coverage, so a regression in the new behaviour would be
  silent. → Mitigation: D3 requires a regression test per fix
  at the route boundary.

- **R4**: Three e2e failures cascade from the same root cause;
  fixing the route / patch path resolves all three for free, but
  the e2e tests still need to run green in CI. → Mitigation:
  reproduce in CI environment before claiming the fix is
  complete; e2e tests depend on Playwright + a live dev server
  which may not be available in the local sandbox.

## Migration Plan

1. **Reproduce**: run the 7 failing tests with `--tb=long` and
   capture the tracebacks + response bodies.
2. **Localise**: for each failure, diff the route handler
   against the test helper and pin the divergence to one of
   {route decorator, handler body, test helper URL, fixture
   seeding, ownership/scope check}.
3. **Decide**: per failure, choose code-edit or test-edit per
   D2. Document the call in the change's tasks.
4. **Fix**: land the minimum-surface change per failure. One
   commit per failure keeps the diff reviewable.
5. **Regression-test**: where the fix is a code change, add a
   route-level test that asserts the new behaviour.
6. **Verify**: `uv run task test` shows the 7 failures resolve
   and no new tests break. `uv run pytest tests/e2e` (in CI
   only — needs Playwright) confirms the e2e cascades clear.

Rollback strategy: each fix is its own commit. Reverting the
merge commit restores the route + test state without affecting
the audit change that just landed. If a fix proves wrong in
production, individual commits revert cleanly.

## Open Questions

- **OQ1**: Is the S03/T05 retire contract documented anywhere
  outside the test docstring (e.g. a planning note in
  `.planning/phases/`)? If yes, that pins the direction (route
  retires vs. test reverts) without needing to reproduce. If no,
  the decision falls back to D2.
- **OQ2**: Does the dashboard's Alpine inline editor (the
  intended replacement for the `/assets` page) depend on the
  `/api/assets/{id}` PATCH endpoint existing? If yes, the
  PATCH path is load-bearing and the test is right; if no,
  the route may also be a retire candidate.
- **OQ3**: Are there any other callers of `GET /assets` or
  `PATCH /api/assets/{id}` outside the test suite (e.g. in
  `scripts/` or commented-out code in templates)? A `git grep`
  resolves this in one minute and pins the breaking-change
  blast radius.
