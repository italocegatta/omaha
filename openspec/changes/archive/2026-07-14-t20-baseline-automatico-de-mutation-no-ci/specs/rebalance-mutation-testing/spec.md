## ADDED Requirements

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
