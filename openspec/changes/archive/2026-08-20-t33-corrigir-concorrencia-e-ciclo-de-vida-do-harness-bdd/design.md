## Context

T33 is follow-up to closed/deferred T32, not a reopening of T32 policy. T32
Review R3 recorded:

- canonical `uv run task test` exit 0 in 244.36 seconds with clean children and
  reconciled population;
- isolated exact BDD target passed;
- `uv run task test-t32-expanded` passed its 12 selected visual cases with 8
  deselections;
- the required BDD check, run while the expanded lane was concurrent, failed
  47/51 cases in 131.43 seconds, mostly at `Page.goto(.../login)` with
  `net::ERR_CONNECTION_REFUSED` on port 8766;
- T32 explicitly forbids adding retries/masking, changing lane membership,
  reducing coverage, or changing server behavior inside its remediation.

Current architecture is session-scoped BDD uvicorn plus per-scenario DB cleanup
and browser contexts. `test-bdd` is serial, while `test-t32-expanded` starts a
separate visual task and a selected unit pytest process. Port 8766 is intended to
be BDD-owned; 8765, 8767, and 8768 are other browser/full-suite assignments.

## Code Map

| File | Symbols / locations | Role in current flow |
|---|---|---|
| `pyproject.toml` | `[tool.taskipy.tasks]::test-bdd`, `test-t32-expanded`, `test` | Canonical isolated BDD, expanded governance, and full-suite entrypoints. |
| `tests/bdd/conftest.py` | `BDD_PORT`, `TEST_BASE_URL`, `live_url`, `clean_seeded_profiles` | Owns BDD DB path, port 8766, session server fixture, and per-scenario profile wipe. Re-exports browser and steps. |
| `tests/support/server.py` | `run_test_server` | Spawns uvicorn, composes test environment, waits for a TCP port, yields URL, and delegates shutdown. |
| `tests/support/browser.py` | `port_is_free`, `wait_for_port`, `uvicorn_log_file`, `read_log_tail`, `shutdown_uvicorn`, `HarnessPage` | Implements socket readiness, uvicorn diagnostics/teardown, and narrow same-URL navigation handling. |
| `tests/e2e/conftest.py` | `_browser_scope`, `live_url`, `live_url_short_ttl`, `_browser`, `browser_context`, `page` | Supplies browser fixtures re-exported by BDD and owns neighboring ports 8765/8767. |
| `tests/conftest.py` | `_INTEGRATION_PREFIXES`, `_UNIT_FILES`, `pytest_collection_modifyitems` | Explicit marker/governance allow-lists. Must not become heuristic or silently change lane classification. |
| `tests/bdd/step_defs/_workflows.py` | `login_and_land`, `create_one_class`, `add_one_asset` | Browser input/output boundaries where refusal is observed; D8 class-save completion waits must remain intact. |
| `tests/scripts/test_t29_harness.py` | existing runner/receipt/governance contract tests | Existing unit-owned harness oracle; location for focused T33 lifecycle/concurrency contracts without adding a new marker decision. |
| `scripts/run_full_suite.py` | `PORTS`, `LANES`, `_preflight`, `_stop`, `_reap`, `main` | Canonical runner's port preflight, lane process groups, failure propagation, and cleanup. Inspect/change only if controlled evidence attributes refusal to runner interference. |
| `scripts/run_expanded_lane.py` | `main` | Expanded T32 visual/unit subprocess boundary. It does not intentionally own port 8766; inspect only to confirm that invariant. |

## Current Relevant Flow

1. `uv run task test-bdd` invokes pytest against `tests/bdd` without coverage.
2. First BDD scenario requests session fixture `live_url`.
3. `live_url` deletes `data/test_bdd.db`, calls `run_test_server`, and starts
   `python -m uvicorn omaha.main:app --host 127.0.0.1 --port 8766` with the BDD
   DB and test secrets.
4. `run_test_server` waits for any TCP connection accepted on 8766, then yields
   `http://127.0.0.1:8766`; it does not currently record a readiness-time child
   PID/ownership assertion beyond the socket probe.
5. BDD imports browser fixtures from e2e. Under lane receipt `bdd`, one browser
   process is reused, each scenario gets a fresh context/page, and
   `clean_seeded_profiles` wipes both seeded profiles before workflow execution.
6. `login_and_land` first navigates to `/login`; later workflows submit API
   requests and wait for server-confirmed response/DOM completion. A dead or
   unavailable 8766 server surfaces as Playwright `ERR_CONNECTION_REFUSED` at
   these navigation boundaries, before business assertions run.
7. Session teardown delegates to `shutdown_uvicorn`, which terminates/kills the
   child, checks whether the port remains bound, closes the log, and reports
   abnormal return codes.
8. Concurrent `test-t32-expanded` runs its own visual and selected-unit
   subprocesses. It should not own 8766. Current evidence proves correlation
   with concurrency, not causation; startup ownership, child death, runner
   signals, DB lock, and host pressure remain distinguishable hypotheses.

Boundary conditions to preserve: BDD remains serial; 8766 remains BDD-owned;
8765/8767/8768 remain distinct; test DBs remain lane-owned; startup failure must
fail loudly; teardown must reap children; same-URL navigation guard and D8's
rendered-row completion boundary are not reworked; T32's 12 versioned cases,
marker, selection, skips, checksums, and population policy remain untouched.

## Goals / Non-Goals

**Goals:**

- Produce an evidence-backed root-cause classification for the refusal.
- Make the confirmed server/port/lane lifecycle invariant executable through
  focused tests before applying a fix.
- Correct only the proven lifecycle boundary and make failure observable.
- Make both isolated BDD and BDD concurrent with expanded execution deterministic.
- Retain full-suite reconciliation and the <=300-second hard ceiling.

**Non-Goals:**

- No product/runtime application changes.
- No changes to BDD scenarios, workflow assertions, D8 navigation behavior,
  browser retry policy, or test coverage/pruning policy.
- No new skip, xfail, deselection, lane removal, population refresh, or
  coverage claim.
- No replacement of concurrent expanded execution with an unrequested blanket
  serialization workaround.
- No archive, roadmap edit, T32 artifact edit, commit, or push.

## Evidence-Based Diagnosis Plan

### Working hypothesis H1 — readiness/ownership gap around the session BDD server

- **Symptoms:** 47 BDD failures, 4 passes, predominantly connection refusal at
  8766; isolated exact target passes; refusal occurs after a session startup
  boundary rather than as a domain assertion failure.
- **Reproducible conditions:** launch `uv run task test-bdd` while
  `uv run task test-t32-expanded` is active, with a fresh BDD DB and no stale
  browser/server processes.
- **Observability:** timestamp first refusal; sample BDD child PID and
  `poll()`/return code; probe 8766; record the owning process; correlate with
  `tmp/uvicorn-logs` tail and BDD DB/WAL state; retain both task receipts.
- **Falsification condition:** the BDD child remains alive, its log shows no
  exit/restart, the same child owns/listens on 8766 through the first refusal,
  and the refusal reproduces with a healthy socket. Then H1 is rejected and no
  readiness/ownership fix is authorized.
- **Minimum correction scope if confirmed:** `run_test_server` and/or its
  socket/process lifecycle primitives, plus focused contract tests. Do not add
  browser retries or alter workflows.

### H2 — runner/process-group interference

- **Symptoms:** refusal aligns with a sibling process termination or signal,
  not with uvicorn startup or DB activity.
- **Reproducible conditions:** only when a parent runner manages BDD and another
  lane; isolated BDD and direct concurrent task pair differ.
- **Observability:** child process-group IDs, signal/return-code timeline,
  `run_full_suite.py` `_stop`/`_reap` events, and lane receipts.
- **Falsification condition:** no signal or process-group overlap reaches the BDD
  child during the first refusal. Then runner changes are out of scope.
- **Minimum correction scope if confirmed:** runner lifecycle/ownership code and
  its focused unit contract only; preserve lane set, selection, and receipts.

### H3 — shared host/DB resource pressure causes server unavailability

- **Symptoms:** BDD child remains nominally present but stops accepting
  connections, with correlated CPU/process/file-descriptor pressure or SQLite
  lock evidence.
- **Reproducible conditions:** concurrent expanded lane reproduces failure;
  isolated BDD does not; pressure metrics coincide with first refusal.
- **Observability:** socket probes, child logs, process counts, DB lock/WAL
  state, and timing around `clean_seeded_profiles`.
- **Falsification condition:** no pressure/lock event and no server accept gap
  at refusal. Then resource-pressure remediation is rejected.
- **Minimum correction scope if confirmed:** the smallest proven isolation or
  cleanup boundary in `tests/support/server.py`, `tests/support/browser.py`, or
  BDD cleanup; no blanket serialization and no coverage reduction.

Diagnosis selects one hypothesis only when its evidence passes and alternatives
are falsified. If evidence remains ambiguous, Apply stops with
`BLOCKED_FOR_IMPLEMENTATION_BRIEF` rather than trial-and-error patches.

## Decisions

### D1. Reproduce before editing

The first implementation tasks capture isolated and concurrent receipts and
diagnostics. No correction is chosen from the historical `ERR_CONNECTION_REFUSED`
string alone. This prevents conflating the earlier T32 same-URL `ERR_ABORTED`
fix with this server/port failure.

### D2. Test the invariant before the fix

Focused tests extend `tests/scripts/test_t29_harness.py`, which is already in
the explicit unit allow-list. Tests model the confirmed boundary with controlled
subprocess/socket doubles or deterministic lifecycle fixtures. They must prove
child readiness/ownership, refusal visibility, teardown/reaping, or the exact
runner invariant selected by diagnosis before production harness code changes.
No new `tests/test_*.py` marker decision is needed.

### D3. Preserve resource ownership instead of retrying browser actions

The correction must keep one BDD owner for 8766, one lane-owned BDD DB, and
existing browser workflow completion boundaries. Browser navigation retries,
swallowed exceptions, scenario reordering, xfail/skip, and expanded-lane
serialization are rejected as masking or scope expansion unless evidence proves
one is the minimum owner-level correction; even then, owner approval would be
required before scope changes.

### D4. Keep observability at the lifecycle boundary

Startup, first refusal, abnormal child exit, port ownership, and teardown must
be reconstructable from receipts/logs without touching production DB. Existing
`uvicorn_log_file`, `read_log_tail`, `wait_for_port`, `shutdown_uvicorn`, and
T29 receipt conventions are preferred over ad-hoc output.

### D5. Conditional change map, bounded by diagnosis

| Confirmed evidence | Intended file/symbol change | From → To | Reason |
|---|---|---|---|
| H1 | `tests/support/server.py::run_test_server`; possibly `tests/support/browser.py::wait_for_port` or `shutdown_uvicorn` | TCP readiness that can outlive or misrepresent child ownership → child-aware, lane-owned startup/teardown contract with explicit diagnostics | Prevent false-ready/dead/stale 8766 lifecycle. |
| H2 | `scripts/run_full_suite.py` only, plus `tests/scripts/test_t29_harness.py` | runner signal/reap behavior that can affect BDD → correct process-group ownership/reaping while preserving all lanes and selection | Fix proven runner interference, not guessed. |
| H3 | smallest proven helper/BDD cleanup symbol among `tests/support/server.py`, `tests/support/browser.py`, `tests/bdd/conftest.py` | cleanup/resource boundary that leaves server unavailable → bounded cleanup/isolation with visible failure | Address measured resource cause without broad serialization. |
| Any hypothesis | `tests/scripts/test_t29_harness.py` | no controlled regression oracle → focused deterministic contract for confirmed invariant | Prevent recurrence. |
| None | no runtime file | uncertain cause → blocked evidence package | Avoid trial-and-error. |

Files/symbols explicitly inspected but not changed absent direct evidence:
`tests/conftest.py` allow-lists, `tests/bdd/step_defs/_workflows.py` workflow
completion, and T32 artifacts. `pyproject.toml` changes only if the canonical
task boundary itself is proven causal; task names and taskipy usage remain
canonical.

## Implementation Decisions

### T33-DIAG-01 — H1 confirmed at readiness boundary; H2/H3 falsified for controlled run

**Context:** Initial worktree already contains T32 governance changes. `git diff
HEAD~1` was captured before any T33 edit. Relevant pre-existing boundaries are:
`pyproject.toml` task/marker additions, `scripts/run_full_suite.py` governance
selection and timing changes, `tests/conftest.py` importance-marker hook,
`tests/bdd/step_defs/_workflows.py` removal of one dashboard navigation, and
T32-related test/fixture files. These hunks remain outside T33 ownership.

**Decision:** Correct H1 only: `run_test_server` must make readiness depend on
the spawned child still being alive, not solely on an arbitrary TCP listener.
Keep host, port, DB, serial BDD execution, browser behavior, and runner lanes
unchanged. Add focused lifecycle contract coverage before changing helper code.

**Impact:** Modify only `tests/support/browser.py::wait_for_port`,
`tests/support/server.py::run_test_server`, and the existing T29 harness
contract test. Do not modify `tests/conftest.py`, `_workflows.py`, T32
artifacts, or runner scheduling.

**Evidence:** Initial isolated run reached 45/51 at the tool's 180-second limit;
fresh controlled concurrent run completed BDD 51/51 and expanded 12/12 selected
+ 8 deselected, both exit 0. Timeline observed BDD launch PID 344984 and
uvicorn PID 345020; 8766 transitioned from startup-unavailable to accepting and
stayed accepting through completion. No refusal, child exit, or runner signal
occurred; expanded lane did not own 8766. BDD uvicorn log contains normal startup
and request traffic, no bind/exit error. This falsifies H2 and gives no H3
pressure event to correlate. Source inspection independently confirms H1 defect:
current `run_test_server` calls `wait_for_port` without child state, so a stale
listener can satisfy readiness before spawned child is proven alive.

**Falsification boundary:** Original concurrent refusal was not reproduced in
this controlled run. If pre-fix controlled child-dead/stale-listener contract
does not fail, stop without runtime correction.

## Risks / Trade-offs

- **Concurrent resource noise can obscure causation** → use fresh DB/port state,
  timestamped process/socket/log evidence, and repeat only the bounded controlled
  reproduction required by the hypothesis matrix.
- **A readiness check can pass for the wrong process** → require child liveness
  and explicit ownership evidence; retain the existing unique-port regression.
- **Teardown hardening can hide abnormal exits** → preserve nonzero return-code
  logging and make abnormal startup/teardown observable in focused assertions.
- **Changing shared helpers can affect e2e/visual** → keep host, port, browser,
  DB, and scope contracts unchanged; run affected browser lanes in validation.
- **T32 policy drift** → review diff must show no T32 artifact, marker, skip,
  xfail, population, checksum, or pruning-policy change.
- **Diagnosis remains ambiguous** → stop with `BLOCKED_FOR_IMPLEMENTATION_BRIEF`;
  do not land speculative fixes.

## Migration Plan

No data or production migration. Apply follows: baseline/reproduce → diagnose →
focused controlled test → minimal confirmed fix → focused validation → isolated
and concurrent BDD/expanded validation → canonical full-suite validation. Rollback
is revert of the bounded harness diff; test DBs and temporary logs are disposable.

## Acceptance Evidence

- Isolated `uv run task test-bdd`: 51 scenarios passed, zero failures.
- Concurrent `uv run task test-bdd` + `uv run task test-t32-expanded`: BDD remains
  51/0 and expanded lane retains its expected governed results.
- Canonical `uv run task test`: exit 0, all six lanes green, clean children,
  reconciled current lanes/checksums/skips, and elapsed wall-clock <=300s.
- `uv run task test-one tests/scripts/test_t29_harness.py`: focused lifecycle
  contracts pass.
- No changed T32 artifact, scenario population, marker/pruning policy, skip,
  xfail, coverage contract, or unrelated file.
