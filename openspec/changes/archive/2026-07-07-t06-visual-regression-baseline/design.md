## Context

The current suite has unit, integration, BDD, and Playwright e2e coverage, but no committed screenshot baseline for the post-D02 visual system. F08/F09/F10/F12 changed palette, typography, state language, tables, and icons; future template/CSS edits need a cheap way to catch unintended visual drift across desktop and mobile.

The visual gate is test infrastructure only. It should not change routes, templates, models, seed data, or production behavior.

## Goals / Non-Goals

**Goals:**
- Add a deterministic Playwright visual suite under `tests/visual/`.
- Cover the main browser surfaces at desktop `1440x900` and mobile `375x667`.
- Commit baselines under `tests/visual/baselines/` and ignore generated diff/output files.
- Add `task test-visual` so visual checks are explicit and separate from `task test-e2e`.
- Assert structural page content before taking screenshots.

**Non-Goals:**
- No runtime UI redesign in T06.
- No CI hard gate unless the dormant workflow is later reactivated.
- No pixel-perfect threshold for every component state; first baseline covers page-level regression.
- No new browser dependency beyond existing Playwright.

## Decisions

### D-T06.1 — Dedicated `tests/visual/` suite

Use `tests/visual/` instead of extending `tests/e2e/`. Visual snapshots have different review ergonomics, artifacts, and update cadence; keeping them separate avoids making `task test-e2e` slower and noisy.

Alternative considered: add screenshot assertions to existing e2e files. Rejected because journey tests should stay behavior-focused.

### D-T06.2 — Commit only baselines, ignore generated outputs

Commit `tests/visual/baselines/**/*.png`. Ignore transient Playwright outputs such as `tests/visual/results/`, `tests/visual/diffs/`, and pytest snapshot temp output. Baselines are source-of-truth artifacts; diffs are local review output.

Alternative considered: keep baselines untracked and regenerate locally. Rejected because that gives no shared regression contract.

### D-T06.3 — Two viewport matrix

First slice captures desktop `1440x900` and mobile `375x667`. These catch top-nav density, table overflow, responsive action visibility, icon alignment, and compact mobile layout without exploding the baseline count.

Alternative considered: add tablet and high-DPI variants now. Rejected as baseline churn before the first gate proves useful.

### D-T06.4 — Structural pre-assertions before screenshots

Each visual test must verify meaningful DOM content before snapshotting: seeded class text, expected data-testid markers, BRL totals, or route-specific form/status markers. This prevents a blank page, login redirect, empty DB, or stale server page from becoming a valid baseline.

Alternative considered: rely on screenshot dimensions alone. Rejected because `test-suite-quality` already documents file-size-only visual gates as false-positive bait.

### D-T06.5 — Explicit threshold starts at 0.5%

Use a 0.5% pixel-diff threshold for page screenshots unless implementation proves it too noisy. The exact value belongs in the helper/fixture so future changes can tune one place.

Alternative considered: zero-diff strict snapshots. Rejected because font antialiasing and browser rasterization create noise, especially with Google Fonts and icons.

### D-T06.6 — Seeded dev state via existing CSV path

Visual tests should use the same seeded state as existing e2e flows: login as a seeded user and depend on `task db-reset`/fixtures, not inline asset creation. T06 must not hardcode asset or position seed rows.

Alternative considered: generate a tiny visual fixture DB. Rejected because it would violate the repo's CSV seed invariant and would not reflect the real portfolio density.

### D-T06.7 — Snapshot names encode page and viewport

Snapshot filenames should include page/state and viewport, e.g. `patrimonio-desktop.png` and `patrimonio-mobile.png`. Keep names stable so diffs are reviewable.

Alternative considered: Playwright-generated platform names only. Rejected because the source page/state becomes harder to review in git.

## Risks / Trade-offs

- Font/network nondeterminism → wait for loaded fonts where possible and keep threshold non-zero.
- Baseline churn after intentional design changes → update baselines in the same OpenSpec change as the visual change.
- Large PNG files in git → keep scope to page-level baselines and avoid diff artifact commits.
- Login/session setup flake → reuse existing Playwright auth helpers where practical and pre-assert authenticated page content before screenshots.

## Migration Plan

1. Add visual fixtures/helpers and baseline directory.
2. Add first page/state matrix and generate baselines from a seeded DB.
3. Add `task test-visual` and document usage in `DESIGN.md`.
4. Run `task test-visual` locally, then standard lint/test subset.
5. Archive the new `visual-regression-baseline` spec after implementation.

Rollback: remove `tests/visual/`, `task test-visual`, baseline ignore rules, and the `DESIGN.md` testing-strategy note.

## Open Questions

- Whether to include `/audit_report` depends on the route's current availability and auth path during apply.
- Whether `rentabilidade` and `proventos` baselines should assert stubs or be skipped if the owner keeps those pages deferred.
