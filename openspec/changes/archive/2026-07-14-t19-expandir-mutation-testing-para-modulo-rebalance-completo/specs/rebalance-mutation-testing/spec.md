## MODIFIED Requirements

### Requirement: Mutation testing harness scoped to rebalance solver and validation

The system SHALL provide a mutation testing harness invocable via
`task mutation` that mutates exclusively the following files in
`src/omaha/rebalance/`:

1. `solver.py`
2. `validation.py`
3. `engine.py`
4. `policy.py`
5. `postprocessing.py`
6. `builders.py`
7. `glue.py`
8. `constants.py`

The harness MUST run the project's existing pytest collection against
each mutant and report per-mutant status as one of `killed`,
`survived`, `no_tests`, `timeout`, or `skipped`. No runtime code
under `src/omaha/rebalance/` SHALL be modified by the harness
itself; mutation is applied only as a transient overlay applied
and reverted per mutant by the mutator tool.

#### Scenario: Harness scopes to the documented files only

- **WHEN** `task mutation` is invoked from the repo root
- **THEN** the mutator runs against all 8 files listed above
- **AND** per-mutant `.meta` JSON files inside `mutants/` carry a
  `path` matching one of those 8 files and no others.

#### Scenario: Per-mutant status is persisted to disk

- **WHEN** `task mutation` finishes (full or partial run) and
  `mutants/<path>.meta` is read afterwards
- **THEN** the file lists every discovered mutant with an
  `exit_code_by_key` mapping that resolves to one of `killed`,
  `survived`, `no_tests`, `timeout`, or `skipped`
- **AND** subsequent reads do not re-run mutation.

#### Scenario: Harness does not require internet or external services

- **WHEN** `task mutation` runs in an offline environment with the
  project's pytest collection already cached locally
- **THEN** the harness completes without network access (the
  collection does not call quote providers, broker APIs, or other
  outbound services during mutation).

#### Scenario: Parallelism keeps wall-clock under 20 minutes

- **WHEN** `task mutation` runs against the full 8-file scope
  (~2500-3400 estimated mutants)
- **THEN** the mutator uses configured parallelism
  (`num_workers` in `[tool.mutmut]`) to evaluate multiple mutants
  concurrently
- **AND** total wall-clock time SHALL NOT exceed 20 minutes on a
  machine with at least 4 CPU cores.

#### Scenario: Test selection covers all newly mutated files

- **WHEN** a mutant is inserted into `engine.py`, `policy.py`,
  `postprocessing.py`, `builders.py`, `glue.py`, or `constants.py`
- **THEN** the per-mutant pytest invocation includes the
  corresponding test files from `pytest_add_cli_args_test_selection`
  (e.g., `test_rebalance_builders.py` for `builders.py` mutants)
- **AND** integration-heavy test files (`test_rebalance_page.py`,
  `test_rebalance_route.py`) are excluded to keep per-mutant
  invocation fast.
