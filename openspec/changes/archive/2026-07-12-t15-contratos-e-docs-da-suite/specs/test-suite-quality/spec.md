## ADDED Requirements

### Requirement: Performance baseline stays as dated snapshot of real suite lanes
The `tests/PERFORMANCE.md` file SHALL present benchmark data as a dated snapshot with environment and branch metadata. Its command examples SHALL use taskipy entrypoints (`uv run task test-unit`, `uv run task test-integration`, `uv run task test-e2e`, `uv run task test-bdd`, `uv run task test`, and related lane commands) instead of stale raw `pytest` examples. Its summary SHALL separate fast lane (unit + integration) from browser lane (e2e + BDD + visual), and SHALL call out BDD serial behavior when documenting browser execution.

#### Scenario: Commands use task wrappers
- **WHEN** a reader inspects the Commands block in `tests/PERFORMANCE.md`
- **THEN** taskipy entrypoints are shown instead of raw `pytest` commands

#### Scenario: Lanes remain separated
- **WHEN** a reader inspects the Summary or Lanes section in `tests/PERFORMANCE.md`
- **THEN** fast lane and browser lane are separated
- **AND** BDD serial behavior is stated where the browser lane is described
