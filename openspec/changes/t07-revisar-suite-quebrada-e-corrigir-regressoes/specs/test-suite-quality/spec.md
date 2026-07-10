## MODIFIED Requirements

### Requirement: Delivery gate requires full suite green
Runtime changes SHALL not be considered delivered while `uv run task test` is red.
Archive/merge must wait for a green full suite, not just a green subset.
For this slice, the canonical regression families are BDD and e2e browser/workflow tests, including import modal and visible navigation/import flows; a red result in any of them SHALL block delivery until the failing expectation is corrected in the owning test or runtime code.

#### Scenario: Full suite is red and delivery is blocked
- **WHEN** `uv run task test` fails
- **THEN** the change stays open
- **AND** no archive step marks it delivered

#### Scenario: Browser-visible change still needs full suite green
- **WHEN** a change touches runtime code, templates, routes, models, seed, migrations, or static assets
- **THEN** the full suite gate still applies
- **AND** the change cannot be archived on partial evidence

#### Scenario: Canonical regression family red blocks delivery
- **WHEN** any of the canonical regression families for this slice is red
- **THEN** delivery stays blocked
- **AND** the failing expectation is traced to test, code, or spec before the change can close
