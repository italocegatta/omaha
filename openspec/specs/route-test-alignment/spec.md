# route-test-alignment Specification

## Purpose
Every route registered in `src/omaha/routes/` must have at
least one unit-level test asserting its exact HTTP status code
and response body shape. Failing tests must be reproduced with
`--tb=long -p no:cacheprovider` before any edit, and the
route-vs-test divergence must be resolved by evidence (a
documented spec, a call-site, or the reproduction traceback),
not by intent.

## Requirements
### Requirement: Every route has a unit-level test asserting its HTTP contract
Every route registered in `src/omaha/routes/` MUST be covered by at
least one unit-level test that asserts the exact HTTP status code
and response body shape for the success path. The route-test
alignment surface (e.g. `tests/test_<module>_routes.py`) is the
canonical home for these tests; e2e or audit-integration tests may
exercise the same routes but MUST NOT be the only assertion.

#### Scenario: GET /assets has a route-boundary test
- **WHEN** the test suite is collected
- **THEN** there exists a unit-level test asserting the exact
  HTTP status code that `GET /assets` returns for an
  authenticated user with an active profile
- **AND** the asserted status code matches the route handler at
  `src/omaha/routes/assets.py:87` (200 for render, or 302 with
  Location header for redirect)

#### Scenario: PATCH /api/assets/{asset_id} has a route-boundary test
- **WHEN** the test suite is collected
- **THEN** there exists a unit-level test asserting the exact
  HTTP status code that `PATCH /api/assets/{asset_id}` returns
  for a happy-path PATCH (200) and for a per-class-sum failure
  (422 with `{"detail": "<Sobra/Falta X%>"}`)
- **AND** the asserted status code matches the route handler at
  `src/omaha/routes/assets.py:324`

### Requirement: Failing tests are reproduced before being fixed
A test that fails under `uv run task test` MUST be reproduced with
`--tb=long -p no:cacheprovider` before any code or test edit
lands. The reproduction MUST capture the traceback, the HTTP
response body (which Starlette prints on 404/422), and a
side-by-side read of the route decorator + handler body + test
helper URL.

#### Scenario: Reproduction precedes the fix
- **WHEN** a test in this change's failure list is marked as
  fixed
- **THEN** the PR description (or commit message) includes the
  traceback excerpt and the URL/body diff that localised the
  divergence
- **AND** the fix touches exactly one of: route handler, test
  helper, fixture, or test expectation — not multiple

### Requirement: Route-vs-test divergence is decided by evidence, not intent
The fix direction (edit the test vs. edit the code) MUST be
chosen by one of: a documented spec in `openspec/specs/` or
`.planning/`; a call-site that depends on the current
behaviour; or the traceback from a fresh reproduction. The
default when no evidence exists is to **fix the test** (the
existing handler keeps working for any unknown callers), UNLESS
the route's docstring explicitly announces the contract the test
asserts.

#### Scenario: Spec-backed contract pins a code fix
- **WHEN** a route's docstring (or a planning note) announces a
  contract the test asserts (e.g. "redirects to dashboard on
  GET /assets") AND the route handler does not honour it
- **THEN** the fix edits the route handler, not the test
- **AND** the fix adds a regression test that exercises the
  redirect at the route boundary

#### Scenario: No spec, no caller → test edit
- **WHEN** a test asserts a status code the route handler does
  not return AND no spec, docstring, or caller backs the test
- **THEN** the fix edits the test to match the route's actual
  behaviour, with a comment citing the reproduction

### Requirement: No new test regressions
After this change lands, `uv run task test` MUST report zero
failures introduced by this change. Pre-existing failures (the 7
catalogued in the proposal) MUST resolve; any new failure MUST
be addressed in this change or rolled back.

#### Scenario: Full suite is green after the fix
- **WHEN** the change is applied and `uv run task test` runs
- **THEN** the 7 pre-existing failures catalogued in
  `proposal.md` all pass
- **AND** no test that passed before this change starts failing
