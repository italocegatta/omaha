# T22 — Delta spec: audit_inventory isolation

## Requirement: audit_inventory tests run in the audit-integration lane, not the integration lane

The `test_audit_inventory.py` test file SHALL reside under `tests/audit_integration/`. It SHALL NOT be collected by `task test-integration` or `task test-integration-parallel` because those tasks pass `--ignore=tests/audit_integration`. It SHALL be collected and executed by `task test-audit-integration`.

### Scenario: audit_inventory excluded from integration lane

- **WHEN** developer runs `uv run task test-integration`
- **THEN** pytest does not collect any test from `tests/audit_integration/test_audit_inventory.py`
- **AND** the integration suite wall-clock does not include the ~48s audit_inventory cost

### Scenario: audit_inventory included in audit-integration lane

- **WHEN** developer runs `uv run task test-audit-integration`
- **THEN** pytest collects all 30 tests from `tests/audit_integration/test_audit_inventory.py`
- **AND** all tests pass

### Scenario: push not blocked by audit_inventory

- **WHEN** developer runs `git push`
- **THEN** the pre-push hook runs `task test-integration-parallel`
- **AND** audit_inventory tests are not collected (excluded by `--ignore=tests/audit_integration`)
- **AND** the push completes without waiting for CSS/template parsing

### Scenario: CI runs audit_inventory in dedicated job

- **WHEN** CI pipeline executes
- **THEN** the `test-audit-integration` job runs `task test-audit-integration`
- **AND** the job includes `tests/audit_integration/test_audit_inventory.py`
- **AND** the job runs independently of the `test-integration` job
