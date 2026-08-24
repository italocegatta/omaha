## Purpose

Provide bounded, offline evidence for synchronization duration and timeout decisions.

## Requirements

### Requirement: T36 measurement SHALL be bounded, repeatable, and offline

The measurement harness SHALL execute exactly 15 fake/mock connector
repetitions through the application-owned job boundary using a temporary
test database and temporary owned paths. It SHALL not load external
credentials, launch a real browser, access a network service, use production
DB state, run a destructive reset, or commit portfolio changes.

#### Scenario: Fake connector measures isolated job attempts

- **WHEN** the named T36 measurement scenario runs
- **THEN** it records 15 bounded fake/mock connector repetitions through
  `MyProfitSyncService`
- **AND** each attempt ends as a declared success or sanitized failure
- **AND** `Asset`, `Position`, and `DbMutation` counts are unchanged
- **AND** owned temporary paths are cleaned without adopting unrelated paths

### Requirement: T36 evidence SHALL expose distribution and boundary data

Each measurement run SHALL persist a machine-readable evidence block in the
active change `tasks.md` with run/environment metadata, total sample size,
success/failure counts and rate, mean, p50, p95, p99, min, max, sample standard
deviation, IQR, MAD, sanitized failure classes, nominal polling boundary, job
expiry, preview TTL, and independent Playwright stage timeout values.

#### Scenario: Evidence reconciles all measured outcomes

- **WHEN** a bounded run completes
- **THEN** success count plus failure count equals 15
- **AND** every duration is finite and non-negative
- **AND** every failure is classified by terminal status and allowlisted stage/code
- **AND** polling, TTL/expiry, connector-stage, and Playwright-harness limits are
  reported as separate boundaries

### Requirement: T36 SHALL produce a bounded timeout decision for F68

The harness SHALL require at least one successful sample and no unclassified
failure before making a decision. A run with no successful samples SHALL emit
`insufficient-evidence`. It SHALL calculate candidate margin as
`p99_success + max(2 × IQR, 5,000 ms)`, round up to the next 5,000 ms, and
compare it with the current nominal polling boundary of 60,000 ms and the
3,600,000 ms job/preview TTL boundaries. It SHALL emit `covered`,
`increase-justified`, or `insufficient-evidence`; it SHALL never modify runtime
timeout configuration.

#### Scenario: Evidence is sufficient and candidate is bounded

- **WHEN** 15 attempts include at least one successful sample and all failures
  are classified
- **AND** the rounded candidate is below both job expiry and preview TTL
- **THEN** evidence emits `covered` when candidate is at or below 60,000 ms
- **OR** evidence emits `increase-justified` when candidate exceeds 60,000 ms
- **AND** candidate is recorded as a review target for F68 only

#### Scenario: Evidence is insufficient or violates safety boundary

- **WHEN** sample count, successful sample minimum, failure classification,
  repeatability, or TTL/expiry bound fails
- **THEN** evidence emits `insufficient-evidence`
- **AND** candidate is null
- **AND** no polling, job expiry, preview TTL, Playwright timeout, status,
  sanitized message, retry, or manual commit behavior changes
