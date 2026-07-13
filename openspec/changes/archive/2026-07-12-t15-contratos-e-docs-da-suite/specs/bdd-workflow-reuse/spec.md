## ADDED Requirements

### Requirement: BDD README mirrors canonical workflow and replay contract
The `tests/bdd/README.md` file SHALL name current canonical workflows using the actual workflow identifiers (`login_and_land`, `create_one_class`, `create_two_default_classes`, `add_one_asset`). It SHALL describe `uv run task test-bdd` as serial because the suite shares seeded SQLite state, and it SHALL describe `uv run task test-bdd-single` as the replay/debug entrypoint that rebuilds `data/test_bdd.db` before running one scenario or ordered prefix.

#### Scenario: Workflow names stay current
- **WHEN** a reader inspects the workflow table in `tests/bdd/README.md`
- **THEN** the canonical workflow names match the current BDD contract

#### Scenario: Serial replay path is documented
- **WHEN** a reader inspects the debugging section in `tests/bdd/README.md`
- **THEN** `uv run task test-bdd-single` is described as rebuild + replay
- **AND** `uv run task test-bdd` remains serial because of shared SQLite state
