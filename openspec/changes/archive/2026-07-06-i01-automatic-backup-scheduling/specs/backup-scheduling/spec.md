## ADDED Requirements

### Requirement: A scheduled service triggers the backup script periodically

The system SHALL run `scripts/backup.py` automatically on a fixed
interval in production via a `backup-scheduler` service defined in
`prod.yml`. The service SHALL use the same `omaha:prod` image and
the same `command` as the existing `backup` service so the snapshot
produced by a scheduled run is byte-identical to one produced by a
manual `docker compose run --rm backup`.

#### Scenario: Scheduler is up by default

- **WHEN** the operator runs `docker compose -f prod.yml up -d`
- **THEN** the `backup-scheduler` service starts alongside `web` and
  `nginx` and begins its periodic loop without further input

#### Scenario: One scheduled run produces the same artifact as a manual run

- **WHEN** the scheduler fires and `scripts/backup.py` executes with
  the same arguments as the manual `backup` service
- **THEN** the resulting `./backups/portfolio-<UTC-timestamp>.db` file
  is byte-equivalent to a snapshot produced by
  `docker compose -f prod.yml run --rm backup` for the same source
  database state

### Requirement: Schedule interval is configurable

The system SHALL expose the interval between scheduled runs as the
`BACKUP_INTERVAL` environment variable, interpreted as integer
seconds. The default value SHALL be `86400` (24 hours). The service
SHALL read `BACKUP_INTERVAL` at start time and re-read it on
container restart; mid-run changes require a container restart.

#### Scenario: Default interval is 24 hours

- **WHEN** `prod.yml` is brought up without overriding
  `BACKUP_INTERVAL`
- **THEN** the scheduler waits 86400 seconds between backup
  invocations

#### Scenario: Operator shortens the interval via env override

- **WHEN** the operator sets `BACKUP_INTERVAL=3600` in the deploy
  environment before `docker compose -f prod.yml up -d`
- **THEN** the scheduler waits 3600 seconds (1 hour) between backup
  invocations

### Requirement: A failed run does not stop the scheduler

The system SHALL keep the `backup-scheduler` container running
indefinitely across individual run failures. A non-zero exit code
from `scripts/backup.py` SHALL be logged with the run's UTC
timestamp; the scheduler SHALL then sleep `BACKUP_INTERVAL` seconds
and attempt the next run.

#### Scenario: Backup failure logs and continues

- **WHEN** `scripts/backup.py` exits non-zero (e.g., source DB
  locked, disk full)
- **THEN** the scheduler logs the exit code and error output to
  `docker compose logs backup-scheduler` and proceeds to the next
  scheduled run after `BACKUP_INTERVAL` seconds without exiting the
  container

#### Scenario: Three consecutive failures still leave the scheduler up

- **WHEN** the scheduler has logged three consecutive non-zero
  exits
- **THEN** the container remains in `running` state and continues
  to attempt the next scheduled run

### Requirement: Each run produces a timestamped, lexically sortable filename

The system SHALL use the same filename pattern as the manual
`backup` service: `portfolio-YYYYMMDDTHHMMSSZ.db` in UTC, where the
trailing `Z` and the date format make the filename lexically
sortable. The file SHALL land in the bind-mounted `./backups`
directory on the host.

#### Scenario: Filename matches manual-backup pattern

- **WHEN** the scheduler fires at `2026-07-06T03:14:15Z`
- **THEN** the produced file is `./backups/portfolio-20260706T031415Z.db`
  and an `ls backups | sort` lists it in chronological order

### Requirement: The scheduler can be disabled without affecting other services

The system SHALL allow the operator to start the rest of the
production stack (`web`, `nginx`) without starting
`backup-scheduler`. Disabling the scheduler SHALL NOT require
modifying `prod.yml` — it SHALL be achievable either by stopping
the specific service (`docker compose -f prod.yml stop
backup-scheduler`) or by overriding via a compose override file.

#### Scenario: Stopping the scheduler does not touch web or nginx

- **WHEN** the operator runs
  `docker compose -f prod.yml stop backup-scheduler`
- **THEN** the `backup-scheduler` container exits and the `web` and
  `nginx` services continue running unaffected

#### Scenario: Scheduler does not start under a disabled-profile override

- **WHEN** the operator brings up the stack via an override file
  that omits `backup-scheduler` (e.g., a local debug override)
- **THEN** only `web` and `nginx` start; no scheduled backups run

### Requirement: Restart policy keeps the scheduler alive across host reboots

The system SHALL configure `backup-scheduler` with
`restart: unless-stopped` so the service resumes after a host
reboot without operator action. A manual `docker compose stop
backup-scheduler` SHALL be respected across subsequent reboots
(unlike `always`).

#### Scenario: Host reboot resumes the scheduler

- **WHEN** the host reboots while `backup-scheduler` was running
- **THEN** Docker restarts the container automatically after the
  daemon comes back up and the scheduler resumes its loop
