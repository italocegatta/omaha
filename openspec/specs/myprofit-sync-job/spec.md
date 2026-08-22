# myprofit-sync-job Specification

## Purpose

Profile-scoped background synchronization with safe preview handoff.

## Requirements

### Requirement: MyProfit synchronization SHALL start as a profile-scoped background job
The system SHALL expose authenticated `POST /api/myprofit/sync`, return HTTP 202 with a queued unique job, and reject Família with HTTP 409 before credential or file access.

### Requirement: Synchronization jobs SHALL enforce bounded concurrency and profile isolation
The system SHALL allow one queued or running job per real profile, permit both real profiles independently, cap workers at two, and hide unknown or foreign jobs with HTTP 404.

#### Scenario: Duplicate profile start is rejected
- **WHEN** profile already has queued or running job
- **THEN** second start returns HTTP 409 with original job id

### Requirement: Job status SHALL expose stable lifecycle and sanitized errors
Polling SHALL expose `queued`, `running`, `succeeded`, `failed`, and `expired`; non-success states SHALL return `preview: null` and safe fixed error data.

#### Scenario: Failed status is sanitized
- **WHEN** job records failure
- **THEN** polling exposes only allowlisted stage/code and fixed safe message

### Requirement: Successful synchronization SHALL reuse existing import preview contract without commit
Successful CSV processing SHALL reuse existing parsing and preview serialization, return `preview_id`, `auto_matched`, `unmatched`, and `asset_classes`, and SHALL NOT commit or mutate assets/positions.

#### Scenario: Success returns review payload
- **WHEN** valid CSV is processed
- **THEN** polling returns existing preview shape and no portfolio mutation

### Requirement: Job files and previews SHALL expire and clean up safely
Each job SHALL use unique private storage, remove only owned files on terminal states and shutdown, and apply configured TTL and bounded retention.

#### Scenario: Expiry removes owned resources
- **WHEN** job passes configured TTL
- **THEN** linked preview and owned files are removed while unrelated paths remain

### Requirement: Synchronization SHALL preserve manual mutation guards
Creating or polling a sync job SHALL not authorize commit; Família, snapshot, audit, and production-DB guards SHALL remain active.

#### Scenario: Sync preview requires explicit commit
- **WHEN** successful preview is shown
- **THEN** assets and positions remain unchanged until existing confirmation commit
