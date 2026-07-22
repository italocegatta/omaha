## MODIFIED Requirements

### Requirement: Baseline update SHALL use an explicit env-var gate

The system SHALL update committed baselines only when `UPDATE_VISUAL_BASELINES=1` is set. Without this variable, the suite SHALL compare against existing baselines and fail if the pixel diff exceeds tolerance. When the variable is set, helper `compare_or_update_screenshot()` SHALL overwrite baseline on disk and skip comparison; subsequent run without env-var SHALL pass if new baseline is correct.

Before accepting regenerated baselines, operator SHALL verify that failures are due to intentional UI changes (baseline-stale) and not regressions. Verification process: (1) run visual suite without flag to see current failures, (2) inspect diff output in `tests/visual/results/`, (3) confirm each failure maps to an intentional change (e.g., F41–F47), (4) run with flag to regenerate, (5) inspect new baselines visually before committing.

#### Scenario: Intentional visual update replaces baselines

- **WHEN** the operator runs `UPDATE_VISUAL_BASELINES=1 uv run task test-visual`
- **THEN** each screenshot overwrites its baseline PNG after pre-assertions pass
- **AND** no diff-ratio comparison is performed during update run

#### Scenario: Missing baseline is caught early

- **WHEN** baseline file does not exist for captured screenshot
- **AND** `UPDATE_VISUAL_BASELINES` is not set to `1`
- **THEN** helper raises `AssertionError` with missing baseline path
- **AND** message tells operator to rerun with `UPDATE_VISUAL_BASELINES=1`

#### Scenario: Baseline refresh requires explicit verification

- **WHEN** visual tests fail due to stale baselines after intentional UI changes
- **THEN** operator MUST run visual suite without flag first to see failures
- **AND** operator MUST inspect `tests/visual/results/` diffs to confirm failures are baseline-stale
- **AND** operator MUST confirm each failure maps to a known intentional change
- **AND** only then run with `UPDATE_VISUAL_BASELINES=1` to regenerate
- **AND** inspect regenerated PNGs before committing
