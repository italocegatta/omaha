## MODIFIED Requirements

### Requirement: Test coverage report

System SHALL provide taskipy shortcuts for coverage reporting. Canonical
`uv run task test` SHALL execute unit, integration, audit integration, E2E, BDD,
and retained visual coverage concurrently through taskipy-owned runner, without
changing individual task entrypoints or selection.

Runner SHALL isolate each child in own process group and use only taskipy task
entrypoints. It SHALL preflight test-only lane DB targets and SHALL NOT invoke
production DB tasks, migrations, seeds, resets, or raw pytest commands. On first
child failure it SHALL terminate remaining child groups; on SIGINT/SIGTERM it
SHALL forward signal to remaining child groups; after bounded grace it SHALL
SIGKILL survivors; it SHALL always reap children. It SHALL return non-zero for
lane, cleanup, or interruption failure.

For T29, runner SHALL compare every canonical execution against committed
immutable post-removal 1,043-node manifest/checksum. Comparison SHALL include
exact node-ID set, lane membership, checksum, and two exact skip identities.
Eighteen focused T29 harness nodes remain deliberate coverage. Runner SHALL NOT
obtain match through deletion, skip, xfail, disable, or lane reduction, except
historical mobile removal and exact owner-authorized desktop removal documented
in `visual-regression-baseline`.

#### Scenario: Full task concurrently preserves complete coverage
- **WHEN** operator runs `uv run task test`
- **THEN** unit, integration, audit integration, E2E, BDD, and visual lanes run
- **AND** each lane uses existing canonical taskipy entrypoint
- **AND** all lane failures make full task fail
- **AND** resulting population matches 1,043-node manifest/checksum

#### Scenario: Interrupted full task reaps browser and server children
- **WHEN** operator interrupts `uv run task test` with SIGINT or SIGTERM
- **THEN** runner forwards signal to every running lane process group
- **AND** waits bounded grace then kills only surviving groups
- **AND** reaps every child before returning non-zero

#### Scenario: Full task refuses non-test database target
- **WHEN** full-task runner detects lane database target outside recognized test paths
- **THEN** it fails before starting children
- **AND** it does not access production database
