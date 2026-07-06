## ADDED Requirements

### Requirement: Mutation testing harness scoped to rebalance engine and data bridges

The system SHALL provide a mutation testing harness invocable via
`task mutation` that mutates exclusively
`src/omaha/rebalance/solver.py` and
`src/omaha/rebalance/validation.py` in the first iteration. The
harness MUST run the project's existing pytest collection against
each mutant and report per-mutant status as one of `killed`,
`survived`, `no_tests`, `timeout`, or `skipped`. No runtime code
under `src/omaha/rebalance/` SHALL be modified by the harness
itself; mutation is applied only as a transient overlay applied
and reverted per mutant by the mutator tool.

#### Scenario: Harness scopes to the documented files only

- **WHEN** `task mutation` is invoked from the repo root
- **THEN** the mutator runs against
  `src/omaha/rebalance/solver.py` and
  `src/omaha/rebalance/validation.py` only
- **AND** `mutmut results | head` reports mutants whose `path`
  matches one of those two file paths and no others.

#### Scenario: Per-mutant status is reported

- **WHEN** `task mutation` finishes a partial run (background or
  interrupted) and the user invokes `mutmut results` against the
  cache
- **THEN** the output lists each mutant with one of `killed`,
  `survived`, `no_tests`, `timeout`, or `skipped`
- **AND** the result is persisted to `.mutmut-cache/` so subsequent
  `mutmut report` calls can re-read the same data without re-running.

#### Scenario: Harness does not require internet or external services

- **WHEN** `task mutation` runs in an offline environment with the
  project's pytest collection already cached locally
- **THEN** the harness completes without network access (the
  collection does not call quote providers, broker APIs, or other
  outbound services during mutation).

### Requirement: Mutation report is human-readable via task wrapper

The system SHALL provide `task mutation-report` which wraps the
mutator's `report` subcommand to produce both a textual summary
(stdout) and an HTML view (written to
`.mutmut-cache/html/index.html`). The textual summary MUST include
counts of each status (`killed`, `survived`, `no_tests`, `timeout`,
`skipped`) plus the killed share computed as
`killed / (killed + survived)` (i.e. excluding `no_tests` from the
denominator). The HTML view MUST list per-mutant details grouped by
file and function so a reader can drill into which mutants
survived.

#### Scenario: Textual summary shows status counts and killed share

- **WHEN** `task mutation-report` runs after at least one
  `task mutation` (so the cache has data)
- **THEN** stdout contains one line per status with its count and a
  final `killed_share = killed / (killed + survived)` formatted to
  3 decimal places.

#### Scenario: HTML view groups mutants by file and function

- **WHEN** `task mutation-report` runs
- **THEN** `.mutmut-cache/html/index.html` exists and contains
  sections per mutated file, each file section lists mutants
  grouped by function name with their surviving/killed annotation
  visible on each row.

#### Scenario: Empty cache produces an actionable error

- **WHEN** `task mutation-report` runs and no prior `task mutation`
  populated `.mutmut-cache/`
- **THEN** the wrapper prints a one-line message starting with
  `no mutation cache found; run task mutation first` and exits
  non-zero
- **AND** no empty HTML file is left behind in `.mutmut-cache/html/`.

### Requirement: Baseline of mutation results is captured in a committable file

The system SHALL provide `task mutation-baseline` that runs
`task mutation` to completion (or resumes from cache if invoked
twice) and writes a textual report to a top-level file named
`.mutmut-baseline`. The file MUST contain the current
counts (killed, survived, no_tests, timeout, skipped), the killed
share value, and a UTC ISO-8601 timestamp marking when the
baseline was generated. The file MUST be human-readable and
parsable by `diff` so future runs can compare against the
baseline via `diff .mutmut-baseline <new-report>` or similar.

#### Scenario: Baseline captures the three primary counts

- **WHEN** `task mutation-baseline` completes against a fresh
  cache
- **THEN** `.mutmut-baseline` exists at the repo root and contains
  lines for `killed=`, `survived=`, `no_tests=`,
  `timeout=`, `skipped=`, `killed_share=`, and `generated_at=`
  (UTC ISO-8601).

#### Scenario: Baseline is regenerable and idempotent

- **WHEN** `task mutation-baseline` is run twice (the second
  invocation resumes from the cache produced by the first)
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
the textual summary, HTML report, and baseline file) but SHALL
NOT block CI on a `fail_under` threshold in the first iteration.
`task mutation` MUST exit zero (success) regardless of how many
mutants survive; the killed share is informational only and is
not promoted to a blocking gate without an explicit owner
decision documented as a follow-up slice. Promoting the score to
a gate (via a `fail_under` setting, a new CI job, or a similar
mechanism) is explicitly out of scope for this capability.

#### Scenario: `task mutation` exits zero even when mutants survive

- **WHEN** `task mutation` finishes with at least one `survived`
  mutant in the cache
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
