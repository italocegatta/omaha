## 1. Pre-Implementation Audit

- [x] 1.1 Inspect existing Playwright fixtures under `tests/e2e/` and identify reusable login/server helpers.
- [x] 1.2 Confirm target page availability and final page/state list: login, patrimonio, classes, assets, rebalance form, rebalance plan, import form, import review, rentabilidade stub, proventos stub, and audit report if route exists.
- [x] 1.3 Confirm seeded DB state via existing CSV path; do not add inline asset or position fixtures.
- [x] 1.4 Confirm `.gitignore` current rules for Playwright/test artifacts before adding visual output paths.

## 2. Visual Suite Structure

- [x] 2.1 Create `tests/visual/` with `conftest.py` fixtures for browser/page setup, login, and viewport matrix.
- [x] 2.2 Add helper for structural pre-assertions and screenshot comparison with default 0.5% pixel threshold.
- [x] 2.3 Add stable snapshot naming helper that encodes page/state and viewport.
- [x] 2.4 Create `tests/visual/baselines/` and keep it eligible for git tracking.

## 3. Snapshot Coverage

- [x] 3.1 Add login page desktop + mobile snapshots with login-form pre-assertions.
- [x] 3.2 Add authenticated Patrimônio desktop + mobile snapshots with seeded class/BRL/testid pre-assertions.
- [x] 3.3 Add Classes and Assets desktop + mobile snapshots with route-specific table/form pre-assertions.
- [x] 3.4 Add Rebalanceamento form desktop + mobile snapshots and, if feasible, plan-state snapshots after a deterministic submit.
- [x] 3.5 Add Import form desktop + mobile snapshots and, if feasible, review-state snapshots using existing test fixture data.
- [x] 3.6 Add Rentabilidade and Proventos stub desktop + mobile snapshots while those pages remain deferred.
- [x] 3.7 Add Audit report desktop + mobile snapshots only if the route is available and stable in the current app.

## 4. Taskipy and Artifact Policy

- [x] 4.1 Add `task test-visual` to `pyproject.toml` targeting `tests/visual/`.
- [x] 4.2 Update `.gitignore` to ignore generated visual diff/output directories while preserving `tests/visual/baselines/`.
- [x] 4.3 Generate and commit initial baseline PNGs under `tests/visual/baselines/`.

## 5. Documentation and Spec Sync

- [x] 5.1 Update `DESIGN.md` with when to run `task test-visual`, where baselines live, and baseline update policy.
- [x] 5.2 Ensure `openspec/specs/visual-regression-baseline/spec.md` is created during archive with the finalized requirements.
- [x] 5.3 Update `openspec/roadmap.md` progress with implementation notes and any page list deviations.

## 6. Verification

- [x] 6.1 Run `task test-visual` and record pass/fail plus baseline count.
- [x] 6.2 Run `task lint`.
- [x] 6.3 Run `task test-unit`.
- [x] 6.4 Run `task test-integration` if implementation touches shared pytest config or fixtures.
- [x] 6.5 Run `openspec validate t06-visual-regression-baseline --json` and repository spec verification.
- [x] 6.6 Because T06 touches test infrastructure and baseline artifacts only, run `refresh-for-test` only if runtime/browser-visible files change during apply.
