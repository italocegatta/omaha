## ADDED Requirements

### Requirement: Snapshot listing endpoint enumerates available rollback points

The system SHALL expose `GET /admin/snapshots` returning a JSON array of snapshot metadata: `id` (the basename minus `.db`), `path` (absolute path), `size_bytes`, `created_at` (UTC ISO-8601), and `mutation_id` (the `db_mutations.id` that produced it, or `NULL` if no mutation references it). The endpoint SHALL require the `X-Admin-Password` header to match the `ADMIN_PASSWORD` env var; missing header or wrong password SHALL return HTTP 401.

#### Scenario: List snapshots — authenticated
- **WHEN** the operator sends `GET /admin/snapshots` with `X-Admin-Password: <correct>`
- **THEN** the system returns HTTP 200 with a JSON array of snapshot metadata
- **AND** the array is sorted by `created_at` descending (most recent first)

#### Scenario: List snapshots — wrong password
- **WHEN** the operator sends `GET /admin/snapshots` with the wrong `X-Admin-Password`
- **THEN** the system returns HTTP 401 with `{"reason": "unauthorized"}`

#### Scenario: List snapshots — missing header
- **WHEN** the operator sends `GET /admin/snapshots` without `X-Admin-Password`
- **THEN** the system returns HTTP 401

### Requirement: Restore endpoint rolls the live DB back to a named snapshot

The system SHALL expose `POST /admin/restore/{snapshot_id}` that overwrites `data/portfolio.db` with the named snapshot file and triggers a uvicorn restart. The endpoint SHALL require the `X-Admin-Password` header. The endpoint SHALL return HTTP 202 with `{"restart_needed": false, "restarted_via": "systemd"}` when the systemd restart succeeds, or HTTP 202 with `{"restart_needed": true, "restarted_via": null}` when the systemd unit is absent (the operator is responsible for `pkill -f 'uvicorn omaha.main' && task serve`).

#### Scenario: Restore — systemd unit present
- **WHEN** the operator sends `POST /admin/restore/portfolio-2026-07-07T14-23-00Z` with the correct `X-Admin-Password`
- **AND** the `omaha-web.service` systemd unit is registered with the user-level manager
- **THEN** the system copies the snapshot over `data/portfolio.db`
- **AND** shells out `systemctl --user restart omaha-web.service`
- **AND** waits for the service to come back healthy
- **AND** returns HTTP 202 with `{"restart_needed": false, "restarted_via": "systemd"}`

#### Scenario: Restore — systemd unit absent
- **WHEN** the operator sends `POST /admin/restore/portfolio-2026-07-07T14-23-00Z` with the correct `X-Admin-Password`
- **AND** no systemd unit is registered
- **THEN** the system copies the snapshot over `data/portfolio.db`
- **AND** emits a structured WARN log line "restart needed: no omaha-web.service unit"
- **AND** returns HTTP 202 with `{"restart_needed": true, "restarted_via": null}`

#### Scenario: Restore — wrong password
- **WHEN** the operator sends `POST /admin/restore/{id}` with the wrong `X-Admin-Password`
- **THEN** the system returns HTTP 401
- **AND** the live DB is not modified

#### Scenario: Restore — snapshot does not exist
- **WHEN** the operator sends `POST /admin/restore/does-not-exist` with the correct `X-Admin-Password`
- **THEN** the system returns HTTP 404 with `{"reason": "snapshot_not_found"}`
- **AND** the live DB is not modified

### Requirement: Audit listing endpoint surfaces recent mutations

The system SHALL expose `GET /admin/audit?since=<utc-iso-timestamp>&limit=<n>` returning a JSON array of `db_mutations` rows newer than `since`, capped at `limit` (default 100, max 500). Each entry SHALL include `id`, `created_at`, `route`, `actor_user_id`, `profile_id`, `before_json`, `after_json`, and `snapshot_path`. The endpoint SHALL require the `X-Admin-Password` header.

#### Scenario: Audit listing — recent mutations
- **WHEN** the operator sends `GET /admin/audit?since=2026-07-01T00:00:00Z` with the correct `X-Admin-Password`
- **THEN** the system returns HTTP 200 with a JSON array of mutation rows
- **AND** the array is sorted by `created_at` descending

#### Scenario: Audit listing — empty result
- **WHEN** the operator sends `GET /admin/audit?since=2099-01-01T00:00:00Z`
- **THEN** the system returns HTTP 200 with an empty array

#### Scenario: Audit listing — limit cap
- **WHEN** the operator sends `GET /admin/audit?limit=10000`
- **THEN** the system clamps the limit to 500 and returns at most 500 rows
