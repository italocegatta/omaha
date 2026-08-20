## 1. Decision gate before Apply

- [x] 1.1 Owner decision recorded: approved pruned cases remain versioned with explicit rationale and stay outside only the standard blocking lane; owner/date/scope/authoritative locations are in proposal, roadmap, and `tests/AUDIT.md`.
- [x] 1.2 Change remained proposal-only until decision; no unapproved node, case, snapshot, assert, lane, skip, xfail, coverage, manifest row, or baseline entry was removed.
- [x] 1.3 Selected disposition is compatible with PRD §4.13, `test-suite-quality`, and delta spec: only named `t32_pruned` cases leave standard blocking execution, with replacement coverage retained.

## 2. Build versioned pruning evidence

- [x] 2.1 Inventory candidates by stable pytest node ID, including parametrized mobile case IDs; classify all 12 as `snapshot` in the versioned T32 register.
- [x] 2.2 Group only demonstrable visual overlap and record protected contract, replacement node IDs/lanes, owner, date, and record version for every candidate in `tests/AUDIT.md`.
- [x] 2.3 Record baseline/candidate population, affected-lane duration, full-suite proof wall-clock/cleanup evidence, and measured visual-lane delta in `tests/PERFORMANCE.md`.
- [x] 2.4 Reject timeout-only, over-ceiling, failure-mask, undocumented-carve-out, and whole-suite/bucket rationales; T32 register contains only owner-authorized contract overlap.

## 3. Apply approved selective policy

- [x] 3.1 Consolidate only owner-approved visual nodes with canonical replacement coverage; preserve structural, positive, error, lane, and coverage contracts. Cases remain in `tests/visual/test_snapshots.py`.
- [x] 3.2 Update versioned audit register, population/checksum evidence, performance record, and owning spec/roadmap decision together; unrelated files untouched.
- [x] 3.3 Named retained-case schedule is `uv run task test-visual-pruned`; owner/date and evidence are recorded. Blocking reports do not claim omitted cases as green coverage.
- [x] 3.4 No new `skip`, `skipif`, `xfail`, `pytest.skip`, empty `pass`, or placeholder was introduced; dedicated `t32_pruned` marker is explicit and allowlisted.

## 4. Verify acceptance criteria

- [x] 4.1 Run affected visual lane through taskipy; collection and focused execution verify replacement coverage and protected contracts.
- [x] 4.2 Existing T29 canonical evidence records three green `uv run task test` proofs at 280.98s/276.10s/274.77s with reconciled population, lanes, checksums, skip identities, and clean children; T32 preserves that evidence and population.
- [x] 4.3 Report before/after visual-lane measurements and negative/zero savings explicitly; no additional pruning is authorized from timing alone.
- [x] 4.4 Strict repository OpenSpec validation is run after implementation; affected spec, acceptance evidence, and unrelated-file boundary are confirmed before archive.

## 5. Owner-authorized bounded expansion

- [x] 5.1 Profile and remediate only harness scheduling, resource isolation, or teardown bottlenecks directly linked to the canonical runner; preserve all protected test population and coverage contracts.
- [x] 5.2 Normalize every stale `Owner-approved coverage removals` occurrence in `tests/AUDIT.md`; retain explicit T32 rationale and outside-standard-blocking-lane disposition.
- [x] 5.3 Run focused affected tests, then exactly one canonical `uv run task test` attempt; accept only exit 0, clean children, reconciled population, and wall-clock `<=300s`, otherwise stop with evidence.
- [x] 5.4 Run `openspec validate t32-revisar-politica-de-poda-seletiva-sob-teto-de-testes --strict` and `openspec validate --specs --strict`.

## 6. Expanded owner policy — 2026-08-19

- [x] 6.1 Apply versioned importance policy (`critical`, `high`, `normal`,
  `low`) to every collected node/case; collection and governance validation
  fail on missing classification.
- [x] 6.2 Replace immutable active-count reconciliation with transparent current
  state: lane checksums, skip identities, protected coverage, and classification
  coverage remain blocking contracts.
- [x] 6.3 Implement deterministic pre-run lowest-importance selection using
  measured/prior-known cost, with no new selection when forecast is within 300s.
- [x] 6.4 Keep all selected cases versioned and runnable through named expanded
  lane; record rationale, owner/date, protected contract, replacement coverage,
  and cost evidence in T32 docs.

## Execution Evidence

- Surgical BDD correction: `tests/bdd/step_defs/common_steps.py::click_button`
  now waits for `/login` and visible `input[name="username"]` after logout.
  This fixes transient page-state failure at `fill_field` line 158 without
  changing production code, seed data, scenarios, or lane membership.
- Pre-edit boundary: `git diff HEAD~1` captured before editing; unrelated user
  work remains outside this slice, including agent/config, runner, manifest,
  and visual-baseline changes already present in the worktree.
- Focused validation: `uv run task test-one tests/bdd/test_scenarios.py::test_italo_sees_ana_classes_after_switch` -> 1 passed in 13.34s.
- BDD validation: `uv run task test-bdd` -> 51 passed in 187.76s.
- Expanded governance: `uv run task test-t32-expanded` -> 12 visual passed,
  8 deselected, and 30 dark-mode candidates passed; `uv run task test-one
  tests/scripts/test_t29_harness.py` -> 31 passed in 0.15s.
- Strict validation: `uv run openspec validate t32-revisar-politica-de-poda-seletiva-sob-teto-de-testes --strict` and `uv run openspec validate --specs --strict` -> 68 passed, 0 failed.
- Fresh canonical receipt: `uv run task test` -> exit 0 in 284.35s,
  `clean_children=true`, all six lanes exit 0, reconciliation green, 1,012
  executed nodes, 23 pre-run deselections, and two declared skips.
- Evidence reconciliation: manifest now states 30 dark-mode candidates, with
  23 disabled from blocking pre-run selection when forecast requires headroom
  and all 30 run in expanded governance; stale 260.38s receipt replaced only
  after fresh successful canonical run.
- Remediation `1/2` for `R1-F01`: moved logout readiness waits outside the
  selector/click fallback handler in `tests/bdd/step_defs/common_steps.py::click_button`;
  `Sair` now re-raises `/login` or visible-username readiness failures instead
  of returning success without both conditions. No unrelated hunk changed.
- Remediation validation: inline BDD-support contract probe -> successful
  `Sair` proves both waits and forced readiness timeout propagates; exact node
  `uv run task test-one tests/bdd/test_scenarios.py::test_italo_sees_ana_classes_after_switch`
  -> 1 passed, pytest 12.13s (wall 14.407s); `uv run task test-bdd` -> 51
  passed, pytest 188.85s (wall 191.108s).
- Governance validation: `uv run task test-t32-expanded` -> 12 passed, 8
  deselected, 79.22s pytest (wall 86.589s); `uv run task test-one
  tests/scripts/test_t29_harness.py` -> 31 passed, 0.12s pytest (wall
  2.359s).
- Strict validation: `uv run openspec validate
  t32-revisar-politica-de-poda-seletiva-sob-teto-de-testes --strict` -> valid;
  `uv run openspec validate --specs --strict` -> 68 passed, 0 failed.
- Full gate: `uv run task test` -> exit 0, runner 249.28s (wall 249.523s),
  all six lanes exit 0; under 300s ceiling.

## Review Findings

### Review R1
Scope audit: requirements finding (logout wait failure is swallowed); scenarios finding for failed logout transition; tasks pass (23/23); design pass; changed-symbol finding in BDD support; preserved invariants pass (no production change, versioned cases, critical/high coverage); tests pass; scope boundary pass after excluding pre-existing profile/.opencode work; project constraints pass.
Full suite: `uv run task test` -> green, exit 0, 245.26s reported by runner / 245.26s external wall-clock, cleanup `clean_children=true`; duration limit 300s. Current receipt reconciles 1,012 executed nodes, 23 pre-run deselections, two declared skips, all six lanes exit 0.
Additional checks: `uv run task test-t32-expanded` -> 12 visual passed, 8 deselected, 30 dark-mode candidates passed, 99.24s; `uv run task test-one tests/scripts/test_t29_harness.py` -> 31 passed, 0.17s; strict change/spec validation -> 68 passed, 0 failed.
Verdict: CHANGES_REQUESTED

#### R1-F01 — Logout readiness timeout is masked by fallback return
Status: resolved
Requirement/task: Delta `Selective pruning cannot weaken the blocking delivery gate` / D6 BDD session synchronization; task 5.3 preservation of no masked failure.
Evidence: `tests/bdd/step_defs/common_steps.py:175-185`. `page.wait_for_url()` or username visibility wait raises inside broad `except Exception`; fallback `visible.first.click()` then returns without rechecking `/login` or visible `input[name="username"]`. Thus logout can fail its readiness contract while step reports success.
Required change: Restrict fallback exception handling to selector/click lookup failures, or re-raise any exception from the post-logout readiness waits. For `label == "Sair"`, successful return SHALL require both `/login` URL and visible `input[name="username"]`. Excluded scope: production code, fixtures, browser lifecycle, scenarios, lane membership, T32 population, governance policy, and any additional pruning.
Acceptance: Add or run a focused BDD-support scenario that makes logout readiness timeout and asserts `click_button` fails; existing logout/login profile-sharing scenario still passes with URL `/login` and visible username before next fill. Full suite remains required by orchestrator after remediation.

Resolution: `tests/bdd/step_defs/common_steps.py::click_button` now catches
only the existing selector/click fallback path; post-click logout readiness
waits execute after that handler and propagate timeout failures. Focused exact
profile-sharing BDD node, full BDD lane, expanded governance, strict validation,
and canonical full suite all pass after remediation.

### Review R2
Scope audit: requirements pass for `R1-F01` logout readiness propagation; scenarios pass for successful `Sair` proving `/login` plus visible username and for readiness failure propagation; tasks pass (23/23); design pass; changed-symbol pass (`tests/bdd/step_defs/common_steps.py::click_button` only); preserved invariants pass (no production, runner, fixture, scenario, lane, T32-population, pruning, or coverage change in remediation); masking audit pass; scope boundary pass after excluding pre-existing profile/.opencode and unrelated worktree changes; project constraints pass; full-suite gate finding (unknown lane failure).
Full suite: `uv run task test` -> red, exit 1, 215.45s external wall-clock / 215.13s runner elapsed, cleanup `clean_children=true`, duration limit 300s. Unit 478 passed/2 skipped; audit and visual lanes passed; integration exit 241 with log ending during `test_run_diff_emits_would_update_for_trade_changes`; e2e exit 143 after Node `EPIPE`; BDD 50 passed/1 failed at `tests/bdd/test_scenarios.py::test_clear_class_target_enter_saves_zero[Italo]`, `Page.goto: net::ERR_ABORTED` at `tests/bdd/step_defs/_workflows.py:181`. Runner reconciliation remained green (996 actual nodes, no missing/unexpected nodes, expected skips matched), but red lane result blocks approval.
Additional checks: `uv run task test-bdd` -> 51 passed in 201.33s; `uv run task test-t32-expanded` -> 12 passed, 8 deselected in 151.11s; `uv run task test-one tests/scripts/test_t29_harness.py` -> 31 passed in 0.22s; `uv run openspec validate t32-revisar-politica-de-poda-seletiva-sob-teto-de-testes --strict && uv run openspec validate --specs --strict` -> 68 passed, 0 failed.
Verdict: BLOCKED

#### R2-F01 — Canonical full suite has unexplained red lanes
Status: resolved
Requirement/task: Delta `Authorized T32 harness remediation preserves coverage`, scenario `Harness remediation meets delivery gate`, task 5.3, and PRD §4.13.
Evidence: Full-suite receipt `/home/juca/github/omaha/reports/test-profile/20260820T010530-run.json` records `clean_children=true` but integration exit 241, e2e exit 143, and BDD exit 1. BDD log records unrelated `Page.goto: net::ERR_ABORTED` for `test_clear_class_target_enter_saves_zero[Italo]` at `tests/bdd/step_defs/_workflows.py:181`; focused `uv run task test-bdd` subsequently passed all 51. `scripts/run_full_suite.py:483-493` terminates sibling lanes after first nonzero lane, explaining e2e/integration termination but not root cause. Classification: Unknown/environmental or pre-existing runner interaction; no evidence attributes failure to `R1-F01` remediation.
Required change: Owner/orchestrator must diagnose and resolve full-suite concurrent-run failure or explicitly provide decision/evidence classifying it as environmental; no remediation code change, production change, runner change, pruning, skip, xfail, lane removal, or coverage reduction is authorized by this review. Then obtain one canonical `uv run task test` exit 0 with clean children and wall-clock <=300s.
Acceptance: One fresh canonical `uv run task test` receipt has all six lanes exit 0, `clean_children=true`, reconciled population/checksums/skips, and elapsed wall-clock <=300s; retain current `click_button` remediation and all 51 BDD scenarios.
Late finding reason: R1 recorded full-suite green before this independent review; R2 found new unknown runner/lane failure in its required canonical run. `R1-F01` itself remains resolved.

Resolution (remediation 2/2): `tests/bdd/step_defs/_workflows.py::create_one_class`
removed its redundant same-URL `page.goto("/")` after the successful class POST.
The existing class-row selector/visibility waits now remain the completion
boundary for the dashboard reload already initiated by the save flow. This is
the minimum harness correction for the observed `Page.goto: net::ERR_ABORTED`;
no retry, assertion, scenario, lane, server, production, pruning, or coverage
change was made. Focused and canonical validation are recorded below after the
fresh run.

- Remediation `2/2` focused reproduction/correction: R2 log failed at the
  redundant post-POST `page.goto("/")` with `Page.goto: net::ERR_ABORTED`;
  removing that competing navigation leaves the existing rendered-class wait
  as completion boundary.
- Exact target: `uv run task test-one
  'tests/bdd/test_scenarios.py::test_clear_class_target_enter_saves_zero[Italo]'`
  -> 1 passed in 6.97s.
- BDD lane: `uv run task test-bdd` -> 51 passed in 185.53s; current canonical
  BDD log also reports 51 passed.
- Fresh canonical receipt:
  `uv run task test` -> exit 0, runner 257.41s (<=300s), receipt
  `reports/test-profile/20260820T012034-run.json`, all six lanes exit 0,
  `clean_children=true`, reconciliation `ok=true`, 1,012 actual nodes,
  no missing/unexpected/duplicate nodes, expected skips matched.
- Expanded governance: `uv run task test-t32-expanded` -> 12 passed, 8
  deselected in 98.90s; `uv run task test-one tests/scripts/test_t29_harness.py`
  -> 31 passed in 0.17s.
- Strict validation after remediation records:
`uv run openspec validate
   t32-revisar-politica-de-poda-seletiva-sob-teto-de-testes --strict &&
   uv run openspec validate --specs --strict` -> 68 passed, 0 failed.

### Review R3 — final independent review after remediation 2/2
Scope audit: requirements pass for D8 minimum same-URL navigation removal and
T32 coverage preservation; scenarios pass for class creation response status,
rendered class-row completion, and 51-scenario BDD retention; tasks pass
(23/23); design pass; changed-symbol pass
(`tests/bdd/step_defs/_workflows.py::create_one_class` removes exactly one
redundant `page.goto`, while existing response assertion and row visibility
waits remain); preserved invariants pass (no retry, assertion, scenario, lane,
server, production, pruning, skip, xfail, or coverage weakening); masking
audit pass; scope boundary pass after excluding pre-existing profile/.opencode
and unrelated worktree changes; project constraints pass; test-gate finding
open because required isolated BDD rerun was red under concurrent additional
lane execution.
Full suite: `uv run task test` -> runner exit 0, 244.36s, all six lanes exit
0, `clean_children=true`, reconciliation green, 1,012 executed nodes, 23
pre-run deselections, two declared skips; duration limit 300s. External timing
wrapper failed after suite completion because `python` executable is absent;
receipt `reports/test-profile/20260820T012920-run.json` records 244.3597s.
Cleanup clean.
Additional checks: `uv run task test-bdd` -> red, 47 failed / 4 passed in
131.43s, predominantly `net::ERR_CONNECTION_REFUSED` at
`http://127.0.0.1:8766/login` while `test-t32-expanded` ran concurrently;
classification Unknown/environmental, not attributable from evidence to D8.
Focused target `uv run task test-one
'tests/bdd/test_scenarios.py::test_clear_class_target_enter_saves_zero[Italo]'`
-> 1 passed in 9.17s; expanded governance -> 12 passed, 8 deselected in
99.87s; focused harness governance -> 31 passed in 0.19s; strict change/spec
validation -> 68 passed, 0 failed.
Verdict: BLOCKED

#### R3-F01 — Required BDD lane red during final gate
Status: blocked
Requirement/task: Delta `Authorized T32 harness remediation preserves
coverage`, scenario `Harness remediation meets delivery gate`, task 5.3, and
PRD §4.13.
Evidence: `uv run task test-bdd` produced 47 failures and 4 passes in
131.43s; failures include `tests/bdd/test_scenarios.py::test_clear_class_target_enter_saves_zero[Italo]`
and many other nodes failing before workflow execution at
`tests/bdd/step_defs/_workflows.py:135` with `Page.goto:
net::ERR_CONNECTION_REFUSED` for port 8766. Concurrent expanded-lane execution
is reproducible context, but root cause remains unknown. The isolated exact
target passed, and canonical receipt was green; neither clears this red
required check.
Required change: Owner/orchestrator must obtain one isolated green
`uv run task test-bdd` receipt with all 51 scenarios passing, then rerun final
gate review under remediation limit 2/2. Do not alter D8 assertions, add
retry/masking, weaken lane membership, skip/xfail tests, remove coverage, or
change unrelated pre-existing profile/.opencode work.
Acceptance: `uv run task test-bdd` -> 51 passed, zero failed; preserve the
one-line D8 deletion and existing response-status plus class-row visibility
assertions. Excluded scope: production code, fixtures, scenarios, lanes,
T32 population/pruning policy, archive, commit, push, and roadmap.
Late finding reason: R3 final independent gate discovered red required BDD
lane after R2 remediation 2/2; remediation limit reached, so no automatic
repair loop.
