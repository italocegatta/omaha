## Test strategy

Measurement is not executed at proposal gate. After owner authorizes Apply,
use existing offline/integration boundaries only:

- **Owner scope decision (2026-08-24):** exactly 15 fake/mock connector
  repetitions per bounded measurement run. Decision aligns workload with owner
  instruction; it does not provide a measurement result or external-service
  performance claim.

- **Test file:** `tests/test_myprofit_sync_jobs.py` for one explicitly named
  T36 harness scenario; existing `tests/test_myprofit_connector.py` and
  `tests/e2e/test_patrimonio_sync_action.py` remain behavioral/boundary oracles.
- **Test state:** pytest-provided temporary DB plus `tmp_path`; fake connector;
  no credentials, network, Playwright launch, production DB, destructive reset,
  or import commit.
- **Focused command:** `uv run task test-one tests/test_myprofit_sync_jobs.py::test_t36_sync_duration_measurement`.
- **Safety preflight command:** `uv run task test-file tests/test_myprofit_sync_jobs.py`.
- **Quality command:** `uv run task lint`.
- **Canonical suite:** not run at this proposal gate. Under current
  `maintenance-suspended` policy, later review records
  `NOT RUN — maintenance-suspended`; focused product evidence remains required.
- **Evidence location:** this file, under `## Execution evidence`, as one
  JSON block per bounded measurement run plus command/result/oracle notes. No
  measurement output is added now.

## Tasks

- [x] 1.1 **Freeze boundary and working-tree ownership.** Target: this change
  dossier plus symbols listed in `design.md`; exact change: record current
  values for polling, TTL/expiry, retention, connector stage timeouts, and E2E
  waits without editing runtime code. Preserve: pre-existing
  `tests/visual/artifacts/f60-atualizar-posicao-*.png` changes and all
  D06/F65/F59/F60 behavior. Acceptance: dossier table distinguishes every
  timeout family and identifies no runtime timeout change. Test file/scenario:
  `tests/test_myprofit_sync_jobs.py` existing expiry/sanitization scenarios as
  safety oracle. Focused taskipy command: `uv run task test-one tests/test_myprofit_sync_jobs.py::test_status_serializer_is_sanitized`.
  Independent oracle: `git diff HEAD~1`, `git status --short --untracked-files=all`,
  and `git diff --check` show no unowned runtime edits or whitespace errors.

- [x] 2.1 **Add bounded fake measurement harness.** Target:
  `tests/test_myprofit_sync_jobs.py`, new named
  `test_t36_sync_duration_measurement`; exact change: inject fake
  `MyProfitConnector`, run exactly 15 fake/mock connector repetitions through
  `MyProfitSyncService`, use temporary DB/path state, capture monotonic and
  persisted durations, reconcile success/failure classes, and assert portfolio
  counts unchanged. Preserve: existing fixture cleanup, profile isolation,
  expiry precedence, sanitized errors, owned-path cleanup, and no commit.
  Acceptance: test is repeatable, bounded, offline, finite, and fails on
  unclassified result, mutation, leaked temp path, or wrong terminal state.
  Test file/scenario: named T36 scenario with valid fake CSV plus injected
  allowlisted connector failures. Focused taskipy command: `uv run task test-one tests/test_myprofit_sync_jobs.py::test_t36_sync_duration_measurement`.
  Independent oracle: test output reports exactly `15` attempts and before /
  after `Asset`, `Position`, `DbMutation` counts match.

- [x] 2.2 **Compute and persist measurement evidence.** Target: harness output
  and `tasks.md` `## Execution evidence`; exact change: calculate mean, p50,
  p95, p99, min/max, sample stdev, IQR, MAD, failure count/rate/statuses,
  current boundaries, and stage-timeout inventory; append schema-conformant
  JSON with run stamp and environment metadata. Preserve: raw sanitized stage /
  code only, no credentials, CSV bytes, paths, or exception text. Acceptance:
  `n=15` repetitions, successful and failed outcomes reconcile to 15, every failure is
  classified, no external access, and evidence contains every required metric
  and separate boundary values. A run with no successful sample remains
  `insufficient-evidence`; no result is claimed at proposal gate.
  Test file/scenario: same named T36 measurement scenario. Focused taskipy
  command: `uv run task test-one tests/test_myprofit_sync_jobs.py::test_t36_sync_duration_measurement`.
  Independent oracle: JSON key/schema audit against `design.md`; success plus
  failure counts equal 15 and every duration is finite/non-negative.

- [x] 2.3 **Apply decision rule without implementing F68.** Target: evidence
  JSON and `tasks.md`; exact change: calculate
  `ceil_to_5s(p99 + max(2*IQR, 5000ms))`, compare to nominal 60,000 ms polling
  boundary and 3,600,000 ms job/preview TTL, then record exactly
  `covered`, `increase-justified`, or `insufficient-evidence`. Preserve: no
  `pollDelay`, `maxPolls`, TTL, Playwright timeout, status, copy, or retry
  change. Acceptance: candidate is null on insufficient evidence; otherwise
  candidate is bounded below both TTLs and is explicitly handed to F68 as a
  target, not applied. The decision input remains exactly 15 fake/mock
  connector repetitions. Test file/scenario: synthetic schedule includes normal,
  slow, and declared failure outcomes. Focused taskipy command: `uv run task test-one tests/test_myprofit_sync_jobs.py::test_t36_sync_duration_measurement`.
  Independent oracle: manually recompute candidate from recorded p99/IQR and
  confirm decision matches comparison table.

- [x] 3.1 **Run focused regression and quality validation.** Target:
  `tests/test_myprofit_sync_jobs.py`, `tests/test_myprofit_connector.py`,
  `tests/e2e/test_patrimonio_sync_action.py`, stable specs, and change dossier;
  exact change: execute applicable focused checks and inspect changed-file
  boundary, without measurement reruns beyond named harness command. Preserve:
  all existing tests, skips, markers, browser oracles, and maintenance policy.
  Acceptance: focused tests/lint pass; stable specs remain unchanged and
  healthy; no production/runtime file changed. Test file/scenario: job
  lifecycle, connector timeout inventory, and intercepted browser handoff.
  Focused taskipy command: `uv run task lint` followed by
  `uv run task test-file tests/test_myprofit_sync_jobs.py`.
  Independent oracle: `openspec validate --change t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao`, stable-spec health command,
  `git diff --check`, and exact changed-file allow-list.

## Acceptance evidence

Proposal gate acceptance requires all of these before status becomes
`Spec Proposed`:

- exact change id and folder match roadmap T36;
- `proposal.md`, `design.md`, and `tasks.md` exist; applicable delta spec is
  limited to internal `sync-duration-measurement` test/observability contract;
- design contains code map, current flow, decisions, change map, risks,
  boundaries, metric formula, evidence location, and F68 handoff;
- tasks contain executable targets, preserved behavior, test scenarios,
  taskipy commands, independent oracles, exact 15-repetition acceptance, and
  explicit no-measurement-yet boundary;
- validation passes for exact change and stable spec health;
- no implementation, runtime timeout, measurement run, review, archive,
  commit, push, or unrelated file edit occurs at this gate.

## Execution evidence

### Task completion receipt — 2026-08-24

- **1.1:** changed `design.md` implementation decisions and this dossier only;
  inspected `imports.py`, `_patrimonio_add_asset_modal.html`, `models.py`,
  `connector.py`, `config.py`, sync/E2E tests, `tests/PERFORMANCE.md`, and
  `openspec/config.yaml`. Recorded distinct polling, TTL, connector-stage, and
  browser-harness boundaries. No production/runtime file changed.
- **2.1:** changed `tests/test_myprofit_sync_jobs.py` symbols
  `_t36_percentile`, `_t36_metrics`, and
  `test_t36_sync_duration_measurement`. Fresh service injected fake connector,
  fixture-safe `SessionLocal`, and owned `tmp_path`; exactly 15 scheduled
  attempts passed through `start()` and `run_myprofit_sync_job()`.
- **2.2:** same named scenario computed inclusive linear percentile metrics,
  sample stdev, IQR, MAD, sanitized failure classes, raw attempt durations, and
  printed machine-readable receipt. This section persists receipt below; no
  credentials, CSV bytes, exception text, or runtime config are recorded.
- **2.3:** candidate formula recomputed from receipt as
  `ceil_to_5s(63.622 + max(2 × 9.177, 5000)) = 10000 ms`; comparison is
  `10000 <= 60000`, therefore `covered`. No F68/runtime timeout edit.

### Accepted bounded measurement run

Command: `uv run task test-one tests/test_myprofit_sync_jobs.py::test_t36_sync_duration_measurement -s`

Result: `1 passed in 1.05s`; fake connector calls `15`; successes `12`;
failures `3`; all terminal outcomes classified; portfolio counts unchanged;
owned temp child absent after bounded cleanup. The earlier same-node command
without `-s` also passed in `1.09s` with 15 attempts; it is recorded as a
focused harness preflight, not combined with this receipt. No run used more
than 15 attempts.

```json
{
  "change_id": "t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao",
  "run_id": "20260824T130913Z",
  "environment": {
    "python": "3.12.13",
    "platform": "Linux-6.6.114.1-microsoft-standard-WSL2-x86_64-with-glibc2.43",
    "pytest": "9.1.1"
  },
  "sample_size": 15,
  "successes": 12,
  "failures": 3,
  "failure_rate": 0.2,
  "percentile_method": "inclusive linear interpolation over successful samples",
  "attempts": [
    {"attempt": 1, "outcome": "success", "duration_ms": 20.288, "persisted_duration_ms": 9.755, "terminal_status": "succeeded"},
    {"attempt": 2, "outcome": "success", "duration_ms": 12.424, "persisted_duration_ms": 7.663, "terminal_status": "succeeded"},
    {"attempt": 3, "outcome": "success", "duration_ms": 12.731, "persisted_duration_ms": 8.581, "terminal_status": "succeeded"},
    {"attempt": 4, "outcome": "success", "duration_ms": 13.428, "persisted_duration_ms": 9.546, "terminal_status": "succeeded"},
    {"attempt": 5, "outcome": "failure", "duration_ms": 12.535, "persisted_duration_ms": 7.935, "terminal_status": "failed", "stage": "download", "code": "timeout"},
    {"attempt": 6, "outcome": "success", "duration_ms": 16.894, "persisted_duration_ms": 12.525, "terminal_status": "succeeded"},
    {"attempt": 7, "outcome": "success", "duration_ms": 19.195, "persisted_duration_ms": 14.793, "terminal_status": "succeeded"},
    {"attempt": 8, "outcome": "success", "duration_ms": 21.682, "persisted_duration_ms": 16.631, "terminal_status": "succeeded"},
    {"attempt": 9, "outcome": "success", "duration_ms": 24.742, "persisted_duration_ms": 19.958, "terminal_status": "succeeded"},
    {"attempt": 10, "outcome": "failure", "duration_ms": 26.538, "persisted_duration_ms": 21.99, "terminal_status": "failed", "stage": "login", "code": "failed"},
    {"attempt": 11, "outcome": "success", "duration_ms": 43.543, "persisted_duration_ms": 38.167, "terminal_status": "succeeded"},
    {"attempt": 12, "outcome": "success", "duration_ms": 66.104, "persisted_duration_ms": 59.147, "terminal_status": "succeeded"},
    {"attempt": 13, "outcome": "success", "duration_ms": 14.869, "persisted_duration_ms": 7.856, "terminal_status": "succeeded"},
    {"attempt": 14, "outcome": "success", "duration_ms": 12.796, "persisted_duration_ms": 8.507, "terminal_status": "succeeded"},
    {"attempt": 15, "outcome": "failure", "duration_ms": 12.059, "persisted_duration_ms": 7.905, "terminal_status": "failed", "stage": "browser", "code": "browser_failed"}
  ],
  "success_duration_ms": {
    "mean": 23.225,
    "p50": 18.045,
    "p95": 53.695,
    "p99": 63.622,
    "min": 12.424,
    "max": 66.104,
    "stdev": 16.018,
    "iqr": 9.177,
    "mad": 4.933
  },
  "failure_statuses": {
    "failed|browser|browser_failed": 1,
    "failed|download|timeout": 1,
    "failed|login|failed": 1
  },
  "boundaries_ms": {
    "poll_delay": 500,
    "max_polls": 120,
    "poll_delay_x_max_polls": 60000,
    "job_expiry": 3600000,
    "preview_ttl": 3600000,
    "terminal_retention": 3600000
  },
  "playwright_stage_timeouts_ms": {
    "navigation": 45000,
    "login_settle": 5000,
    "two_factor_probe": 30000,
    "export_button": 30000,
    "csv_option": 10000,
    "download": 45000
  },
  "playwright_harness_timeouts_ms": {
    "local_success_state": 3000,
    "sync_terminal_state": 8000,
    "sync_review_modal": 2000,
    "import_review": 15000,
    "import_review_table": 5000
  },
  "portfolio_counts_before": {"Asset": 0, "Position": 0, "DbMutation": 0},
  "portfolio_counts_after": {"Asset": 0, "Position": 0, "DbMutation": 0},
  "candidate_timeout_ms": 10000,
  "decision": "covered",
  "recommendation": "F68 change not justified; current nominal polling boundary covers candidate.",
  "limitation": "15 deterministic fake samples describe application-boundary overhead only; they do not establish MyProfit network performance or an external SLA."
}
```

### Focused validation and spec evidence

- `uv run task test-one tests/test_myprofit_sync_jobs.py::test_status_serializer_is_sanitized`
  -> pass (preflight oracle).
- `uv run task test-file tests/test_myprofit_sync_jobs.py -k "not t36_sync_duration_measurement"`
  -> pass; 19 existing sync lifecycle tests passed, measurement was excluded
  only to avoid a third 15-attempt run.
- `uv run task test-file tests/test_myprofit_connector.py` -> pass; connector
  timeout inventory and sanitized error oracles remain green.
- `uv run task lint` -> pass.
- `openspec validate --change t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao`
  -> command rejected (`unknown option --change`); no repository resource was
  touched. Corrected command:
  `openspec validate t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao --type change --no-interactive`
  -> pass; active dossier/delta valid.
- `openspec validate --specs --no-interactive` -> 77 passed, 0 failed.
- Stable product specs unchanged; no runtime/template/model/connector file
  changed. `git diff --check` -> pass.

### Ownership ledger receipt

Run owner: `t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao` /
apply agent. Registration occurred before each command through the wrapper's
`T36_OWNER_REGISTERED` line with run id, PID, PGID, and UTC start timestamp.

| resource_kind | resource_id | owner / owner_evidence | started_at / ended_at | status / classification | evidence / cleanup_result |
|---|---|---|---|---|---|
| child process | PID/PGID `101164/101164` | `t36-apply-20260824T130830Z`; wrapper registration before `exec` | `2026-08-24T13:08:43Z` / process exited before receipt | exited / owned-cleaned | first 15-attempt harness preflight passed; no descendant residue observed; no cleanup needed |
| child process | PID/PGID `101235/101235` | `t36-measurement-20260824T130903Z`; wrapper registration before `exec` | `2026-08-24T13:09:10Z` / process exited before receipt | exited / owned-cleaned | accepted measurement passed; no descendant residue observed; no cleanup needed |
| child process | PID/PGID `101541/101541` | `t36-status-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:14:38Z` / command return | exited / owned-cleaned | status serializer oracle: 1 passed; no descendant residue; no cleanup needed |
| child process | PID/PGID `101586/101586` | `t36-sync-regression-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:14:49Z` / command return | exited / owned-cleaned | 19 sync lifecycle tests passed, 1 deliberate selection deselection; no descendant residue; no cleanup needed |
| child process | PID/PGID `101641/101641` | `t36-connector-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:15:01Z` / command return | exited / owned-cleaned | connector inventory: 30 passed; no browser/network launch; no cleanup needed |
| child process | PID/PGID `101678/101678` | `t36-lint-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:15:11Z` / command return | exited / owned-cleaned | first lint exposed one E501 and hook formatting; fixed exact T36 test line; no residue |
| child process | PID/PGID `102915/102915` | `t36-lint-rerun-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:15:47Z` / command return | exited / owned-cleaned | lint all hooks passed; no residue; no cleanup needed |
| child process | PID/PGID `103947/103947` | `t36-spec-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:16:15Z` / command return | exited / owned-cleaned | invalid `--change` option detected before validation; no DB/path/process residue |
| child process | PID/PGID unavailable | `openspec validate --help` ran outside wrapper; command owner is current apply agent but pre-registration was not emitted | command return / command return | exited / unknown | help-only process ended with no residue; no cleanup/adoption attempted; procedural gap retained for review |
| child process | PID/PGID `104012/104012` | `t36-spec-correct-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:16:29Z` / command return | exited / owned-cleaned | exact change valid; no residue; no cleanup needed |
| child process | PID/PGID `104051/104051` | `t36-stable-specs-20260824T131500Z`; wrapper registration before `exec` | `2026-08-24T13:16:37Z` / command return | exited / owned-cleaned | 77 stable specs passed; no residue; no cleanup needed |
| child process | PID/PGID `104223/104223` | `t36-final-validate-20260824T131700Z`; wrapper registration before commands | `2026-08-24T13:17:48Z` / command return | exited / owned-cleaned | final exact change validation passed and `git diff --check` passed; no residue |
| child process | PID/PGID `104376/104376` | `t36-final-boundary-20260824T131800Z`; wrapper registration before commands | `2026-08-24T13:18:15Z` / command return | exited / owned-cleaned | final worktree/diff boundary inspected; no cleanup needed |
| test DB resource | `/tmp/omaha-conftest-safe-iqenk2sv/portfolio.db` | `T29_DB_TARGET` emitted by current integration lane after safe bootstrap; run-owned temp DB | `2026-08-24T13:09:10Z` / `2026-08-24T13:21:35Z` | cleanup-attempted / owned-cleaned | exact run-owned temp SQLite removed with bounded parent cleanup; observed exists=true, result exists=false; no `data/portfolio.db` access |
| temporary path | `/tmp/pytest-of-juca/pytest-48/test_t36_sync_duration_measurecurrent/t36-myprofit-sync` | test-created `tmp_path` child; exact path observed under current run receipt | `2026-08-24T13:09:10Z` / `2026-08-24T13:12:51Z` | cleanup-attempted / owned-cleaned | exact bounded `shutil.rmtree`; observed exists=true, result exists=false |
| temporary path | `/tmp/pytest-of-juca/pytest-48/test_t36_sync_duration_measure0/t36-myprofit-sync` | first run's test-created child; exact prior-run identity | `2026-08-24T13:08:43Z` / `2026-08-24T13:13:09Z` | absent / absent | cleanup attempt observed exists=false; idempotent no-op; no adoption or broad deletion |
| temporary path | `/tmp/pytest-of-juca/pytest-48/test_t36_sync_duration_measurecurrent` | pytest runner parent, not T36-owned cleanup target | runner-managed / runner-managed | preserved / pre-existing | parent and unrelated runner state preserved; no discovery or broad cleanup |

The failed initial `python -c` cleanup command returned `python: command not
found`; it did not touch resources. Retried with `uv run python` against exact
current-run path only and recorded bounded result above. No process kill,
listener cleanup, production DB mutation, destructive reset, credential load,
network access, or foreign-resource action occurred.

The first same-node harness preflight used pytest capture, so its separate
conftest temporary DB identity was not emitted into the durable receipt. It was
not adopted or discovered by broad path search; accepted measurement run used
the exact `T29_DB_TARGET` above and was cleaned. Review SHALL use an isolated
runner and stop if preflight finds any relevant residue from that earlier
unregistered preflight.

### Canonical review isolation

Preflight relevant process/listener inventory: no owned or unowned Omaha
listener launched; measurement used no server process, browser, network, or
external connector. Relevant test DB was exact run-created safe SQLite path and
was not production. Current-run owned measurement child was cleaned; prior
pytest parent state is preserved/non-target. No baseline exception or literal
allowlist was used. Canonical `uv run task test` remains `NOT RUN —
maintenance-suspended`; review must perform its own isolated preflight.

## Review Findings

### Review R1

Scope audit: proposal **pass**; design **pass**; tasks 1.1–3.1 **pass**;
delta requirements/scenarios **pass**; exact 15-attempt harness **pass**;
12 successes plus 3 classified failures **pass**; metric schema and
reconciliation **pass**; polling/TTL/retention boundaries **pass**; separate
Playwright stage and harness boundaries **pass**; candidate formula and F68
handoff **pass**; focused product behavior **pass**; stable specs **pass**;
changed-symbol and preserved-invariant audit **pass**; no external network or
credentials **pass**; no production DB or fixed E2E DB mutation **pass**; no
listener/process adoption **pass**; no runtime/model/template/connector
behavior change **pass**; no test deletion, skip, xfail, retry, lane, or
coverage contamination **pass**; working-tree boundary **pass** with roadmap
and four F60 visual artifacts recorded as pre-existing/non-target.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**. Policy
receipt from `openspec/config.yaml:87-99` and PRD §4.13 permits no canonical
launch during owner-authorized suspension. Six lanes (unit, integration, audit
integration, e2e, bdd, visual): not run under suspension; no canonical
coverage/tests/skips/fail-fast/elapsed receipt claimed. Focused receipt remains
mandatory and is green: measurement `1 passed`; sync lifecycle `19 passed`
(measurement intentionally excluded from this regression command); connector
`30 passed`; lint passed. No canonical duration classification applies.

Preflight: ledger `t36-review-r1-20260824T000000Z` inspected
`resource_kind`, `resource_id`, `owner`, `owner_evidence`, `started_at`,
`ended_at`, `status`, `classification`, `evidence`, and `cleanup_result`.
Exact declared lane listeners `8765–8768`: **absent**. Exact fixed E2E DBs
`data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, and
`data/test_visual.db`: **absent**. Current T36 temp paths from apply receipt:
**absent**. Omaha server PID/PGID on port 8000 and `data/portfolio.db` were
classified **pre-existing/non-target**, preserved, and not adopted; they are
outside review-run ownership. No relevant foreign/unknown declared suite
resource remained. Runner isolation: **pass** for focused audit; no suite
launch authorized.

Postflight: review launched no suite, browser, listener, or DB writer.
Focused command processes exited; no current-run child residue. Repeated exact
declared listener/DB/temp inventory remained absent; product server and product
DB remained preserved/non-target. Cleanup: **not applicable**, no broad or
foreign cleanup performed. Postflight decision: **pass**.

Statistical limitation: 15 deterministic fake attempts support **descriptive**
reporting of this run, including p95/p99 under documented inclusive linear
interpolation over 12 successful samples. They do not support an external
service percentile, confidence claim, or SLA; p99 is effectively an upper-tail
description of this small sample. Existing limitation at `tasks.md:224` is
adequate. Recommendation: F68 must require separate owner-approved real-service
evidence before any future timeout increase; do not add samples or alter
owner-approved `n=15` in T36.

Evidence audit: receipt `tasks.md:149-225` reconciles `sample_size=15`,
`successes=12`, `failures=3`, failure rate `0.2`, three allowlisted
`failed|stage|code` classes, finite attempt durations, unchanged
`Asset`/`Position`/`DbMutation` counts, and owned-temp cleanup. Boundary audit
matches `500 ms × 120 = 60,000 ms`, job expiry/preview TTL/retention
`3,600,000 ms`, and independent Playwright stage values. Recalculation:
`ceil_5s(63.622 + max(2 × 9.177, 5,000)) = 10,000 ms`; `10,000 <= 60,000`.

OpenSpec validation: exact change validation **pass**; stable spec health
`77 passed, 0 failed`; `git diff --check` **pass**. No runtime files changed;
the only implementation diff is test-only T36 measurement code in
`tests/test_myprofit_sync_jobs.py:33-63,572-766`.

F68 handoff: explicit `covered` decision and recommendation at
`tasks.md:221-224`; roadmap handoff at `openspec/roadmap.md:692` says offline
evidence does **not** justify increase. F68 remains pending and must not change
polling, job/preview TTL, status, failure handling, retry behavior, or
connector timeout based on T36 alone.

Verdict: **APPROVED**

Findings: none. No `R1-Fxx` findings open.
