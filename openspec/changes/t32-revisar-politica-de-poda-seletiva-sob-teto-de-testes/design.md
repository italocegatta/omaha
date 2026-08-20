## Context

PRD §4.13 makes `uv run task test` green and `<=300s` a delivery
requirement. It also forbids removing tests, skips, coverage, or lanes merely
to fit the ceiling. The current `test-suite-quality` contract additionally
ties the accepted population to node IDs, lanes, checksum, skip identities,
and audit evidence. `tests/PERFORMANCE.md` supplies dated lane timings;
`tests/AUDIT.md` supplies per-node retention evidence.

T32 applies governance to 12 owner-approved visual snapshot cases. The owner
decision is resolved: cases remain versioned with explicit `t32_pruned`
rationale and are excluded only from the standard blocking lane. Canonical
replacement coverage remains in blocking lanes.

## Goals / Non-Goals

**Goals:**

- Define one versioned pruning record for individual nodes/cases.
- Require classification, redundancy grouping, protected contract,
  replacement coverage, measured savings, owner, and date.
- Preserve behavioral coverage and make gate membership explicit before Apply.
- Define an auditable decision gate and acceptance criteria for a later Apply.

**Non-Goals:**

- No production, fixture behavior, or assertion changes in T32. Baseline files
  may be generated for the expanded lane only after visual review against the
  intended current UI.
- No whole-suite, bucket-wide, or failure-driven removal.
- No `skip`, `skipif`, `xfail`, `pytest.skip`, empty `pass`, placeholder, or
  timeout-time decision.
- Owner decision is recorded before Apply in proposal, roadmap, and audit
  register.

## Decisions

### D1 — Record pruning at node/case granularity

Each candidate uses stable pytest node ID (including parametrized case ID when
applicable). Record category is one of `parametrized-case`, `example`,
`snapshot`, or `redundant-low-value-assert`. A redundancy group names all
overlapping nodes; it never treats an entire suite as one removable unit.

### D2 — Require contract-to-replacement mapping

Candidate record MUST name protected requirement/scenario or behavioral
contract, then identify surviving replacement node IDs and their lanes. A
replacement must assert same contract with equal or stronger boundary,
positive-path, error-path, and structural coverage where relevant. Deleting a
duplicate without a canonical replacement is rejected.

### D3 — Measure before deciding

Record collection population, node duration, affected-lane duration, and
full-suite wall-clock including child cleanup from fresh canonical task runs.
Savings are reported as measured deltas, not estimates. A timeout or green
run over 300 seconds is evidence for bottleneck remediation, never a reason to
decide removal during that run.

### D4 — Version approved cases outside blocking lane

Every approved record has `gate_disposition: outside-blocking-standard-lane`,
with `t32_pruned` marker, rationale, owner, date, named retained case, and
replacement evidence. The standard blocking task excludes only this marker;
retained cases remain discoverable through the named `test-visual-pruned` task.

### D5 — Preserve immutable delivery safeguards

Later Apply may proceed only after owner decision, updated versioned manifest
and audit record, replacement verification, no masked-pass construct, and
fresh canonical evidence that remains green and within `<=300s`. Any accepted
population/checksum/marker change must be explicit and reviewable. Existing
protected contracts, lanes, coverage obligations, and full-suite delivery gate
remain in force; only the owner-authorized T32 marker is excluded from standard
blocking execution.

## Risks / Trade-offs

- **[Risk]** Redundancy judgment removes a subtle boundary case. → Require
  exact node IDs, protected contract, replacement node IDs, and reviewable
  evidence before Apply.
- **[Risk]** A faster blocking gate hides coverage moved outside it. → Require
  explicit gate disposition, named schedule/owner/evidence, and no silent
  carve-out.
- **[Risk]** Baseline and audit manifest drift. → Reconcile node IDs, lanes,
  checksum, skip identities, and audit rows as one versioned change.
- **[Trade-off]** Recordkeeping costs time before any savings. → Keep records
  per candidate/group and measure only affected lanes plus canonical proof.

## Migration Plan

T32 has no runtime migration. Apply updates only approved versioned test cases,
policy/spec, manifest/audit/performance evidence, and blocking-lane selection;
it is reversible by removing the marker/task exclusion and restoring prior
manifest evidence. Archive requires acceptance evidence and no unrelated files.

## Open Questions

1. Decision resolved on 2026-08-19: approved cases remain versioned with
   explicit prioritization rationale and are excluded from standard blocking
   execution only.

## Authorized Apply expansion — 2026-08-19

Owner authorized only:

1. Harness remediation: measured scheduling, resource-isolation, or teardown
   changes in the canonical test runner and directly linked test harness files,
   preserving every test, lane, marker, skip, xfail, and coverage contract.
2. Audit copy normalization: replace stale `Owner-approved coverage removals`
   wording in `tests/AUDIT.md` with wording that states T32 cases remain
   versioned and outside only the standard blocking lane.

Acceptance remains one canonical `uv run task test` exit 0 at `<=300s`, plus
strict OpenSpec validation. A timeout, deselection, coverage reduction, or
masked failure is not an acceptable remediation.

### Expanded governance implementation

`tests/fixtures/test_importance.json` is versioned policy `t32.v5`. Collection
applies one explicit importance marker to every node/case and fails if
resolution is missing. Runner reconciliation reports current population and
lane checksums without making active count immutable. Before any child launch,
a deterministic pre-run function intersects versioned candidates with the
audit manifest, excludes already-disabled T32 cases, and sorts by importance,
prior-known cost, and node ID. Current policy selects 23 low-importance cases
from a 30-case dark-mode candidate manifest and a 301.04s prior-known forecast,
preserving 10.00s headroom; all 30 candidates remain in the expanded unit
schedule. Existing owner-approved T32
cases remain outside the standard lane and are runnable with `uv run task
test-visual-pruned`; the combined expanded schedule is `uv run task
test-t32-expanded`. Fresh canonical receipt `20260820T003216` passed in 284.35s
with all six lanes green and clean children. Canonical E2E and BDD processes reuse
one browser process while retaining fresh per-test contexts, removing repeated
Chromium startup/teardown contention.

## Implementation Decisions

### D6 — Synchronize BDD logout before next login

- **Context:** The canonical profile-sharing scenario failed at
  `common_steps.py:158` because the next `username` lookup could run while the
  browser was still transitioning from dashboard logout to `/login`.
- **Decision:** Keep BDD session state deterministic by making the existing
  `clico em "Sair"` step wait for `/login` and the visible username input before
  returning. No production code, fixture seed, browser lifecycle, or scenario
  contract changes.
- **Impact:** Subsequent login steps observe a ready login page instead of a
  transient dashboard/document state; all 51 BDD scenarios remain unchanged.
- **Evidence:** Exact failing node passed after the surgical wait; full
  `uv run task test-bdd` passed all 51 cases.

### D7 — Guard Sair default candidate path

- **Context:** `Sair` is resolved by `click_button`'s default candidate loop,
  not `STEP_CLICK_ALIASES`; guarding only the alias loop would leave the real
  logout flow returning before readiness verification.
- **Decision:** Apply same post-click `/login` and visible-username waits to
  default candidates, outside selector/click fallback handling. Preserve
  existing fallback behavior for selector/click failures.
- **Impact:** Every successful `Sair` step proves both readiness conditions;
  timeout exceptions propagate. No production code, fixtures, scenarios,
  browser lifecycle, or lane membership changes.
- **Evidence:** `tests/bdd/step_defs/common_steps.py::click_button` has both
  candidate paths guarded; exact profile-sharing node passes after change.

### D8 — Do not race dashboard reload with explicit same-URL navigation

- **Context:** The canonical-only failure occurred in
  `tests/bdd/step_defs/_workflows.py::create_one_class` immediately after the
  API response for class creation. The workflow explicitly called
  `page.goto("/")` even though the dashboard save flow already starts a
  same-URL reload; under concurrent browser-lane load, Playwright reported
  `Page.goto: net::ERR_ABORTED` at that navigation.
- **Decision:** Remove only the redundant explicit `page.goto("/")`. Keep the
  existing class-row selector and visibility waits as the completion boundary;
  they observe the dashboard reload initiated by the save flow before the next
  workflow step. No retry, assertion, scenario, lane, server, or production
  behavior changes.
- **Impact:** Class creation no longer starts competing navigations on the same
  BDD page. Existing response-status and rendered-class checks remain intact;
  all 51 scenarios retain execution.
- **Evidence:** R2 receipt `/home/juca/github/omaha/reports/test-profile/20260820T010530-bdd.log`
  failed at this `page.goto` with `net::ERR_ABORTED`; the immediately prior
  `expect_response` block and following class-row wait form a deterministic
  duplicate-navigation boundary. Fresh receipt
  `/home/juca/github/omaha/reports/test-profile/20260820T012034-run.json`
  passed all six lanes after removal in 257.41s with `clean_children=true`.

### Review reconciliation evidence (`t32.v5`)

| Stable node ID | Classification | Rationale | Protected contract | Replacement coverage | Owner/date/version | Measured cost |
|---|---|---|---|---|---|---:|
| `tests/test_dark_mode_tokens.py::test_class_swatches_against_bg[1]` | normal | Existing low-value Class-1 dark-mode boundary check retained; no new pruning | Class-1 dark-mode token remains contrasted against `--bg` | Remaining class-swatch cases plus CSS token audit | repository owner / 2026-08-19 / `t32.v5` | 0.847s |
| `tests/test_dark_mode_tokens.py::test_negative_ink_on_negative_passes_aa` | normal | Existing low-value negative status contrast check retained; no new pruning | Negative status ink remains readable on negative fill | Status-ink siblings plus CSS token audit | repository owner / 2026-08-19 / `t32.v5` | 0.786s |
