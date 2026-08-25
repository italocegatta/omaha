## ADDED Requirements

### Requirement: Canonical preflight uses practical bounded inventory

Canonical test preflight SHALL inspect only runner-declared ports, process
groups, logs, temporary roots, and lane database paths. It SHALL classify each
relevant observation as `absent`, `owned-current-run`, `ephemeral-preexisting`,
`pre-existing`, `foreign`, or `unknown`, and SHALL persist owner evidence before
launch or cleanup. Exact E2E disposable DB disposition is not process ownership
and MUST carry `adopted: false`.

#### Scenario: Clean canonical inventory permits launch

- **WHEN** declared ports are free, declared dynamic roots are absent, and
  declared fixed resources have a valid disposition
- **THEN** preflight records all canonical resources and permits child launch
- **AND** no host-wide process, port, or temporary-path scan becomes a cleanup
  target

#### Scenario: Foreign or unknown canonical inventory blocks safely

- **WHEN** a declared port, process, DB, or temporary resource has foreign,
  unknown, contradictory, or incomplete ownership evidence
- **THEN** preflight records exact identity and failed isolation evidence
- **AND** it blocks before affected child launch without killing, deleting,
  adopting, freeing, or allowlisting the resource

### Requirement: Exact ephemeral E2E DB recreation is separate from ownership

The ownership protocol SHALL permit bounded recreation only for exact fixed E2E
DB paths already registered to the E2E lane, including
`data/test_e2e.db`. Recreate SHALL require a resolved path under the repository
`data/` directory, a regular non-symlink file or absence, no active server
identity using the target, and an explicit receipt disposition. Recreate SHALL
never authorize adoption of old DB contents, process signaling, or any action
against `data/portfolio.db` or an unregistered path.

#### Scenario: Pre-existing E2E DB is recreated without adoption

- **WHEN** exact `data/test_e2e.db` is pre-existing and no active foreign or
  current server owns its declared E2E port
- **THEN** the helper removes only that exact disposable file and records
  `ephemeral-recreated` with `adopted: false`
- **AND** the next server creates the DB through its existing migration/seed
  path

#### Scenario: Protected or contradictory DB is preserved

- **WHEN** recreate receives `data/portfolio.db`, a symlink, a directory, an
  unregistered path, or a path with active foreign ownership evidence
- **THEN** it raises a bounded non-zero/untrusted result with evidence
- **AND** it leaves the path and foreign process untouched

### Requirement: Stale Omaha process recovery requires current-run identity

Stale-process recovery SHALL diagnose exact canonical listener/process evidence
using run/lane, PID, PGID, exact command, repository cwd, port, DB mapping, and
timestamps. A process-name match, PID-only match, or listener-only match SHALL
not prove ownership. Only a current-run-owned process group may receive
graceful stop and bounded escalation; stale, foreign, or unknown state remains
preserved and blocks the affected operation.

#### Scenario: Current-run Omaha child shuts down gracefully

- **WHEN** the recorded child and exact process-group identity match the active
  lane and the lane exits or requires restart
- **THEN** workflow sends `SIGTERM`, waits bounded grace, records exit/port
  evidence, and sends `SIGKILL` only if the same owned group survives
- **AND** receipt records every signal and final cleanup result

#### Scenario: Stale listener cannot be adopted

- **WHEN** requested canonical port is occupied by a dead, foreign, or
  identity-mismatched Omaha-like process
- **THEN** workflow records stale/foreign/unknown diagnosis and returns
  non-zero/untrusted
- **AND** it does not yield a URL, kill the listener, or retry until the port is
  free
