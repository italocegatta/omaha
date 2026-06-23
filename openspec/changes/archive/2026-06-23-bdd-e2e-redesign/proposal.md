## Why

The existing e2e suite under `tests/e2e/` (11 Playwright files: s01–s10
plus s06_full_journey) drives a real browser but its scenarios are
expressed as long imperative Python bodies — the *intent* of each test
is buried in 200-line locator dictionaries, `page.evaluate` blocks,
and SQLite backdating hacks. That opacity is why the recent
`<select>` + `<template x-for>` binding regression
(`openspec/changes/archive/2026-06-16-fix-import-modal-select-binding/`)
and the `Alpine.store('importModal')` class-suggestion bug
(`openspec/changes/archive/2026-06-16-fix-import-class-suggestion/`)
both shipped despite passing the suite: the tests asserted on the
Alpine store snapshot, not on the user-visible DOM, and the
"select.value === suggestion" check arrived in a later fix-up commit,
not in the original test that should have caught the bug.

The functional reference backlog (PRD §1.4 — five product features)
is currently only smoke-tested. Combinatorial coverage of "login →
profile pick → classes → assets (manual) → assets (import) → target
PATCH (per-class) → target PATCH (per-asset) → derived portfolio %
display" does not exist as a single readable spec; tests live in
isolated files with overlapping setup helpers that drift apart.

This change adds a BDD e2e suite, in PT-BR `.feature` files, that
captures the *intent* of each user-visible flow as Given/When/Then
scenarios a non-developer can read and a regression guard can
enforce. Old tests are disabled (not deleted) until the new suite is
green for two consecutive runs, then the old suite is deleted in a
separate change.

## What Changes

- Add `pytest-bdd` to `pyproject.toml` dev dependencies; pin a version
  compatible with the existing pytest ≥ 8 (currently resolved via
  `uv.lock`).
- Add `tests/bdd/` as the new BDD e2e suite, structured as:
  - `tests/bdd/features/*.feature` — PT-BR Gherkin scenarios.
  - `tests/bdd/step_defs/*.py` — Python step definitions grouped by
    page area (`auth_steps.py`, `class_steps.py`, `asset_steps.py`,
    `import_steps.py`, `target_steps.py`, `dashboard_steps.py`,
    `common_steps.py`).
  - `tests/bdd/conftest.py` — overrides the live URL/port to
    `127.0.0.1:8766` (one off from `tests/e2e/`'s 8765) so the two
    suites can run in parallel without colliding.
- Add `tests/fixtures/tiny_portfolio.csv` — a 4-row broker CSV
  (2 tickers destined for `Renda Fixa`, 2 for `Ações`) that drives the
  full import flow without the 48-ticker noise of
  `posicao_italo.csv` and `sample_broker.csv`.
- Add `[tool.pytest.ini_options]` BDD markers and register
  `pytest_bdd` so `pytest -m bdd` runs the new suite and
  `pytest -m "not bdd"` excludes it.
- Disable (do not delete) the 11 existing `tests/e2e/test_s*.py`
  files by renaming the suite-level pytest collection: move them to
  `tests/e2e/_disabled/` so a `git grep tests/e2e` surfaces them for
  audit but pytest does not collect them. The directory and its
  shared `conftest.py` are retained for fixture reuse (the new BDD
  suite imports `_resolve_chromium` and `_wait_for_port` from
  `tests/e2e/conftest.py`).
- Add a taskipy alias `task test-bdd` that runs `pytest tests/bdd -v`
  and registers `bdd` as a new task alongside `test-e2e`.
- Add an OpenSpec capability `bdd-e2e-coverage` with one REQUIREMENT
  covering the seven scenario groups and the parametrization rule.

## Capabilities

### New Capabilities

- `bdd-e2e-coverage`: defines the seven required scenario groups
  (login + profile pick, class CRUD, asset CRUD manual, asset
  import, target PATCH per-class, target PATCH per-asset, derived
  portfolio % display), the parametric dual-profile rule
  (`Italo` + `Ana`), the combinatorial-coverage rule (one scenario
  may combine stages; the suite must include at least one full
  end-to-end happy-path scenario that exercises every stage in
  order), and the PT-BR `.feature` file rule.

### Modified Capabilities

(none — the BDD suite asserts behavior already described in
`openspec/specs/import-modal/`, `openspec/specs/import-class-auto-suggest/`,
`openspec/specs/dashboard-inline-editing/`, and the PRD's
unwritten-but-active flows.)

## Impact

- `pyproject.toml` — +1 dev dep (`pytest-bdd`); +1 taskipy alias
  (`test-bdd`); +1 pytest config block.
- `tests/e2e/test_s*.py` (11 files, ≈2.5k lines total) — moved to
  `tests/e2e/_disabled/` so pytest collection skips them. Code
  preserved for diff mining during the parallel-bringup window.
- `tests/e2e/conftest.py` — untouched. The new suite imports the
  helpers `_wait_for_port` and `_resolve_chromium`; the new
  `tests/bdd/conftest.py` re-exports the `page` and `live_url`
  fixtures via `from tests.e2e.conftest import page, live_url`.
- `tests/bdd/` — new tree, ≈7 feature files + 7 step_defs modules +
  conftest, ≈1.5–2k lines.
- `tests/fixtures/tiny_portfolio.csv` — new, 4 data rows + 1 header
  + 1 banner line, ≈200 bytes.
- `openspec/specs/bdd-e2e-coverage/spec.md` — new.
- `openspec/changes/bdd-e2e-redesign/{proposal,design,tasks}.md` —
  new (this change).
- `tests/conftest.py` — no change. The
  `pytest_collection_modifyitems` allow-list rule remains valid
  because BDD files live under `tests/bdd/`, not under `tests/`; the
  `UnknownTestPath` warning would only fire if a `test_*.py` is added
  under `tests/bdd/` (none is — pytest-bdd collects from
  `.feature` files, not `test_*.py`).
- `AGENTS.md` — one new bullet under the "Test marker rule" section
  recording that BDD scenarios live under `tests/bdd/` and run via
  `pytest-bdd`; the `pytest_collection_modifyitems` rule does not
  apply to `.feature` files.

No backend change. No migration. No new selector contract on the
dashboard (the existing `data-testid` attributes are reused by the
BDD step definitions). The full-journey scenario lands on the same
DOM the existing s04/s06 e2e suite drove.
