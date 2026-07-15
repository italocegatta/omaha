# rebalance-mutation-testing Specification

## Purpose

Mutation testing as a structural audit tool for the rebalance
solver. The T03 slice added `mutmut` to the project's dev
toolchain plus a `task mutation` / `task mutation-report` /
`task mutation-baseline` triplet under `pyproject.toml` so that
mutations inserted into `src/omaha/rebalance/solver.py` and
`src/omaha/rebalance/validation.py` are run against the project's
existing pytest collection, and the resulting kill/survive counts
are surfaced as a signal (not a gate) on the developer's local
machine.

Per the slice's D-T03.2 decision, the killed share is read-only —
the slice does not promote mutation score to a CI gate. Promoting
the score to a `fail_under` threshold or a CI-blocking check is
explicitly a follow-up slice (the "Promotion to a gate" scenario
below contracts this boundary).

The actual mutation cache lives in `mutants/` (mutmut3 convention,
created on the first `task mutation` run), NOT in
`.mutmut-cache/` as referenced in the original T03 delta spec —
mutmut3 dropped the `report` and `html` subcommands that the
delta assumed. The textual summary (`task mutation-report`) and
baseline capture (`task mutation-baseline`) read directly from the
per-source-file `mutants/<path>.meta` JSON files mutmut3 writes.

## Requirements

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

### Requirement: Mutation report is human-readable via task wrapper

The system SHALL provide `task mutation-report` which runs
`uv run python -m scripts.mutation_report`. The script reads every
`mutants/**/*.meta` JSON (recursive glob from the `mutants/`
directory, since mutmut3 nests them under `<source_paths>/<path>`
— e.g. `mutants/src/omaha/rebalance/solver.py.meta`), aggregates
the per-status counts, computes `killed_share = killed / (killed
+ survived)` (excluding `no_tests` from the denominator), and
prints both to stdout. Per-mutant drill-down is available via the
on-disk `.meta` JSONs (each carries `exit_code_by_key`,
`type_check_error_by_key`, `durations_by_key`, and
`estimated_durations_by_key`).

#### Scenario: Textual summary shows status counts and killed share

- **WHEN** `task mutation-report` runs after at least one
  `task mutation` (so `mutants/` has data)
- **THEN** stdout contains one line per status with its count and a
  final `killed_share = killed / (killed + survived)` formatted to
  3 decimal places.

#### Scenario: Mutant-level details are readable from `.meta` JSONs

- **WHEN** a maintainer wants to inspect surviving mutants
  file-by-file or function-by-function
- **THEN** `mutants/<source-path>.meta` is a JSON document whose
  `exit_code_by_key` mapping lets the reader enumerate every
  generated mutant and its surviving/killed state.

#### Scenario: Empty cache produces an actionable error

- **WHEN** `task mutation-report` runs and no prior `task mutation`
  populated `mutants/`
- **THEN** the wrapper prints a one-line message starting with
  `no mutation cache found; run task mutation first` and exits
  non-zero
- **AND** no `.meta` placeholder files are created by this probe.

### Requirement: Baseline of mutation results is captured in a committable file

The system SHALL provide `task mutation-baseline` which runs
`uv run python -m scripts.mutation_baseline` to read the same
`mutants/**/*.meta` JSONs and write a textual report to a
top-level file named `.mutmut-baseline`. The file MUST contain the
current counts (killed, survived, no_tests, timeout, skipped), the
killed share value, and a UTC ISO-8601 timestamp marking when the
baseline was generated. The file MUST be human-readable and
parsable by `diff` so future runs can compare against the
baseline via `diff .mutmut-baseline <new-report>` or similar.

#### Scenario: Baseline captures the seven baseline lines

- **WHEN** `task mutation-baseline` completes against a populated
  `mutants/`
- **THEN** `.mutmut-baseline` exists at the repo root and contains
  lines for `killed=`, `survived=`, `no_tests=`,
  `timeout=`, `skipped=`, `killed_share=`, and `generated_at=`
  (UTC ISO-8601).

#### Scenario: Baseline is regenerable and idempotent

- **WHEN** `task mutation-baseline` is run twice
- **THEN** `.mutmut-baseline` is overwritten with the most recent
  counts; no second copy (e.g. `.mutmut-baseline.bak`) is left
  behind; the baseline file remains a single source of truth.

#### Scenario: Baseline file is plain text and parses via diff

- **WHEN** a future mutation run produces a new report and the
  user runs `diff .mutmut-baseline <new-report-path>`
- **THEN** `diff` exits non-zero iff any numeric count has
  changed, and exits zero iff every count matches the baseline.

### Requirement: Mutation score is a signal, not a CI gate

The system SHALL expose mutation score as a readable signal (via
the textual summary and baseline file) but SHALL NOT block CI on a
`fail_under` threshold in the first iteration. `task mutation`
MUST exit zero (success) regardless of how many mutants survive;
the killed share is informational only and is not promoted to a
blocking gate without an explicit owner decision documented as a
follow-up slice. Promoting the score to a gate (via a `fail_under`
setting, a new CI job, or a similar mechanism) is explicitly out
of scope for this capability.

#### Scenario: `task mutation` exits zero even when mutants survive

- **WHEN** `task mutation` finishes with at least one `survived`
  mutant recorded in `mutants/<path>.meta`
- **THEN** the task exit code is zero and the workflow's CI gate
  (if it were to invoke the task) would not fail on the kill rate.

#### Scenario: Baseline does not assert a minimum threshold

- **WHEN** a maintainer reads `.mutmut-baseline` to decide whether
  to merge a PR
- **THEN** no portion of the file is a "minimum score" or
  "fail_under" assertion; the file documents observed counts and
  is compared against future reports via plain `diff`, not via
  any scripted threshold check inside `task mutation-baseline`.

#### Scenario: Promotion to a gate is an explicit follow-up

- **WHEN** the owner decides (in a future slice) to promote the
  mutation score to a CI gate
- **THEN** that promotion is recorded as a separate slice (e.g.
  `t03.1-promote-mutation-score-to-ci-gate` or analogous), with
  its own proposal that documents the threshold, the CI job
  structure, and the caching strategy for mutants across runs.

### Requirement: Baseline is regenerated automatically in CI on merge to main

The system SHALL provide a GitHub Actions job named `mutation-baseline`
that runs on every push to `main` (not on pull requests), executes
`task mutation` followed by `task mutation-baseline`, and commits the
updated `.mutmut-baseline` file back to `main` automatically.

#### Scenario: Job triggers on push to main only

- **WHEN** a commit is pushed to the `main` branch
- **THEN** the `mutation-baseline` job runs `task mutation-ci`
- **AND** the job does NOT trigger on pull request events

#### Scenario: Job commits updated baseline to main

- **WHEN** `task mutation-ci` completes successfully
- **THEN** the job runs `git add .mutmut-baseline`
- **AND** the job runs `git commit -m "chore: update mutation baseline [skip ci]"`
- **AND** the job runs `git push` to update `.mutmut-baseline` on `main`

#### Scenario: Job skips commit when baseline is unchanged

- **WHEN** `task mutation-ci` completes but `.mutmut-baseline` content
  is identical to the committed version
- **THEN** `git diff --cached .mutmut-baseline` exits zero
- **AND** the job skips the commit and push steps

#### Scenario: Job runs a fresh mutation (no cache)

- **WHEN** the `mutation-baseline` job starts
- **THEN** any existing `mutants/` directory is deleted before
  `task mutation` runs
- **AND** the mutation run processes all 8 files from scratch

#### Scenario: Job does not block on mutation score

- **WHEN** `task mutation` completes with survived mutants
- **THEN** the job exit code is zero regardless of killed share
- **AND** the baseline file is committed even if the score decreased
  from the previous baseline

### Requirement: mutation-ci taskipy task chains mutation and baseline

The system SHALL provide a `mutation-ci` taskipy task that runs
`task mutation` followed by `task mutation-baseline` as a single
invocation, failing fast if the mutation run errors.

#### Scenario: mutation-ci chains both tasks

- **WHEN** `task mutation-ci` is invoked
- **THEN** `task mutation` runs first
- **AND** if `task mutation` exits zero, `task mutation-baseline` runs
- **AND** if `task mutation` exits non-zero, the chain stops and
  `mutation-ci` exits non-zero

#### Scenario: mutation-ci is usable locally

- **WHEN** a developer runs `task mutation-ci` from the repo root
- **THEN** the same chain executes as in CI
- **AND** `.mutmut-baseline` is updated locally
