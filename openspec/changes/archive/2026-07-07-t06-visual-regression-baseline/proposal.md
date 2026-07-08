## Why

F08/F09/F10/F12 changed the visual system substantially, but the test suite still lacks a repeatable screenshot baseline for browser-visible regressions. T06 adds a focused Playwright visual gate so future CSS/template changes can detect unexpected layout and palette drift before the user opens the LAN URL.

## What Changes

- Add a dedicated visual regression test suite under `tests/visual/`.
- Capture desktop (`1440x900`) and mobile (`375x667`) baselines for key pages and states.
- Commit baseline PNGs under `tests/visual/baselines/` and keep generated diff artifacts out of version control.
- Add `task test-visual` as the explicit command for the screenshot gate.
- Require structural pre-assertions before screenshots so empty/stale pages cannot produce valid baselines.
- Keep visual regression separate from `task test-e2e`; local dev does not pay the screenshot cost unless explicitly requested.

## Capabilities

### New Capabilities
- `visual-regression-baseline`: Playwright screenshot baseline suite, baseline artifact policy, viewport matrix, structural pre-assertions, diff threshold, and taskipy entry point.

### Modified Capabilities
- None.

## Impact

- `tests/visual/` for Playwright visual fixtures, snapshot tests, and baseline images.
- `pyproject.toml` for `task test-visual`.
- `.gitignore` for generated visual diff/output paths while preserving committed baselines.
- `DESIGN.md` for the visual regression testing strategy.
- No runtime routes, models, templates, or production behavior change in the proposal itself.
