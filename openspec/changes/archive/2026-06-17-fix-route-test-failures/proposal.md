## Why

Seven tests in the suite currently fail on `uv run task test` — all
pre-existing (confirmed via `git stash` of the
`review-unit-tests-effectiveness` change), unrelated to that
change's audit-test rewrite. The failure pattern is concentrated on
the assets routes (``/assets`` and ``/api/assets/{id}``) and on the
e2e flows that depend on them, which makes it a focused subset of
the codebase rather than a systemic regression.

The test artifacts encode a contract the production code no longer
satisfies (or never fully did):

* `tests/test_s03_t05_assets_retire.py::test_get_assets_redirects_to_dashboard`
  pins `GET /assets` to a **302 → /** redirect for authenticated
  users. The route today renders `assets.html` (200).
* `tests/test_t99_assets_patch.py::test_patch_asset_updates_target_pct`
  and `::test_patch_asset_invalid_sum_returns_422` pin
  `PATCH /api/assets/{asset_id}` to 200 / 422 with bodies
  `{"id", "target_pct"}` and `{"detail": "Sobra X%"}`. The route
  today returns 404 — the URL `/api/assets/1` is not matched by
  any handler that accepts a single-segment id.
* Three e2e tests in `tests/e2e/test_s01_inline_edit.py` and
  `tests/e2e/test_s03_asset_crud.py` cascade from the same root
  causes (the asset editor they exercise doesn't 302 to `/`, and
  PATCH calls land on a non-matching path).

We need **fewer tests asserting what the code does today, more
tests asserting what the code SHOULD do tomorrow** — but the
direction of travel (route retirement vs. test update vs. handler
fix) is **not yet pinned**. Multiple plausible root causes exist:

1. **Routes were never retired.** The T05 retire docstring claims
   `GET /assets` is "replaced by inline asset management" but the
   handler at `src/omaha/routes/assets.py:87` still renders the
   template. The test names ("retire", "redirects_to_dashboard")
   anticipate a code change that never landed (or was reverted).
2. **PATCH path mismatch.** `test_patch_asset_invalid_sum_returns_422`
   calls `_patch_asset(client, target_asset_id, "50")`. If the
   helper PATCHes `/api/assets/{id}` but the route is mounted
   elsewhere (e.g. `/assets/{id}` or `/api/assets/{id}/target_pct`),
   every test in the file is 404. Worth checking the helper URL
   *and* the route decorator signature against each other before
   assuming a code fix is needed.
3. **Seeding drift.** `test_patch_asset_updates_target_pct` seeds
   the asset via `_seed_class_with_assets(1, "Renda Fixa", ["0"], …)`
   and then PATCHes that asset's id. If the seed helper now writes
   to a different table / column / session than the PATCH route
   reads from, the asset exists but the PATCH 404s on lookup.
4. **Auth/permission contract drift.** A 404 may also come from the
   ownership check (`asset.asset_class.profile_id != profile.id`)
   being inverted, or from the session-scope fixture clearing
   fixtures between login and PATCH.
5. **Test-only state leak.** Both `test_get_assets_redirects_to_dashboard`
   and `test_patch_asset_*` rely on `_omaha_test_env` seeding.
   Recent changes to `tests/conftest.py` (e.g. the marker hook in
   the audit change, or unrelated seed cleanup) may have altered
   fixture visibility in ways that didn't show up locally but do
   in CI.

The proposal exists to **stop guessing from failure text**. Every
plausible cause above requires a different fix shape (route edit
vs. test edit vs. fixture edit vs. seed edit), and picking the
wrong one wastes a slice. The right next step is a focused
reproduction: run each failing test under `--tb=long -p no:cacheprovider`,
read the route decorators and the test helpers side-by-side, and
diff the live response against the test's expected `status_code`
and body. **Only then** do we know whether the test is correct and
the code is wrong, or vice versa.

## What Changes

- Reproduce each of the 7 failures with the full traceback and
  identify whether the divergence is in the **production code**
  (route decorator, handler body, ownership check, redirect), the
  **test helpers** (URL path, body shape, helper name), the
  **fixtures** (DB seeding, session scoping, conftest marker
  hook), or the **specs** (the retire contract was never
  implemented).
- Land the minimum-surface fix for each. Possible shapes (chosen
  after reproduction, not before):
  - Retire `GET /assets` to a 302 → `/` (one-line change in
    `routes/assets.py:87`); update `assets.html` references if any
    remain (the dashboard inline editor already replaces the
    surface per the docstring).
  - Fix the PATCH path: either change the route to match what the
    test calls, or update the test helper to call what the route
    accepts. Either is a 1-3 line change once the gap is
    identified.
  - Update tests where the spec has shifted (e.g. the inline
    editor now lives at a different route). These tests stay
    valuable as documentation of the redirect / PATCH contract;
    only the expectation changes.
- Add a single regression test per fix (where one doesn't already
  exist) so the failure mode is locked at the cheapest layer.
- Re-run `uv run task test` and confirm the 7 pre-existing
  failures resolve without introducing new ones.

**BREAKING**: any change to `GET /assets` or `PATCH /api/assets/{id}`
semantics is observable by callers — a separate slice may be
needed if external scripts depend on the current behaviour.

## Capabilities

### New Capabilities

- `route-test-alignment`: A documented contract that every route
  in `src/omaha/routes/` has at least one unit-level test asserting
  the exact HTTP status + body shape, and that the test's
  expectation matches the route decorator + handler body. The
  failure mode we're fixing (test expects 302, code returns 200)
  is the canonical case this capability prevents.

### Modified Capabilities

None — no existing spec describes these routes' HTTP contract in
a way that would change. The work is internal to
`src/omaha/routes/`, `tests/`, and `tests/conftest.py`.

## Impact

- `src/omaha/routes/assets.py` — `get_assets` (line 87) and
  `patch_asset` (line 343) are the candidates for code edits.
- `tests/test_t99_assets_patch.py` and `tests/test_s03_t05_assets_retire.py`
  — test-side adjustments if the spec has shifted.
- `tests/conftest.py` — fixture scope / seed adjustments only if
  reproduction shows a seeding bug.
- `tests/e2e/test_s01_inline_edit.py`,
  `tests/e2e/test_s03_asset_crud.py` — e2e cascades that depend
  on the underlying route behaviour.

**Caveat**: the actual root cause must be confirmed via fresh
reproduction before any of the above is touched. The failure
output alone is **not** sufficient to pick the right edit — the
five plausible causes above map to five different fix shapes, and
a misread here turns a 1-line fix into a 50-line revert. Treat the
"Impact" list as a candidate set, not an action plan.
