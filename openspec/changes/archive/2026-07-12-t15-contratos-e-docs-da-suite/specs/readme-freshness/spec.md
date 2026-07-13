## ADDED Requirements

### Requirement: README tests section uses canonical task lanes
The `README.md` Tests section SHALL describe taskipy entrypoints using current suite behavior. `uv run task test` SHALL be described as full suite (unit + integration + audit + e2e + visual + BDD). `uv run task coverage` SHALL be described as fast lane only (unit + integration) and the only canonical command that writes `reports/coverage.xml`. The browser lane SHALL be described as e2e + BDD + visual and explicitly noted as no-coverage.

#### Scenario: Full-suite wording matches current task
- **WHEN** an operator reads the `Tests` section in `README.md`
- **THEN** `uv run task test` is described as full suite including audit, e2e, visual, and BDD
- **AND** it is not described as unit + integration + e2e only

#### Scenario: Coverage lane stays fast only
- **WHEN** an operator reads the `Tests` section in `README.md`
- **THEN** `uv run task coverage` is described as unit + integration only
- **AND** the section states that `reports/coverage.xml` is written only by that command
