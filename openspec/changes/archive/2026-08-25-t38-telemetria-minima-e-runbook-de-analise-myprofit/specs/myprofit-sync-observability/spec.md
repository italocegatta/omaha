## ADDED Requirements

### Requirement: MyProfit telemetry SHALL be bounded and correlated by job

The application SHALL emit telemetry through the existing `omaha` logger for
each MyProfit run, using the job's UUID-shaped `job_id` as its only run
correlation identity. Events SHALL use finite allowlists for event, domain,
status, stage, and code, and SHALL contain no profile name, credential,
filename, CSV, URL, path, page content, or arbitrary label.

#### Scenario: Successful run emits bounded lifecycle evidence

- **WHEN** real profile starts a MyProfit job and connector/preview completes
- **THEN** telemetry contains actual `queued`→`running` transition, completed
  stage events, one `succeeded` terminal event, and total/stage durations
- **AND** all events carry same `job_id` and only allowlisted dimensions

#### Scenario: Failure emits sanitized evidence

- **WHEN** connector or preview fails with stage/code or unexpected exception
- **THEN** telemetry emits `failed` or `expired` terminal evidence with a
  sanitized allowlisted stage/code and finite duration
- **AND** no exception text, secret, CSV content, URL, path, or filename is
  emitted

### Requirement: Telemetry SHALL expose transitions, stages, and durations

The telemetry contract SHALL emit one event per actual job status transition,
one completed stage event for instrumented connector/preview/handoff stages,
and one terminal event. Terminal events SHALL include total duration; stage
events SHALL include non-negative finite integer `duration_ms`. Telemetry
emission failure SHALL NOT change job status, preview handoff, cleanup, or
manual commit behavior.

#### Scenario: Expiry wins over late worker result

- **WHEN** job expires before a late connector success or failure settles
- **THEN** job remains `expired`, terminal telemetry reports `expired`, and no
  later success/failure terminal event is emitted for that run
- **AND** owned preview/path cleanup behavior remains unchanged

#### Scenario: Concurrent profiles remain distinguishable

- **WHEN** Italo and Ana each run one job concurrently
- **THEN** each event stream is keyed by its own `job_id`
- **AND** worker cap, profile isolation, duplicate rejection, and status API
  behavior remain unchanged

### Requirement: Telemetry SHALL classify analysis boundaries without raw data

Events SHALL distinguish `connector`, `browser`, `preview_handoff`,
`polling_ui`, and `concurrency` domains using finite stage/code values. The
application SHALL use existing stdout logging as storage source; it SHALL NOT
create telemetry tables/files, query APIs, external collectors, or retention
automation. Collected log lines SHALL be retained outside application code for
at least four weeks and at most eight weeks for this observation slice, with
the runbook marking evidence unavailable when stdout was not retained.

#### Scenario: Duplicate start is classified without leaking input

- **WHEN** second start for same profile is rejected as already running
- **THEN** one bounded concurrency event may report `rejected` and
  `sync_in_progress`
- **AND** no request body, profile label, credential, or exception is logged

#### Scenario: Existing logger boundary remains sole sink

- **WHEN** telemetry is emitted in JSON or text logging mode
- **THEN** it appears through configured `omaha` stdout logging
- **AND** no DB row, migration, file artifact, or new retention setting is
  required

### Requirement: UI SHALL report local polling limit without changing polling

When `$store.patrimonioSync` reaches its existing `maxPolls` boundary, the UI
SHALL send at most one fixed `local_limit_reached` signal for current `job_id`
to an authenticated, profile-owned observation boundary, then SHALL preserve
the existing safe error state. The signal SHALL not alter job status, timeout,
retry, preview handoff, or commit behavior.

#### Scenario: Polling reaches local limit

- **WHEN** 120 existing 500 ms polling attempts are exhausted while job is not
  terminal
- **THEN** one `polling_ui`/`local_limit_reached` event is attempted for that
  `job_id`, no further poll is scheduled, and existing safe timeout copy is
  shown
- **AND** server job remains governed by existing lifecycle/expiry rules

#### Scenario: Successful polling still hands off preview

- **WHEN** polling receives valid `succeeded` status before local limit
- **THEN** no local-limit event is emitted, existing import review opens, and
  no automatic commit occurs

#### Scenario: Foreign or repeated UI signal is harmless

- **WHEN** signal references foreign, missing, or already-observed job, or UI
  code attempts duplicate notification
- **THEN** server rejects/ignores observation without DB mutation or status
  change, and UI does not schedule another poll

### Requirement: Runbook SHALL define bounded real-run analysis gate

The versioned runbook SHALL instruct operators to retain and analyze real
telemetry for a minimum four-week window targeting 4–8 real executions per
week, extending to eight weeks when weekly volume is below four or evidence is
incomplete. It SHALL group by `domain/stage/code`, report run counts, failure
counts/rates, p50/p95/p99 total and stage durations, local-limit count,
concurrency count, and missing/invalid event count.

#### Scenario: Evidence window is sufficient for triage

- **WHEN** four-week minimum window has retained valid events and target run
  volume, or an extended eight-week window completes because volume/evidence
  was insufficient
- **THEN** runbook permits a future cause-diagnosis proposal only when one
  normalized stage/code cluster appears in at least three runs across at least
  two weeks and represents at least 50% of failed runs, or local-limit signals
  occur in at least two runs
- **AND** this gate does not authorize timeout, retry, external-service, or F68
  changes

#### Scenario: Evidence is unavailable or below gate

- **WHEN** stdout was not retained, fields are unbounded/invalid, fewer than
  four weeks are available, or no stated recurrence threshold is met
- **THEN** runbook records `insufficient-evidence` and does not infer root
  cause, SLA, timeout, or retry behavior
