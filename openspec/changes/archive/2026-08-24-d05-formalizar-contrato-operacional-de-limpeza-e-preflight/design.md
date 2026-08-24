## Context

D05 is a protocol-only prerequisite for I08. F61 review R1 recorded an
854.89-second canonical run with incomplete child cleanup, `process PID not
found`, and Playwright `write EPIPE`. F58 review R1 recorded a separate
`Page.goto: net::ERR_ABORTED` browser-server failure; F58 R1-F02 remains an
independent timeout finding. These incidents show that process and temporary
resource state must be attributable before cleanup or suite verdicts are
trusted.

### Code map

- `AGENTS.md`: repository routing and standing-rule index. It points to PRD
  §4, AGENTIC_DEVELOPMENT.md, roadmap lifecycle, taskipy entrypoints, and the
  no-broad-change boundary. It is inspected for governing references and is
  not a D05 edit target.
- `.opencode/agents/apply.md`: `Test gate (ZERO TOLERANCE)` lines 54-90,
  `Required handoff to review` lines 98-114, and `Preflight and durable
  execution record` lines 31-48. Current flow requires focused tests and a
  handoff but does not require an ownership ledger or bounded cleanup receipt.
- `.opencode/agents/review.md`: full-suite gate lines 27-57 and durable
  `Review Findings` format lines 96-119. Current flow runs one timed
  `uv run task test`, but lacks an explicit preflight/postflight ownership
  check and residue stop classification.
- `.opencode/skills/openspec-apply-change/SKILL.md`: steps 3-7 select a change,
  read context, and execute tasks; guardrails lines 145-160 preserve scoped
  implementation. It is the operational apply entrypoint and must carry the
  same ownership vocabulary without implementing runner mechanics.
- `AGENTIC_DEVELOPMENT.md`: workflow lines 3-10, apply/review ownership lines
  26-45, durable-record rules lines 51-64, and 300-second gate lines 66-75.
  It is the cross-agent protocol source for the new ledger, receipts, and
  stop policy.
- `openspec/roadmap.md`: D05 lines 606-613 define exact scope and acceptance;
  I08 lines 615-622 owns runner mechanics and depends on D05 vocabulary.
  F61/F58 boundaries and the six-lane/fail-fast/coverage/300-second
  invariants are preserved rather than edited.
- `openspec/changes/archive/2026-08-20-f61-documentar-ambiente-local-e-alinhar-cookie-seguro/tasks.md`:
  Review R1/R1-F01 lines 188-225 provide the 854.89-second PID/EPIPE evidence;
  R2 lines 228-246 show later clean-run evidence without changing F61.
- `openspec/changes/f58-integrar-automacao-playwright-myprofit/tasks.md`:
  review R1-F01 lines 172-190 record `ERR_ABORTED` and sibling termination;
  R1-F02 lines 192-208 remain separate and excluded from D05.

### Current relevant flow

1. Apply reads an approved dossier, performs implementation preflight, runs
   focused taskipy tests, and returns `READY_FOR_REVIEW`. It records changed
   files and focused results, but ownership of child processes, ports, logs,
   temporary paths, and cleanup is implicit.
2. Review reads the dossier and apply handoff, launches exactly one canonical
   `uv run task test`, waits for six lane outcomes, measures wall-clock through
   child cleanup, and records a verdict. It currently has no mandatory state
   snapshot before launch or explicit residue classification after cleanup.
3. A process/resource observation can therefore be PID-not-found, EPIPE,
   `ERR_ABORTED`, stale, foreign, or unknown without a durable distinction
   between current-run ownership and unrelated host state.
4. D05 changes only written protocol. I08 later maps ledger and stop rules to
   `scripts/run_full_suite.py`, `scripts/run_expanded_lane.py`, taskipy, and
   harness tests. D05 must not infer implementation details from I08.

Boundary conditions:

- Ownership is valid only when current run records resource identity plus owner
  and start timestamp before using it; an observed PID/port/path alone is not
  proof of ownership.
- Ledger must cover PID, PGID, port, temporary resource, owner, start
  timestamp, end timestamp, and evidence/cleanup result. Resource kind and
  status may be added for clarity, but required fields cannot be omitted.
- Unknown, pre-existing, stale, or foreign residue is never repaired by
  guessing. Apply/review stop safely, preserve original failure when known,
  record diagnosis, and escalate.
- Cleanup may target only current-run owned resources recorded in the ledger;
  repeated cleanup is a no-op for already absent resources.
- No broad kill, process-name/pattern kill, host-wide port cleanup,
  indiscriminate descendant termination, or cleanup of production DB or
  unrelated files is authorized.

## Goals / Non-Goals

**Goals:**

- Establish one shared ownership ledger vocabulary and receipt minimum for
  apply/review.
- Make apply cleanup bounded, owned, idempotent, and auditable.
- Make review preflight happen before canonical suite launch and postflight
  happen before verdict, with explicit residue classification.
- Define safe blocking/escalation for ownership uncertainty and cleanup races.
- Preserve six lanes, fail-fast, coverage, all tests/skips, taskipy commands,
  and the absolute 300-second ceiling.

**Non-Goals:**

- No implementation of runner/process-group/port cleanup, taskipy changes,
  test harness changes, or application/runtime code.
- No edits to F58, F58 R1-F02, F61, T33, I08 artifacts, tests, reports,
  database, seed, server, or production resources.
- No retry policy for browser navigation, PID races, EPIPE, or full-suite
  failures; no broad host repair or automatic foreign-resource takeover.
- No change to six-lane ordering, fail-fast semantics, coverage ownership,
  skip identities, or the 300-second gate.

## Decisions

### 1. Use one ownership ledger across apply and review

The protocol requires a per-run ledger record for every child/process-group,
port, log, temporary resource, or other test-only resource. Required fields:
`resource_kind`, `resource_id` (PID/PGID/port/path as applicable), `owner`,
`started_at`, `ended_at`, `status`, `evidence`, and `cleanup_result`. The
minimum user-required identity fields remain explicit: PID, PGID, port,
temporary resource, owner, and start/end timestamps.

Alternative rejected: infer ownership from process name, port number, path
prefix, or current descendants. Those signals can identify foreign or stale
resources and caused the unsafe ambiguity D05 addresses.

### 2. Apply owns bounded cleanup; review owns trust assessment

Apply records resources before launch/use and cleans only records with current
run ownership. Cleanup is idempotent: absent resource, already-closed group,
or already-removed temporary path becomes a recorded no-op, not a new target.
Apply handoff must include ledger receipt, cleanup result, residue list, and
foreign/unknown classification.

Review performs preflight before the one canonical suite invocation and
postflight after child cleanup. Review may record and classify state, but must
not repair unknown or foreign resources. A current-run owned residue is
acceptable only when bounded cleanup is recorded as complete; otherwise review
blocks with evidence. This separates trust/verdict ownership from future I08
mechanics.

Alternative rejected: let review "clean what looks related" before or after
the suite. That can terminate another run and obscure the original failure.

### 3. Stop on uncertainty, preserve causal evidence

Classify each observed residue as `owned-current-run`, `pre-existing`,
`foreign`, `unknown`, `absent`, or `owned-cleaned`. `pre-existing`, `foreign`,
and `unknown` stop the affected operation before destructive action. If a
child vanished or signaling returns PID-not-found/EPIPE, preserve the original
lane/fail-fast/deadline result, record the race and available PID/PGID evidence,
and block when ownership or cleanup cannot be trusted.

Alternative rejected: retry signal, adopt PID, kill by name, free port
globally, or convert an incomplete receipt into success.

### 4. Receipts are mandatory boundaries, not implementation telemetry

Apply handoff receipt and review preflight/postflight receipt must identify run,
timestamps, every ledger entry, ownership evidence, cleanup outcome, residue
classification, and stop/escalation decision. Review receipt additionally
records canonical command, six lane status, fail-fast/coverage/skip evidence,
elapsed wall-clock through cleanup, and the <=300-second verdict input.
Missing or contradictory receipt data makes state untrustworthy and blocks;
the protocol never authorizes a second full suite merely to repair telemetry.

### 5. Keep D05 documentation-only and I08 as implementation owner

The change edits only protocol documents and adds this OpenSpec contract.
I08 will implement runner mechanics against these terms. This prevents D05
from changing process behavior while resolving the vocabulary dependency.

## Implementation Decisions

- **Context:** F61 R1's 854.89-second run and F58 R1's `ERR_ABORTED` evidence
  show cleanup/attribution uncertainty, while later F61/F58 receipts prove
  these were separate environmental or runner conditions.
  **Decision:** encode ownership and stop rules before any runner fix.
  **Impact:** I08 can implement bounded cleanup without inventing ownership
  semantics; F58/F61 remain untouched. **Evidence:** archived F61 tasks R1-F01
  and F58 tasks R1-F01/R1-F02 listed in the code map.
- **Context:** Existing apply/review handoffs contain focused/full-suite
  results but no resource ledger. **Decision:** require ledger and receipt
  sections in the agent protocols and AGENTIC_DEVELOPMENT workflow.
  **Impact:** future apply/review output becomes independently auditable.
  **Evidence:** `.opencode/agents/apply.md` handoff lines 98-114 and
  `.opencode/agents/review.md` receipt lines 96-119.
- **Context:** Existing suite contracts already require six lanes, fail-fast,
  coverage, skips, and <=300s. **Decision:** add ownership as a prerequisite,
  never as a replacement for suite evidence. **Impact:** no lane or coverage
  relaxation and no second routine full-suite run. **Evidence:**
  `openspec/specs/agent-test-performance-gate/spec.md`,
  `openspec/specs/test-suite-quality/spec.md`, and `openspec/specs/dev-tasks/spec.md`.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `.opencode/agents/apply.md` — preflight, test gate, required handoff | Focused tests and file/result handoff; cleanup ownership implicit | Record ledger before resource use; clean only current-run owned entries; require idempotent cleanup/residue receipt and safe stop before `READY_FOR_REVIEW` | Prevent apply from killing or deleting foreign residue |
| `.opencode/agents/review.md` — test gate, durable receipt, handoff | One full suite and timing receipt without mandatory resource preflight/postflight | Preflight before `uv run task test`, postflight after cleanup, classify residue, block unknown/foreign state, and include ownership receipt before verdict | Make suite verdict trustworthy |
| `.opencode/skills/openspec-apply-change/SKILL.md` — implementation loop and guardrails | Generic task loop/guardrails with no ownership protocol | Require reading/maintaining ownership ledger and bounded cleanup evidence while preserving scoped apply behavior | Keep skill entrypoint aligned with agent contract |
| `AGENTIC_DEVELOPMENT.md` — workflow, durable record, duration gate | Apply/review sequence records tests and findings only | Add shared ownership/preflight/receipt vocabulary and explicit prohibitions; retain six lanes/fail-fast/coverage/skips/300s | Single cross-agent source of protocol |
| `openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight/specs/test-run-ownership-contract/spec.md` | No stable capability for resource ownership | Add normative requirements/scenarios for ledger, cleanup, preflight/postflight, stop policy, prohibitions, idempotence, and preserved suite invariants | Durable implementation oracle for I08 |

## Risks / Trade-offs

- **[Overly broad cleanup remains possible through ambiguous wording]** → name
  exact ownership proof, forbid name/host-wide cleanup, and make unknown,
  pre-existing, and foreign residue blocking classifications.
- **[Receipt overhead delays review]** → use bounded ledger fields and one
  preflight/postflight around the already-required single full suite; never add
  routine suite retries.
- **[PID reuse or port reuse creates false ownership]** → require current-run
  owner plus start timestamp and evidence; identity alone is insufficient.
- **[I08 interprets protocol as a new lane or timeout policy]** → explicitly
  preserve six lanes, fail-fast, coverage, skips, taskipy entrypoints, and
  300-second ceiling; keep runner files out of D05.
- **[F58/F61 review evidence gets reopened]** → cite evidence only as reason
  and boundary; exclude F58, F58 R1-F02, F61, T33, and their artifacts from
  change map and acceptance.

## Migration Plan

1. Apply edits only mapped documentation files and add D05 contract/spec.
2. Validate artifact completeness, strict change syntax, strict stable specs,
   whitespace, and changed-file scope.
3. I08 consumes vocabulary in a later slice; no D05 runner migration or
   runtime rollout exists. Rollback is removal/reversion of documentation and
   the unsynced delta only; no process, database, or host resource changes.

## Open Questions

- None blocking proposal. I08 must choose concrete ownership evidence APIs and
  cleanup primitives without weakening this contract; that is implementation
  detail, not D05 scope.

## Proposal Gate Evidence

- Inspected D05 roadmap entry/dependency, AGENTS.md, AGENTIC_DEVELOPMENT.md,
  apply/review agents, apply skill, config, existing performance/suite/task
  specs, archived F61 review evidence, and active F58 review evidence.
- No agent docs/skills, runner, taskipy, test, application, database, F58, F61,
  or I08 files were edited during proposal creation.
- No tests, server, database operation, cleanup command, or external service
  was executed during proposal.

### Validation receipt

- `openspec status --change d05-formalizar-contrato-operacional-de-limpeza-e-preflight --json`
  → `isComplete: true`; proposal, design, spec, and tasks are `done`;
  `applyRequires: ["tasks"]` satisfied.
- `openspec validate d05-formalizar-contrato-operacional-de-limpeza-e-preflight --type change --strict --json`
  → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json`
  → valid, 70/70 stable specs passed, 0 failures; existing informational
  long-requirement notices remain.
- `rtk git diff --check -- openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight`
  → clean.
- `rtk git status --short --untracked-files=all -- openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight`
  → only `.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`, and the
  D05 delta spec under the exact change directory.
- Tests run: none. No taskipy test/lint, full suite, server, cleanup, DB,
  migration, seed, browser, network, or external-service command was run.
