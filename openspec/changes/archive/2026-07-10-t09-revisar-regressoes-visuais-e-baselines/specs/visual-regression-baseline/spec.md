## MODIFIED Requirements

### Requirement: Visual regression suite SHALL be a dedicated Playwright task

The system SHALL provide a dedicated Playwright visual regression suite under `tests/visual/` and expose it through `task test-visual`. The suite SHALL be separate from `task test-e2e` so standard e2e journeys remain behavior-focused and do not run screenshot diffs by default.

**Modification**: Document the session-scoped browser lifecycle: a single Chromium process is launched per session (fixture `_browser`), and each test creates a fresh browser context + page via fixture `visual_page`. This avoids per-test launch cost while keeping isolated browser state.

#### Scenario: Visual task runs the visual suite
- **WHEN** the operator runs `uv run task test-visual`
- **THEN** pytest collects tests from `tests/visual/`
- **AND** Playwright screenshot assertions execute for the visual baseline suite

#### Scenario: Session-scoped browser reduces launch overhead
- **WHEN** multiple visual tests run in a single pytest session
- **THEN** they share a single Chromium process (`_browser` session fixture)
- **AND** each test still gets a fresh `browser.new_context()` + `context.new_page()`
- **AND** browser state is never shared across tests

#### Scenario: E2E task stays behavior-focused
- **WHEN** the operator runs `uv run task test-e2e`
- **THEN** pytest collects tests from `tests/e2e/`
- **AND** it does not collect `tests/visual/` snapshot tests

### Requirement: Screenshot tests SHALL assert structural content before capture

**Modification**: Each visual test SHALL assert route-specific structural content before taking a screenshot, using `data-testid` selectors. The helper `assert_structural_content()` SHALL wait up to 10 seconds for each selector to become visible. Screenshots SHALL be captured with `full_page=True` and `animations="disabled"` to suppress CSS animation variance.

#### Scenario: Authenticated page is not screenshotted while empty or redirected
- **WHEN** a visual test targets an authenticated page such as Patrimônio or Rebalanceamento
- **THEN** the test asserts authenticated page content before the screenshot
- **AND** a login redirect or empty seeded state fails before baseline comparison

#### Scenario: Animations are suppressed in screenshots
- **WHEN** a visual test captures a screenshot
- **THEN** the `page.screenshot()` call includes `animations="disabled"`
- **AND** the browser context sets `reduced_motion="reduce"`
- **AND** these together eliminate CSS animation variance from baseline comparisons

#### Scenario: Page-specific state is asserted before screenshot
- **WHEN** a visual test targets a page state such as import review or rebalance plan
- **THEN** the test asserts at least one marker unique to that state before taking the screenshot

### Requirement: Visual diffs SHALL use an explicit tolerance

The visual regression suite SHALL use an explicit page screenshot tolerance. The default tolerance SHALL be 0.5% pixels different unless implementation evidence requires a tighter or looser value documented in the change. The tolerance SHALL be configurable per-screenshot via the `max_diff_ratio` parameter of `compare_or_update_screenshot()`.

**Modification**: Document that the 0.5% threshold was chosen empirically: the suite passes deterministically across the current 20-snapshot matrix; no false positives or negatives have been observed. If a page contains large solid-color areas (e.g., stub pages), the ratio may understate localized diff severity — reviewers SHOULD visually inspect `tests/visual/results/` when a failure is investigated.

#### Scenario: Screenshot comparison uses configured tolerance
- **WHEN** Playwright compares a screenshot to its baseline
- **THEN** the comparison uses the visual suite's configured pixel-difference threshold (default 0.5%)
- **AND** the comparison is pixel-per-exact-match first (short-circuit if bytes equal)
- **AND** the per-screenshot `max_diff_ratio` parameter allows override for known high-variance snapshots

### Requirement: Baseline update SHALL use an explicit env-var gate

The system SHALL update committed baselines only when the `UPDATE_VISUAL_BASELINES=1` environment variable is set. Without this variable, the suite SHALL compare against existing baselines and fail if the pixel diff exceeds the tolerance. When the variable is set, the helper SHALL overwrite the baseline on disk and skip the comparison — a subsequent run without the env-var SHALL pass if the new baseline is correct.

**Modification**: Document the update flow explicitly. When a baseline file does not exist and `UPDATE_VISUAL_BASELINES` is not set, the helper SHALL raise an `AssertionError` with a clear message instructing the operator to run with the env-var. Intentional visual changes update baselines in the same change: run `UPDATE_VISUAL_BASELINES=1 task test-visual`, review the changed PNGs, then re-run without the env-var to prove committed baselines pass.

#### Scenario: Intentional visual update replaces baselines
- **WHEN** the operator runs `UPDATE_VISUAL_BASELINES=1 uv run task test-visual`
- **THEN** each screenshot overwrites its baseline PNG if the test passes pre-assertions
- **AND** no comparison or diff-ratio check is performed during the update run

#### Scenario: Missing baseline is caught early
- **WHEN** a baseline file does not exist for a captured screenshot
- **AND** `UPDATE_VISUAL_BASELINES` is not set to `1`
- **THEN** the helper raises `AssertionError` with the baseline path and instructs the operator to rerun with `UPDATE_VISUAL_BASELINES=1`
