## ADDED Requirements

### Requirement: Visual regression suite SHALL be a dedicated Playwright task

The system SHALL provide a dedicated Playwright visual regression suite under `tests/visual/` and expose it through `task test-visual`. The suite SHALL be separate from `task test-e2e` so standard e2e journeys remain behavior-focused and do not run screenshot diffs by default.

#### Scenario: Visual task runs the visual suite
- **WHEN** the operator runs `uv run task test-visual`
- **THEN** pytest collects tests from `tests/visual/`
- **AND** Playwright screenshot assertions execute for the visual baseline suite

#### Scenario: E2E task stays behavior-focused
- **WHEN** the operator runs `uv run task test-e2e`
- **THEN** pytest collects tests from `tests/e2e/`
- **AND** it does not collect `tests/visual/` snapshot tests

### Requirement: Baseline artifacts SHALL be committed and generated diffs SHALL be ignored

The system SHALL keep canonical visual baseline PNGs under `tests/visual/baselines/` in version control. Generated diff/output artifacts SHALL be ignored so local review noise is not committed.

#### Scenario: Baselines are kept under the canonical directory
- **WHEN** visual baselines are generated for committed coverage
- **THEN** the PNG files live under `tests/visual/baselines/`
- **AND** the repository does not ignore that baseline directory

#### Scenario: Generated visual output is ignored
- **WHEN** Playwright or pytest creates visual diff/output artifacts
- **THEN** those generated output paths are ignored by git
- **AND** only reviewed baseline PNGs are eligible for commit

### Requirement: Visual coverage SHALL include desktop and mobile viewports

The system SHALL capture visual baselines for each covered page/state at desktop `1440x900` and mobile `375x667` viewports. Snapshot names SHALL include the page/state and viewport.

#### Scenario: Desktop baseline exists for each covered page
- **WHEN** the visual suite runs for a covered page/state
- **THEN** it captures or compares a `1440x900` desktop screenshot
- **AND** the snapshot name identifies the page/state and desktop viewport

#### Scenario: Mobile baseline exists for each covered page
- **WHEN** the visual suite runs for a covered page/state
- **THEN** it captures or compares a `375x667` mobile screenshot
- **AND** the snapshot name identifies the page/state and mobile viewport

### Requirement: Screenshot tests SHALL assert structural content before capture

Each visual test SHALL assert route-specific structural content before taking a screenshot. Acceptable pre-assertions include data-testid markers, seeded class names, BRL totals, route headings, form controls, or review/status markers that prove the intended page state rendered.

#### Scenario: Authenticated page is not screenshotted while empty or redirected
- **WHEN** a visual test targets an authenticated page such as Patrimônio or Rebalanceamento
- **THEN** the test asserts authenticated page content before the screenshot
- **AND** a login redirect or empty seeded state fails before baseline comparison

#### Scenario: Page-specific state is asserted before screenshot
- **WHEN** a visual test targets a page state such as import review or rebalance plan
- **THEN** the test asserts at least one marker unique to that state before taking the screenshot

### Requirement: Visual diffs SHALL use an explicit tolerance

The visual regression suite SHALL use an explicit page screenshot tolerance. The initial tolerance SHALL be 0.5% pixels different unless implementation evidence requires a tighter or looser value documented in the change.

#### Scenario: Screenshot comparison uses configured tolerance
- **WHEN** Playwright compares a screenshot to its baseline
- **THEN** the comparison uses the visual suite's configured pixel-difference threshold
- **AND** the threshold value is visible in the test helper or assertion options

### Requirement: Design documentation SHALL describe the visual gate

`DESIGN.md` SHALL document when to run `task test-visual`, where baselines live, and how intentional visual changes update baselines.

#### Scenario: Design doc explains baseline update policy
- **WHEN** a future visual change modifies layout, typography, palette, icons, or component states intentionally
- **THEN** `DESIGN.md` directs the implementer to update affected `tests/visual/baselines/` PNGs in the same change
