## 1. Apply ownership and cleanup protocol

- [x] 1.1 `.opencode/agents/apply.md` — update `Preflight and durable
  execution record`, `Test gate`, and `Required handoff to review`. Add an
  executable ownership ledger contract with PID/PGID/port/temporary-resource,
  owner, start/end timestamp, evidence, status, and cleanup-result fields;
  require cleanup only for current-run owned entries; define idempotent no-op
  behavior for absent/already-closed resources; require residue classification
  and receipt before `READY_FOR_REVIEW`; stop on unknown/pre-existing/foreign or
  contradictory state. Preserve focused-only taskipy validation, no routine
  full suite, no masked tests, and existing handoff fields. Acceptance:
  apply handoff cannot claim review-ready without ownership and cleanup
  evidence, and text explicitly forbids broad/name/host-wide cleanup.
  Test file/scenario: no runtime test file (protocol-only); manually audit
  owned-resource cleanup, repeated cleanup, foreign-resource block, and
  vanished-child/PID-not-found/EPIPE scenarios against the new spec.
  Focused taskipy command: `uv run task lint` (apply; not run at proposal
  gate). Independent oracle: strict D05 change validation plus exact textual
  checklist of required ledger fields and prohibitions.

- [x] 1.2 `.opencode/skills/openspec-apply-change/SKILL.md` — update apply
  steps/guardrails so implementation reads the ledger contract, records owned
  resources before use, performs only bounded owned cleanup, and stops with a
  receipt when ownership is unknown. Preserve change selection, complete
  dossier reading, task checkbox flow, focused taskipy commands, no archive,
  no unrelated scope, and no routine `uv run task test`. Acceptance: skill
  instructions cannot authorize broad kill, name-pattern kill, host-wide port
  cleanup, or indiscriminate descendant cleanup. Test file/scenario: none;
  protocol audit covers owned and foreign resource cases. Focused taskipy
  command: `uv run task lint` (apply; not run at proposal gate). Independent
  oracle: compare every new guardrail to
  `test-run-ownership-contract` requirements and inspect no runner/test/code
  path is named as an implementation target.

## 2. Review preflight, postflight, and stop policy

- [x] 2.1 `.opencode/agents/review.md` — update full-suite gate and durable
  receipt/handoff to require preflight before the one canonical
  `uv run task test`, postflight after cleanup, complete ledger/resource
  evidence, residue classification, safe blocking, and receipt before verdict.
  Require PID/PGID/port/temporary-resource, owner, timestamps, cleanup result,
  six lane results, coverage/skips, fail-fast disposition, elapsed wall-clock,
  cleanup state, and <=300s classification. Preserve exactly one full-suite
  invocation, failure classification, no apply fixes, no masked tests, and
  APPROVED only when existing gates pass. Acceptance: unknown, pre-existing,
  foreign, incomplete, or contradictory residue returns `BLOCKED` without
  cleanup attempt; owned-cleaned state remains auditable. Test file/scenario:
  none; protocol audit covers trusted preflight, foreign port, vanished child,
  and clean postflight. Focused taskipy command: `uv run task lint` (apply;
  not run at proposal gate). Independent oracle: strict change validation and
  line-by-line comparison against review agent's existing six-lane/300s rules.

- [x] 2.2 `AGENTIC_DEVELOPMENT.md` — update workflow, durable-record, and
  duration-gate sections with shared ownership-ledger vocabulary, apply
  cleanup ownership, review preflight/postflight, residue classes, safe stop
  and escalation, and prohibited broad cleanup. Preserve `spec -> dossier ->
  focused apply -> one full review -> owner -> finalize`, taskipy entrypoints,
  all tests/skips/coverage, six lanes, fail-fast, and 300-second ceiling.
  Acceptance: this document gives one consistent protocol definition and does
  not turn ownership checks into a new lane, retry, skip, or timeout policy.
  Test file/scenario: none; documentation consistency audit against apply and
  review protocols. Focused taskipy command: `uv run task lint` (apply; not
  run at proposal gate). Independent oracle: required-term matrix across all
  three operational docs and D05 stable delta validation.

## 3. Validate D05 contract and scope

- [x] 3.1 `openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight/specs/test-run-ownership-contract/spec.md` — retain/add normative
  requirements and scenarios for ledger fields, bounded/idempotent apply
  cleanup, review preflight/postflight, residue classes, unknown/foreign
  blocking, PID race/EPIPE preservation, broad-cleanup prohibitions, and
  preserved six lanes/fail-fast/coverage/skips/300s. Acceptance: every
  measurable roadmap condition maps to at least one scenario, including one
  controlled foreign-resource non-termination case and one owned-resource
  bounded-cleanup case. Test file/scenario: no runtime test; OpenSpec scenario
  validation only. Focused taskipy command: `uv run task lint` (apply; not run
  at proposal gate). Independent oracle: `openspec validate
  d05-formalizar-contrato-operacional-de-limpeza-e-preflight --type change
  --strict --json` reports zero issues.

- [x] 3.2 D05 change directory — run proposal/apply-readiness validation only:
  `openspec status --change d05-formalizar-contrato-operacional-de-limpeza-e-preflight --json`,
  strict change validation, strict stable-spec validation, and whitespace plus
  changed-file audit. Preserve F58, F58 R1-F02, F61, T33, I08, runner,
  taskipy, tests, app, DB, and reports outside D05. Acceptance: proposal,
  design, tasks, delta spec, and `.openspec.yaml` are present; status is
  complete/apply-ready; changed files are only D05 artifacts plus the D05
  lifecycle line in `openspec/roadmap.md` at proposal gate; no tests, full
  suite, server, cleanup, database, or external service runs.
  Test file/scenario: N/A — artifact/scope gate. Focused taskipy command:
  `uv run task lint` is the implementation-time docs check (not run at
  proposal gate). Independent oracle: OpenSpec status/validators and
  `git diff --check`/status scope inspection.

## Test strategy

- Protocol-only documentation change. No runtime test file is added or edited;
  scenarios are validated through OpenSpec strict parsing, cross-document
  contract audit, and changed-file scope inspection.
- Apply focused validation: `uv run task lint` after documentation edits. Apply
  must not run the canonical full suite as routine validation.
- Review retains ownership of exactly one `uv run task test` run for any later
  implementation slice; D05 proposal runs no taskipy tests, lint, server,
  cleanup, database, or external command.
- Acceptance evidence must show: all required ledger fields; apply-only
  current-run cleanup; idempotence; review preflight/postflight; unknown,
  pre-existing, foreign, and contradictory residue blocking; one owned-resource
  bounded-cleanup scenario; one foreign-resource no-termination scenario;
  explicit broad/name/host-wide cleanup prohibitions; preserved six lanes,
  fail-fast, coverage, tests/skips, taskipy entrypoints, and <=300s gate.

## Preflight Boundaries

- Inspected: `AGENTS.md`, `AGENTIC_DEVELOPMENT.md`, D05 roadmap entry and
  dependency note, `.opencode/agents/apply.md`, `.opencode/agents/review.md`,
  `.opencode/skills/openspec-apply-change/SKILL.md`, config, existing
  performance/suite/task specs, archived F61 dossier, and active F58 dossier.
- Owned by D05 proposal: exact change directory plus D05's own lifecycle/status
  line in `openspec/roadmap.md`.
- Explicitly not changed: agent docs/skills, runner/taskipy/test/app files,
  F58/F58 R1-F02, F61, T33, I08 artifacts, reports, DB, seed, server, and
  external resources. Those files are future apply targets or evidence only;
  proposal gate creates no implementation edits.

## Execution Evidence

### Proposal gate

- `openspec status --change d05-formalizar-contrato-operacional-de-limpeza-e-preflight --json`
  → complete; all four artifact IDs are `done`; `applyRequires: ["tasks"]`
  satisfied.
- `openspec validate d05-formalizar-contrato-operacional-de-limpeza-e-preflight --type change --strict --json`
  → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json`
  → valid, 70/70 stable specs passed, 0 failures; informational
  long-requirement notices only.
- `rtk git diff --check -- openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight`
  → clean.
- Scope audit: exact D05 directory contains only `.openspec.yaml`,
  `proposal.md`, `design.md`, `tasks.md`, and
  `specs/test-run-ownership-contract/spec.md`. No implementation files,
  agent docs/skills, runner/taskipy/test/app files, F58/F61/I08 artifacts,
  reports, DB, or server resources changed; roadmap change is limited to D05
  lifecycle/status and progress log.
- Tests run: none. Proposal gate intentionally ran no taskipy command, pytest,
  full suite, lint, server, cleanup, database, browser, network, or external
  service operation.

### Apply gate — initial pass

- Task 1.1 complete. Changed `.opencode/agents/apply.md` symbols/sections:
  `Preflight and durable execution record`, `Test gate`, and `Required handoff
  to review`. Added ledger fields for resource kind/identity (PID, PGID, port,
  log, temporary path, test DB), owner/owner evidence, timestamps, status,
  classification, evidence, cleanup result; executable owned-vs-foreign
  decision procedure; bounded/idempotent cleanup; residue receipt; and explicit
  broad/name-pattern/host-wide/indiscriminate cleanup prohibitions.
- Task 1.2 complete. Changed `.opencode/skills/openspec-apply-change/SKILL.md`
  implementation loop and guardrails. Skill now requires ledger-before-use,
  exact current-run ownership, idempotent no-op, safe stop/escalation, receipt,
  focused-only apply validation, and no runtime process operation authorization.
- Task 2.1 complete. Changed `.opencode/agents/review.md` workflow and test
  gate/receipt. Trusted preflight now precedes one canonical suite; unknown,
  pre-existing, foreign, contradictory, or incomplete state blocks before
  launch without foreign cleanup; postflight receipt is required before
  verdict and preserves six lanes, coverage/skips, fail-fast, and `<=300s`.
- Task 2.2 complete. Changed `AGENTIC_DEVELOPMENT.md` with shared ledger,
  classification, apply cleanup, review preflight/postflight, receipt,
  escalation, and prohibited-action protocol. Explicitly preserves taskipy,
  six lanes, fail-fast, coverage, tests/skips, and 300-second ceiling without
  adding lane/retry/skip/mask/timeout behavior.
- Task 3.1 complete. Updated D05 delta spec to name log, temporary path, and
  test DB resources plus owner evidence and DB-path non-ownership proof. Its
  scenarios express bounded owned cleanup, repeated-cleanup no-op, foreign
  non-termination, vanished-child/PID-not-found/EPIPE preservation, trusted
  versus blocked preflight, prohibitions, and preserved suite invariants.
- Controlled acceptance audit: (1) owned-current-run ledger entry is the only
  cleanup target and repeated absent/closed cleanup is recorded no-op; (2)
  foreign/pre-existing/unknown or no-ledger resource is classified and left
  untouched, with BLOCKED/escalation; (3) vanished child, PID-not-found, PID
  reuse, or EPIPE preserves original lane/fail-fast/deadline result; (4)
  trusted review preflight permits exactly one canonical suite, while untrusted
  preflight launches none; (5) ownership is not a lane, retry, skip, mask, or
  timeout relaxation.
- Task 3.2 validation:
  - `openspec status --change d05-formalizar-contrato-operacional-de-limpeza-e-preflight --json`
    -> complete; proposal/design/spec/tasks `done`; apply-ready.
  - `openspec validate d05-formalizar-contrato-operacional-de-limpeza-e-preflight --type change --strict --json`
    -> valid, 1/1 passed, 0 issues.
  - `openspec validate --specs --strict --json` -> valid, 70/70 stable specs
    passed, 0 failures; existing informational long-requirement notices only.
  - `rtk git diff --check -- .opencode/agents/apply.md .opencode/agents/review.md .opencode/skills/openspec-apply-change/SKILL.md AGENTIC_DEVELOPMENT.md openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight`
    -> clean.
  - `rtk git status --short --untracked-files=all -- .opencode/agents/apply.md .opencode/agents/review.md .opencode/skills/openspec-apply-change/SKILL.md AGENTIC_DEVELOPMENT.md openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight`
    -> only four mapped docs plus exact D05 change artifacts. Existing
    worktree changes outside this slice remain untouched.
- No runtime tests, canonical suite, server, process termination, cleanup,
  database, browser, network, or external-service command was run. `uv run
  task lint` was not run because this gate explicitly limits validation to
  documentation/OpenSpec commands and excludes test/task execution; strict
  OpenSpec validators and whitespace/scope checks are the independent oracle.

### Apply gate — remediation 1

- Owner-directed policy selected: **runner isolated**. No foreign-resource
  baseline exception or allowlist exception is accepted.
- Changed files/symbols: `.opencode/agents/apply.md` canonical review isolation
  policy and handoff receipt; `.opencode/agents/review.md` isolated-runner
  precondition, safe stop, and receipt; `.opencode/skills/openspec-apply-change/SKILL.md`
  review isolation guardrail; `AGENTIC_DEVELOPMENT.md` review protocol and
  durable receipt; D05 delta `test-run-ownership-contract` isolated-runner
  requirement/scenarios; this `tasks.md` R1-F01 resolution and evidence.
- `openspec validate d05-formalizar-contrato-operacional-de-limpeza-e-preflight
  --type change --strict --json` -> valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json` -> valid, 70/70 stable specs
  passed, 0 failures; existing informational long-requirement notices only.
- `rtk git diff --check -- .opencode/agents/apply.md
  .opencode/agents/review.md .opencode/skills/openspec-apply-change/SKILL.md
  AGENTIC_DEVELOPMENT.md` -> clean.
- `git diff --no-index --check /dev/null <D05 delta spec>` and the equivalent
  check for this `tasks.md` -> clean; exit 1 represented expected untracked-file
  difference, with no whitespace errors.
- Scope audit: mapped docs plus D05 delta/tasks only; no F58, I08, runner,
  application, test, DB, server, process, or host-resource action.
- Tests run: none. No taskipy command, suite, server start, process inspection,
  cleanup, database, browser, network, or external-service command was run.

## Review Findings

- No review round exists at proposal gate. Review owns later full-suite receipt;
  no `uv run task test` is run or claimed here.

### Review R1

Scope audit: requirements/ledger `pass`; apply-owned bounded and idempotent cleanup `pass`; review preflight/postflight and receipts `pass`; unknown/foreign/pre-existing safe blocking `pass`; prohibitions against broad/name-pattern/host-wide/indiscriminate cleanup `pass`; preserved six lanes, fail-fast, coverage, tests/skips, taskipy entrypoints, and 300-second ceiling `pass`; D05-only scope and F58/F61/I08 exclusions `pass`; task completion `pass` (6/6); OpenSpec change/stable-spec validation `pass`; full-suite gate `not assessable` because trusted preflight blocked before launch.

Full suite: `uv run task test` -> NOT RUN; review preflight blocked launch; duration N/A; cleanup state N/A (no suite resources created; no cleanup attempted).

Preflight: run `D05-R1-2026-08-20T15:40:09-03:00`; no current-run ledger resources existed before launch. Inspection found pre-existing listening services on `0.0.0.0:8000` and `0.0.0.0:5443` (no D05 ledger ownership evidence), an `opencode` listener on `0.0.0.0:4096` (PID 252080), and pre-existing `/tmp/pytest-of-juca/`. Relevant observed resources classified `pre-existing`/ownership-not-established; no process, port, or file was terminated, freed, adopted, or deleted. Decision: BLOCKED before suite launch per D05 ownership contract.

Postflight: not applicable; canonical suite did not launch. No cleanup attempted. No lane, coverage, skip, fail-fast, or duration receipt exists because preflight correctly stopped before execution.

OpenSpec verification: `openspec validate d05-formalizar-contrato-operacional-de-limpeza-e-preflight --type change --strict --json` -> valid, 1/1 passed, 0 issues; `openspec validate --specs --strict --json` -> valid, 70/70 passed, 0 failures (informational long-requirement notices only); `git diff --check` on mapped files -> clean. Changed-file audit contains only four mapped docs plus D05 artifacts.

Verdict: BLOCKED

#### R1-F01 — Trusted preflight unavailable because pre-existing residue lacks ownership receipt
Status: resolved
Requirement/task: D05 delta `Review preflight and postflight govern canonical suite`, Scenario `Untrusted preflight blocks before launch`; tasks 2.1 and Test strategy.
Evidence: preflight command output at review start showed listeners on `0.0.0.0:8000` and `0.0.0.0:5443`, `opencode` PID 252080 on `0.0.0.0:4096`, and existing `/tmp/pytest-of-juca/`; review run had no ledger entries or owner evidence for these observed host resources. Contract requires pre-existing/ownership-uncertain state to block; no suite was run.
Required change: owner must establish clean, trusted preflight state with explicit ledger ownership/evidence for any resources relevant to this review run, or explicitly decide how unrelated pre-existing services/temp root are isolated without terminating, freeing, adopting, or deleting them. Do not modify D05 protocol, runner mechanics, F58, F61, I08, tests, or host resources as part of review remediation.
Acceptance: repeat review preflight records one complete ledger and classifies every relevant resource; only `absent` or current-run `owned-current-run`/`owned-cleaned` state remains; foreign/unknown/pre-existing residue stays untouched and blocks. Then one `uv run task test` may run, with postflight receipt recording six lanes, coverage/skips, fail-fast disposition, cleanup, elapsed wall-clock, and <=300s result.
Late finding reason: N/A; initial review.

### Remediation 1 — owner-directed isolated-runner policy

- Owner decision: **runner isolated**. Foreign-resource baseline exceptions and
  allowlist exceptions are rejected. Review MUST require an isolated runner
  with no unowned relevant process, listener, or test-temporary resource before
  the canonical suite.
- R1-F01 resolution: policy is now explicit in `.opencode/agents/review.md`,
  `.opencode/agents/apply.md`,
  `.opencode/skills/openspec-apply-change/SKILL.md`,
  `AGENTIC_DEVELOPMENT.md`, and the D05 delta spec. Review blocks before
  `uv run task test`, requests an isolated environment, and records inventory
  plus ownership evidence when relevant foreign/pre-existing/unknown residue is
  observed. It never adopts, kills, masks, deletes, frees, or allowlists that
  residue.
- Changed symbols: review full-suite/preflight gate and receipt; apply ownership
  handoff; apply skill cleanup guardrails; shared agent workflow and durable
  receipt; `test-run-ownership-contract` isolated-runner requirement and
  scenarios.
- Review remains historically `BLOCKED` for R1: this remediation supplies
  policy only. A later review on an actually isolated runner must perform the
  single canonical suite and postflight receipt; no environment action was
  taken in this pass.
- Focused validation: strict D05/OpenSpec validation and mapped diff check only;
  tests, suite, server, process inspection/cleanup, and taskipy commands were
  not run.
- Acceptance evidence: all mapped docs explicitly reject baseline/allowlist
  exceptions; isolated-runner precondition, inventory/receipt, safe stop,
  escalation, and broad-cleanup prohibition are consistent across docs; owner
  choice recorded above; F58, F61, I08, runner, app, test, DB, and host
  resources remain outside this remediation.

### Review R2

Scope audit: dossier/proposal/design/tasks/delta-spec `pass`; ledger fields and
ownership evidence `pass`; bounded current-run cleanup and idempotence `pass`;
preflight/postflight, residue classification, safe stop, and receipts `pass`;
broad/name-pattern/host-wide/indiscriminate cleanup prohibitions `pass`;
preserved six lanes, fail-fast, coverage, tests/skips, taskipy entrypoints, and
300-second ceiling `pass`; changed-doc cross-consistency `pass`; D05-only scope
and F58/F58 R1-F02/F61/I08 exclusions `pass`; task completion `pass` (6/6);
OpenSpec change/stable-spec validation `pass`; full-suite acceptance `finding`
because canonical suite was red. D05's own prospective preflight policy was
explicitly not applied retroactively: this documentation bootstrap review ran
the one canonical suite despite the policy's isolated-runner precondition.

Full suite: `uv run task test` -> RED; runner receipt
`reports/test-profile/20260820T163416-run.json` reports 204.724 seconds against
300 seconds, cleanup untrusted/incomplete (lane logs report `process PID not
found`; no trustworthy postflight receipt). Unit 498 passed/2 skipped; audit
40 passed; integration, e2e, and bdd exited 1; visual 5 failed/3 passed. The
external timing wrapper could not print its own elapsed value because
`python` is unavailable, so 204.724 seconds is runner-provided elapsed evidence.
No second suite, environment repair, process action, or broad cleanup was run.

Failure classification:

- Integration `tests/test_real_csv_flow.py::TestParseRealCsv::test_parse_real_csv_47_positions` — **Unknown**. Log ends at failure with
  `process PID not found (pid=458435)` and no assertion traceback
  (`20260820T163416-integration.log:269-392`). D05 docs-only scope gives no
  causal evidence for test drift, code bug, or regression.
- E2E `tests/e2e/test_rebalance_page.py::TestRebalancePage::test_asset_table_poc_parity_interactions` — **Unknown**. Lane ends with
  `process PID not found (pid=458429)` and taskipy signal-handler traceback
  (`20260820T163416-e2e.log:50-63`).
- BDD `tests/bdd/test_scenarios.py::test_clear_asset_class_target_enter_saves_zero[Ana]` — **Unknown**. Lane ends with
  `process PID not found (pid=458450)` and no assertion traceback
  (`20260820T163416-bdd.log:51-54`).
- Visual `test_patrimonio_snapshot[desktop]`, `test_rebalance_form_snapshot[desktop]`,
  `test_rebalance_plan_snapshot[desktop]`, `test_import_form_snapshot[desktop]`,
  and `test_import_review_snapshot[desktop]` — **Unknown**. Failures are
  baseline dimension/diff mismatches (1605x4293 expected vs 1605x4241 actual;
  23.7445%-26.5121% diff) in
  `20260820T163416-visual.log:30-35,79-82,158-162,247-250,294-297`;
  no evidence attributes them to D05 documentation.

Verdict: BLOCKED

#### R2-F01 — Canonical suite red with unknown lane failures
Status: blocked
Requirement/task: PRD §4.13; D05 tasks 2.1, 3.2, and Test strategy; delta
`Review preflight and postflight govern canonical suite`, `Unknown or foreign
residue stops safely`.
Evidence: `uv run task test` produced lane exits integration=1, e2e=1,
bdd=1, visual=1; runner receipt reports 204.724s; lane evidence and failure
classification above. D05 docs are unchanged by these failures and no failure
has attributable D05 implementation cause.
Required change: owner must decide/assign bounded diagnosis and remediation
for these unknown suite failures in their owning slices or environment before
any approval. Do not alter D05 contract, rerun suite in this review, repair or
clean host resources, touch F58/F58 R1-F02/F61/I08, or weaken tests, skips,
coverage, lanes, fail-fast, or duration gate.
Acceptance: one later review receipt shows all six lanes green, preserved
coverage/tests/skips/fail-fast semantics, trusted cleanup/postflight evidence,
and elapsed wall-clock <=300s; D05 documentation remains internally
consistent and bounded to run-owned resources.
Late finding reason: R2 rechecked previously `not assessable` full-suite area;
owner explicitly authorized this D05-only exception to run suite without
prospective preflight.

### Review R3
Scope audit: dossier/proposal/design/tasks/delta-spec `pass`; tasks complete
(6/6); ledger fields and ownership evidence `pass`; bounded current-run cleanup
and idempotence `pass`; review preflight/postflight, residue classification, safe
stop, and receipt contract `pass`; broad/name-pattern/host-wide/indiscriminate
cleanup prohibitions `pass`; preserved six lanes, fail-fast, coverage,
tests/skips, taskipy entrypoints, and 300-second ceiling `pass`; D05-only scope
and F58/F58 R1-F02/F61/I08 exclusions `pass`; prior R2 finding acceptance
aligned with owner-authorized I08 R5 receipt `pass`; stable-spec validation
`pass`; diff-check `pass`; no blocking findings.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**. I10
maintenance-suspended policy receipt is recorded in
`AGENTIC_DEVELOPMENT.md:105-112`; no canonical suite invocation, lane
resources, cleanup, or host action occurred. Focused/product evidence is the
owner-authorized I08 R5 receipt at
`openspec/changes/archive/2026-08-20-i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane/tasks.md:708-745`:
all six lanes green (unit 515 passed/2 skipped, integration 390, audit 40,
e2e 51, bdd 51, visual 8), reconciliation `ok=true`, owned cleanup
`owned-cleaned`, and 240.60s <= 300s. D05 has no runtime product tests;
focused protocol acceptance is covered by dossier/source audit and I08 R5.

Preflight: maintenance-suspended review receipt; canonical launch preflight
not applicable because gate was suspended by owner policy. Per-run ledger has
no resources created: process/PGID `absent`, listener `absent`, test DB
`absent`, declared temporary paths `absent`; no ownership adoption, kill,
free, delete, mask, or allowlist action. Decision: suite withheld under
suspension.

Postflight: not applicable to this suspended receipt; no suite or cleanup
started. No current-run residue exists to classify; no broad or foreign
cleanup ran. I08 R5 independently supplies trusted postflight/cleanup evidence
for owner-authorized acceptance.

OpenSpec verification: `openspec validate
d05-formalizar-contrato-operacional-de-limpeza-e-preflight --type change
--strict --json` -> valid, 1/1 passed, 0 issues;
`openspec validate --specs --strict --json` -> valid, 76/76 passed, 0
failures (informational long-requirement notices only); `rtk git diff --check
-- openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight`
-> clean. Evidence paths: active D05 dossier files under
`openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight/`;
prior R2 at `tasks.md:286-350`; I08 R5 acceptance at archived tasks
`tasks.md:708-745`.

Verdict: APPROVED

Findings: none. Owner authorized I08 R5 receipt as D05 acceptance and
authorized closing D05 on 2026-08-23. No remediation, archive, roadmap,
code, test, spec, commit, or push action performed.
