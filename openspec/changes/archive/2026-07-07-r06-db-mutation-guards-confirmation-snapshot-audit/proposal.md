## Why

`data/portfolio.db` is the single source of truth for the household — no staging/prod split, no replication. On 2026-07-07 the DB was observed corrupted to 2 classes + 2 assets (RF+RV+Selic+ETF BOVA11 × R$ 6000 + R$ 4000) after routine UI use, with no recovery path and no record of which mutation caused the collapse. PRD §4.11 codifies the process contract: prod DB changes must be documented and formalized, and the platform needs a recovery path for any wipe — accidental or intentional.

The original 2026-07-07 R06 design proposed a threshold-based gate (`count > 10 && after < 5`) plus auto-snapshot plus audit plus admin recovery. The owner rejected the gate on 2026-07-07: the dev seed (Italo: 6 classes) sits below the threshold and a `POST /classes` with 2 form rows silently wiped 4 classes + cascaded 48 assets. A code-level gate is the wrong abstraction — the prevention is at the process level (OpenSpec review, tests, validation against established contracts). The R06 design is reduced to its reactive core: auto-snapshot + audit + admin restore. The owner can roll back any wipe via `POST /admin/restore/{snapshot_id}`.

## What Changes

- **Auto-snapshot** of `data/portfolio.db` before every destructive class/asset/import mutation via new `scripts/snapshot_db.py` (wraps `sqlite3.Connection.backup()` — same pattern as `scripts/backup.py`). Snapshots land in `data/snapshots/portfolio-<UTC>.db`; FIFO-pruned to retain 50. The snapshot row commits atomically with the destructive mutation.
- **Audit trail** in a new `db_mutations` table (timestamp, route, actor_user_id, profile_id, before_json, after_json, snapshot_path). Destructive routes insert one row after commit (best-effort — a failed audit insert does NOT roll back the mutation; the snapshot is the recovery path).
- **Admin recovery endpoints** in new `src/omaha/routes/admin.py`: `GET /admin/snapshots` lists available rollback points; `POST /admin/restore/{snapshot_id}` (gated by `X-Admin-Password`) copies the snapshot over `data/portfolio.db` and restarts uvicorn via `systemctl --user restart omaha-web.service` when present, otherwise logs a "restart needed" warning; `GET /admin/audit?since=<ts>&limit=<n>` paginates the mutation history.
- New Alembic migration `0018_db_mutation_guards.py` for `db_snapshots` + `db_mutations` tables (backfill zero).
- **No code-level gate.** Per the owner's directive (2026-07-07), prevention of accidental wipes is at the process level (PRD §4.11): every new DB feature must be reviewed against established contracts, tested in isolation, and traceable via the audit row. The reactive layer is the recovery path, not the prevention path.

## Why the reactive layer is enough

A code-level gate (threshold, `confirm` flag, diff-before-commit, type-to-confirm) attempts to prevent a class of bug. The class of bug — accidental destructive writes — has many attack surfaces (a typo in a form, a misclicked button, a copy-paste error, a stale UI). Code-level prevention is brittle: it must cover every surface, must not have false positives, must not have false negatives. The reactive layer — snapshot + audit + restore — is robust: every destructive op captures state and the operator can roll back any wipe, regardless of how it happened.

The prevention is at the process level (PRD §4.11): OpenSpec review ensures destructive features are documented; tests cover the established contracts (sum to 100, FK cascade behavior, audit row insertion); the audit trail means we can ALWAYS tell who did what and roll back. The smoke test pattern is read-only against prod (per the `refresh-for-test` skill update 2026-07-07) — destructive verification happens in the test suite, not against the live DB.

## Capabilities

### New Capabilities

- `db-mutation-safety`: pre-mutation snapshot trigger + audit row schema for destructive DB writes. The reactive layer for the PRD §4.11 contract.
- `admin-recovery`: snapshot listing + restore endpoint with `X-Admin-Password` gating + audit listing with `since`/`limit` pagination.

### Modified Capabilities

<!-- No existing spec captures destructive-route snapshot, audit-trail, or admin-restoration semantics. The new specs above are the contract. -->

## Impact

- **Code touched**:
  - `src/omaha/models.py` (new `DbSnapshot`, `DbMutation` SQLAlchemy models)
  - `alembic/versions/0018_db_mutation_guards.py` (new migration, 2 tables)
  - `src/omaha/mutation_guards.py` (new module: `snapshot_before_destructive`, `record_mutation_audit`, count helpers)
  - `src/omaha/routes/classes.py` (capture snapshot + write audit on `POST /classes`, `POST /classes/{id}/delete`, `DELETE /api/classes/{id}`)
  - `src/omaha/routes/assets.py` (capture snapshot + write audit on `POST /assets/{id}/delete`, `DELETE /api/assets/{id}`)
  - `src/omaha/routes/imports.py` (capture snapshot + write audit on `POST /api/import/commit`)
  - `src/omaha/routes/admin.py` (new — 3 endpoints)
  - `src/omaha/main.py` (lifespan snapshot-prune)
  - `scripts/snapshot_db.py` (new — `sqlite3.Connection.backup()` wrapper)
  - `tests/test_db_snapshot.py` (new, unit — roundtrip + prune)
  - `tests/test_db_mutations.py` (new, integration — audit + snapshot happy paths)
  - `tests/test_admin_recovery.py` (new, integration — admin endpoints)
  - `tests/conftest.py` (extend `SNAPSHOT_SOURCE` / `SNAPSHOT_DEST_DIR` env vars)
- **Critical area**: destructive class/asset/import routes — cap 1 `Applying`.
- **No regressions**: solver CVXPY, yfinance quote, Família aggregate, or read-only `require_profile_writable` gate are untouched.
- **Storage**: `data/snapshots/` is already gitignored (same rule as `backups/` and `data/`).
- **Effort**: 4-6h (snapshot infra + audit + admin + tests).
