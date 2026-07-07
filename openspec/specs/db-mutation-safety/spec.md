# db-mutation-safety Specification

## Purpose
The platform's reactive safety layer for destructive class, asset,
and import routes. Every destructive commit captures a pre-mutation
snapshot of the live SQLite DB and writes an audit row, so the
operator can roll back any wipe via the [`admin-recovery`](./admin-recovery/spec.md)
endpoints. This is the technical implementation of the PRD §4.11
contract — "any change to the prod DB must be documented and
formalized; no surprises". Prevention of accidental wipes is at
the process level (OpenSpec review, tests, validation against
established contracts); the reactive layer is the recovery path.

## Requirements

### Requirement: Pre-mutation snapshot is captured before destructive commits

The system SHALL capture a hot copy of the live `data/portfolio.db`
to `data/snapshots/portfolio-<UTC>.db` immediately before every
destructive class/asset/import transaction commits. The snapshot
row is committed atomically with the destructive mutation. If
the snapshot operation fails (disk full, permission denied), the
destructive operation SHALL fail with HTTP 500 and a structured
log entry; the database SHALL NOT be mutated.

The snapshot is the **reactive layer** for PRD §4.11: any wipe
(accidental or intentional) is recoverable via
`POST /admin/restore/{snapshot_id}`.

#### Scenario: Destructive delete — snapshot captured
- **WHEN** a destructive class/asset/import operation is about to commit
- **THEN** the system writes `data/snapshots/portfolio-<UTC>.db` containing the pre-mutation state
- **AND** the path is captured in the mutation's `snapshot_path` column

#### Scenario: Snapshot write fails — mutation rejected
- **WHEN** `snapshot_live_db()` raises an exception (disk full, EACCES on `data/snapshots/`)
- **THEN** the destructive operation does not commit
- **AND** the system returns HTTP 500 with a structured error
- **AND** a log line includes the exception detail

#### Scenario: Snapshot directory is auto-created
- **WHEN** the platform boots and `data/snapshots/` does not exist
- **THEN** the platform creates the directory before the first destructive operation

### Requirement: Audit row records every destructive DB mutation

The system SHALL insert a row into the `db_mutations` table after
every destructive class/asset/import mutation commits. The row
SHALL include: `created_at` (UTC ISO-8601), `route` (HTTP method +
path template), `actor_user_id` (the authenticated user, or `NULL`
for system-initiated mutations), `profile_id` (the affected
profile, or `NULL` for cross-profile), `before_json` (counts of
classes/assets/positions before the mutation), `after_json`
(counts after), and `snapshot_path` (path to the pre-mutation
snapshot, or `NULL` if no snapshot was taken). The audit row
SHALL be best-effort — if the insert fails, the mutation is not
rolled back, but a structured log entry SHALL be emitted.

#### Scenario: Destructive delete writes an audit row
- **WHEN** a destructive operation commits successfully
- **THEN** the system inserts a `db_mutations` row with `route`, `actor_user_id`, `profile_id`, `before_json`, `after_json`, and `snapshot_path` populated
- **AND** the audit row is queryable via `GET /admin/audit?since=<ts>`

#### Scenario: Audit insert fails — mutation survives
- **WHEN** the destructive operation commits but the audit insert raises
- **THEN** the mutation is preserved (already committed)
- **AND** a structured ERROR log line is emitted with the exception
- **AND** the user-visible response is HTTP 200/204/303

### Requirement: Snapshot retention is FIFO-pruned to 50

The system SHALL retain at most the 50 most recent snapshot files
in `data/snapshots/`. The prune SHALL run once per FastAPI
lifespan boot, sorting by filename (which embeds the UTC
ISO-8601 timestamp) and deleting the oldest files beyond the
50th. The prune SHALL NOT touch the operator's `backups/`
directory.

#### Scenario: Boot with 60 snapshots
- **WHEN** the platform boots and `data/snapshots/` contains 60 files
- **THEN** the platform deletes the 10 oldest
- **AND** retains the 50 most recent
- **AND** the operator's `backups/` directory is untouched

#### Scenario: Boot with 30 snapshots
- **WHEN** the platform boots and `data/snapshots/` contains 30 files
- **THEN** the platform takes no action (under the retention threshold)
