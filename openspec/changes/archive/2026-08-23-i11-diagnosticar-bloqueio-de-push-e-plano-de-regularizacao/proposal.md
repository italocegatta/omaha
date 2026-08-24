## Why

F65 has a local commit (`544e175`, one commit ahead of `origin/main`), but its normal pre-push gate is red. Reproduction reaches the integration hook after `ruff` passes and `uv-lock` is skipped, then fails because `tests/test_myprofit_sync_jobs.py::test_internal_csv_handoff_reuses_preview_shape_and_does_not_mutate` still requires the pre-F65 exact preview key set and rejects additive `triage`.

I11 records this first-failure evidence and permits only the smallest correction confirmed by the gate, preserving hook/test enforcement until a non-bypassed push succeeds.

## What Changes

- Preserve the current prek pre-push entrypoint and blocking integration gate.
- Correct only the confirmed assertion drift in `tests/test_myprofit_sync_jobs.py`, if focused validation confirms it remains the first failure after proposal handoff.
- Validate the focused MyProfit job contract and the exact pre-push sequence (`ruff`, `uv-lock`, integration hook) without removing, weakening, skipping, xfail-ing, retrying, or bypassing any check.
- Record HEAD/tracking state, resolved hook path, first failing hook/test, before/after diff boundary, focused results, and normal push acceptance evidence in the change dossier.
- Escalate instead of repairing when the next failure is foreign, pre-existing outside this slice, environmental, remote/permission-related, or requires an unrelated file or change.

## Capabilities

### New Capabilities

None. I11 introduces no product capability.

### Modified Capabilities

- `test-suite-quality`: require MyProfit preview integration assertions to preserve legacy keys while accepting additive F65 `triage`, with the existing pre-push integration gate remaining blocking.

## Impact

- **Diagnostic boundary:** `.git/hooks/pre-push`, `prek.toml`, `pyproject.toml`, repository tracking state, and F65 finalization evidence in `openspec/roadmap.md`.
- **Confirmed correction candidate:** `tests/test_myprofit_sync_jobs.py` exact preview-shape assertion at the internal CSV handoff contract; additive F65 `triage` data must remain accepted without changing production behavior.
- **Validation:** focused test task, hook-stage validation, delta/stable OpenSpec validation, and owner-authorized normal push evidence. Canonical `uv run task test` remains `NOT RUN — maintenance-suspended`; focused applicable tests remain mandatory.
- **Explicitly untouched:** application features, F65 implementation artifacts/specs, unrelated working-tree changes, remote history, force-push/bypass paths, and broad hook/task refactors.
