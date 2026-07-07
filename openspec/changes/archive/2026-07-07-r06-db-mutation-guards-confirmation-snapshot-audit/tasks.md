## 1. Migration + models

- [x] 1.1 Create `alembic/versions/0018_db_mutation_guards.py` — adds `db_snapshots` (`id` PK, `path` String, `size_bytes` Integer, `created_at` DateTime UTC) and `db_mutations` (`id` PK, `created_at`, `route`, `actor_user_id` nullable FK, `profile_id` nullable FK, `before_json` JSON, `after_json` JSON, `snapshot_path` nullable String). `down_revision = "0017_is_family_sentinel"`.
- [x] 1.2 Extend `src/omaha/models.py` with `DbSnapshot` and `DbMutation` SQLAlchemy 2.0 mapped classes (string-typed, `Mapped[...]` style matching the surrounding `Profile` / `Asset` declarations).
- [x] 1.3 Run `task db-migrate` against the dev DB and confirm both tables exist (`alembic current` reports `0018_db_mutation_guards`).

## 2. Snapshot infra

- [x] 2.1 Create `scripts/snapshot_db.py` exposing `snapshot_live_db(src: Path, dest_dir: Path) -> Path`. Use `sqlite3.connect(str(src))` + `src_conn.backup(dest_conn)` pattern, mirroring `scripts/backup.py`. Ensure `dest_dir` exists (`mkdir(parents=True, exist_ok=True)`) before opening the dest connection. Return the absolute path of the written file.
- [x] 2.2 Add `prune_snapshots(dest_dir: Path, retention: int = 50) -> int` to the same file. Sort by filename (UTC ISO-8601 is lexicographically sortable), delete oldest beyond `retention`, return the count deleted.
- [x] 2.3 Add a `__main__` block that snapshots `data/portfolio.db` to `data/snapshots/` and prunes — for operator one-shot use.
- [x] 2.4 Wire the prune into the FastAPI lifespan in `src/omaha/main.py`: call `prune_snapshots(Path("data/snapshots"))` once on startup. (Snapshot capture itself lives in the route — see §3.)

## 3. Route-level gate + audit wiring

- [x] 3.1 Add `require_destructive_confirmation` dependency in `src/omaha/auth.py` (or a new `src/omaha/routes/_guards.py` if cleaner). Signature: `Depends`-able function returning the count check result; raises HTTP 400 `{"reason": "confirmation_required", "before": N, "after": M}` when the threshold is met and the request lacks `confirm=true`.
- [x] 3.2 Wire the gate into `POST /classes` (the snapshot-replace path at `src/omaha/routes/classes.py:189-219`): compute `count(AssetClass where profile_id == active)` + the post-mutation count, apply the threshold, and require `confirm=true` from the form.
- [x] 3.3 Wire the gate into `POST /classes/{id}/delete` and `DELETE /api/classes/{id}`.
- [x] 3.4 Wire the gate into `POST /assets/{id}/delete` and `DELETE /api/assets/{id}` in `src/omaha/routes/assets.py`.
- [x] 3.5 Wire the gate into `POST /api/import/commit` in `src/omaha/routes/imports.py` with the custom message "X ativos no DB / Y no CSV — substituir?".
- [x] 3.6 In each gated route, call `snapshot_live_db()` immediately before the destructive `session.commit()`; abort with HTTP 500 if the snapshot raises. Store the snapshot path on the request `state` for the audit row.
- [x] 3.7 After the destructive commit, write a `DbMutation` row with `route`, `actor_user_id`, `profile_id`, `before_json`, `after_json`, and the `snapshot_path` from §3.6. Best-effort (try/except + structured WARN log on failure).

## 4. Admin recovery endpoints

- [x] 4.1 Create `src/omaha/routes/admin.py` with `require_admin` dependency that checks `X-Admin-Password` against `os.environ["ADMIN_PASSWORD"]` (raises HTTP 401 on mismatch).
- [x] 4.2 Implement `GET /admin/snapshots` returning the JSON array described in the `admin-recovery` spec (sorted by `created_at` desc, joined with `db_mutations.mutation_id`).
- [x] 4.3 Implement `POST /admin/restore/{snapshot_id}`: validates the snapshot exists, copies it over `data/portfolio.db` via `shutil.copy2`, attempts `systemctl --user restart omaha-web.service` via `subprocess.run` with a 10-second timeout, polls the `/healthz` endpoint for readiness, returns the appropriate 202 response.
- [x] 4.4 Implement `GET /admin/audit?since=<ts>&limit=<n>` with the spec's `since` filter and `limit` clamping (default 100, max 500).
- [x] 4.5 Mount the router in `src/omaha/main.py` with `app.include_router(admin_router)`.

## 5. Frontend confirmation modal

- [x] 5.1 Extend `src/omaha/templates/_patrimonio_actions.html` with a confirmation modal (`.confirm-modal`, `.confirm-modal__body`, `.confirm-modal__actions`) that reuses the F10 `.input-prefix-wrap` styling tokens.
- [x] 5.2 Add Alpine data + handlers so the modal is shown when the destructive response is `400 confirmation_required` and resubmits the form with `confirm=true` on confirm.
- [x] 5.3 Add the modal's CSS in `src/omaha/static/app.css` (`.confirm-modal`, `.confirm-modal__body`, `.confirm-modal__actions`) — base, reusable across the 3 destructive surfaces.
- [x] 5.4 Surface a small data-testid (`confirm-modal`, `confirm-modal-confirm`, `confirm-modal-cancel`) so the e2e selectors can pin the modal.

## 6. Tests

- [x] 6.1 `tests/test_db_snapshot.py` (unit) — roundtrip `snapshot_live_db` + restore via `shutil.copy2`; `prune_snapshots` deletes oldest beyond retention; idempotent prune when under retention. Register in `tests/conftest.py::_UNIT_FILES`.
- [x] 6.2 `tests/test_db_mutations.py` (integration) — gate fires when `count(assets) > 10 && count(after) < 5`; gate silent when small profile; backend 400 on unconfirmed; audit row written after confirmed commit. Register in `tests/conftest.py::_INTEGRATION_PREFIXES` per PRD §4.6.
- [x] 6.3 `tests/test_admin_recovery.py` (integration) — `GET /admin/snapshots` lists, `POST /admin/restore/{id}` happy path with a stubbed systemd, `GET /admin/audit` paginates + clamps limit. Register in `tests/conftest.py::_INTEGRATION_PREFIXES`.

## 7. Spec verification + delivery

- [x] 7.1 Run `openspec validate r06-db-mutation-guards-confirmation-snapshot-audit --json` — expect `valid: true`.
- [x] 7.2 Run `task lint` — ruff + prek both green.
- [x] 7.3 Run `task test-unit` — 271 (pre-R06 baseline) + new snapshot test cases.
- [x] 7.4 Run `task test-integration` — 369 (pre-R06 baseline) + new mutation/admin tests.
- [x] 7.5 Run `task test-bdd` — 51 (T05 baseline) + any new BDD scenarios (likely none; modal is e2e territory).
- [x] 7.6 Run `task db-reset` + `bash scripts/print_lan_url.sh` — confirm Italo/Ana/Família render, and the destructive UI surfaces still work (a single class delete should NOT trigger the gate on the F01 fixture).
- [x] 7.7 Hand off to `refresh-for-test` skill (PRD §4.9) and emit the delivery receipt.
