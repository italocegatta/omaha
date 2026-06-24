## Purpose

End-to-end test suite re-enabled after the multi-user seed
migration (commit `35bf15d`) and the M002 fix (`a8b1d13`).
The suite runs a real chromium browser against a real uvicorn
instance bound to `127.0.0.1:8765` and exercises the operator
journeys that the BDD scenarios cover at a lower level
(per-test isolation, screenshot capture, real DOM events
including drag/scroll/clipboard).
## Requirements
### Requirement: e2e suite is enabled and uses current seed users

The e2e test suite MUST be runnable as `uv run task test-e2e`,
collecting tests from `tests/e2e/test_*.py` (the
`tests/e2e/_disabled/` quarantine directory is reserved for
tests awaiting rework — its presence MUST NOT be required
for any test to be collected). Login helpers MUST use a
seeded user (`Italo` or `Ana`); the historical single-user
`family` username was removed in commit `35bf15d` and any
helper that fills the login form with `family` MUST be
replaced with a seeded username.

A test that codifies a removed bug as a feature (e.g.
`test_inline_edit_blocks_when_sum_neq_100`, which asserts
that the dashboard BLOCKS the user from editing an inline
`target_pct` that would push the per-class sum off 100) MUST
be removed rather than updated, because keeping it would
re-introduce the regression the production code was fixed
to remove. The behavioral inverse (off-100 IS accepted) is
covered by the BDD scenario "Inline edit off-100 é aceito
(D006)" in `tests/bdd/features/asset_crud.feature`.

#### Scenario: task test-e2e collects tests

- **WHEN** the operator runs `uv run task test-e2e`
- **THEN** pytest reports at least one test collected from
  `tests/e2e/test_*.py` (no "0 tests collected" exit)
- **AND** the suite either passes or fails with concrete
  test names (not the silent "no tests" silent pass)

#### Scenario: no helper fills the login form with "family"

- **GIVEN** a grep of `tests/e2e/test_*.py` for the string
  `"family"` in a login form-fill context
- **THEN** zero matches are reported
- **AND** every login form fill uses a seeded username
  (`Italo` or `Ana`)

#### Scenario: removed bug is not codified as a feature

- **GIVEN** the change `fix-inline-edit-off-100-blocking`
  was applied (D006: per-class sum off-100 is accepted by
  the server and the client)
- **THEN** `tests/e2e/test_s01_inline_edit.py` does NOT
  contain a test whose name includes
  `blocks_when_sum_neq_100`
- **AND** the BDD scenario
  `"Edição inline preserva a posição visual da linha (row pin)"`
  in `tests/bdd/features/asset_crud.feature` covers the
  accepted-path behavior
