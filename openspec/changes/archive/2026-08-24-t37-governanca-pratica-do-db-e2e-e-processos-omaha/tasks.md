## Test Strategy and Evidence Contract

Implementation SHALL use temporary paths, controlled child doubles, monkeypatch,
and synthetic receipts only. No task may run persistent-DB migration, seed,
reset, clear, restore, live server, browser, external network, or write
`data/portfolio.db`. `uv run task test-unit` may exercise existing conftest
bootstrap against its dynamic temporary DB; it is not permission to touch a
persistent database.
Existing `tests/scripts/test_t29_harness.py` remains unit-scoped and is the
focused test file. Every implementation task uses `uv run task test-unit` as
focused taskipy command; the test name/scenario and independent oracle below
must also be recorded in handoff evidence. Canonical `uv run task test` is not
run by this proposal; implementation/review follows
`maintenance-suspended` policy from `openspec/config.yaml`.

Acceptance evidence must include: exact changed-file allowlist, `git diff
--check`, focused task result, receipt JSON assertions, and proof that foreign,
contradictory, and production paths were preserved. No `skip`, `xfail`, retry,
placeholder, lane removal, or coverage reduction is accepted.

## 1. Canonical preflight and ownership

- [x] 1.1 **Target:** `scripts/run_full_suite.py` — `LANE_DATABASES`, `CANONICAL_DATABASE_PATHS`, `_canonical_resource_inventory`, `_preflight`, `_fixed_db_preflight_classification`. **Change:** add exact E2E disposable classification and bounded process identity observations for declared canonical ports/DBs; classify `absent`, `owned-current-run`, `ephemeral-preexisting`, `pre-existing`, `foreign`, and `unknown`, with `adopted: false` for recreate disposition. **Preserve:** six lanes, canonical ports, production `DATABASE_URL` refusal, no broad host scan, and no foreign cleanup. **Acceptance:** clean inventory permits launch; foreign/unknown/contradictory canonical state blocks before child launch with exact evidence. **Test file/scenarios:** `tests/scripts/test_t29_harness.py` — clean inventory, canonical port collision, irrelevant host observation, and protected DB scenarios. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** inspect inventory JSON for only declared resources, `adopted is False`, no `data/portfolio.db` cleanup target, and `git diff --check`.

- [x] 1.2 **Target:** `scripts/run_full_suite.py` — `_lane_metadata`, `_record_lifecycle`, `_persist_receipt`, `main` receipt stages. **Change:** record exact command, repo cwd, parent/child PID, PGID, lane port, DB mapping, preflight/recreate disposition, restart phases/signals, stale diagnosis, `adopted` flag, timestamps, residue, and receipt errors while retaining atomic write/fallback behavior. **Preserve:** six placeholders before launch, current T29 markers/regex keys, first failure, fail-fast, deadline, and non-zero-on-receipt-failure semantics. **Acceptance:** preflight block, partial launch, finalization error, timeout, and serialization failure each retain complete six-lane evidence and causal exit. **Test file/scenarios:** `tests/scripts/test_t29_harness.py` — `test_runner_partial_launch_emits_all_lane_receipts`, `test_runner_timeout_receipt_includes_cleanup`, `test_runner_serialization_failure_falls_back_without_losing_telemetry`, plus new receipt-field scenarios. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** load emitted run JSON and assert all six lane names, required identity fields, `receipt_errors` on injected failure, and non-zero final code.

- [x] 1.3 **Target:** `scripts/run_full_suite.py` — `_owned_process_group`, `_stop`, `_reap`. **Change:** retain current-run PGID gate and make graceful stop/reap phases explicit; TERM first, bounded grace, KILL only same owned PGID, lifecycle race recorded as untrusted while original lane/fail-fast/deadline result survives. **Preserve:** no process-name/pattern kill, no PID-only adoption, no foreign signal, no retry, and existing `GRACE_SECONDS`/300-second timing. **Acceptance:** owned survivor escalates once after grace; foreign/mismatched child receives no signal; vanished child preserves causal failure. **Test file/scenarios:** `tests/scripts/test_t29_harness.py` — `test_runner_signals_recorded_pgid_not_child_pid`, `test_runner_reaps_owned_survivor`, `test_runner_preserves_foreign_resource`, `test_runner_vanished_child_during_signal`. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** captured `killpg` calls contain only recorded owned PGID; receipt classification is `foreign`/`untrusted` for mismatch and never `clean`.

## 2. Safe E2E database recreation

- [x] 2.1 **Target:** `tests/support/db.py` — new exact-target E2E recreation helper adjacent to `emit_db_receipt` and `set_asset_target_pcts_via_db`. **Change:** centralize recreate for registered E2E fixed DB paths, requiring resolved repo `data/` path, regular non-symlink file/absence, explicit run/lane disposition, and `adopted: false`; reject `data/portfolio.db`, directories, symlinks, outside paths, and active foreign ownership evidence. **Preserve:** dynamic safe DB bootstrap, import-before-pytest ordering, `verify_session_local_is_safe`, existing DB/temp receipt markers, and current seed/migration ownership. **Acceptance:** exact pre-existing E2E file becomes `ephemeral-recreated`; absent file is idempotent no-op; protected/contradictory targets remain byte-identical and fail non-zero. **Test file/scenarios:** `tests/scripts/test_t29_harness.py` — new helper tests for recreate, absent no-op, portfolio refusal, symlink/directory refusal, and foreign active-server refusal. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** use only `tmp_path`; assert inode/path disposition and `adopted is False`; assert protected target bytes unchanged.

- [x] 2.2 **Target:** `tests/e2e/conftest.py` — `TEST_DB_PATH`, `TEST_DB_PATH_SHORT_TTL`, `live_url`, `live_url_short_ttl`. **Change:** replace direct `Path.unlink()` calls with shared exact-target helper before `run_test_server`; keep each fixture's path, port, env, server scope, and same-file startup contract. **Preserve:** 8765/8767 separation, migration/seed through uvicorn startup, per-test cleanup, and no access to `data/portfolio.db`. **Acceptance:** both E2E fixtures recreate only their declared DB, pass same path to server, and emit lane-bound receipt; foreign listener or contradictory DB prevents URL yield. **Test file/scenarios:** `tests/scripts/test_t29_harness.py` — helper contract plus existing stale-listener and E2E DB receipt scenarios. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** static diff confirms no bare `unlink` remains in these fixture startup paths and no `portfolio.db` target is introduced; `git diff --check` passes.

## 3. Omaha server identity and graceful lifecycle

- [x] 3.1 **Target:** `tests/support/server.py` — `_server_event`, `run_test_server`. **Change:** record exact launch command, repo cwd, DB path, parent/child PID, actual PGID, lane, port, and identity verdict; require spawned-child liveness plus exact lane readiness; emit teardown-start, TERM/wait, owned-only escalation, exit, port-free, stale/foreign, and residue events. **Preserve:** current `127.0.0.1` test host, lane ports, `compose_server_env`, log capture, `start_new_session=False`, existing `shutdown_uvicorn` bounded behavior, and no browser retry. **Acceptance:** dead child/stale listener raises with actionable identity/log evidence; owned server teardown is graceful and bounded; foreign listener remains untouched. **Test file/scenarios:** `tests/scripts/test_t29_harness.py` — `test_t33_server_does_not_accept_stale_listener_for_dead_child`, `test_server_ready_receipt_binds_spawned_child_and_teardown`, `test_visual_readiness_dead_child_includes_flushed_log_tail`, plus new identity/escalation assertions. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** parse `T29_SERVER_EVENT` lines and assert one run/lane identity, matching child/PGID/port/DB, ordered TERM before optional KILL, and final port result.

- [x] 3.2 **Target:** `tests/conftest.py` — module-load safe DB block, `_TEMP_ROOT_BOUNDARY`, `pytest_runtest_logreport`, `_omaha_test_env`, marker allow-lists. **Change:** thread runner identity/recreate metadata only where environment provides it and keep failure/temp/DB receipts compatible with new runner fields. **Preserve:** critical import ordering, dynamic safe DB binding, production guard, explicit `_INTEGRATION_PREFIXES`/`_UNIT_FILES`, BDD marker behavior, and no marker heuristic changes. **Acceptance:** ordinary pytest collection still binds safe temp DB before discovery; runner lanes emit exact temp/DB/failure receipts; no new test path classification changes. **Test file/scenarios:** `tests/scripts/test_t29_harness.py` — DB receipt lane matrix, temp-root identity/reconciliation, failure receipt, and marker-independent collection scenarios. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** static inspect of allowlist intersection and import order; assert `DATABASE_URL` never resolves to `data/portfolio.db` in helper-level tests.

## 4. Focused contract coverage and delivery gate

- [x] 4.1 **Target:** `tests/scripts/test_t29_harness.py` — existing controlled child/inventory helpers and new T37 test cases. **Change:** add positive and negative tests for exact E2E recreate, protected production DB, symlink/foreign preservation, process command/cwd/PGID mismatch, graceful TERM→bounded KILL, stale recovery, complete receipts, idempotent cleanup, and original failure preservation. **Preserve:** `pytestmark = pytest.mark.unit`, no live SQLite/uvicorn/browser/network, existing T29 tests, and no masked-pass constructs. **Acceptance:** every T37 delta scenario has a deterministic oracle and all existing tests remain green. **Test file/scenarios:** this file, covering all scenarios named in T37 delta specs. **Focused taskipy command:** `uv run task test-unit`. **Independent oracle:** `uv run pytest tests/scripts/test_t29_harness.py -q` may be used only as a diagnostic equivalent; final evidence must report canonical taskipy result, changed-file allowlist, and `git diff --check`.

- [x] 4.2 **Target:** exact T37 change folder and repository scope. **Change:** run local OpenSpec validation and final audit; do not edit roadmap, stable specs, T36, F67, D06, T38, D08, application code, production DB, seed data, or unrelated tests. **Preserve:** proposal/design/spec/task consistency and current maintenance-suspended gate. **Acceptance:** exact folder contains proposal/design/tasks and four delta specs; `openspec validate t37-governanca-pratica-do-db-e2e-e-processos-omaha --type change --strict` passes; no forbidden path changed; no DB/server/browser command was used for validation. **Test file/scenarios:** artifact sanity only; review every T37 delta requirement against its design/task oracle. **Focused taskipy command:** `uv run task test-unit` is not required for artifact-only validation; if implementation is present, rerun it before handoff. **Independent oracle:** `git status --short --untracked-files=all`, `git diff --check`, exact path allowlist, and OpenSpec strict validation output.

## Acceptance Evidence Checklist

- [x] All focused taskipy results and test node IDs recorded in this file or
  implementation handoff.
- [x] Run/server receipts show identity, ownership, recreate, restart, cleanup,
  residue, and final status fields; missing evidence is non-zero.
- [x] `data/test_e2e.db` behavior is exact disposable recreate only;
  `data/portfolio.db` remains protected and untouched.
- [x] No foreign resource is adopted, signaled, freed, deleted, or allowlisted.
- [x] No application behavior, T36/F67/D06/T38/D08 scope, lane, coverage,
  skip, retry, or duration contract changes.

## Execution Evidence

### Initial implementation pass

- Completed tasks: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2.
- Changed files/symbols: `scripts/run_full_suite.py` inventory, preflight,
  lane metadata, lifecycle, reconciliation, and owned-group cleanup;
  `tests/support/db.py` exact E2E recreation helper;
  `tests/e2e/conftest.py` E2E fixture setup;
  `tests/support/server.py` server identity/readiness/teardown events;
  `tests/support/browser.py` bounded teardown callbacks;
  `tests/conftest.py` runner identity receipt fields;
  `tests/scripts/test_t29_harness.py` T37 contract coverage;
  `openspec/changes/t37-governanca-pratica-do-db-e2e-e-processos-omaha/design.md`
  implementation decisions and this task dossier.
- Focused validation: `uv run task test-unit` -> `596 passed, 2 skipped,
  551 deselected, 3 warnings in 18.77s`; exit 0.
- Diagnostic history: remediation of earlier `t37-apply-20260824-02` five
  runner receipt failures completed before successful `-03`, `-04`, `-05`, and
  `-06` runs. No test was weakened, skipped, xfailed, retried, or deleted.
- Artifact validation: `openspec validate
  t37-governanca-pratica-do-db-e2e-e-processos-omaha --type change --strict`
  -> valid; `git diff --check` -> clean.
- Acceptance evidence: six lane receipt preservation remains covered;
  `data/portfolio.db` is excluded by helper/runner guards; exact E2E DB
  recreation records `adopted: false`; foreign and unknown resources remain
  preserved; TERM-first owned-PGID cleanup and bounded escalation are covered
  by focused tests; canonical full suite is not run under
  `maintenance-suspended` policy.

## Ownership Ledger Receipts

### Apply focused validation run `t37-apply-20260824-01`

Owner: `t37-governanca-pratica-do-db-e2e-e-processos-omaha/apply`
Agent identity: `openai/gpt-5.6-luna` apply
Run registration timestamp: 2026-08-24T00:00:00Z (registration before launch;
actual command start/end timestamps appended after execution).

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | wrapper PID 189008 | current T37 run | `tool_036851de8001tDrh7gAhdMoSa8` pre-launch registration | 2026-08-24T22:24:30-03:00 | 2026-08-24T22:24:52-03:00 | exited | owned-cleaned | task-only run; PID absent after receipt | idempotent no-op: already absent |
| process group | PGID 189008 | current T37 run | same pre-launch registration | 2026-08-24T22:24:30-03:00 | 2026-08-24T22:24:52-03:00 | exited | owned-cleaned | no live server/browser child | idempotent no-op: already absent |
| test DB resource | dynamic conftest temporary DB, exact path not emitted | current T37 run | pytest conftest safe-DB bootstrap | 2026-08-24T22:24:30-03:00 | 2026-08-24T22:24:52-03:00 | absent | owned-cleaned | no persistent DB target; receipt ended at coverage write | no-op: exact resource absent; no rediscovery |
| temporary path | task-scoped pytest temp resources, exact paths not emitted | current T37 run | task-scoped temporary resource registration | 2026-08-24T22:24:30-03:00 | 2026-08-24T22:24:52-03:00 | absent | owned-cleaned | no host-wide temp discovery | no-op: exact resources absent; no rediscovery |

No resource may be cleaned unless exact identity matches this ledger. Foreign,
unknown, pre-existing, contradictory, and incomplete observations remain
untouched and block affected handoff.

### Apply focused validation run `t37-apply-20260824-02`

Owner: `t37-governanca-pratica-do-db-e2e-e-processos-omaha/apply`
Agent identity: `openai/gpt-5.6-luna` apply
Run registration: recorded before launching `uv run task test-unit`.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | wrapper PID 189526 | current T37 run | `tool_036874475001Rsf4URuHl70AdI` pre-launch registration | 2026-08-24T22:26:52-03:00 | 2026-08-24T22:27:13-03:00 | exited | owned-cleaned | five runner receipt assertions failed; no live server/browser | idempotent no-op: already absent |
| process group | PGID 189526 | current T37 run | same pre-launch registration | 2026-08-24T22:26:52-03:00 | 2026-08-24T22:27:13-03:00 | exited | owned-cleaned | bounded task process tree | idempotent no-op: already absent |
| test DB resource | dynamic conftest temporary DB, exact path not emitted | current T37 run | module-load conftest safe DB bootstrap | 2026-08-24T22:26:52-03:00 | 2026-08-24T22:27:13-03:00 | absent | owned-cleaned | no `data/portfolio.db` target | no-op: exact resource absent; no rediscovery |
| temporary path | task-scoped pytest temp resources, exact paths not emitted | current T37 run | command-owned temporary resource registration | 2026-08-24T22:26:52-03:00 | 2026-08-24T22:27:13-03:00 | absent | owned-cleaned | no host-wide temp discovery | no-op: exact resources absent; no rediscovery |

### Apply focused validation run `t37-apply-20260824-03`

Registration: exact wrapper PID/PGID and start timestamp recorded immediately
before command launch; same bounded ownership and cleanup policy applies.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | wrapper PID 189873 | current T37 run | `tool_036888dab001ibdkchqPQLrHwj` pre-launch registration | 2026-08-24T22:28:15-03:00 | 2026-08-24T22:28:37-03:00 | exited | owned-cleaned | 593 passed, 2 skipped, 551 deselected; no live server/browser | idempotent no-op: already absent |
| process group | PGID 189873 | current T37 run | same pre-launch registration | 2026-08-24T22:28:15-03:00 | 2026-08-24T22:28:37-03:00 | exited | owned-cleaned | unit-only task process group | idempotent no-op: already absent |
| test DB resource | dynamic conftest temporary DB, exact path not emitted | current T37 run | module-load safe DB bootstrap | 2026-08-24T22:28:15-03:00 | 2026-08-24T22:28:37-03:00 | absent | owned-cleaned | persistent DB excluded | no-op: exact resource absent; no rediscovery |
| temporary path | task-scoped pytest temp resources, exact paths not emitted | current T37 run | command-owned temporary resource registration | 2026-08-24T22:28:15-03:00 | 2026-08-24T22:28:37-03:00 | absent | owned-cleaned | no broad temp scan | no-op: exact resources absent; no rediscovery |

### Apply focused validation run `t37-apply-20260824-06`

Owner: `t37-governanca-pratica-do-db-e2e-e-processos-omaha/apply`
Agent identity: `openai/gpt-5.6-luna` apply
Run registration: 2026-08-25T01:37:38Z, before launching focused validation.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | wrapper PID 191311 | current T37 run | pre-launch registration in `tool_036915016001QnmwwnxAxjo7ym` | 2026-08-25T01:37:50Z | 2026-08-25T01:38:11Z | exited | owned-cleaned | 596 passed, 2 skipped, 551 deselected, 3 warnings; exit 0 | idempotent no-op: already absent |
| process group | PGID 191311 | current T37 run | same pre-launch registration; `pid=pgid` observed before exec | 2026-08-25T01:37:50Z | 2026-08-25T01:38:11Z | exited | owned-cleaned | no server/browser child | idempotent no-op: already absent |
| test DB resource | dynamic conftest temporary DB, exact path not emitted | current T37 run | module-load safe DB bootstrap | 2026-08-25T01:37:50Z | 2026-08-25T01:38:11Z | absent | owned-cleaned | `data/portfolio.db` excluded; coverage generated | no-op: exact resource absent; no rediscovery |
| temporary path | task-scoped pytest temp resources, exact paths not emitted | current T37 run | command-owned temporary resource registration | 2026-08-25T01:37:50Z | 2026-08-25T01:38:11Z | absent | owned-cleaned | no host-wide temp discovery | no-op: exact resources absent; no rediscovery |

### Apply focused validation run `t37-apply-20260824-05`

Registration: exact wrapper PID/PGID and start timestamp recorded immediately
before command launch.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | wrapper PID 190657 | current T37 run | `tool_0368bb788001D5WfP10kywnJD0` pre-launch registration | 2026-08-24T22:31:43-03:00 | 2026-08-24T22:32:05-03:00 | exited | owned-cleaned | 596 passed, 2 skipped, 551 deselected; no live server/browser | idempotent no-op: already absent |
| process group | PGID 190657 | current T37 run | same pre-launch registration | 2026-08-24T22:31:43-03:00 | 2026-08-24T22:32:05-03:00 | exited | owned-cleaned | unit-only task process group | idempotent no-op: already absent |
| test DB resource | dynamic conftest temporary DB, exact path not emitted | current T37 run | module-load safe DB bootstrap | 2026-08-24T22:31:43-03:00 | 2026-08-24T22:32:05-03:00 | absent | owned-cleaned | persistent DB excluded | no-op: exact resource absent; no rediscovery |
| temporary path | task-scoped pytest temp resources, exact paths not emitted | current T37 run | command-owned temporary resource registration | 2026-08-24T22:31:43-03:00 | 2026-08-24T22:32:05-03:00 | absent | owned-cleaned | no broad temp scan | no-op: exact resources absent; no rediscovery |

### Apply focused validation run `t37-apply-20260824-04`

Registration: exact wrapper PID/PGID and start timestamp recorded immediately
before command launch.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | wrapper PID 190407 | current T37 run | `tool_0368a7349001Cf1NEc4pGNa3F2` pre-launch registration | 2026-08-24T22:30:19-03:00 | 2026-08-24T22:30:42-03:00 | exited | owned-cleaned | 596 passed, 2 skipped, 551 deselected; no live server/browser | idempotent no-op: already absent |
| process group | PGID 190407 | current T37 run | same pre-launch registration | 2026-08-24T22:30:19-03:00 | 2026-08-24T22:30:42-03:00 | exited | owned-cleaned | unit-only task process group | idempotent no-op: already absent |
| test DB resource | dynamic conftest temporary DB, exact path not emitted | current T37 run | module-load safe DB bootstrap | 2026-08-24T22:30:19-03:00 | 2026-08-24T22:30:42-03:00 | absent | owned-cleaned | persistent DB excluded | no-op: exact resource absent; no rediscovery |
| temporary path | task-scoped pytest temp resources, exact paths not emitted | current T37 run | command-owned temporary resource registration | 2026-08-24T22:30:19-03:00 | 2026-08-24T22:30:42-03:00 | absent | owned-cleaned | no broad temp scan | no-op: exact resources absent; no rediscovery |

## Review Findings

### Review R1

Scope audit: proposal and design intent pass; four delta specs and 14/14 task
checkboxes pass; exact E2E DB recreation and `data/portfolio.db` protection pass;
bounded canonical inventory and no foreign-resource action pass; process
identity, TERM-first owned-PGID cleanup, stale-listener preservation, receipts,
six-lane/fail-fast/coverage contracts pass by focused evidence and static audit;
repository scope boundary finding; roadmap preservation finding; product
behavior/non-goals pass; test deletion/masking/retry/skip/xfail audit pass;
canonical full-suite result not assessable under owner-authorized
`maintenance-suspended` policy, recorded below rather than inferred green.

Full suite: `NOT RUN — maintenance-suspended` (canonical gate state in
`openspec/config.yaml:85-99`; no full-suite process launched). Focused evidence:
`uv run task test-unit` -> `596 passed, 2 skipped, 551 deselected, 3 warnings`,
exit 0, reported `18.77s` in apply handoff. `openspec validate
t37-governanca-pratica-do-db-e2e-e-processos-omaha --type change --strict` ->
valid; Ruff -> no issues; `git diff --check` -> clean. No product behavior tests
apply to harness-only scope. No test deletion, skip, xfail, retry, lane removal,
or coverage reduction observed.

Preflight: review ownership ledger was inspected before standards/spec audit. No
current-run child/process-group was launched. Exact declared ports 8765, 8766,
8767, 8768 classified `absent` by bind probe. Exact declared DBs classified:
`data/test_e2e.db` `ephemeral-preexisting`/preserved for review (disposable
target, no review-run ownership), `data/test_e2e_short_ttl.db` `absent`,
`data/test_bdd.db` `absent`, `data/test_visual.db` `absent`, and
`data/portfolio.db` `pre-existing`/protected. No foreign, unknown, or
contradictory listener was adopted or touched. Apply ledgers contain incomplete
exact temporary-path identities (`tasks.md:102-103,119-120,131-132,144-145`),
so review did not treat their cleanup claims as proof of broad host cleanup.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| declared listener | 127.0.0.1:8765, :8766, :8767, :8768 | review R1 | exact bind probes, no suite launch | 2026-08-25 review preflight | 2026-08-25 review preflight | not launched | absent | exact canonical ports only | not applicable |
| declared E2E DB | `/home/juca/github/omaha/data/test_e2e.db` | pre-existing environment | exact `Path` stat; no current-run owner evidence | 2026-08-25 review preflight | 2026-08-25 review preflight | preserved | ephemeral-preexisting | exact registered disposable target | preserved/non-target for review |
| declared DB | `/home/juca/github/omaha/data/test_e2e_short_ttl.db`, `test_bdd.db`, `test_visual.db` | review R1 | exact `Path` stat | 2026-08-25 review preflight | 2026-08-25 review preflight | absent | absent | exact registered paths | not applicable |
| protected DB | `/home/juca/github/omaha/data/portfolio.db` | pre-existing environment | exact `Path` stat; protected invariant | 2026-08-25 review preflight | 2026-08-25 review preflight | preserved | pre-existing | no mutation attempted | preserved/non-target |
| review process/temp resources | no canonical suite resources | review R1 | no suite launch; no declared lane boundary created | 2026-08-25 | 2026-08-25 | not launched | absent | no process/temp ownership to reconcile | not applicable |

Postflight: no canonical suite launch, therefore no child cleanup phase. Exact
declared-port probes remained absent; no review-owned process, DB, or temporary
resource existed to clean. Protected and pre-existing resources remained
untouched. Decision: no postflight suite receipt is claimed; suspension receipt
is non-blocking only for canonical full-suite enforcement.

Runner isolation: no suite launch because gate is suspended. Review preflight
found no declared listener/process residue; exact E2E pre-existing DB is
disposable pre-existing state and was preserved, while production DB remained
protected. No baseline or allowlist exception was used; no foreign cleanup was
performed.

Verdict: CHANGES_REQUESTED

#### R1-F01 — Unrelated repository files changed
Status: open
Requirement/task: proposal Non-goal lines 30-38; design Change Map lines
156-169; task 4.2 (`tasks.md:45`), acceptance `no_unrelated_files_changed`.
Evidence: `git status --short` and diff show `openspec/roadmap.md` and
`tests/support/browser.py` changed in addition to mapped T37 files. `browser.py`
is not in proposal Impact, design Code Map/Change Map, or task target allowlist;
task 4.2 explicitly forbids roadmap edits. Diff: `openspec/roadmap.md` changes
slice lifecycle/status; `tests/support/browser.py:88-130` adds lifecycle
callback behavior outside declared mapped symbols.
Required change: revert only T37-unapproved changes in `openspec/roadmap.md`
and `tests/support/browser.py`, or obtain owner-approved scope/artifact update
before re-review. Excluded scope: do not alter mapped harness implementation,
proposal, design, four delta specs, stable specs, application code, DB/seed data,
or unrelated slices.
Acceptance: `git status --short --untracked-files=all` contains only declared
T37 implementation files and exact T37 change artifacts; `git diff --check`
clean; strict change validation remains valid; no roadmap or browser-support
diff remains unless explicitly owner-approved and added to T37 scope.

#### R1-F02 — Roadmap mutation violates task scope boundary
Status: open
Requirement/task: task 4.2 (`tasks.md:45`) and proposal Non-goal line 36.
Evidence: `openspec/roadmap.md:82-101` changes T37 from `Ready` to `Applying`,
rewrites active queue, and records apply progress. This is direct violation of
the task's explicit “do not edit roadmap” acceptance, independent of F01's
unmapped-file finding.
Required change: restore `openspec/roadmap.md` to pre-T37-review state; do not
move lifecycle state as part of implementation review. Excluded scope: no
roadmap redesign or lifecycle transition; orchestrator owns later status update.
Acceptance: roadmap diff is empty relative to review baseline and strict
repository scope audit reports no roadmap mutation.

Late finding reason: none; initial whole-slice scope audit.

## R1 Remediation — pass 1/2

- [x] R1-F01 boundary audit: `tests/support/browser.py` is retained as a
  supporting implementation detail of approved task 3.1, not as new scope.
  `run_test_server` in the task-3.1-approved `tests/support/server.py` passes
  `lifecycle_callback` to `shutdown_uvicorn`; `tests/support/browser.py` owns
  the actual TERM, bounded wait, optional owned-group KILL, exit, and port-free
  phases. Removing its 11-line callback bridge would make the approved server
  path fail with an unsupported keyword and would remove required lifecycle
  receipt evidence. No product or caller behavior is added. This is the exact
  task-3.1 dependency/rationale permitted by the remediation brief.
- [x] R1-F02 boundary audit: preserve `openspec/roadmap.md` unchanged in this
  pass. Its T37 `Applying` lifecycle/progress/queue entries are orchestrator-
  mandated bookkeeping, not implementation scope. Apply owns no roadmap hunk;
  orchestrator owns that boundary and later lifecycle transitions. No roadmap
  content was edited by this remediation.

### R1 resolution evidence

- **R1-F01 — resolved for re-review.** No implementation file was reverted or
  added. The browser-support hunk is covered by approved task 3.1 as the
  callback dependency required for `tests/support/server.py` lifecycle
  receipts; exact symbols and failure mode are recorded above. No unrelated
  implementation boundary changed.
- **R1-F02 — resolved for re-review.** `openspec/roadmap.md` was not edited.
  Its pre-existing orchestrator bookkeeping diff remains deliberately outside
  this apply pass and is not counted as T37 implementation ownership.
- Focused validation: `uv run task test-unit` -> `596 passed, 2 skipped, 551
  deselected, 3 warnings in 18.52s`; exit 0. `openspec validate
  t37-governanca-pratica-do-db-e2e-e-processos-omaha --type change --strict` ->
  valid. `uv run ruff check scripts/run_full_suite.py tests/conftest.py
  tests/e2e/conftest.py tests/support/db.py tests/support/server.py
  tests/support/browser.py tests/scripts/test_t29_harness.py` -> all checks
  passed. `git diff --check` -> clean.
- Boundary audit: implementation names are the seven dossier-covered harness
  files listed below; exact T37 artifacts are confined to the named change
  folder; roadmap is separately classified as orchestrator bookkeeping. No
  production DB, server, browser, migration, seed, or network command ran.

### Ownership ledger receipt — `t37-remediation-r1-20260825-01`

Owner: `t37-governanca-pratica-do-db-e2e-e-processos-omaha/apply`; agent:
`openai/gpt-5.6-luna` apply. Registration was emitted before `uv run task
test-unit` launch by wrapper PID/PGID 193122 at `2026-08-24T22:50:30-03:00`.
Focused task ended at `2026-08-24T22:50:49-03:00`; exact PID/PGID probe after
exit returned absent. No canonical server/browser child or declared port was
launched.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID 193122 | current T37 remediation run | pre-launch wrapper registration in `tool_0369ceb050016YDD6Z4tZmCbou`, PID/PGID recorded before task | 2026-08-24T22:50:30-03:00 | 2026-08-24T22:50:49-03:00 | exited | owned-cleaned | task-only pytest process; exact PID absent at postflight | idempotent no-op: already absent; no signal issued |
| process group | PGID 193122 | current T37 remediation run | same pre-launch registration; wrapper PID equaled PGID | 2026-08-24T22:50:30-03:00 | 2026-08-24T22:50:49-03:00 | exited | owned-cleaned | no server/browser descendant launched; exact PGID absent at postflight | idempotent no-op: already absent; no group cleanup |
| test DB resource | pytest dynamic safe temporary DB, exact path not emitted | current T37 remediation run | taskipy unit lane/conftest safe-DB bootstrap; no persistent target configured | 2026-08-24T22:50:30-03:00 | 2026-08-24T22:50:49-03:00 | absent | owned-cleaned | process-local test DB scope ended with pytest; `data/portfolio.db` not targeted | no-op: exact resource not present after task; no rediscovery |
| temporary path | pytest-managed task temporary resources, exact paths not emitted | current T37 remediation run | task-scoped pytest ownership; no host-wide temp discovery | 2026-08-24T22:50:30-03:00 | 2026-08-24T22:50:49-03:00 | absent | owned-cleaned | no canonical review lane boundary created | no-op: exact task resources absent; no rediscovery |

Cleanup decision: only current-run ledger entries were reconciled; all were
`owned-cleaned` or idempotent absent. No foreign, pre-existing, unknown, or
contradictory resource was adopted, signaled, freed, deleted, or allowlisted.

### Remediation diff boundary

Implementation diff remains limited to T37 harness/support files covered by the
dossier: `scripts/run_full_suite.py`, `tests/conftest.py`,
`tests/e2e/conftest.py`, `tests/support/db.py`, `tests/support/server.py`,
`tests/support/browser.py` (task 3.1 callback dependency), and
`tests/scripts/test_t29_harness.py`. T37 artifacts remain under the exact
change folder. `openspec/roadmap.md` is recorded separately as orchestrator
bookkeeping and is excluded from implementation ownership. No other worktree
 boundary is changed.

## Review Findings

### Review R2
Scope audit: proposal/design alignment **pass**; four delta specs and 16/16
task checkboxes **pass**; exact E2E disposable recreation and `data/portfolio.db`
protection **pass**; bounded preflight, ownership classification, process
identity, TERM-first owned-PGID cleanup, stale recovery, receipts, six-lane,
fail-fast, coverage, skip, retry, and 300-second contract **pass** by focused
evidence plus static audit; browser-support dependency boundary **pass**;
roadmap bookkeeping boundary **pass**; product behavior/non-goals and forbidden
scope **pass**; no test deletion/masking/xfail/retry/lane removal/coverage
reduction **pass**. Canonical full-suite enforcement is **not assessable** under
owner-authorized `maintenance-suspended`; policy permits approval only with
explicit suspended receipt and green applicable focused evidence.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**;
`openspec/config.yaml:87-99` is canonical receipt. Six lanes: unit **not run**,
integration **not run**, audit integration **not run**, e2e **not run**, bdd **not
run**, visual **not run**; no fail-fast or canonical cleanup disposition was
claimed. Focused command: `uv run task test-unit` -> **596 passed, 2 skipped,
551 deselected, 3 warnings**, exit 0, measured wall-clock **22.341s** from
wrapper start through child cleanup. Focused coverage remained enabled and
reported by pytest; no product behavior test applies beyond harness contract
tests. Canonical `<=300s` classification: **not applicable while suspended**;
no canonical green result inferred.

Preflight: review-owned wrapper PID/PGID was registered before focused launch;
exact declared ports `127.0.0.1:8765`, `:8766`, `:8767`, `:8768` classified
`absent`. Exact declared DB inventory: `data/test_e2e.db` `pre-existing`
regular disposable target, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, and
`data/test_visual.db` `absent`, `data/portfolio.db` `pre-existing` regular
protected target. No foreign, unknown, contradictory, or incomplete relevant
listener/process state observed; no foreign-resource action, adoption, signal,
free, deletion, or allowlist occurred. Existing apply ledger's non-exact temp
path descriptions were not treated as proof of host-wide cleanup.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| declared listener | `127.0.0.1:8765,:8766,:8767,:8768` | review R2 | exact bind probes before focused command | 2026-08-25T01:53:54Z | 2026-08-25T01:53:54Z | not launched | absent | all exact probes bindable | not applicable |
| declared DB | `/home/juca/github/omaha/data/test_e2e.db` | pre-existing environment | exact `lstat`; no review-run owner | 2026-08-25T01:53:54Z | 2026-08-25T01:54:49Z | preserved | ephemeral-preexisting | regular inode `518994`, size `143360` | preserved/non-target |
| declared DB | `test_e2e_short_ttl.db`, `test_bdd.db`, `test_visual.db` | review R2 | exact `lstat` | 2026-08-25T01:53:54Z | 2026-08-25T01:54:49Z | absent | absent | exact registered paths | not applicable |
| protected DB | `/home/juca/github/omaha/data/portfolio.db` | pre-existing environment | exact `lstat`; protected invariant | 2026-08-25T01:53:54Z | 2026-08-25T01:54:49Z | preserved | pre-existing | regular inode `241846`, size `282624` | preserved/non-target |
| focused wrapper process/group | PID/PGID `193710` | review R2 | wrapper registration immediately before task | 2026-08-25T01:54:02Z | 2026-08-25T01:54:25Z | exited | owned-cleaned | exit 0; no server/browser descendant | idempotent no-op: exact PID/PGID absent |
| focused temporary/test DB resources | task-scoped pytest resources; exact paths unavailable | review R2 | taskipy unit process scope | 2026-08-25T01:54:02Z | 2026-08-25T01:54:25Z | exited | owned-cleaned | no canonical lane boundary created | no broad rediscovery; no-op |

Postflight: exact declared ports remained `absent`; `data/test_e2e.db` remained
same regular inode/size and `data/portfolio.db` remained same protected regular
inode/size; other declared DBs remained absent. Focused wrapper/group was
absent after exit. No canonical suite launch means no canonical child cleanup
phase or postflight suite receipt is claimed. Runner isolation: **pass** for
focused review command; no canonical runner isolation decision is claimed under
suspension. No baseline or allowlist exception was used.

Changed files: implementation diff is limited to declared T37 harness/support
files `scripts/run_full_suite.py`, `tests/conftest.py`, `tests/e2e/conftest.py`,
`tests/support/db.py`, `tests/support/server.py`, `tests/support/browser.py`,
and `tests/scripts/test_t29_harness.py`. `tests/support/browser.py:81-137` is a
genuine task-3.1 dependency: `server.py:178-200` and `:241-263` pass its
callback, which emits TERM, bounded wait, owned-group escalation, exit, and
port-free events from existing shutdown behavior. It adds no caller, port,
browser, or product behavior. `openspec/roadmap.md` remains separately
classified as pre-existing orchestrator lifecycle bookkeeping, not T37
implementation ownership; remediation introduced no roadmap hunk. Exact T37
artifacts remain under this change folder.

Checks: strict OpenSpec validation **valid**; Ruff focused file set **passed**;
`git diff --check` **clean**. Acceptance conditions for safe DB recreate,
portfolio protection, identity/preflight/cleanup/recreate/restart/receipts,
stale recovery, and foreign-resource preservation remain true. No DB mutation,
server, browser, migration, seed, or network command ran.

Verdict: **APPROVED**

#### R2-F01 — R1-F01 unrelated-file boundary
Status: resolved
Requirement/task: proposal non-goals 30-38; design Change Map 156-169; task
3.1 and task 4.2.
Evidence: `tests/support/server.py:178-200,241-263` consumes
`tests/support/browser.py:91-137` callback; focused suite passed; current
implementation allowlist contains only dossier-covered harness/support files.
Roadmap is separately orchestrator bookkeeping, not implementation.
Required change: none. Excluded scope: no new implementation files or scope
expansion.
Acceptance: browser lifecycle callback remains required by task 3.1 and no
foreign resource action or product behavior changes.
Late finding reason: remediation re-audit of R1-F01.

#### R2-F02 — R1-F02 roadmap/task boundary
Status: resolved
Requirement/task: task 4.2 (`tasks.md:45`) and proposal non-goal 36.
Evidence: remediation record states no roadmap hunk was edited; current roadmap
diff is orchestrator lifecycle/progress bookkeeping, while implementation
diff and change artifacts are independently enumerated. Strict validation and
`git diff --check` pass.
Required change: none. Excluded scope: no roadmap edit, redesign, lifecycle
transition, or archive action by review.
Acceptance: roadmap is not classified as implementation ownership; orchestrator
retains bookkeeping boundary.
Late finding reason: remediation re-audit of R1-F02.
