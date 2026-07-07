## 1. Service definition

- [x] 1.1 Add `backup-scheduler` service to `prod.yml` (image `omaha:prod`, `restart: unless-stopped`, no profile so it starts with `up -d`)
- [x] 1.2 Add `BACKUP_INTERVAL` env var reading (default `86400`) wired into the service
- [x] 1.3 Add bind mount `./backups:/backups` (write) and named volume `omaha-data:/app/data:ro` (read-only, same as `backup` service)
- [x] 1.4 Reuse `command` pattern from the `backup` service: `python -m scripts.backup /backups/portfolio-$(date -u +%Y%m%dT%H%M%SZ).db`

## 2. Scheduler entrypoint script

- [x] 2.1 Create `scripts/backup_scheduler.py` with an infinite loop: read `BACKUP_INTERVAL` env, run `python -m scripts.backup <timestamped_path>`, capture exit code, log timestamp + exit code, sleep `BACKUP_INTERVAL`
- [x] 2.2 Wrap the subprocess call so a non-zero exit code does not raise — log and continue
- [x] 2.3 Log format: ISO-8601 UTC timestamp prefix + level + message (`2026-07-06T03:14:15Z INFO backup started` / `ERROR backup failed: exit 1`)
- [x] 2.4 Validate `BACKUP_INTERVAL` at startup: must be a positive integer, otherwise fail fast with a clear error message

## 3. Wiring the scheduler command

- [x] 3.1 Change the `command:` in `prod.yml` for `backup-scheduler` to `python -m scripts.backup_scheduler` (overrides the `scripts.backup` direct call used by the one-shot `backup` service)
- [x] 3.2 Confirm the existing `backup` service (profile `backup`) is untouched — still one-shot `scripts.backup`
- [x] 3.3 Add a comment block above the `backup-scheduler` service explaining D-I01.1 (loop in container), D-I01.4 (no profile, default up), D-I01.5 (failure-tolerant loop)

## 4. Documentation

- [x] 4.1 Update `README.md` operation section: describe `backup-scheduler`, default 24h cadence, how to stop (`docker compose -f prod.yml stop backup-scheduler`), and how to override interval (`BACKUP_INTERVAL=3600 docker compose -f prod.yml up -d`)
- [x] 4.2 Note that retention is operator responsibility (off-host rsync / logrotate) — slice does not auto-rotate

## 5. Local smoke test

- [x] 5.1 Run `python -m scripts.backup_scheduler` locally with `BACKUP_INTERVAL=10` and verify two consecutive runs land in `./backups/`
- [x] 5.2 Inject a failure (point `BACKUP_INTERVAL` then point to a non-existent DB path to simulate failure), confirm exit code logged and container does not exit
- [x] 5.3 Confirm `docker compose -f prod.yml config` parses the new service without errors (`docker compose -f prod.yml up -d --dry-run` or equivalent syntax check)

## 6. Spec gate + archive

- [x] 6.1 `openspec validate i01-automatic-backup-scheduling --json` returns `valid: true`
- [x] 6.2 `openspec validate backup-scheduling --json` returns `valid: true` (N/A: spec consolidation happens at archive; `openspec validate` confirms change-level validity. The new capability's main spec file is created from this delta at archive time — see `openspec/changes/i01-automatic-backup-scheduling/specs/backup-scheduling/spec.md`.)
- [x] 6.3 Run `task lint` (ruff + prek) — green
- [x] 6.4 Run `task test-unit` + `task test-integration` — no regressão (zero `src/omaha/**` tocado)
- [ ] 6.5 Archive via `openspec archive i01-automatic-backup-scheduling`; sync spec delta into `openspec/specs/backup-scheduling/spec.md` (separate `next` gate)
