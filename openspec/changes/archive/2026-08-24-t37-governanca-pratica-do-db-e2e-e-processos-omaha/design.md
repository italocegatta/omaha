## Context

T37 is harness governance, not application behavior. The current canonical
runner already has six lanes, exact lane ports, fixed test-DB declarations,
per-lane temp roots, process groups, lifecycle receipts, and bounded TERM →
grace → KILL cleanup. The remaining operational gap is policy at boundaries:
pre-existing `data/test_e2e.db` is treated like protected residue even though
it is disposable, process identity is not sufficiently useful for diagnosing a
stale Omaha listener, and E2E fixture recreation is performed by an inline
unlink rather than one guarded helper.

T37 must preserve the PRD invariants: `data/test_e2e.db` and its E2E-only
short-TTL companion are ephemeral test targets; `data/portfolio.db` is never a
cleanup or recreate target; foreign resources are never adopted; taskipy
entrypoints, six lanes, fail-fast, coverage, skips, and the 300-second ceiling
remain unchanged. T36, F67, D06, T38, and D08 are outside this change.

## Code Map

| File | Symbols / exact region | Role in current flow |
|---|---|---|
| `scripts/run_full_suite.py` | `LANES`, `LANE_PORTS`, `LANE_DATABASES`, `CANONICAL_DATABASE_PATHS` | Declare canonical lanes, ports, and fixed DB targets used by preflight and reconciliation. |
| `scripts/run_full_suite.py` | `_canonical_resource_inventory`, `_preflight`, `_fixed_db_preflight_classification` | Build bounded canonical inventory, reject production `DATABASE_URL`, probe ports, classify fixed DB state, and fail before child launch when trust is absent. |
| `scripts/run_full_suite.py` | `_lane_metadata`, `_record_lifecycle`, `_persist_receipt`, `main` launch/monitor/finalization | Create run/lane ownership ledger, launch children, persist receipts, monitor fail-fast/deadline state, collect DB/temp/server evidence, and select final exit code. |
| `scripts/run_full_suite.py` | `_reconcile_fixed_db_targets`, `_reconcile_dynamic_db_targets`, `_reconcile_temp_root` | Remove exact current-run-owned resources after lane completion and preserve contradictory, foreign, or pre-existing state. |
| `scripts/run_full_suite.py` | `_owned_process_group`, `_stop`, `_reap` | Restrict signals to recorded current-run PGIDs, use bounded grace, escalate only owned survivors, and retain lifecycle races. |
| `tests/conftest.py` | module-load safe DB block; `_SAFE_DATABASE`; `_TEMP_ROOT_BOUNDARY`; `pytest_runtest_logreport`; `_omaha_test_env`; marker allow-lists | Bind ordinary pytest lanes to dynamic safe DB before discovery, emit temp/failure receipts, protect `SessionLocal`, and preserve explicit marker classification. |
| `tests/support/db.py` | `emit_db_receipt`, `emit_temp_root_receipt`, `prepare_safe_test_database`, `prepare_worker_database`, `verify_session_local_is_safe`, `set_asset_target_pcts_via_db` | Publish lane DB identity, provision temporary DBs, enforce production-DB refusal, and provide the E2E setup default. |
| `tests/support/server.py` | `_server_event`, `run_test_server` | Launch lane uvicorn, capture parent/child/PGID/port/log identity, require child-backed readiness, and invoke bounded teardown. |
| `tests/e2e/conftest.py` | `TEST_DB_PATH`, `TEST_DB_PATH_SHORT_TTL`, `live_url`, `live_url_short_ttl` | Current E2E callers delete fixed test DBs before spawning uvicorn; both use shared server lifecycle and receipts. This is adjacent caller wiring only, not product behavior. |
| `tests/scripts/test_t29_harness.py` | existing runner/server/DB receipt tests and helpers `_lane_entry`, `_bind_child`, `_patch_main_preflight` | Focused unit oracle for inventory classification, process-group cleanup, receipts, fixed/dynamic DB reconciliation, lifecycle races, and six-lane failure paths. |

## Current Relevant Flow

1. **Input:** `uv run task test` enters `run_full_suite.main`; runner reads
   policy and manifest, declares canonical ports/DBs, probes exact ports, and
   rejects a production `DATABASE_URL`. Each child receives `T29_RUN_ID`, a
   lane, an exact temp boundary, a timing path, and a lane DB receipt contract.
2. **Transformation:** `_lane_metadata` registers six placeholders before the
   first child. `launch` starts each lane in its own process group and records
   actual PID/PGID. Child conftest binds dynamic lanes to a temp SQLite file,
   emits DB/temp receipts, and server fixtures emit `T29_SERVER_EVENT` records.
   `monitor` applies fail-fast, parent interruption, and the bounded deadline.
3. **Output:** `_reap` terminates/reaps owned groups; finalization parses logs,
   timing, server, failure, DB, and temp receipts; reconciliation checks lane
   population and skips; `_persist_receipt` writes run JSON atomically; final
   exit code preserves lane, cleanup, receipt, reconciliation, or timeout
   failure.
4. **E2E fixture boundary:** `tests/e2e/conftest.py` currently unlinks fixed
   DB paths before `run_test_server`; uvicorn then runs migrations/seed against
   the same path. T37 replaces direct unlink with a helper that accepts only
   exact registered E2E DB paths and records recreate disposition before
   startup. The helper never treats old bytes as current-run-owned data.
5. **Server boundary:** `run_test_server` starts `uvicorn omaha.main:app` on a
   requested lane port, waits only while its spawned child is alive, yields the
   URL, then calls existing bounded shutdown. A stale/unrelated listener is
   preserved; startup or restart is untrusted unless child and exact lane
   identity agree.

Boundary states are explicit: `absent`, `owned-current-run`,
`ephemeral-preexisting`, `owned-cleaned`, `pre-existing`, `foreign`, and
`unknown`. `ephemeral-preexisting` is a disposition for an exact disposable
   E2E file, not an ownership class and never permission to signal a process.

## Goals / Non-Goals

**Goals:**

- Make canonical preflight bounded, actionable, and receipt-backed.
- Prove Omaha process identity from current-run evidence plus exact command,
  cwd, PID/PGID, lane, port, and DB mapping; do not infer ownership from a
  name or listener alone.
- Centralize safe E2E DB recreate and reject production/symlink/contradictory
  targets before mutation.
- Make graceful restart/teardown observable: TERM, bounded wait, owned-only
  KILL escalation, port result, exit code, and residue.
- Make stale-process recovery a diagnose-and-block/preserve path unless the
  stale resource is proven current-run-owned.

**Non-Goals:**

- No routes, models, migrations, seed content, UI, API, or product behavior.
- No broad process scan for cleanup, `pkill`, process-name kill, host-wide port
  freeing, foreign-resource adoption, or broad `/tmp` deletion.
- No recreation of `data/portfolio.db`; no production DB read/write is needed.
- No change to taskipy commands, six-lane population, fail-fast, coverage,
  skips, BDD/e2e/visual concurrency class, or duration policy.
- No reopening of T36, F67, D06, T38, or D08 decisions.

## Decisions

### 1. Exact allowlist is the only cleanup/recreate boundary

Use existing `LANE_DATABASES` and canonical lane ports as the source of
relevance. Add one explicit disposable classification for the E2E fixed DB
targets (`data/test_e2e.db` and its already-declared short-TTL companion).
Recreate requires: resolved path equals registered target, parent is the repo
`data/` directory, path is absent or a regular non-symlink file, and no active
current/foreign server identity is using the target. Recreate records
`adopted: false`, removes only exact old bytes, and lets uvicorn recreate schema
through its existing migration/seed startup.

Alternative rejected: treat every fixed test DB as deletable, use a filename
pattern, or delete `data/portfolio.db` by exclusion after a broad glob. That
would make a typo or foreign path destructive.

### 2. Ownership combines run/lane identity with process evidence

Receipts SHALL identify `run_id`, lane, parent PID, child PID, actual PGID,
exact command, repo cwd, lane port, DB path, and timestamps. A current-run
`Popen` result plus matching command/cwd/PGID is the positive ownership proof.
For a port collision, preflight may collect bounded exact-port diagnostic
identity (PID/command/cwd when the host exposes it); inability to collect it is
`unknown`, not permission to kill. A process named `uvicorn` or `omaha` alone
never becomes owned.

Alternative rejected: `pkill -f`, PID-only matching, port-only matching, or
adopting an already-running Omaha process. These fail under PID reuse,
worktree collisions, and concurrent owner sessions.

### 3. Graceful restart is owned-group lifecycle, not retry

Startup failure, context exit, and stale recovery use existing bounded
shutdown: signal `SIGTERM` to the recorded owned process/group, wait within the
existing grace bound, then send `SIGKILL` only to the same recorded owned group
if it survives. Emit start, readiness, graceful-stop, escalation, exit,
port-free, and residue events. If identity is absent, mismatched, foreign, or
the child vanished, preserve the resource and return non-zero/untrusted; do not
retry startup or browser navigation.

Alternative rejected: immediate KILL, retry-until-port-free, or terminating
whatever process currently listens on the port. Those hide causality and can
destroy another Omaha session.

### 4. Receipts are acceptance evidence

Extend existing JSON/run and `T29_SERVER_EVENT` structures additively. Required
new evidence: preflight disposition, process identity, DB recreate decision,
restart phase/signals, port result, `adopted` flag, stale/foreign diagnosis,
cleanup result, and exact error. Missing or contradictory evidence makes the
affected operation non-zero/untrusted. Existing atomic persistence and
serialization fallback remain in force.

Alternative rejected: human-readable logs only or a second full suite run to
repair missing telemetry. Receipts must explain a blocked run without changing
the canonical test gate.

### 5. Test changes stay in the existing T29 contract oracle

Add focused tests to `tests/scripts/test_t29_harness.py`, preserving its unit
marker and no-DB/no-live-server design. Use `tmp_path`, controlled child
objects, monkeypatch, synthetic inventories, and receipt JSON. Do not add
inline production data, persistent DB mutation, network access, skip, xfail,
retry, or test population changes.

## Change Map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `scripts/run_full_suite.py` — inventory/preflight symbols | Exact ports/DBs are classified, but fixed pre-existing E2E DB is not disposable and collision diagnostics are sparse | Classify exact E2E DB as `ephemeral-preexisting`, record bounded process identity evidence, and block/preserve foreign or unknown state | Make preflight practical without broad host actions. |
| `scripts/run_full_suite.py` — `_reconcile_fixed_db_targets` | Deletes fixed DB only when preflight said `absent`; pre-existing fixed E2E DB is preserved | Reconcile only exact registered E2E disposable targets through explicit recreate disposition; preserve all protected/foreign/contradictory paths | Permit safe recreate while retaining no-adoption and production protection. |
| `scripts/run_full_suite.py` — `_lane_metadata`, `_record_lifecycle`, `main` receipt stages | Receipts contain lifecycle and cleanup data but not explicit process identity/recreate/stale disposition | Add exact command/cwd, process identity verdict, recreate/adoption flag, restart phases, and stale/foreign diagnosis; missing evidence remains non-zero | Make operator handoff independently auditable. |
| `scripts/run_full_suite.py` — `_stop`, `_reap` | Owned PGID gating and TERM/grace/KILL exist | Preserve exact owned-group gating while recording graceful restart phases and treating identity/race uncertainty as untrusted | Prevent stale recovery from becoming foreign cleanup. |
| `tests/support/db.py` — DB receipt/bootstrap helpers | E2E caller performs direct `Path.unlink`; production guard exists only for dynamic `SessionLocal` | Add exact allowlisted ephemeral-E2E recreate helper with regular-file/symlink/production guards and structured disposition receipt | Centralize safe recreate semantics. |
| `tests/e2e/conftest.py` — `live_url`, `live_url_short_ttl` | Direct unlink before server spawn | Call shared exact-target recreate helper; keep same path/inode through each server fixture and current env/ports | Remove ad-hoc destructive path handling without product changes. |
| `tests/conftest.py` — temp/DB/failure receipt hooks | Dynamic safe DB and temp ownership receipts exist | Preserve import ordering and marker allowlists while including explicit ownership/recreate metadata where runner identity is present | Keep ordinary pytest lanes compatible with runner reconciliation. |
| `tests/support/server.py` — `_server_event`, `run_test_server` | Child liveness/readiness and teardown events exist; identity fields are partial | Record exact launch command/cwd/DB/PGID identity and graceful stop/escalation/port result; reject stale listener and preserve foreign state | Make restart and stale-process diagnosis actionable. |
| `tests/scripts/test_t29_harness.py` — runner/server/DB contract tests | Existing tests cover current receipts, fixed/dynamic DB cleanup, races, and stale listener readiness | Add positive and negative oracles for E2E recreate, portfolio refusal, identity mismatch, graceful escalation, complete receipt, foreign preservation, and idempotent no-op | Prove each new invariant without live DB/server or test masking. |
| `openspec/changes/.../specs/**/*.md` | Existing contracts do not distinguish disposable recreate from ownership or specify process identity/stale recovery | Add T37 delta requirements to `test-run-ownership-contract`, `dev-tasks`, `shared-test-support`, and `e2e-fixture-isolation` | Give Apply exact normative oracle. |

## Validation and Acceptance

Implementation is accepted only when focused tests prove: exact E2E paths can
be recreated and reported without adoption; `data/portfolio.db`, symlinks,
foreign listeners, unknown identity, and unrelated paths remain untouched;
owned server restart is TERM-first and escalates only after bounded grace;
stale/dead child does not yield a URL; all six runner lane receipts remain
complete; receipt and cleanup failures return non-zero; and existing T29
population/skip/reconciliation tests remain green.

Canonical `uv run task test` remains governed by `maintenance-suspended` in
config during this proposal's implementation/review. Focused command is
`uv run pytest tests/scripts/test_t29_harness.py -q`; implementation may also
run `uv run task test-unit` if required by the repository gate. No DB mutation
task, server start, browser, external network, seed, migration, or
`data/portfolio.db` operation is part of proposal validation.

## Risks / Trade-offs

- **[Disposable path mistaken for production]** → compare resolved exact path,
  parent, filename, file type, and explicit E2E lane allowlist; reject
  `portfolio.db`, symlink, directory, and unknown path before unlink.
- **[Foreign process looks like Omaha]** → require current-run Popen identity
  and exact command/cwd/PGID/port/DB mapping; diagnostic identity never grants
  cleanup authority.
- **[Stale listener blocks useful run]** → report exact listener evidence and
  request operator isolation; never kill or adopt it automatically.
- **[Receipt schema breaks existing parsers]** → additive optional fields,
  preserve existing keys/regex markers, and retain JSON-safe fallback.
- **[Graceful shutdown exceeds suite ceiling]** → reuse existing bounded grace
  and include all teardown in timing; no retry or ceiling relaxation.
- **[Direct E2E caller bypass remains]** → route both E2E fixture DB resets
  through one helper and add contract tests for every fixed E2E target.

## Migration Plan

1. Implement helper/runner/server changes only in mapped harness files; do not
   run persistent DB mutation commands.
2. Run focused T29 harness tests and inspect receipts/diff for exact scope.
3. Run applicable unit task under current canonical maintenance policy and
   record full-suite as `NOT RUN — maintenance-suspended` when required.
4. Rollback is reverting mapped harness/helper changes and delta specs; no
   migration, seed, production DB, or host cleanup rollback is needed.

## Open Questions

None. T37 scope fixes exact E2E disposable targets, preserves all other fixed
test DB behavior, and keeps production DB and foreign process ownership
protected.

## Implementation Decisions

- **Exact E2E recreate stays fixture-owned.** Preflight marks existing
  `test_e2e.db` targets `ephemeral-preexisting`, but only the shared DB helper
  removes them after exact path/type checks and emits `adopted: false`. This
  preserves distinction between disposable bytes and process ownership.
  Evidence: existing `tests/e2e/conftest.py` performed direct `Path.unlink()`
  before `run_test_server`; `run_full_suite.py` already declared both exact
  E2E paths in `LANE_DATABASES`.
- **Shared server group remains non-detached.** `run_test_server` preserves
  `start_new_session=False` and records child plus actual PGID; teardown
  lifecycle callbacks make TERM, bounded wait, escalation, exit, and port
  state observable without changing caller ports or host binding. Evidence:
  `tests/support/server.py` runs inside runner-owned lane processes and
  `shutdown_uvicorn` already gates group signaling against `parent_pgid`.
