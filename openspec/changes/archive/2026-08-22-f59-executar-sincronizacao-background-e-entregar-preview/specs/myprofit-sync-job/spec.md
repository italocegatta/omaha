## ADDED Requirements

### Requirement: MyProfit synchronization SHALL start as a profile-scoped background job

The system SHALL expose authenticated `POST /api/myprofit/sync` for the active
real profile. It SHALL create one job with a unique `job_id`, return HTTP 202
with `{"job_id", "status": "queued"}`, and run the F58 connector outside the
request handler. It SHALL reject Família with HTTP 409 and
`{"reason":"household_read_only"}` before credential resolution, connector
access, temporary-directory creation, or file creation.

#### Scenario: Real profile starts synchronization

- **WHEN** an authenticated operator has active real profile Italo or Ana
- **AND** sends `POST /api/myprofit/sync`
- **THEN** response is HTTP 202 with unique `job_id` and status `queued`
- **AND** no asset, position, class, or import commit row is mutated

#### Scenario: Família cannot start synchronization

- **WHEN** active session profile is the Família sentinel
- **AND** operator sends `POST /api/myprofit/sync`
- **THEN** response is HTTP 409 with reason `household_read_only`
- **AND** credential lookup, connector, browser, network, temporary-file, and job-worker spies observe zero calls

### Requirement: Synchronization jobs SHALL enforce bounded concurrency and profile isolation

The system SHALL allow at most one queued or running job for each real profile
and SHALL return HTTP 409 with stable code `sync_in_progress` and the existing
job id when a second start is requested for that profile. It SHALL permit the two
real profiles to run independently, with no more than two active workers in the
application process. `GET /api/myprofit/sync/{job_id}` SHALL return 404 for an
unknown job or a job owned by another active real profile.

#### Scenario: Duplicate start does not create second active job

- **WHEN** Italo already has a queued or running synchronization job
- **AND** the same active profile requests another synchronization
- **THEN** response is HTTP 409 with code `sync_in_progress` and original `job_id`
- **AND** the database contains one queued/running Italo job

#### Scenario: Real profiles remain isolated while running concurrently

- **WHEN** Italo and Ana each start one synchronization
- **THEN** each job carries its own profile id and may run concurrently
- **AND** each reservation, worker session, preview link, and owned path is
  profile-scoped

#### Scenario: Foreign job status is hidden

- **WHEN** Italo polls a job created for Ana
- **THEN** response is HTTP 404
- **AND** response does not reveal Ana's status, filename, preview id, or error

### Requirement: Job status SHALL expose stable lifecycle and sanitized errors

The system SHALL expose authenticated `GET /api/myprofit/sync/{job_id}` with
states `queued`, `running`, `succeeded`, `failed`, and `expired`. While queued or
running, response SHALL contain `preview: null`. A failed response SHALL contain
only a stable stage/code and fixed PT-BR page-safe message; it SHALL omit
credentials, raw exception text, URLs, CSV bytes, and filesystem paths.

#### Scenario: Polling reports queued and running without preview

- **WHEN** an owned job has not completed or is executing
- **THEN** polling returns HTTP 200 with its lifecycle state
- **AND** `preview` is null

#### Scenario: Normalized job failure stays page error

- **WHEN** internal job execution records a bounded stage/code failure
- **THEN** job reaches `failed` with stage/code and safe PT-BR message
- **AND** response has `preview: null`
- **AND** no import-modal open command or preview handoff is emitted

### Requirement: Successful synchronization SHALL reuse existing import preview contract without commit

After F58 returns non-empty CSV bytes, the system SHALL reuse
`parse_positions`, `ImportPreview`, and `_build_preview_response` used by
`POST /api/import/preview`. A succeeded status SHALL return the existing
`preview_id`, `auto_matched`, `unmatched`, and `asset_classes` shape as `preview`
for `$store.importModal` review. Synchronization SHALL NOT call
`POST /api/import/commit` or persist `Asset`/`Position` changes.

#### Scenario: Valid internal CSV produces existing review payload

- **WHEN** the internal preview helper receives valid UTF-8 position CSV bytes
  for Italo
- **THEN** job reaches `succeeded`
- **AND** polling returns preview payload with existing preview fields and profile-scoped `preview_id`
- **AND** manual class assignment remains required for unmatched rows

#### Scenario: Invalid internal CSV fails before modal handoff

- **WHEN** the internal preview helper receives empty, non-UTF-8, oversized, or
  parser-empty bytes
- **THEN** job reaches `failed` with sanitized preview/parser stage and `preview: null`
- **AND** no asset, position, or import commit mutation occurs

### Requirement: Job files and previews SHALL expire and clean up safely

Each job SHALL use a unique private temporary directory and sanitized basename
for downloaded CSV material. The service SHALL remove job files on success,
failure, expiry, and owned shutdown. The job and linked preview SHALL use the
existing configured preview TTL (`PREVIEW_TTL_SECONDS`); after expiry, polling
an owned job SHALL return HTTP 200 with `status: "expired"` and `preview: null`.
Cleanup SHALL remove only paths recorded as owned by that job.

#### Scenario: Successful job leaves no job file

- **WHEN** a job successfully creates an `ImportPreview`
- **THEN** its private CSV directory is removed
- **AND** the preview remains available through the existing preview TTL for manual review

#### Scenario: Expired job removes preview and files

- **WHEN** an owned job or its review preview passes the configured TTL
- **THEN** polling returns `status: "expired"` with `preview: null`
- **AND** linked preview and job-owned temporary files are removed
- **AND** unrelated temporary paths and production DB files remain untouched

### Requirement: Synchronization SHALL preserve manual mutation guards

The synchronization boundary SHALL preserve Família read-only behavior and the
existing manual import confirmation, `db-mutation-safety` pre-mutation snapshot,
post-commit audit, and production-DB test guard. Creating or polling a sync job
is not authorization to commit imported positions.

#### Scenario: Review remains manual and auditable

- **WHEN** a succeeded sync preview is shown to an operator
- **THEN** no position or asset mutation occurs until existing explicit import confirmation
- **AND** a later commit continues to require existing snapshot and audit guards

#### Scenario: Internal focused tests do not involve connector behavior or production DB

- **WHEN** focused sync tests exercise internal start, polling, expiry,
  preview-handoff, page-state, and commit-boundary behavior
- **THEN** synthetic internal inputs and temporary test DB/path resources are
  used
- **AND** connector, Playwright, browser, network, credential, and production
  DB behavior count zero
