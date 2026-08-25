## MODIFIED Requirements

### Requirement: Runbook SHALL define bounded real-run analysis gate

The versioned runbook SHALL instruct operators to discover the authoritative
`omaha` stdout source for the active deployment, retain and analyze real
telemetry for a minimum four-week window targeting 4–8 real executions per
week, and extend to eight weeks when weekly volume is below four or evidence is
incomplete. It SHALL document extraction from both existing JSON and text
logging envelopes using the exact bounded `myprofit_telemetry` message shape.
It SHALL validate UUID-shaped `job_id`, finite event/domain/status/stage/code
allowlists, non-negative bounded integer durations or `na`, fixed fields, and
exact duplicate-line handling without repairing invalid values.

The runbook SHALL group accepted events by `job_id` and bounded
`domain/stage/code`, report observed-run and terminal-run denominators,
succeeded/failed/expired counts, failure rates, incomplete runs, p50/p95/p99
total and stage durations, local-limit count, concurrency count, and
missing/invalid event count. It SHALL classify terminal `failed` only as a
failed run, terminal `expired` only as an expired run, and an absent terminal
event as incomplete evidence. A missing `ui_limit` event SHALL NOT be treated
as proof that the browser did not reach its local polling boundary.

The runbook SHALL provide a read-only correlation procedure for selected
`job_id` values against existing `myprofit_sync_jobs` fields, including
`profile_id`, status, normalized error fields, lifecycle timestamps, and
retention availability. Correlation SHALL use exact `job_id` and the declared
profile foreign key only; missing/pruned rows SHALL be reported as
`db-correlation-unavailable`, not reconstructed or joined by time, filename, or
profile label.

#### Scenario: Retained source supports bounded weekly analysis

- **WHEN** at least four complete weeks have retained authoritative stdout,
  valid event fields, and target real-run volume, or an extended eight-week
  window completes because volume/evidence was initially insufficient
- **THEN** the runbook permits a future cause-diagnosis proposal only when one
  normalized `stage/code` cluster appears in at least three terminal failed
  runs across at least two weeks and represents at least 50% of failed
  terminal runs, or local-limit signals occur in at least two runs
- **AND** the weekly report includes observed and terminal denominators,
  failed/expired/incomplete separation, bounded factor groups, duration
  percentiles, and missing/invalid counts
- **AND** this gate does not authorize timeout, retry, external-service, or
  F68 changes

#### Scenario: JSON or text stdout is collected without inventing a sink

- **WHEN** an operator retrieves retained output from the existing development
  stdout capture or production Compose `web` stdout
- **THEN** the runbook extracts the telemetry message from JSON `msg` or the
  existing text prefix, records source/rotation coverage, and keeps only the
  fixed bounded event fields
- **AND** the runbook does not assume an application-owned file, collector,
  telemetry table, query API, or retention daemon

#### Scenario: Exact job correlation is read-only

- **WHEN** an accepted event has a selected UUID-shaped `job_id`
- **THEN** the operator may issue a read-only `SELECT` for the matching
  `myprofit_sync_jobs` row and compare profile ownership, status, error fields,
  and lifecycle timestamps
- **AND** a missing or pruned row is marked `db-correlation-unavailable`
- **AND** no database write, inferred time join, profile-label join, or
  reconstruction is permitted

#### Scenario: Evidence is unavailable or classification is incomplete

- **WHEN** stdout was not retained, rotation removed part of the requested
  window, fields are invalid, fewer than four weeks are available, a job has no
  terminal event, or no stated recurrence threshold is met
- **THEN** the runbook records `insufficient-evidence` and does not infer root
  cause, SLA, timeout, retry, failed status, expired status, or absence of a
  local-limit event
