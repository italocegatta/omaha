## 1. Authoritative source discovery and bounded collection

- [x] 1.1 **Target:** `docs/runbooks/myprofit-sync-telemetry.md`, source and retention sections. **Change:** document how to identify the existing `omaha` stdout boundary from the current dev launcher or production Compose `web` service, then give bounded retrieval commands for retained output without assuming an application log file, journald, `/tmp`, or a shipper. Include source identity, format, earliest/latest coverage, rotation segments, and safe operator-owned output copy. **Preserve:** T38 stdout-only storage decision; no collector, retention daemon, restart, connector, credential, CSV, URL, path, filename, or DB mutation. **Acceptance:** operator can name authoritative source, retrieve text/JSON output, inventory retention/rotation, and receive explicit `insufficient-evidence` for missing coverage. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`, existing required-token contract plus manual command review. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** exact changed-file allow-list; commands are read-only; runbook contains no invented sink/path or destructive DB task.

- [x] 1.2 **Target:** `docs/runbooks/myprofit-sync-telemetry.md`, bounded extraction procedure. **Change:** add exact JSON-envelope extraction from `JsonFormatter.msg` and text-mode extraction, then filter only `myprofit_telemetry` lines into a bounded analysis copy. State rejection of unknown fields/dimensions, malformed UUIDs, negative/non-integer/out-of-bound durations, missing fixed fields, and exact duplicate-line handling. **Preserve:** `logging_config.py` seven-key JSON envelope, fixed T38 message order, allowlists from `telemetry.py`, and no raw operational payload. **Acceptance:** an operator can reproduce extraction in both formats and distinguish accepted, invalid, and absent records without repairing values by guesswork. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** compare documented shape and finite sets against `telemetry.py` constants and `JsonFormatter`; forbidden-value scan passes.

## 2. Job correlation and terminal classification

- [x] 2.1 **Target:** `docs/runbooks/myprofit-sync-telemetry.md`, `myprofit_sync_jobs` correlation section. **Change:** provide exact read-only SQLite `SELECT` for selected `job_id` values returning `profile_id`, status, normalized error fields, and created/started/finished/expiry/retention timestamps; document FK-based profile ownership verification and the boundary for Postgres/read-only operational clients without inventing credentials or DSNs. **Preserve:** `MyProfitSyncJob` schema, profile isolation, product-row retention/pruning, and PRD §4.11–§4.12 prohibition on DB writes. **Acceptance:** operator can correlate an exact job ID, detect missing/pruned rows as `db-correlation-unavailable`, and cannot infer joins by timestamp, filename, profile label, or status alone. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`; manual SQL safety review. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** compare query columns/FK/status values against `src/omaha/models.py` and `alembic/versions/0020_myprofit_sync_jobs.py`; query is `SELECT`/read-only only.

- [x] 2.2 **Target:** `docs/runbooks/myprofit-sync-telemetry.md`, classification and denominator sections. **Change:** define `observed_runs`, `terminal_runs`, `succeeded`, `failed`, `expired`, `incomplete_runs`, invalid/missing counts, and `ui_limit_count`; define failure rate denominator and require separate treatment of missing terminal evidence. State that `failed` comes from terminal status `failed`, `expired` from terminal status `expired`, and UI local-limit presence/absence never changes server classification. **Preserve:** T38 lifecycle/expiry precedence, existing `500 ms × 120` browser boundary, and safe error behavior. **Acceptance:** procedure cannot classify missing terminal telemetry as failed/expired or classify missing UI-limit telemetry as proof that limit was not reached. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`; manual comparison with `imports.py` lifecycle and UI-limit paths. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** classification matrix matches `MyProfitSyncJob` status constraint and T38 event contract; denominators are explicit.

## 3. Repeatable weekly analysis and safety boundary

- [x] 3.1 **Target:** `docs/runbooks/myprofit-sync-telemetry.md`, weekly analysis section. **Change:** document a repeatable four-to-eight-week worksheet for 4–8 real runs/week: exact `job_id` grouping, bounded `domain/stage/code` groups, unique-run counts, terminal/failure/expiry rates, total/stage p50/p95/p99, UI-limit and concurrency counts, missing/invalid records, and top failed-run factors. Include the existing diagnosis threshold: one normalized `stage/code` cluster in at least three runs across at least two weeks and at least 50% of failed terminal runs, or UI-limit in at least two runs. **Preserve:** descriptive-only analysis; no SLA, timeout, retry, F68, external-service, or root-cause claim. **Acceptance:** operator can repeat same weekly measures and decide between escalation and `insufficient-evidence` without changing denominator or percentile method. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** required windows, thresholds, dimensions, measures, and forbidden remediation claims all appear and agree with T38 `design.md`/`tasks.md`.

- [x] 3.2 **Target:** `docs/runbooks/myprofit-sync-telemetry.md`, safety and final checklist sections. **Change:** add explicit sanitization checklist for retained evidence and a final changed-file/scope statement covering no runtime, DB/schema/migration, telemetry behavior, timeout, retry, F68, T38 artifact mutation, secrets, raw exception, CSV, sensitive URL, and broad ops cleanup. **Preserve:** PRD §4.1, §4.9, §4.11–§4.14 and T38 review resolutions; doc-only work skips `refresh-for-test` and does not touch product DB. **Acceptance:** runbook tells operator what may be retained/shared, what must be redacted/rejected, and what actions are prohibited; no new runtime or test file is needed. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`; repository diff audit. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** exact path allow-list contains only the runbook in implementation scope; `git diff --check` is clean; no forbidden runtime/schema/config/T38 files changed.

## 4. Focused validation and acceptance evidence

- [x] 4.1 **Target:** D08 dossier and `docs/runbooks/myprofit-sync-telemetry.md`. **Change:** run documentation contract test, inspect every operator command for read-only/bounded behavior, and record exact command, timestamp, exit code, and test count in implementation evidence. **Preserve:** no full-suite launch requirement during maintenance-suspended state, no skipped/xfail/retried test, no live connector, and no persistent DB write. **Acceptance:** focused runbook test passes; OpenSpec change validation passes for exact change id; `git diff --check` passes; changed files are limited to D08 dossier plus the single runbook during Apply. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** `openspec validate d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit --type change --no-interactive`, `git diff --check`, and exact changed-path audit.

## Test Strategy

- Documentation contract: reuse `tests/test_myprofit_sync_jobs.py::test_myprofit_telemetry_runbook`; no test source changes are in scope.
- Source-of-truth review: compare runbook event shape/allowlists to
  `src/omaha/myprofit/telemetry.py` and JSON placement to
  `src/omaha/logging_config.py`.
- Correlation safety: compare read-only query to `MyProfitSyncJob` and
  `0020_myprofit_sync_jobs.py`; do not execute query against product DB during
  Apply unless owner separately authorizes a read-only inspection.
- Scope validation: `openspec validate ... --type change --no-interactive`,
  `git diff --check`, and exact changed-path/forbidden-token audit.
- Canonical full suite: `NOT RUN — maintenance-suspended`; focused runbook
  test remains mandatory.

## Acceptance Evidence Required Before READY_FOR_REVIEW

1. Exact implementation changed-file list: D08 dossier files and the one
   runbook file only; no roadmap, config, stable spec, T38 artifact, runtime,
   schema, migration, test, DB, secret, or financial file changed.
2. Focused taskipy command, timestamp, exit code, and test count for
   `uv run task test-integration -- -k myprofit_telemetry_runbook`.
3. Documentation inspection proving authoritative stdout discovery, JSON/text
   extraction, exact event shape and allowlists, bounded `job_id` grouping,
   rotation/retention gate, and safe collection instructions.
4. Documentation inspection proving read-only `myprofit_sync_jobs` correlation,
   profile ownership check, product-row retention limitation, and separate
   succeeded/failed/expired/incomplete/UI-limit classification.
5. Documentation inspection proving weekly denominators, error rates, invalid
   and missing counts, top `domain/stage/code` factors, 4–8 week procedure,
   and diagnosis thresholds.
6. Explicit `insufficient-evidence` behavior for absent/partial stdout,
   invalid records, low volume, missing terminal events, and unavailable DB
   rows; no inferred cause or runtime remediation.
7. OpenSpec validation and `git diff --check` results recorded; canonical
   suite recorded as `NOT RUN — maintenance-suspended`.

## Execution Evidence

### Apply initial — 2026-08-24

Implementation boundary before validation:

- `docs/runbooks/myprofit-sync-telemetry.md` — authoritative runbook.
- This D08 `design.md` — implementation decisions only.
- This D08 `tasks.md` — task completion and evidence only.
- No runtime, test, schema, migration, stable spec, T38 artifact, roadmap, or
  config file is owned by D08.

Pre-launch ownership registration for one bounded validation run:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-focused-20260824T202528-0300` | child process / process group / test DB resource | pytest PID `172347`, PGID `172339`, and temporary integration-test DB resources created by exact command below | D08 apply agent | current change id plus exact taskipy command registered before launch; PID/PGID observed from test failure receipt; no process or database adopted | `2026-08-24T20:25:28-03:00` | `2026-08-24T20:25:35-03:00` | exited | owned-cleaned | focused documentation test exited 1 because existing token contract required contiguous `4–8 real runs per week`; no product DB target; failure diagnosed as documentation test drift | pytest child exited; isolated fixture DB cleanup completed; no residue observed; no foreign action |

Pre-launch registration for remediation validation after documentation test drift fix:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-remediation1-20260824T202841-0300` | child process / process group / test DB resource | exact taskipy pytest/OpenSpec/static validation children and isolated test DB resources created by commands below | D08 apply agent | current change id plus exact taskipy/OpenSpec/static commands registered before launch; no PID, process group, database, or path adopted | `2026-08-24T20:28:41-03:00` | `2026-08-24T20:29:32-03:00` | exited | owned-cleaned | focused documentation test passed; OpenSpec validation and diff check passed; static checker failed only because its case-sensitive local token list expected lowercase `rotation` while runbook uses `Rotation`; no product failure | pytest child and validation processes exited; isolated fixture DB cleanup completed; no residue observed; no foreign action |

Pre-launch registration for final documentation/static validation rerun:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-remediation1-final-20260824T202945-0300` | child process / process group | exact OpenSpec validator, git diff-check, and static validation children created by commands below | D08 apply agent | current change id plus exact commands registered before launch; no PID or process group adopted | `2026-08-24T20:29:45-03:00` | `2026-08-24T20:30:07-03:00` | exited | owned-cleaned | OpenSpec validation and diff check passed; static checker failed only because it expected fenced `python3` blocks while runbook intentionally labels complete heredoc commands `sh`; no product failure | validator, diff-check, and static processes exited; no temporary or foreign resource residue |

Pre-launch registration for final static-validation correction:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-final-static-20260824T203020-0300` | child process / process group | exact OpenSpec validator, git diff-check, and static validation children created by command below | D08 apply agent | current change id plus exact commands registered before launch; no PID or process group adopted | `2026-08-24T20:30:20-03:00` | `2026-08-24T20:30:43-03:00` | exited | owned-cleaned | checker compiled heredoc bodies identified by `python3 -`; OpenSpec valid, diff clean, static checks passed; no runtime or DB operation | validator, diff-check, and static processes exited; no temporary or foreign resource residue |

Pre-launch registration for final focused and documentation validation after
safe Compose extraction correction:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-final-focused-20260824T203155-0300` | child process / process group / test DB resource | pytest child resources and isolated integration-test DB resources created by exact command below | D08 apply agent | current change id plus exact focused command registered before launch; test receipt exited cleanly; no PID, process group, database, or path adopted | `2026-08-24T20:31:55-03:00` | `2026-08-24T20:32:26-03:00` | exited | owned-cleaned | final focused docs contract passed: 1 passed, 1152 deselected, exit 0; no product DB target | pytest children exited; isolated fixture DB cleanup completed; no residue observed; no foreign action |

Pre-launch registration for final strict change, diff, static, and scope
validation:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-final-audit-20260824T203235-0300` | child process / process group | exact OpenSpec validator, git diff-check, static checker, and scope-audit children created by commands below | D08 apply agent | current change id plus exact commands registered before launch; no PID or process group adopted | `2026-08-24T20:32:35-03:00` | `2026-08-24T20:33:10-03:00` | exited | owned-cleaned | strict change validation valid; diff check clean; static checks passed with 2 Python heredocs and 9 shell blocks; exact path audit passed; no runtime or DB operation | validator, diff-check, static, and scope-audit children exited; no temporary or foreign resource residue |

### Acceptance receipt

Owned Apply paths:

- `docs/runbooks/myprofit-sync-telemetry.md`
- `openspec/changes/d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit/design.md`
- `openspec/changes/d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit/tasks.md`

Pre-existing worktree paths preserved and not owned by D08 Apply: roadmap,
T38 runtime/test files, T38 telemetry module, and T38 dossier artifacts. D08
proposal, delta spec, and `.openspec.yaml` were pre-existing proposal-gate
artifacts and were not edited during Apply.

Focused validation receipts:

| Timestamp (America/Sao_Paulo) | Command | Result |
|---|---|---|
| `2026-08-24T20:25:28-03:00` → `20:25:35-03:00` | `uv run task test-integration -- -k myprofit_telemetry_runbook` | exit 1; 1 selected, 1152 deselected; documentation test exposed line-wrap drift for required contiguous token `4–8 real runs per week`; fixed in runbook, no test weakened |
| `2026-08-24T20:28:41-03:00` → `20:28:50-03:00` | `uv run task test-integration -- -k myprofit_telemetry_runbook` | exit 0; 1 passed, 1152 deselected |
| `2026-08-24T20:32:17-03:00` → `20:32:26-03:00` | `uv run task test-integration -- -k myprofit_telemetry_runbook` | exit 0; 1 passed, 1152 deselected; final run after Compose extraction correction |
| `2026-08-24T20:33:09-03:00` → `20:33:10-03:00` | `openspec validate d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit --type change --no-interactive && git diff --check` | valid; both exit 0; diff clean |
| `2026-08-24T20:33:09-03:00` → `20:33:10-03:00` | bounded documentation static check | exit 0; 2 Python heredoc blocks parsed by `ast`, 9 shell blocks checked for bounded/read-only markers, forbidden tokens absent |
| `2026-08-24T20:33:09-03:00` → `20:33:10-03:00` | exact changed-path audit | exit 0; Apply-owned paths limited to runbook plus D08 `design.md`/`tasks.md`; pre-existing T38/roadmap work preserved |
| `2026-08-24T20:35:21-03:00` → `20:35:32-03:00` | `uv run task test-integration -- -k myprofit_telemetry_runbook && openspec validate d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit --type change --no-interactive && git diff --check` plus bounded static/path audit | exit 0; 1 passed, 1152 deselected; OpenSpec valid; diff clean; 2 Python heredocs parsed, 9 shell blocks checked, owned-path audit passed |
| `2026-08-24T20:43:18-03:00` → `20:43:29-03:00` | `uv run task test-integration -- -k myprofit_telemetry_runbook && openspec validate d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit --type change --no-interactive && git diff --check` plus bounded coverage/path audit | exit 0; 1 passed, 1152 deselected; OpenSpec valid; diff clean; 2 Python heredocs parsed, 10 shell blocks checked, 3 Apply-owned paths confirmed |

Acceptance evidence:

- Source procedure identifies dev stdout capture and existing Compose `web`
  stdout, distinguishes application guarantee from operator-retained output,
  inventories declared rotation segments, and labels gaps
  `insufficient-evidence`.
- JSON extraction requires exact seven-key envelope placement, `msg`, logger,
  and null `exc_info`; text extraction removes only known `omaha` prefix.
- Canonical message shape, finite allowlists, UUID/duration validation, exact
  duplicate handling, bounded filters, and one-job trace are executable.
- Correlation is exact `job_id` plus FK-scoped `profile_id` through SQLite
  `-readonly` `SELECT`; status, normalized errors, lifecycle/retention fields,
  pruning, and `db-correlation-unavailable` are documented without inferred
  joins.
- Classification separates observed/terminal/succeeded/failed/expired/
  incomplete/UI-limit/concurrency/missing/invalid counts and makes
  `failed / terminal_runs` denominator explicit.
- Weekly worksheet covers four-to-eight weeks, 4–8 real runs per week,
  bounded `domain/stage/code` factors, unique-run counts, p50/p95/p99,
  UI-limit/concurrency counts, missing/invalid records, and the exact
  escalation threshold.
- Sanitization and prohibited-action checklist excludes secrets, exception
  payloads, CSV/content, URLs, paths, filenames, writes, live connectors,
  restarts, and broad cleanup.

Canonical suite: `NOT RUN — maintenance-suspended`. No application test
outside the focused documentation contract ran. `refresh-for-test` skipped
per doc-only scope; no application DB command, product DB write, live
connector, or foreign-resource cleanup occurred.

Post-evidence validation registration:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-post-evidence-validation-20260824T203400-0300` | child process / process group | exact OpenSpec validator and git diff-check children created by command below | D08 apply agent | current change id plus exact command registered before launch; no PID or process group adopted | `2026-08-24T20:34:00-03:00` | `2026-08-24T20:34:15-03:00` | exited | owned-cleaned | final dossier after evidence edit valid; diff check clean; no runtime or DB operation | validator and diff-check children exited; no temporary or foreign resource residue |

Pre-launch registration for final validation after preserving Compose's
application envelope:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-final-envelope-20260824T203446-0300` | child process / process group / test DB resource | exact taskipy pytest, OpenSpec, diff-check, static-check, and isolated test DB resources created by commands below | D08 apply agent | current change id plus exact commands registered before launch; no PID, process group, database, or path adopted | `2026-08-24T20:34:46-03:00` | `2026-08-24T20:35:32-03:00` | exited | owned-cleaned | final focused test passed: 1 passed, 1152 deselected; strict change validation valid; diff clean; static checks passed with 2 Python heredocs and 9 shell blocks; no product DB or live service operation | pytest children and validation processes exited; isolated fixture DB cleanup completed; no residue observed; no foreign action |

Final post-evidence validation registration:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-post-envelope-validation-20260824T203540-0300` | child process / process group | exact OpenSpec validator and git diff-check children created by command below | D08 apply agent | current change id plus exact command registered before launch; no PID or process group adopted | `2026-08-24T20:35:40-03:00` | `2026-08-24T20:36:18-03:00` | exited | owned-cleaned | final post-evidence validation valid; diff check clean; no runtime or DB operation | validator and diff-check children exited; no temporary or foreign resource residue |

Pre-launch registration for final coverage inventory validation:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-final-coverage-20260824T203735-0300` | child process / process group / test DB resource | exact taskipy pytest, OpenSpec, diff-check, static-check, and isolated test DB resources created by commands below | D08 apply agent | current change id plus exact commands registered before launch; no PID, process group, database, or path adopted | `2026-08-24T20:37:35-03:00` | `2026-08-24T20:43:29-03:00` | exited | owned-cleaned | final focused test passed: 1 passed, 1152 deselected; OpenSpec valid; diff clean; static checks passed with 2 Python heredocs, 10 shell blocks, and 3 owned paths; no product DB or live service operation | pytest children and validation processes exited; isolated fixture DB cleanup completed; no residue observed; no foreign action |

Post-final-evidence strict validation registration:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-apply-final-post-evidence-20260824T204416-0300` | child process / process group | exact OpenSpec validator and git diff-check children created by command below | D08 apply agent | current change id plus exact command registered before launch; no PID or process group adopted | `2026-08-24T20:44:16-03:00` | `2026-08-24T20:44:34-03:00` | exited | owned-cleaned | final strict change validation valid; final diff check clean; no runtime or DB operation | validator and diff-check children exited; no temporary or foreign resource residue |

## Review Findings

### Review R1
Scope audit: proposal, design, tasks 1.1–4.1, delta requirements/scenarios, runbook source discovery, Compose `web` retrieval, JSON/text extraction, retention/rotation, event shape and allowlists, UUID/duration validation, bounded traces, SQLite correlation, profile FK ownership, lifecycle/status/timestamp mapping, terminal/UI-limit classification, weekly denominators/rates/percentiles, escalation threshold, sanitization, read-only command boundary, T38 scope preservation, changed-path boundary, and PRD §4 constraints: pass except R1-F01 and R1-F02. No area not assessable.

Full suite: `uv run task test` -> `NOT RUN — maintenance-suspended`; canonical six-lane result, coverage/skips, fail-fast disposition, elapsed duration, cleanup duration, and `<=300s` classification do not apply under owner-authorized suspension. Focused product evidence: `uv run task test-integration -- -k myprofit_telemetry_runbook` -> 1 passed, 1152 deselected, exit 0, 5.75s. No test deletion, skip, xfail, retry, masking, or coverage reduction observed.

Preflight: existing D08 per-run ownership ledger was inspected before focused validation. Exact current review command, repository cwd, isolated pytest fixture DB resources, and taskipy child resources were registered by command boundary; classifications: focused child/process resources `owned-current-run` during execution, fixture DB `owned-current-run`, then `owned-cleaned`; no foreign, unknown, contradictory, incomplete, production DB, listener, or declared temporary residue observed. Canonical suite launch was prohibited by `openspec/config.yaml` `canonical_full_suite_gate.status: maintenance-suspended`. Decision: focused runner isolation sufficient; canonical launch not permitted.

Postflight: focused pytest/taskipy children exited; fixture DB cleanup completed; no review process or relevant temporary residue remained. No runtime listener, product DB, foreign resource, or broad cleanup was touched. Exact current-run resources classified `owned-cleaned` or `absent` after completion.

Runner isolation: pass for focused documentation audit; relevant test process and fixture DB were isolated and bounded. Canonical isolated-runner precondition not exercised because suspension forbids canonical launch. No baseline or allowlist exception used.

Verification: `openspec validate d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit --type change --no-interactive` -> valid, exit 0. `rtk git diff --check` -> clean, exit 0. Changed-path audit: D08 dossier plus runbook are present; runtime/T38 files are pre-existing worktree changes and unchanged by D08 review. No roadmap/config/T38 artifact/runtime/schema/test mutation by this review. Static command audit: bounded segment/time/line/UUID limits present; SQLite operation is `-readonly` and `SELECT` only; no inferred joins or DB writes.

Verdict: CHANGES_REQUESTED

#### R1-F01 — Weekly report command violates documented single-week assignment
Status: resolved in Remediation 1/2
Severity: high
Requirement/task: Delta requirement “group accepted events by `job_id`”; scenario “Retained source supports bounded weekly analysis”; task 3.1; runbook §4.1 assignment rule.
Evidence: `docs/runbooks/myprofit-sync-telemetry.md:433-436` requires assigning each job to the week of its earliest accepted timestamp and keeping all events in that week. Executable report at `docs/runbooks/myprofit-sync-telemetry.md:495-498` instead calculates `week` independently for every event, then `docs/runbooks/myprofit-sync-telemetry.md:507-521` inserts each event into that event week. One job spanning UTC Monday is therefore counted in multiple weekly `observed_runs`, groups, terminal/duration/factor measures, contradicting “preventing double-counting across a boundary.”
Required change: in §4.2 command, derive one earliest valid accepted timestamp per `job_id`, assign one Monday bucket per job, and route every event/measure for that job through that bucket. Preserve bounded input, exact UUID grouping, no inferred joins, read-only behavior, percentile method, and all other scope; do not change runtime/T38 code or add persistence.
Acceptance: documentation contract or executable command fixture containing one job with events on both sides of UTC Monday produces one weekly assignment and one observed-run/group count; two jobs in separate weeks remain separately counted. Existing `test_myprofit_telemetry_runbook` remains green.

#### R1-F02 — Weekly factor command counts failed stages without proving failed terminal run
Status: resolved in Remediation 1/2
Severity: high
Requirement/task: Delta requirement “report top `domain/stage/code` factors”; scenario “Retained source supports bounded weekly analysis”; task 3.1; runbook §4.1 items 5 and 10 and §4.3 threshold.
Evidence: `docs/runbooks/myprofit-sync-telemetry.md:458-460` requires factors to use failed terminal runs only, but `docs/runbooks/myprofit-sync-telemetry.md:520-521` adds any `event == "stage" and status == "failed"` to `factors` without checking that same `job_id` has accepted terminal `status=failed`. A failed stage followed by terminal success can be reported as a failed factor, and stage evidence can be counted without terminal failure proof. This can change escalation numerator/threshold interpretation.
Required change: make §4.2 factor aggregation first restrict jobs to accepted terminal events with `status=failed`, then count each eligible job once per normalized `stage/code` cluster. Keep expired, UI-limit, incomplete, and successful jobs outside failed factors; preserve bounded fields, no inferred joins, no runtime/T38 changes, and no DB writes.
Acceptance: documentation command fixture with failed stage → succeeded terminal excludes job from `failed_factor`; failed stage → failed terminal counts job once per cluster; expired/incomplete/UI-limit jobs never enter failed factors. Existing runbook contract remains green.

### Remediation 1/2 — 2026-08-24

#### R1-F01 — resolved

Changed `docs/runbooks/myprofit-sync-telemetry.md` §4.1 and §4.2. Report
command now builds one record per valid `job_id`, selects earliest accepted
timestamp as run anchor, assigns one UTC Monday bucket, and routes every event
and measure through that bucket. No job crossing Monday can create a second
weekly observed/group/duration count. No-terminal jobs remain in anchor week as
`incomplete_runs`; terminal conflicts are reported and excluded; expected runs
without accepted events remain independent `missing_event_count` evidence.

#### R1-F02 — resolved

Changed same report command and §4.2 factor definition. It first restricts
factor eligibility to jobs with exactly one accepted terminal event having
`status=failed`, then accepts only failed stage events for those jobs and
counts each job once per normalized `stage/code`. Failed-stage → succeeded,
expired, incomplete, UI-limit-only, and successful jobs cannot enter
`failed_factor`; denominator is `terminal_failed_runs`.

Changed files/symbols: runbook §4.1 assignment rules and §4.2 bounded report
command; D08 `design.md` implementation decision; this evidence section.
No runtime/T38/spec/schema/DB/test behavior changed.

Pre-launch ownership registration for remediation validation:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-remediation1-focused-20260824T205129-0300` | child process / process group / test DB resource / temporary path | exact taskipy pytest children, isolated integration-test DB resources, OpenSpec/static children, and `/tmp/d08-remediation1-fixture-20260824.tsv` | D08 apply agent, remediation 1/2 | current change id plus exact commands registered before launch; exact fixture path declared and verified absent before launch; no PID, process group, DB, or path adopted | `2026-08-24T20:51:29-03:00` | `2026-08-24T20:53:46-03:00` | exited | owned-cleaned | focused test passed; strict OpenSpec validation passed; `git diff --check` passed; fixture/static audit exited 1 at first output assertion; fixture trap removed exact path; no runtime, production DB, listener, or foreign resource touched | owned child/process-group resources exited; isolated test DB cleaned; exact fixture path removed by bounded trap; no residue |

Post-failure diagnostic ownership registration:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-remediation1-diagnostic-20260824T205400-0300` | child process / temporary path | exact diagnostic Python child and `/tmp/d08-remediation1-fixture-20260824.tsv` | D08 apply agent, remediation 1/2 | current change id plus exact command registered before launch; exact fixture path verified absent before recreation; no PID or path adopted | `2026-08-24T20:54:00-03:00` | `2026-08-24T20:55:12-03:00` | exited | owned-cleaned | report output inspected; first assertion expected wrong fixture distribution (`j1` and `j3` anchor week 2026-07-27, leaving four jobs in 2026-08-03); runbook output and terminal-factor logic behaved as designed | exact fixture path removed by bounded trap; diagnostic child exited; no residue |

Final remediation validation ownership registration:

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `D08-remediation1-final-20260824T205600-0300` | child process / process group / test DB resource / temporary path | exact taskipy pytest children, isolated integration-test DB resources, OpenSpec/static children, and `/tmp/d08-remediation1-fixture-20260824.tsv` | D08 apply agent, remediation 1/2 | current change id plus exact command registered before launch; exact fixture path verified absent before launch; no PID, process group, DB, or path adopted | `2026-08-24T20:56:00-03:00` | `2026-08-24T20:56:16-03:00` | exited | owned-cleaned | focused test passed; strict OpenSpec validation passed; `git diff --check` passed; static audit and executable cross-Monday/terminal-factor fixture passed; no runtime, production DB, listener, or foreign resource touched | owned child/process-group resources exited; isolated test DB cleaned; exact fixture path removed by bounded trap; no residue |

Final remediation evidence:

- `uv run task test-integration -- -k myprofit_telemetry_runbook` at
  `2026-08-24T20:56:06-03:00` -> `1 passed, 1152 deselected`, exit 0,
  5.76s.
- `openspec validate d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit --type change --no-interactive` -> valid, exit 0.
- `git diff --check` -> clean, exit 0.
- Executable fixture -> one job spanning UTC Monday remains in one anchor
  week; failed-stage → succeeded/expired/incomplete/UI-limit jobs produce no
  failed factor; one eligible failed job produces one factor; exit 0.
- Static audit -> report AST parses; anchor/terminal-failed guards present;
  bounded read-only shell commands preserved; exit 0.
- Canonical suite -> `NOT RUN — maintenance-suspended`.

### Review R2 — remediation 1/2
Scope audit: pass. Rechecked complete D08 dossier, all tasks, delta requirement/scenarios, updated §4.1 assignment rules, §4.2 executable report, §4.3 escalation formula, incomplete/no-terminal handling, terminal conflict handling, factor attribution, bounded source extraction, sanitization, SQLite correlation, T38 telemetry/logging/model/import boundaries, no-mutation constraints, and changed-file scope. No area not assessable.

R1-F01: resolved. `docs/runbooks/myprofit-sync-telemetry.md:433-443` defines one earliest accepted timestamp anchor per valid `job_id`, one UTC Monday bucket, and keeps no-terminal jobs in anchor week as `incomplete_runs`; expected runs without accepted events remain independent `missing_event_count`. The report implementation at `docs/runbooks/myprofit-sync-telemetry.md:511-555` builds per-job records, computes anchor bucket once, routes all events/measures through that bucket, and excludes terminal conflicts from terminal arithmetic. Cross-Monday fixture evidence in D08 tasks confirms one job remains one weekly observed/group/duration assignment.

R1-F02: resolved. `docs/runbooks/myprofit-sync-telemetry.md:460-472` defines `terminal_failed_runs` as unique jobs with exactly one accepted terminal `status=failed`, and restricts factors to failed stage events belonging to that set. Implementation at `docs/runbooks/myprofit-sync-telemetry.md:539-554` excludes no-terminal, conflicting-terminal, succeeded, expired, UI-limit-only, and failed-stage→succeeded jobs; each eligible job enters each normalized `stage/code` factor once. Factor fixture evidence confirms one eligible failed job yields one factor and excluded outcomes yield none.

Full suite: `uv run task test` -> `NOT RUN — maintenance-suspended`; canonical six-lane result, coverage/skips, fail-fast disposition, elapsed duration, cleanup duration, and `<=300s` classification do not apply. Focused product evidence: `uv run task test-integration -- -k myprofit_telemetry_runbook` -> 1 passed, 1152 deselected, exit 0, 5.68s. Remediation fixture/static evidence: cross-Monday and terminal-factor fixture exit 0; AST/static safety audit exit 0. No test deletion, skip, xfail, retry, masking, or coverage reduction.

Preflight: inspected remediation ledger `D08-remediation1-final-20260824T205600-0300` before review. Ledger fields identify exact taskipy pytest/OpenSpec/static child resources, isolated test DB, and exact fixture path; owner evidence is current D08 change plus registered exact commands/path, with no adoption. Classifications: remediation child/process/test-DB/fixture resources `owned-current-run` during execution and `owned-cleaned` after; no foreign, unknown, contradictory, incomplete, production DB, listener, or unowned declared-boundary resource observed. `openspec/config.yaml` confirms canonical gate `maintenance-suspended`; canonical launch prohibited. Decision: focused runner isolation trusted; no canonical suite launched.

Postflight: remediation child/process resources exited; isolated test DB and exact fixture path were cleaned; no review residue remained. No runtime listener, product DB, T38 resource, foreign resource, broad cleanup, or runtime restart occurred. Postflight classifications in remediation ledger are `owned-cleaned`/`absent`.

Runner isolation: pass for focused documentation validation. Relevant process, test DB, and declared fixture path had exact owner evidence and bounded cleanup. Canonical isolated-runner precondition not exercised because suspension forbids canonical launch. No baseline or allowlist exception used.

Verification: `openspec validate d08-runbook-operacional-para-consulta-e-analise-da-telemetria-myprofit --type change --no-interactive` -> valid, exit 0. `rtk git diff --check` -> clean, exit 0. Updated report AST/static audit passes; shell commands retain explicit time/segment/line/UUID bounds; SQLite remains `-readonly` with `SELECT` only; no inferred joins, DB writes, runtime changes, T38 mutation, schema/config/test/roadmap edits, or sanitization breach found.

Verdict: APPROVED

#### R1-F01 — Weekly report command violates documented single-week assignment
Status: resolved in Remediation 1/2

#### R1-F02 — Weekly factor command counts failed stages without proving failed terminal run
Status: resolved in Remediation 1/2
