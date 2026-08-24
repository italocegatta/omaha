## Context

F65 finalization created local commit `544e175d14e74a931ebba6b52bf0d858a2b5f52d` (`chore(F65): finalize triagem de ativos`), with `main` one commit ahead of `origin/main` and not behind. Current working tree also contains unrelated roadmap edits and untracked F63/import-review change artifacts; I11 MUST not adopt or alter those files.

Pre-push is installed at `.git/hooks/pre-push` and delegates to the resolved `prek` binary with `hook-type=pre-push`. `prek.toml` defines validation-only pre-push hooks in order: ruff, uv-lock, commitizen-branch, and local `pytest-integration` with `entry = "uv run task test-integration-parallel"`, `pass_filenames = false`, and priority 5. `pyproject.toml` defines that task as the integration marker bucket with xdist `-n auto --dist loadgroup`, excluding audit integration.

Reproducible evidence already captured for this proposal:

```text
uv run task test-one tests/test_myprofit_sync_jobs.py
18 passed, 1 failed in 3.56s
FAIL tests/test_myprofit_sync_jobs.py::test_internal_csv_handoff_reuses_preview_shape_and_does_not_mutate
tests/test_myprofit_sync_jobs.py:307
Extra items in the left set: 'triage'

uv run prek run --stage pre-push --last-commit --fail-fast --show-diff-on-failure
ruff: Passed
uv-lock: Skipped (no files to check)
pytest-integration: Failed
418 passed, 1 failed, 28 warnings in 73.11s
same failing node and extra `triage` key
```

The hook command temporarily stashed existing unstaged changes and restored them, proving the diagnostic must preserve dirty-worktree boundaries. No push, commit, force operation, bypass, or source repair was performed.

## Code Map

- `.git/hooks/pre-push:1-14` — generated executable hook; resolves its directory, selects `.venv/bin/prek` or `PATH`, and invokes `hook-impl` for `pre-push`. Inspect only; do not hand-edit generated plumbing unless diagnosis proves regeneration is the blocker.
- `prek.toml:80-122` — pre-push stage declarations. Ruff is validation-only, uv-lock is lockfile validation, commitizen validates branch policy, and local `pytest-integration` delegates to taskipy with no filenames. Preserve priority and blocking semantics.
- `pyproject.toml:235-243` — canonical test tasks. `test-integration-parallel` owns the pre-push integration command and its collection boundary. Do not replace it with raw pytest or alter marker/exclusion/xdist behavior.
- `tests/test_myprofit_sync_jobs.py:289-321`, symbol `test_internal_csv_handoff_reuses_preview_shape_and_does_not_mutate` — F59 internal CSV handoff regression contract. It currently asserts an exact four-key preview shape at line 307, while F65 intentionally adds additive `preview["triage"]`; this is confirmed test drift candidate.
- `openspec/roadmap.md:662-671` — F65 finalization and remediation evidence. It records the local commit, focused green F65 evidence, and the exact unrelated-looking MyProfit assertion drift blocking push. I11 consumes this evidence; it does not edit F65 artifacts or status during proposal.
- `openspec/specs/prek-hooks/spec.md:7-181` — stable hook contract. It already requires validation-only pre-push and the canonical parallel integration task. I11 does not alter this hook requirement.
- `openspec/specs/test-suite-quality/spec.md:6-17` — stable maintenance-suspension/focused-evidence contract. I11 adds one narrow requirement below this capability for additive MyProfit preview consumers; it does not alter suspension policy.
- `openspec/changes/archive/2026-07-10-i03-regularizar-plumbing-do-pre-push/` — prior `&&` parsing correction; constrains hook entries to independent taskipy invocations.
- `openspec/changes/archive/2026-07-15-i05-otimizar-hooks-pre-commit-e-pre-push/` — prior duplicate-unit removal and parallel integration decision; preserve current pre-push boundary.
- `openspec/changes/archive/2026-07-15-i06-reorganizar-hooks-prek-modificar-em-pre-push/` — prior stage split; preserve validate-only pre-push semantics.

## Current Relevant Flow

1. Git push invokes `.git/hooks/pre-push` unless `core.hooksPath` resolves another hook directory. The hook passes control to `prek hook-impl --hook-type=pre-push`.
2. `prek` loads `prek.toml`, selects files from the last commit/ref range, then runs pre-push hooks by priority. Current evidence shows ruff passes, uv-lock has no applicable files, and the first blocking hook is `pytest-integration`.
3. The local hook runs `uv run task test-integration-parallel`; taskipy resolves the canonical integration task from `pyproject.toml`, and pytest-xdist executes DB/TestClient integration tests with existing loadgroup semantics.
4. The failing test creates an owned MyProfit sync job, processes CSV bytes through `MyProfitSyncService._process_downloaded_csv`, reads `status_for_profile`, and checks preview compatibility without mutating Asset/Position/DbMutation counts. F65 now adds `triage` additively to this preview, so exact equality against only legacy keys fails before mutation assertions can complete.
5. After a surgical test expectation update, apply MUST rerun the focused test, then the same pre-push diagnostic with fail-fast. Any newly exposed failure becomes a new evidence boundary, not permission for speculative cleanup.

Boundary conditions:

- Existing unstaged/untracked files are foreign to I11 and must remain byte-for-byte unchanged.
- F65 production code, archived F65 artifacts, snapshot/audit/commit state, and remote history are outside this slice.
- `uv run task test` stays executable but is `NOT RUN — maintenance-suspended` for this gate; focused applicable tests and the blocking pre-push hook remain mandatory.
- Normal push acceptance requires no `--no-verify`, no force option, and no hook/test disablement. Proposal does not execute push.

## Goals / Non-Goals

**Goals:**

- Preserve reproducible first-failure evidence and exact diagnosis command.
- Repair only the confirmed compatibility assertion drift in `tests/test_myprofit_sync_jobs.py`, if apply re-confirms the same failure.
- Preserve additive F65 `triage` output and all existing legacy preview keys, job lifecycle, no-mutation assertions, hook ordering, taskipy entrypoint, and enforcement.
- Prove focused test success, pre-push hook success, unchanged hook configuration, and owner-authorized ordinary push success.
- Stop/escalate when failure is foreign, pre-existing outside I11, environmental, remote-related, or requires unrelated scope.

**Non-Goals:**

- No application, connector, route, model, migration, seed, F65 implementation, F65 artifact/spec, or UI change.
- No `prek.toml`, `.git/hooks/pre-push`, or `pyproject.toml` change unless a fresh diagnostic proves one of those files is the first blocker; current evidence does not.
- No hook bypass, skip, xfail, retry, masked assertion, test deletion, lane removal, timeout relaxation, or full-suite substitution.
- No force push, remote-history rewrite, commit creation/amendment, push execution during Propose, or broad refactor.

## Decisions

### D1 — Treat current integration failure as confirmed test drift

**Choice:** Apply may change only the exact preview-key assertion in `test_internal_csv_handoff_reuses_preview_shape_and_does_not_mutate`, after capturing `git diff HEAD~1`/`git log -1` and reproducing the focused failure.

**Rationale:** The first failing hook and node are deterministic. F65's additive `triage` contract is already present in archived F65 evidence/specs, and the test's exact four-key set is the incompatible legacy assertion. Production output, compatibility arrays, and no-mutation behavior remain valid.

**Alternative rejected:** Remove `triage` from production output or weaken the hook. Both would regress F65 or mask the gate rather than repair the stale consumer.

### D2 — Keep hook and task boundaries unchanged

**Choice:** Do not alter `.git/hooks/pre-push`, `prek.toml`, or `pyproject.toml` for current evidence.

**Rationale:** The actual pre-push run proves ruff passes, uv-lock is correctly skipped, and the canonical integration task starts and reaches all tests. I03/I05/I06 already define and validate this plumbing.

**Alternative rejected:** Replace integration hook with a raw command, skip the failing test, remove the hook, or change parallelism. These violate PRD §4.8/§4.13 and destroy enforcement.

### D3 — Diagnose each post-repair failure once, then stop on scope mismatch

**Choice:** Repeat the exact fail-fast pre-push command after the surgical correction. Repair only a directly related confirmed blocker; stop and escalate for foreign, environmental, remote, or unrelated failures.

**Rationale:** First-failure order prevents speculative batch edits. It also protects unrelated dirty worktree files and prevents turning I11 into a general suite or hook cleanup.

### D4 — Add one narrow test-quality delta

**Choice:** Add one `test-suite-quality` requirement covering additive MyProfit preview compatibility at the blocking integration boundary.

**Rationale:** Existing `prek-hooks` requirements already describe unchanged validation-only pre-push behavior. The confirmed blocker is a stale test consumer, so a minimal test-quality delta makes the required compatibility and non-masking oracle durable without changing hook configuration. If apply proves a stable hook requirement inaccurate, stop for owner scope decision rather than widening this delta.

## Implementation Decisions

### ID1 — Make pre-push replay see only bounded intended correction

**Context:** After the surgical assertion correction, an exact
`uv run prek run --stage pre-push --last-commit --fail-fast --show-diff-on-failure`
replay still failed because prek stashed unstaged I11 changes before running;
the integration process therefore executed the last committed F65 test. The
focused test and the corrected assertion were independently green.

**Decision:** Preserve hook and task configuration. For validation only, stage
the one intended test file, replay the exact non-bypassed hook, then restore the
index with `git restore --staged -- tests/test_myprofit_sync_jobs.py`. Do not
commit, push, alter hook/task files, or stage unrelated paths.

**Impact:** This preserves blocking enforcement while making replay observe the
bounded correction. Passing replay evidence is valid only with exact one-file
temporary staging; ordinary push remains owner-authorized work outside this
Apply pass.

**Evidence:** Unstaged replay reproduced `418 passed, 1 failed` at the stale
assertion; staged replay passed `ruff`, skipped `uv-lock` with no applicable
files, passed `pytest-integration`, and passed `commitizen check branch`. The
index was restored and working-tree correction remained unstaged.

## Change Map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `tests/test_myprofit_sync_jobs.py::test_internal_csv_handoff_reuses_preview_shape_and_does_not_mutate` | Exact preview key set contains only `preview_id`, `auto_matched`, `unmatched`, `asset_classes` | Exact expected set includes additive `triage`, while legacy keys and subsequent no-mutation/job assertions remain intact | Accept F65's confirmed additive preview contract without changing production behavior |
| `.git/hooks/pre-push` | Generated `prek` dispatcher | No change expected | Hook dispatch passes diagnosis; generated file is not repair target |
| `prek.toml` pre-push hooks | Ruff/uv-lock/commitizen/integration validation boundary | No change expected | I05/I06 contract and run evidence show plumbing is healthy |
| `pyproject.toml` `test-integration-parallel` | Canonical xdist integration task | No change expected | Task is first-failure executor; preserve marker/exclusion/parallel boundary |
| `openspec/specs/prek-hooks/spec.md` | Existing validation-only pre-push requirement | No change | Requirement remains true; hook plumbing is not the blocker |
| `openspec/changes/i11-diagnosticar-bloqueio-de-push-e-plano-de-regularizacao/specs/test-suite-quality/spec.md` | No I11 requirement | Add one additive-preview compatibility requirement with blocking pre-push scenario | Preserve F65 payload and prevent stale exact-shape assertions from masking or bypassing the gate |

## Risks / Trade-offs

- **[Risk]** Focused assertion repair exposes another failure. **Mitigation:** rerun fail-fast, record exact first new node, and stop if it is outside I11 or foreign/pre-existing; no speculative repair.
- **[Risk]** Dirty worktree causes prek stash/restore or obscures diff ownership. **Mitigation:** capture status and hook path first, inspect `git diff HEAD~1`, never stage/adopt unrelated files, and verify their status/content boundary after diagnostics.
- **[Risk]** A remote/permission failure remains after local gate turns green. **Mitigation:** classify it as remote/environmental, do not alter remote history or force-push, and escalate owner decision.
- **[Risk]** Test assertion could be weakened rather than aligned. **Mitigation:** require exact additive key assertion plus existing status, no-mutation, filename, and cleanup assertions; no broad subset assertion.
- **[Risk]** Canonical full-suite status is misreported. **Mitigation:** record `NOT RUN — maintenance-suspended`; run only applicable focused commands per PRD §4.13.

## Migration Plan

1. Apply records baseline status/tracking/hook-path evidence and rechecks `git diff HEAD~1` before editing.
2. Apply confirms focused failure, makes one surgical test assertion correction, and inspects the diff for only that correction.
3. Apply runs `uv run task test-one tests/test_myprofit_sync_jobs.py`, then `uv run prek run --stage pre-push --last-commit --fail-fast --show-diff-on-failure`.
4. Apply records hook order, exit codes, test counts, and unchanged enforcement. During maintenance suspension, canonical full suite is recorded as not run.
5. Only after owner authorization, normal `git push` is attempted without bypass or force flags. If it fails for a new foreign/environmental/remote reason, stop and escalate; do not expand I11.

Rollback is surgical: revert only the assertion line if owner rejects the contract or validation proves F65 output is not the source of truth. Do not revert F65 commit, alter remote history, or touch unrelated worktree files.

## Open Questions

- Owner must authorize the post-apply ordinary push and validate the evidence before F65 leaves `Blocked`; proposal does not perform that push.
- If push remains blocked after local hooks pass, owner must decide whether remote/credential/permission remediation belongs outside I11; no remote mutation is authorized here.
