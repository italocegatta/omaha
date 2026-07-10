## Context

Visual regression suite in `tests/visual/` has 10 test functions × 2 viewports = 20 passing snapshots. Current state:

- **Test structure**: `test_snapshots.py` with 10 tests covering login, patrimonio, assets table, classes, rebalance form, rebalance plan, import form, import review, rentabilidade stub, proventos stub.
- **Fixture architecture** (post-T08 refactor): session-scoped `_browser` fixture (shared Playwright browser), per-test `visual_page` fixture (fresh context+page per test). `live_url_visual` session fixture spawns isolated uvicorn on port 8768.
- **Baseline management**: `compare_or_update_screenshot()` helper with 0.5% pixel tolerance, `UPDATE_VISUAL_BASELINES=1` env-var flow, custom PNG pixel-diff decoder.
- **Structural assertions**: each test asserts `data-testid` selectors + text content before screenshot.
- **Current health**: 20/20 green, no baseline drift detected (baseline vs result file sizes match).

Recent changes that touched visual surface area (F14–F20, T08) may have introduced:
- Fragile selectors that match today but break on next template change.
- Missing wait conditions (e.g., relying on `wait_for_timeout(200)` instead of state-based waiter).
- Baseline matrix gaps (pages/states not covered).
- Conftest behavior that drifted from DESIGN.md documentation.

## Goals / Non-Goals

**Goals:**
- Audit all 10 test selectors for fragility against template renames/restructuring.
- Audit wait/state setup: replace time-based `wait_for_timeout` with state-based waits where possible.
- Audit baseline PNG set: confirm each captures the intended state, not intermediate/empty state.
- Audit conftest.py: verify `UPDATE_VISUAL_BASELINES=1` flow is correct; validate pixel-diff tolerance adequacy; check PNG decoder for edge cases.
- Align `openspec/specs/visual-regression-baseline/spec.md` with current conftest behavior (session-scoped browser, reduced-motion, animations-disabled).
- Align DESIGN.md §Visual Regression with current behavior.
- Fix confirmed UI regressions on runtime side (templates/CSS) when triage finds one — never suppress regression signal on the test side.

**Non-Goals:**
- No BDD or e2e test changes.
- No parallelism/harness changes (T08 already covered).
- No CSV pipeline or seed_from_csv changes (T10).
- No rebalance solver or schema changes (T11).
- No new baseline PNGs for uncovered pages/states (beyond fixing existing ones).
- No broad redesign of the test harness.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Triage order | structural assertions → waits → baselines → conftest → docs | Logic flow: test can't capture reliably if selector/state is wrong; baseline is only as good as the capture setup. |
| Selector fragility audit | grep all `data-testid` refs in test + template; flag any selector that relies on visual-class or positional rules | `data-testid` attributes are stable anchors by convention; verify each still exists in current template. |
| Wait-for-timeout replacement | Replace `wait_for_timeout(200)` in `test_import_review_snapshot` with `wait_for_selector('[data-testid="import-commit-btn"]', state="visible")` | Time-based waits are inherently fragile across machine speeds; state-based waits are deterministic. |
| Baseline update policy | Keep `UPDATE_VISUAL_BASELINES=1` as documented, no change | Flow works correctly; conftest already guards against missing baseline (raises AssertionError with clear message). |
| Pixel tolerance | Keep 0.5% default; document rationale in spec | No evidence of false positives/negatives at this threshold. Suite passes deterministically. |
| Delta spec scope | Update existing `visual-regression-baseline/spec.md` — no new spec files | No new capability needed; only contract alignment with current behavior. |

## Risks / Trade-offs

- **[Risk] Conftest PNG decoder misses Chromium pixel-format change** → Mitigation: add a smoke test that decodes a known PNG and validates pixel count; or at minimum document the decoder's assumptions (8-bit RGB/RGBA, deflate compression, no Adam7 interlace).
- **[Risk] Triage finds zero issues, slice appears wasted** → Not a risk: confirming the suite is healthy is valuable output. The slice documents the audit and updates docs to match reality.
- **[Risk] Template/CSS fix for a confirmed regression masks future drift** → Mitigation: fix must include a structural assertion that proves the correct state, so future drift still fails.
- **[Risk] Design doc outdated again after next feature slice** → Mitigation: no procedural fix; visual regression doc is inherently a maintenance responsibility of any slice that touches browser UI.
