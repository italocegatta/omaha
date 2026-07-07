## Context

`data/portfolio.db` is the only persistence layer for the household — SQLite locally, Postgres in prod, but always a single file/cluster. The seed (`scripts/seed_from_csv.py` + `data/seed/`) is the only sanctioned way to create classes/assets/positions per PRD §4.3, but the live UI exposes destructive routes that can mutate many rows in one POST: the CSV-import `commit` endpoint overwrites the active profile's class set in a single transaction; the classes edit-and-save flow rewrites targets in `routes/classes.py:189-219`; and the asset/class delete endpoints can shrink the table drastically in one click.

On 2026-07-07 the DB was observed in a state with only 2 classes + 2 assets (`RF`+`RV`+`Selic`+`ETF BOVA11` × R$ 6000 + R$ 4000) after routine UI use. The cause was not diagnosed (no audit trail existed) and there was no path to roll back to a pre-mutation snapshot. The household has no way to recover short of a `db-reset` from the CSV seed — which itself is destructive.

The platform already has a one-off snapshot primitive in `scripts/backup.py` (uses `sqlite3.Connection.backup()`), but it is operator-driven (the `task backup` invocation) and not wired into mutating routes. The Plataforma needs three coupled mechanisms so a single bad POST does not become permanent: a UI gate that warns the user when a mutation would shrink the dataset by a meaningful fraction; a transparent pre-mutation snapshot the platform writes automatically and retains for a configurable window; and an audit row recording who, what, when, and what the DB looked like before/after.

## Goals / Non-Goals

**Goals:**

- Confirmation gate fires before destructive operations on the class/asset/import routes when the mutation would meaningfully shrink the dataset (`count(assets) > 10 && count(target) < 5`); small legitimate edits are unaffected.
- Pre-mutation snapshot is captured automatically, by the route itself, before the destructive transaction commits. The snapshot is a copy of the live `data/portfolio.db` written via `sqlite3.Connection.backup()` to `data/snapshots/portfolio-<UTC-ISO>.db`.
- Audit row is written after the mutation commits, capturing the route, actor, profile, before/after counts (classes, assets, positions), and the snapshot path. Queryable via `GET /admin/audit?since=<ts>`.
- Recovery endpoint lets the operator roll back: `GET /admin/snapshots` lists available snapshots, `POST /admin/restore/{id}` restores one (gated by `ADMIN_PASSWORD`). Restore restarts uvicorn via `systemctl --user restart omaha-web.service` if present, else logs "restart needed".
- Snapshot retention is FIFO-pruned to the most recent 50; the prune runs in the FastAPI lifespan on every boot.

**Non-Goals:**

- Migration of `data/portfolio.db` between SQLite and Postgres (existing scope; out of band).
- Per-row audit (we capture route-level summary + before/after counts, not every row diff). Trade-off chosen because per-row diffs would be a few MB per mutation and the operator wants *recoverability*, not *replayability*.
- Real-time replication / streaming to a separate DB (out of platform complexity tier).
- Auto-restart when `systemd` is unavailable — the operator is responsible for `pkill` + `task serve`. Auto-restart via a different supervisor is a follow-up.
- Mutating the `Family` sentinel profile from destructive routes (the F07 read-only gate is untouched by this slice).

## Decisions

### D-R06.1 — Gate threshold derived from the dataset, not the route

The trigger condition is `count(assets_in_profile) > 10 AND count(target_after) < 5`. Rationale: small profiles (the F01/RF2 fixture) should never gate; massive profiles (Italo ~48 assets, Ana ~52 assets) should always gate when a mutation collapses them. The threshold is per-profile (the route receives `profile_id` from the session and queries `count(Asset)` for it). Alternatives considered: (a) gate every destructive operation (rejected — interrupts legitimate single-row edits); (b) gate only when `count > 50` (rejected — too high for Ana which sits at 52); (c) gate by `delta > 50%` (rejected — a profile with 12 assets losing 7 still looks catastrophic; absolute threshold of `< 5` captures the "catastrophic loss" pattern more reliably than ratio).

### D-R06.2 — Gate lives in the route, not in a global middleware

A FastAPI `Depends` on each destructive route is the seam. Rationale: (a) the gate needs the route's `count(target)` math which only the route knows; (b) a global middleware would have to peek into the request body to compute `target` and is brittle; (c) keeping the gate close to the mutation makes the safety guarantee auditable in the route's source. Trade-off: 5 routes get a new dependency each, but the dependency is the same `Depends(require_destructive_confirmation)` everywhere.

### D-R06.3 — Snapshot via `sqlite3.Connection.backup()`, not `cp`

`sqlite3.Connection.backup(target_conn)` is the documented way to take a hot copy of an open SQLite database (it uses SQLite's online backup API and is safe even with writers). `cp` works when uvicorn is stopped but would corrupt mid-write if the platform is running. The new `scripts/snapshot_db.py` wraps the connection call into a CLI/importable function `snapshot_live_db(src, dest_dir) -> Path` that the route invokes before the destructive transaction.

### D-R06.4 — Snapshots land in `data/snapshots/`, separate from `backups/`

`backups/` is the operator-driven path (`task backup` / `scripts/backup.py`) for periodic full copies. `data/snapshots/` is auto-managed by the platform and contains pre-mutation rollback points. Keeping them separate prevents a 5 GB `backups/` directory from being polluted with platform-managed snapshots, and keeps the operator's manual restore path (`task restore` from `backups/`) orthogonal to the platform's auto-recovery path.

### D-R06.5 — FIFO retention of 50, prune in lifespan

50 snapshots is roughly one month of destructive operations at the current rate (the observed rate is ~1 per week). The prune runs once per app boot in the FastAPI lifespan, not on a timer. Trade-off: snapshots survive only as long as the process is alive to re-prune; an idle server could grow the directory beyond 50. Accepted because prune-on-boot is enough for the dev workflow and the operator can run `rm data/snapshots/portfolio-*.db` ad-hoc if the directory grows.

### D-R06.6 — `ADMIN_PASSWORD` env var gates the recovery endpoints, not a User role

The platform has no User-role table; both Italo and Ana share the same family password (PRD §1.2). Forcing an env-var gate keeps the recovery path decoupled from the session cookie — the operator authenticates with the env password even after the user DB is corrupted, and the gate is a one-time secret rotated via deployment. The endpoint is `POST /admin/restore/{id}` with `X-Admin-Password` header (or `?admin_password=...` query for CLI use).

### D-R06.7 — Restore restarts uvicorn only via `systemctl --user`

If `omaha-web.service` is registered with the user-level systemd manager, the restore endpoint shells out `systemctl --user restart omaha-web.service` and waits for it to come back. If not, the endpoint logs a structured warning and returns `202 Accepted` with `{"restart_needed": true}`; the operator is responsible for `pkill -f 'uvicorn omaha.main' && task serve`. Trade-off: silent fail-vs-succeed on the restart path would be worse than an explicit "restart needed" response the operator can act on.

### D-R06.8 — Audit row is best-effort, not transactional with the mutation

The audit row is inserted in a *separate* transaction *after* the mutation commits. Rationale: a transactionally-coupled audit row would force the audit write to be inside the same session as the destructive mutation, which would mean a failed audit would roll back the user-visible change. We choose the opposite: the user-visible change is the source of truth, the audit row is a courtesy. If the audit insert fails (e.g., `db_mutations` table is missing because the migration was not run), the mutation still succeeded; the operator sees a 500 in the log and can diagnose.

### D-R06.9 — `data/snapshots/` is gitignored, follows the `backups/` rule

`.gitignore` already excludes `backups/`, `data/`, and `data/portfolio.db`. `data/snapshots/` is created on demand by `scripts/snapshot_db.py`; the directory inherits the `data/` exclusion. No `.gitignore` change needed.

## Risks / Trade-offs

- **Snapshot write I/O on the destructive path** → Each destructive POST now performs an extra `sqlite3.Connection.backup()` (typically 1-10 MB read from the source DB and write to `data/snapshots/`). On a 50 MB DB this is ~50-200 ms on a SATA SSD. The latency is bounded by the source DB size and is acceptable for the dev workflow. If the operator ever migrates to a 1 GB DB, the gate should be moved to async background write — but the current 50 MB scale is fine.
- **50-snapshot FIFO can lose older corruption signals** → If the operator runs 51 destructive operations in one day, the oldest snapshot (potentially a "good" state) is pruned. The audit table retains the metadata forever, but the actual DB file is gone. Accepted because 50 is well above the dev cadence and the audit row links to the now-missing path. Follow-up if the cadence climbs: bump retention via `SNAPSHOT_RETENTION` env.
- **`data/portfolio.db` is locked during the `backup()` call** → `sqlite3.Connection.backup()` is documented to work with concurrent readers/writers via SQLite's online backup API. Verified by the `scripts/backup.py` precedent which has been used in production since slice R01. The risk is theoretical: if a writer takes an exclusive lock (which would require explicit `BEGIN EXCLUSIVE`), the backup would block until that transaction releases. No code in the destructive routes uses `BEGIN EXCLUSIVE`.
- **Gate threshold is a magic number** → The `count(assets) > 10 && count(target) < 5` rule is captured in the spec (`db-mutation-safety`) so the number is documented and the spec is the place to change it. No code constant duplicates the rule.
- **Restore endpoint is irreversible** → `POST /admin/restore/{id}` overwrites `data/portfolio.db` with the snapshot and restarts uvicorn. The current state is *not* snapshotted before the restore (the pre-restore state is, by definition, the state the operator just declared bad). A "restore-of-restore" recovery would require the audit trail + a pre-restore snapshot, which is out of scope. The spec documents this trade-off so the operator can plan.
- **Failed snapshot blocks the destructive POST** → If `snapshot_db()` raises (e.g., disk full, `data/snapshots/` not writable), the destructive POST fails with 500. This is intentional: a snapshot failure means the rollback path is broken, and letting the mutation proceed without a rollback would defeat the whole point. The 500 surfaces a structured log entry the operator can diagnose.

## Migration Plan

1. **Apply order**: migration first (`0018_db_mutation_guards.py`), then model registrations (`models.py`), then `scripts/snapshot_db.py` (no model dep), then the route-level `Depends` wiring, then the admin endpoints, then the UI modal.
2. **Backfill**: zero — both new tables are empty on migration. The `Family` sentinel row is unaffected.
3. **Rollback**: downgrade the migration (drops `db_snapshots` + `db_mutations`) + revert the route changes. Existing `data/snapshots/*.db` files become orphans and can be removed with `rm data/snapshots/portfolio-*.db`. The operator's `backups/` directory is untouched.
4. **No CI impact** — the new tests run under the existing `task test-integration` suite (the routes still work as before when no gate fires).

## Open Questions

- **Snapshot naming**: should the filename include the route name (e.g., `portfolio-2026-07-07T14-23-00Z-post-classes-DELETE.db`)? Current plan: keep the name `portfolio-<UTC>.db` for simplicity and put the route in the audit row. If the operator wants per-route names, change in a follow-up.
- **Restore → snapshot the current bad state first?** Currently the restore endpoint overwrites the DB immediately. A safer flow is: snapshot the current state to `data/snapshots/pre-restore-<UTC>.db`, then restore, then log the pre-restore path in the audit row. Cost: extra I/O + extra audit row. **Owner decision needed before apply** (proposal currently chooses "do not snapshot" for simplicity).
- **`X-Admin-Password` header vs. Basic auth vs. session cookie?** Proposal currently uses `X-Admin-Password` because it works for both browser and CLI (`curl -H "X-Admin-Password: ..."`). A session cookie would require the operator to log in to the admin UI, which means `data/portfolio.db` is required to look up the User row — defeating the purpose when the DB is corrupted. **Owner decision pending.**
