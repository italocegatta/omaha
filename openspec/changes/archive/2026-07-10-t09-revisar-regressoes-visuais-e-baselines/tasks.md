## 1. Triage: structural selectors and wait conditions

- [x] 1.1 Audit all 10 `data-testid` selectors in `test_snapshots.py` against current template markup (`src/omaha/templates/`). Flag missing, renamed, or fragile selectors.
- [x] 1.2 Audit `wait_for_selector()` calls for adequate timeout (currently 10s) and state parameter (`state="visible"`). Flag cases where wait targets an element that may exist but be hidden.
- [x] 1.3 Replace `wait_for_timeout(200)` in `test_import_review_snapshot` with state-based wait (`wait_for_selector('[data-testid="import-commit-btn"]', state="visible")`).
- [x] 1.4 Verify `wait_for_function` in `test_rebalance_plan_snapshot` has a fallback or timeout guard for empty plan state.

## 2. Triage: baseline set and capture state

- [x] 2.1 For each of the 20 baseline PNGs, confirm the captured state is intentional: login page after fill, patrimonio after data load, rebalance form with empty plan, rebalance plan after submit, import form with modal open, import review with parsed data, stubs with correct marker.
- [x] 2.2 Run `task test-visual` to confirm 20/20 green before any change. Record baseline timestamps and sizes.
- [x] 2.3 Manually inspect `tests/visual/results/*.png` vs `tests/visual/baselines/*.png` for any visual drift that the 0.5% tolerance might hide (large solid-color areas can mask localized diffs).
- [x] 2.4 If any baseline captures stale/intermediate state (e.g., empty table before data populates, modal before Alpine store hydrates), fix the test wait or regenerate the baseline with `UPDATE_VISUAL_BASELINES=1`.

## 3. Triage: conftest.py helper audit

- [x] 3.1 Validate `compare_or_update_screenshot()` update flow: confirm `UPDATE_VISUAL_BASELINES=1` correctly overwrites baseline and skips comparison.
- [x] 3.2 Validate missing-baseline assertion: delete one baseline, run test without `UPDATE_VISUAL_BASELINES`, confirm `AssertionError` with clear message.
- [x] 3.3 Review `_png_pixel_diff` decoder for edge cases: PNGs with no IDAT chunks, RGBA vs RGB, different bit depths. Confirm decoder assumptions are documented or add a guard.
- [x] 3.4 Verify `DEFAULT_MAX_DIFF_RATIO = 0.005` adequacy: run `UPDATE_VISUAL_BASELINES=1` on all 20 snapshots, then without env-var to confirm determinism.
- [x] 3.5 Add docstrings to `_png_pixel_diff` and `_decode_png_rgba` explaining assumptions (8-bit, deflate, no interlace, RGB/RGBA only).

## 4. Fix: confirmed UI regressions

- [x] 4.1 If triage (tasks 1-3) finds a real UI regression (template/CSS difference between baseline and current runtime), fix the runtime side — never suppress the regression signal by updating the baseline. *(N/A — no runtime regression found during T09 triage.)*
- [x] 4.2 If a runtime fix is applied, add or verify a structural assertion in the relevant screenshot test that proves the correct state captures, so future drift still fails. *(N/A — no runtime fix applied.)*
- [x] 4.3 If no regression found, skip 4.1-4.2 and document that the suite is healthy.

## 5. Documentation alignment

- [x] 5.1 Update `DESIGN.md` §Visual Regression to reflect current conftest behavior: session-scoped browser, `reduced_motion="reduce"`, `animations="disabled"`, `UPDATE_VISUAL_BASELINES=1` update flow, pixel-tolerance rationale.
- [x] 5.2 Update `openspec/specs/visual-regression-baseline/spec.md` with MODIFIED requirements from T09 delta spec (sync after archive).
- [x] 5.3 Run `task test-visual` one final time to confirm 20/20 green after all changes.

## 6. Archive preparation

- [x] 6.1 Verify no unrelated files changed (`git diff --stat`).
  - Verified T09 edits stay in visual test/docs/spec files; unrelated `openspec/roadmap.md` worktree diff pre-existed this apply session.
- [x] 6.2 Run `openspec list --specs` to validate spec health gate.
- [ ] 6.3 Commit all changes with message `chore(visual): T09 triage visual regression selectors, waits, and baseline policy`.
  - Deferred in this apply session: repo policy says do not commit unless user explicitly requests it.
