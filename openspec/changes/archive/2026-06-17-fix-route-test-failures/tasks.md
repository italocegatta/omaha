## 1. Reproduce every failure (gate the rest)

Reproduction MUST happen before any edit. Without it, we are
guessing among the five plausible causes in `proposal.md` and
risk picking the wrong fix shape.

- [x] 1.1 Run `uv run pytest tests/test_t99_assets_patch.py::test_patch_asset_updates_target_pct --tb=long -p no:cacheprovider` and capture the full traceback + response body printed by Starlette. Save under `openspec/changes/fix-route-test-failures/notes/01-patch-updates.md`.
- [x] 1.2 Run the same for `test_t99_assets_patch.py::test_patch_asset_invalid_sum_returns_422`. Save under `notes/02-patch-422.md`.
- [x] 1.3 Run `uv run pytest tests/test_s03_t05_assets_retire.py::test_get_assets_redirects_to_dashboard --tb=long`. Save under `notes/03-get-assets-redirect.md`.
- [x] 1.4 Run the 4 e2e failures individually (`tests/e2e/test_s01_inline_edit.py::TestS01InlineEdit::test_inline_edit_asset_target`, `...::test_inline_edit_blocks_when_sum_neq_100`, `...::test_dashboard_displays_four_percentages_per_asset`, `tests/e2e/test_s03_asset_crud.py::TestS03AssetCRUD::test_assets_route_redirects_to_dashboard`) with `--tb=long`. Note that e2e tests need the dev server running; if the sandbox cannot start Playwright, capture the failure mode from a CI log or a parallel invocation. Save under `notes/04-e2e-cascades.md`.
- [x] 1.5 For each failure, side-by-side read the route decorator + handler body against the test helper. Pin the divergence to one of {route decorator, handler body, test helper URL, fixture seeding, ownership/scope check}. Write a one-paragraph "finding" in each `notes/*.md` file.

## 2. Resolve the open questions

The design §OQ1-OQ3 pin the test-vs-code decision per failure.
Without answers, we are guessing.

- [x] 2.1 `git grep "GET /assets\|/assets[\"']" -- src/ scripts/` and `git grep "/api/assets" -- src/ scripts/` to enumerate non-test callers. Write the result under `notes/05-callers.md`. This resolves design §OQ3.
- [x] 2.2 Search `.planning/phases/` for any S03/T05 or assets retire documentation that pins the intended contract. Write the result under `notes/06-planning.md`. This resolves design §OQ1.
- [x] 2.3 Inspect the dashboard Alpine inline editor (`src/omaha/templates/dashboard.html` + the component Alpine state) to confirm whether `PATCH /api/assets/{id}` is the URL it calls. Write the result under `notes/07-dashboard-patch-url.md`. This resolves design §OQ2.

## 3. Fix per failure (code vs test, decided by §1 + §2)

Each fix lands in its own commit, smallest surface that resolves
the divergence. The fix direction (route edit vs. test edit) is
recorded in the commit body citing the reproduction note.

- [x] 3.1 Fix the divergence for `test_patch_asset_updates_target_pct` (404 vs 200). Per D2 of design, the default is test-edit unless §1.5 / §2 pins a code-edit. Land the minimum edit; one commit.
- [x] 3.2 Fix the divergence for `test_patch_asset_invalid_sum_returns_422` (also 404, same root cause expected). Verify §3.1 fixes both before landing a second edit.
- [x] 3.3 Fix the divergence for `test_get_assets_redirects_to_dashboard` (200 vs 302). The route docstring + planning note §2.2 likely pin the direction here. Land the minimum edit; one commit.
- [x] 3.4 Fix the 3 e2e cascades in `test_s01_inline_edit.py`. These should resolve automatically once §3.1 / §3.3 land; if not, reproduce under the same protocol as §1 and localise per §1.5.
- [x] 3.5 Fix the e2e cascade `test_s03_asset_crud.py::test_assets_route_redirects_to_dashboard`. Same dependency on §3.3.

## 4. Lock the contract with route-boundary tests

Where the fix is a **code** edit, add a unit-level test at the
route boundary that asserts the new behaviour. Where the fix is a
**test** edit, the existing test IS the regression — no new file.

- [x] 4.1 (skipped — test edit) If §3.1 / §3.2 was a code edit: extend or add to `tests/test_t02_assets_routes.py` (or the nearest routes test file) a parametrized test for the PATCH success path (200 with `{"id", "target_pct"}`) and the validation path (422 with `{"detail": "Sobra X%"}`). If it was a test edit, skip.
- [x] 4.2 (covered by existing test_s03_t05_assets_retire.py::test_get_assets_redirects_to_dashboard) If §3.3 was a code edit: add a test in `tests/test_s03_t05_assets_retire.py` (or the routes test file) asserting `GET /assets` returns 302 with `Location: /` for an authenticated user. If it was a test edit, skip.
- [x] 4.3 Run the new tests under `uv run pytest -m unit` and confirm they pass.

## 5. Verify no regressions

- [x] 5.1 Run `uv run task test` and confirm the 7 pre-existing failures catalogued in `proposal.md` all resolve.
- [x] 5.2 Run `uv run pytest -m unit` and confirm no new failures (count should match the post-`review-unit-tests-effectiveness` baseline + any new tests from §4).
- [x] 5.3 Run `uv run pytest -m integration` and confirm no new failures.
- [x] 5.4 Run `uv run task lint` and confirm no new ruff violations from the route or test edits.
- [x] 5.5 Open `openspec status --change fix-route-test-failures` and confirm all `applyRequires` artifacts are `done`. Run `openspec archive fix-route-test-failures` to finalise.
