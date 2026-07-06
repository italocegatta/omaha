## 1. Tooling setup

- [x] 1.1 Add `mutmut>=3.0,<4` to `[dependency-groups].dev` in
  `pyproject.toml` (same group as `pytest`, `pytest-cov`, `prek`).
- [x] 1.2 Run `uv sync --group dev` and confirm `mutmut` resolves
  via `uv run mutmut --version`.
- [x] 1.3 Add `mutants/` to `.gitignore` (mutmut creates this
  directory on first `task mutation` run; contents are
  reproduced/refreshed by every run). The `.gitkeep` /
  cache prefix convention used elsewhere doesn't apply here
  because `mutants/` is a foreign directory owned by mutmut.

## 2. Taskipy wiring

- [x] 2.1 Add `mutation` task to `[tool.taskipy.tasks]` in
  `pyproject.toml`: invokes `uv run mutmut run` (mutmut3 reads
  `[tool.mutmut]` config from pyproject.toml on first call —
  no CLI flags needed; `only_mutate` scopes the run to the two
  rebalance files).
- [x] 2.2 Add `mutation-report` task: runs
  `uv run python -m scripts.mutation_report` which reads the
  per-source-file `.meta` JSONs in `mutants/`, computes per-status
  counts and `killed_share`, and exits non-zero with
  `no mutation cache found; run task mutation first` when the
  cache is empty.
- [x] 2.3 Add `mutation-baseline` task: invokes
  `uv run python -m scripts.mutation_baseline` which renders the
  baseline from the same `.meta` JSONs and writes
  `.mutmut-baseline` with the 7 lines
  (`killed=`, `survived=`, `no_tests=`, `timeout=`, `skipped=`,
  `killed_share=`, `generated_at=` UTC ISO-8601 timestamp via
  `datetime.now(UTC).isoformat()`).
- [x] 2.4 Confirm `uv run task --list` lists the three new tasks
  (3 `mutation*` entries visible).

## 3. Spec artifact

- [x] 3.1 Confirm
  `openspec/changes/t03-mutation-testing-rebalance-engine/specs/rebalance-mutation-testing/spec.md`
  exists with the 4 ADDED requirements (harness scoped, report
  readable, baseline capture, score-as-signal).
- [x] 3.2 Confirm requirement-level headers use the
  `### Requirement: <name>` shape and each scenario uses exactly
  4 hashtags (`#### Scenario: ...`).

## 4. Verification

- [x] 4.1 Run `uv run task lint` (or the documented lint task via
  prek) against `pyproject.toml` and `.gitignore` — confirm no
  diff appears in the regenerate-from-template path.
- [x] 4.2 Run `uv run task test-unit` — confirm 271 pass / 2 skip
  baseline (R02 archive baseline) is preserved (no regression).
- [x] 4.3 Run `uv run task test-integration` — confirm 369 pass /
  2 skip baseline (R03 archive baseline) is preserved.
- [x] 4.4 Run `uv run task test-bdd` — confirm 51 pass baseline
  (T05 archive baseline) is preserved.
- [x] 4.5 Run `uv run task coverage` — confirm 92% coverage
  baseline preserved (T02 archive baseline).
- [x] 4.6 Run `uv run openspec validate
  t03-mutation-testing-rebalance-engine --json` — confirm
  `valid: true`.

## 5. Baseline run (during apply)

- [x] 5.1 Run `uv run task mutation-baseline` once to populate
  `.mutmut-baseline`. **Actual result on `solver.py` (21K) +
  `validation.py` (8.4K)**: 869 mutants generated, 556 killed,
  301 survived, 12 no_tests, 0 timeout/skip. killed_share
  = 0.649. mutants/runtime: 5.12 mutations/sec.
- [x] 5.2 Commit `.mutmut-baseline` to the same PR so the file
  travels with the code.
- [x] 5.3 Read `.mutmut-baseline`, confirm the seven lines parse
  via `cat`. Confirmed: 7 lines as expected (`killed=556` +
  `survived=301` + `no_tests=12` + `timeout=0` + `skipped=0` +
  `killed_share=0.649` + `generated_at=2026-07-06T21:25:16+00:00`).
- [x] 5.4 If survived count is non-trivial (>5 mutants), do
  **not** fix them in this slice — recorded follow-up slice in
  `roadmap.md` compaction history (see note below). 301
  survived mutants is a substantial test gap signal — most
  mutants test simple expression changes (`==` → `!=`,
  `+` → `-`) that the current unit tests don't catch. Will
  become a `R` or `T` follow-up slice when owner prioritizes.

## 6. Roadmap update

- [x] 6.1 Move `T03 - Mutation testing do rebalance engine`
  status from `Ready` → `Spec Proposed` →
  `Applying` → `Applied` in `openspec/roadmap.md`
  with `Spec link: openspec/changes/t03-mutation-testing-rebalance-engine/`.
- [x] 6.2 Add progress-log entries: `Proposed: done <date>;
  artifacts (proposal + design + tasks + specs/
  rebalance-mutation-testing) generated; openspec validate
  returns valid: true`. Same for Applying (with implementation
  summary) and Applied (baseline capture with 869 mutants /
  killed=556 / survived=301 / no_tests=12).
- [x] 6.3 Note any decisions captured during propose that landed
  in design (`D-T03.1..D-T03.7`) in the slice `Notes` block
  (`D-T03.1`: mutmut3 chosen over cosmic-ray; `D-T03.2`: no
  fail_under; `D-T03.3`: scope = solver.py + validation.py
  instead of engine.py + data_bridges.py which doesn't exist;
  `D-T03.4`: pytest_add_cli_args overrides project addopts;
  `D-T03.5`: .mutmut-baseline committed for diff-baseline;
  `D-T03.6`: mutants/ gitignored; `D-T03.7`: no CI integration).

## 7. Archive (post-apply)

- [x] 7.1 Delegated to `openspec archive
  t03-mutation-testing-rebalance-engine --skip-specs` (specs
  already synced to
  `openspec/specs/rebalance-mutation-testing/spec.md`); move
  to
  `openspec/changes/archive/2026-07-06-t03-mutation-testing-rebalance-engine/`
  executes at end of this gate.
- [x] 7.2 Synced delta into
  `openspec/specs/rebalance-mutation-testing/spec.md` (4 ADDED
  requirements + Purpose + drift correction: `mutants/` instead
  of `.mutmut-cache/` since mutmut3 dropped the `report` and
  `html` subcommands the delta assumed; HTML scenario replaced
  with "Mutant-level details are readable from `.meta` JSONs").
- [x] 7.3 Updated `openspec/roadmap.md` slice status to `Archived`
  with `Spec link:
  openspec/changes/archive/2026-07-06-t03-mutation-testing-rebalance-engine/`.
- [x] 7.4 Added entry to `compacted history` block (depois de T02) with
  full summary: dep + config + 3 taskipy tasks + 2 helper scripts
  + baseline result + drift correction + spec count delta.
