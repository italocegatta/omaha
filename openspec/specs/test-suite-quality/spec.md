# test-suite-quality Specification

## Purpose
TBD - created by archiving change test-architecture-marker-and-dedup. Update Purpose after archive.
## Requirements
### Requirement: Delivery gate preserves focused protection during maintenance suspension
Runtime changes SHALL retain applicable product behavior tests and focused regression evidence. Owner-authorized I10 `maintenance-suspended` MAY suspend only parallel canonical `uv run task test` as mandatory apply/review/pre-push gate; it SHALL NOT delete, disable, skip, xfail, retry, mask, serialize, remove, or weaken tests, lanes, markers, coverage, commands, DB safety, receipts, cleanup, or fail-fast rules.

#### Scenario: Product change proceeds on focused evidence
- **WHEN** applicable focused product behavior tests pass while canonical gate is `maintenance-suspended`
- **THEN** review audits scope, coverage, command/result evidence, and suspension visibility
- **AND** canonical suite is recorded `NOT RUN — maintenance-suspended`, not falsely green

### Requirement: Additive MyProfit preview contract remains accepted by integration gate

The MyProfit sync-job integration contract SHALL preserve legacy preview keys
while accepting additive F65 `triage` data. The canonical blocking pre-push
integration gate SHALL continue to execute this contract through
`uv run task test-integration-parallel`; stale exact-shape expectations MUST be
corrected rather than hidden or bypassed.

#### Scenario: F65 additive preview passes without mutation regression

- **WHEN** `_process_downloaded_csv` publishes a preview containing
  `preview_id`, `auto_matched`, `unmatched`, `asset_classes`, and additive
  `triage`
- **THEN** the integration assertion accepts all five keys
- **AND** legacy keys, job status, no-Asset/Position/DbMutation-mutation
  behavior, cleanup, and security assertions remain enforced
- **AND** the pre-push hook continues to block on a real failure without
  skip, xfail, retry, or bypass behavior

#### Scenario: Reactivation requires exact diagnosis and one green suite
- **WHEN** isolated diagnosis resolves concurrent dynamic SQLite readonly-DB and BDD browser-timeout failures
- **THEN** one isolated six-lane `uv run task test` run SHALL be green with complete evidence and cleanup in `<=300s`
- **AND** any red lane, missing evidence, untrusted cleanup, or duration breach keeps gate suspended
### Requirement: Delivery gate requires full suite green
Runtime changes SHALL not be considered delivered while `uv run task test` is red.
Archive/merge must wait for a green full suite, not just a green subset.
For this slice, the canonical regression families are BDD and e2e browser/workflow tests, including import modal and visible navigation/import flows; a red result in any of them SHALL block delivery until the failing expectation is corrected in the owning test or runtime code.

Canonical routine SHALL include unit, integration, audit integration, E2E, BDD,
and retained visual coverage. Current suite state is reported by node IDs, lane
membership, checksums, and two exact skip identities; active node count is a
snapshot, not a delivery contract. T29's historical 1,043-node evidence is
dated history and is not authoritative for current population.

Every canonical `uv run task test` delivery run SHALL finish in <=300 seconds
through cleanup. This is a hard delivery ceiling, not telemetry. A green run
above the ceiling SHALL block review and archive until the measured bottleneck
is remediated without reducing tests, lanes, skips, or coverage.

#### Scenario: Full suite is red and delivery is blocked
- **WHEN** `uv run task test` fails
- **THEN** the change stays open
- **AND** no archive step marks it delivered

#### Scenario: Full suite exceeds duration ceiling
- **WHEN** `uv run task test` exits green after more than 300 seconds including cleanup
- **THEN** review returns `CHANGES_REQUESTED`
- **AND** no archive step marks it delivered
- **AND** remediation preserves the accepted test population and coverage

#### Scenario: Browser-visible change still needs full suite green
- **WHEN** a change touches runtime code, templates, routes, models, seed, migrations, or static assets
- **THEN** the full suite gate still applies
- **AND** the change cannot be archived on partial evidence

#### Scenario: Canonical regression family red blocks delivery
- **WHEN** any of the canonical regression families for this slice is red
- **THEN** delivery stays blocked
- **AND** the failing expectation is traced to test, code, or spec before the change can close

#### Scenario: Three consecutive full routines prove ceiling
- **WHEN** T29 claims canonical full-routine performance acceptance
- **THEN** three fresh `uv run task test` runs are green and <=300 seconds
- **AND** each run reports reconciled current lanes, classification coverage,
  protected coverage, and two exact skips

#### Scenario: Ceiling proof misses
- **WHEN** any fresh required proof run is red, exceeds 300 seconds, differs from
  manifest, or reports unclean children
- **THEN** T29 stops remaining proof runs and records measured alternatives
- **AND** it does not claim a <=300-second fix or remove further coverage

### Requirement: Canonical test bucket matrix stays documented and aligned
The test suite SHALL keep an explicit decision matrix for each named bucket: `unit`, `integration`, `audit_integration`, `bdd`, `e2e`, `visual`, and full-suite. For each bucket, the matrix MUST name the canonical task entrypoint, hook or CI owner, concurrency class (`serial`, `parallelizable`, or `too risky for now`), and the reason for any carve-out from another gate.

Changes to markers, task help text, hooks, CI jobs, or suite docs MUST update that matrix in the same slice so bucket drift is visible at review time.

The matrix MUST document which buckets produce coverage reports and which do not. Browser-backed buckets (`bdd`, `e2e`, `visual`) SHALL be documented as running without coverage instrumentation. Fast-lane buckets (`unit`, `integration`) SHALL be documented as the only producers of coverage data.

#### Scenario: BDD bucket is documented as serial
- **WHEN** an operator reads the canonical bucket matrix after T08
- **THEN** the `bdd` bucket is labeled `serial`
- **AND** the reason names the live-server and fixture-isolation constraints that block parallel execution today

#### Scenario: Audit cost center has an explicit owner
- **WHEN** an operator reads the canonical bucket matrix after T08
- **THEN** the `audit_integration` or equivalent heavy audit family has an explicit task or CI owner
- **AND** it is not silently omitted from hooks or CI without a written reason

#### Scenario: Coverage lane assignment is documented
- **WHEN** an operator reads the canonical bucket matrix after T13
- **THEN** the matrix shows `unit` and `integration` as coverage-producing buckets
- **AND** the matrix shows `bdd`, `e2e`, and `visual` as non-coverage buckets
- **AND** the canonical coverage command is `task coverage` (unit + integration only)

### Requirement: Every collected node has governed importance

Every collected test node/case SHALL receive exactly one explicit importance
classification from `critical`, `high`, `normal`, or `low`. Collection SHALL
fail when a node cannot be classified, and governance validation SHALL report
classification coverage for current suite state. Parametrized instances inherit
classification as individual collected node/cases.

#### Scenario: Unclassified node is detectable
- **WHEN** a new test node does not match the versioned importance policy
- **THEN** collection or focused governance validation fails
- **AND** it cannot silently enter any blocking lane

#### Scenario: Current suite state is transparent
- **WHEN** an operator inspects the governance report
- **THEN** it can distinguish current blocking nodes from versioned outside-lane
  cases, importance levels, lane checksums, and protected coverage

### Requirement: Ceiling policy selects only lowest importance before execution

If measured or prior-known cost in the versioned blocking manifest predicts that
canonical execution would exceed the hard 300-second ceiling, the runner SHALL
deterministically select only lowest-importance versioned cases before launching
blocking children. It SHALL never decide at timeout time. Disabled cases SHALL
remain discoverable in their source and runnable through a separately named
expanded lane. Each selection record SHALL include rationale, owner/date,
protected contract, replacement coverage, and measured or prior-known
cost/savings. The blocking runner SHALL not launch a second full-lane collection
pass solely to make this selection.

#### Scenario: Pre-run selection is deterministic
- **WHEN** preflight forecast exceeds 300 seconds
- **THEN** selection orders importance first, then known cost, then stable node ID
- **AND** selected cases are recorded before blocking execution starts

#### Scenario: Forecast is within ceiling
- **WHEN** preflight forecast is at or below 300 seconds
- **THEN** no new case is disabled by timing policy
- **AND** existing owner-approved outside-lane cases remain versioned and
  separately runnable

#### Scenario: Expanded lane restores selected cases
- **WHEN** an operator runs the named expanded lane
- **THEN** versioned outside-lane cases are collected and executable
- **AND** blocking output does not claim their execution as green coverage

### Requirement: Browser-backed throughput changes require repeated-run evidence
Any harness change that widens fixture scope, reuses browser/server resources, or changes the concurrency class of `bdd`, `e2e`, or `visual` suites SHALL be justified by repeated focused verification on the affected family. If a suite stays serial or keeps per-test browser launch because reuse is too risky, the decision record MUST say so explicitly.

Harness-only optimization MAY come from fixture reuse, bucket realignment, or duplicate-coverage pruning with a clear canonical owner. It MUST NOT rely on undocumented ignores, baseline refreshes, or moving product regressions into unrelated slices.

#### Scenario: Risky parallelism is rejected with a written reason
- **WHEN** repeated focused verification shows that a browser-backed suite still flakes or leaks state under broader reuse or concurrency
- **THEN** the suite remains in its safer current class
- **AND** the decision record marks it `too risky for now` with the observed reason

#### Scenario: Duplicate coverage can be pruned only with a canonical replacement
- **WHEN** T08 removes or consolidates a slow test for throughput reasons
- **THEN** review can point to the remaining canonical test that still owns the same contract
- **AND** the change does not replace the removed coverage with `skip`, `xfail`, or an undocumented carve-out

### Requirement: Masked-pass test constructs are forbidden
New or edited tests SHALL NOT introduce `skip`, `skipif`, `xfail`, `pytest.skip`, empty `pass` placeholders, or `NotImplementedError` used as stand-ins for missing coverage.
If a legacy carve-out is truly necessary, it MUST be explicitly allowlisted in the canonical spec / roadmap with a written reason.
CI verification SHALL include a masked-pass guard and SHALL run xfail unmasked (`--runxfail` or equivalent) so bypassed assertions cannot masquerade as green.

#### Scenario: New xfail without allowlist is rejected
- **WHEN** a diff adds `@pytest.mark.xfail` to a test file without explicit allowlist support
- **THEN** review or CI rejects the change
- **AND** the reason is "masked pass is not a delivery"

#### Scenario: Legacy allowlisted skip remains valid
- **WHEN** a pre-existing skip is already documented and allowlisted
- **THEN** the suite may continue to honor that carve-out
- **AND** the allowlist must name the file, reason, and owning spec or roadmap entry

### Requirement: No duplicate test coverage between retire-stubs and route tests
Duplicate-coverage tests MUST be deleted, not left in place.
Specifically, the "retire-stub" pattern (one assertion per file:
`GET /x → 302 → /`) MUST NOT co-exist with a route-level test
asserting the same redirect. The canonical location is the file
that owns the route contract (e.g. `test_t02_classes_routes.py` for
`/classes` redirects). The retire-stub file MUST be deleted.

#### Scenario: S02 classes redirect has one canonical test
- **WHEN** the change is applied
- **THEN** `tests/test_s02_t07_classes_retire.py` does not exist
- **AND** the assertion `GET /classes → 302 → /` lives in exactly
  one test function in `tests/test_t02_classes_routes.py`

#### Scenario: S03 assets redirect has one canonical test
- **WHEN** the change is applied
- **THEN** `tests/test_s03_t05_assets_retire.py` does not exist
- **AND** the assertion `GET /assets → 302 → /` lives in exactly
  one test (either `tests/test_t03_pages_routes.py` or the e2e
  redirect test under `tests/e2e/test_s03_asset_crud.py`)

#### Scenario: S04 import redirect has one canonical test
- **WHEN** the change is applied
- **THEN** `tests/test_s04_t09_import_retire.py` does not exist
- **AND** the assertions `GET /import → 302 → /` and `GET
  /import/review → 302 → /` live in exactly one test each in
  `tests/test_t03_imports_routes.py`

### Requirement: Docstrings must describe what the file tests
A test module's top-level docstring MUST describe the actual
assertions in the module. A docstring that lists a test name with
assertion A while the actual test asserts B is a
false-positive-bait pattern (an agent reading the docstring sees
the opposite of what the file does).

#### Scenario: S02 T01 docstring reflects allocation-is-informational
- **WHEN** the change is applied
- **THEN** the module docstring in `tests/test_s02_t01_classes_patch.py`
  describes `test_patch_class_allows_any_target_pct` as expecting
  status 200 (not 422) when the per-profile sum exceeds 100

#### Scenario: S02 T02 docstring reflects allocation-is-informational
- **WHEN** the change is applied
- **THEN** the module docstring in `tests/test_s02_t02_classes_post.py`
  describes `test_post_class_creates_even_with_non_100_sum` as
  expecting status 201 (not 422) when the per-profile sum exceeds 100

#### Scenario: S03 T01 docstring reflects allocation-is-informational
- **WHEN** the change is applied
- **THEN** the module docstring in `tests/test_s03_t01_assets_post.py`
  does not list `test_post_api_asset_per_class_sum_returns_422` in
  the "Five tests:" enumeration unless such a test exists in the
  file (today it does — line 233 — so this is a clarifying
  enumeration, not a removal)

### Requirement: Parametrized tests must include a positive case when the function returns positive values
Parametrized blocks MUST include a positive case (a case whose
expected value is a concrete non-sentinel result) when the function
under test is documented to return non-sentinel values in some
cases. A parametrize block whose every expected value is `None`
(or any sentinel for "no match") is a false-positive bait: if the
function under test were deleted, every parametrized case would
still pass.

#### Scenario: TestSuggestClassId has at least one positive case
- **WHEN** the change is applied
- **THEN** `tests/test_s04_t04_real_csv_flow.py::TestSuggestClassId`
  parametrizes at least one `(category, expected_id)` pair where
  `expected_id` is an integer class id (the fixture classes match
  the CSV category via `normalize_name` exact-match or substring
  match)

#### Scenario: A test that only parametrizes None-equivalents is rejected
- **WHEN** a test author adds a new
  `@pytest.mark.parametrize("category,expected", [("a", None),
  ("b", None), ("c", None)])` to any test file
- **THEN** code review rejects the change with the reason
  "parametrize block has no positive case — function may be deleted
  without breaking the test"

### Requirement: No loose percentage thresholds for binary outcomes
Tests MUST NOT use loose percentage thresholds (`ratio < X` or
`count < N`) for behavior that is logically `==`. Such assertions
MUST be tightened to `== 0` (or the actual expected count). Loose
thresholds let a partial bug masquerade as a passing test. The
"looseness budget" is zero for binary outcomes (the bug either
exists or it does not).

#### Scenario: S06 thresholds are exact
- **WHEN** the change is applied
- **THEN** `tests/e2e/test_s06_full_journey.py` asserts
  `mismatch_ratio == 0`, `len(wrong_assignments) == 0`, and the
  expected row count is an exact integer (derived from the
  parser output) — not `< 0.15`, `< 5`, or `>= 10`

#### Scenario: A test that accepts `ratio < X` for a binary outcome is rejected
- **WHEN** a test author adds `assert failure_rate < 0.05` to a
  test where the contract is "the function never fails"
- **THEN** code review rejects with the reason "tighten to
  `failure_rate == 0`; the contract is binary"

### Requirement: Visual gate tests assert structural content, not file size
A test whose name contains "visual gate" or "screenshot" SHALL
assert at least three structural data-testid markers on the rendered
page (class sections, asset rows, BRL totals) before checking the
screenshot file. The file-size assertion is a tie-breaker, not the
gate.

#### Scenario: S05 visual gate has structural pre-assertions
- **WHEN** the change is applied
- **THEN** `tests/e2e/test_s05_visual_gate.py`
  asserts `data-testid="class-summary-row"` count == 3,
  `data-testid="dashboard-asset-row"` count >= 1, and the page
  text contains `R$` before capturing the screenshot

#### Scenario: A screenshot-only test is rejected
- **WHEN** a test author adds a `test_visual_*` whose only
  assertion is `screenshot.stat().st_size > 1024`
- **THEN** code review rejects with the reason "visual gate tests
  must assert structural content; file size is not a gate"

### Requirement: No copy-string assertions in non-i18n tests
Translated UI strings in non-i18n tests MUST be paired with a
structural anchor (e.g. `data-testid="login-error"`) so a
copy-refactor does not produce a false-positive failure. The
translated string MAY be present as a secondary assertion for
i18n-correctness, but the structural anchor MUST come first.

#### Scenario: Auth error has structural anchor
- **WHEN** the change is applied
- **THEN** `tests/test_t03_auth.py::test_login_wrong_password_rerenders_form`
  asserts the presence of `data-testid="login-error"` as its
  primary check, with the localized "Usuário ou senha inválidos"
  string as secondary (or removed)

#### Scenario: A copy-only assertion is rejected
- **WHEN** a test author adds `assert "Bem-vindo, Italo" in body`
  without an accompanying `data-testid` or structural anchor
- **THEN** code review rejects with the reason "i18n copy is not
  a stable test anchor; pair with `data-testid`"

### Requirement: Performance baseline stays as dated snapshot of real suite lanes

The `tests/PERFORMANCE.md` file SHALL present benchmark data as a dated snapshot with environment and branch metadata. Its command examples SHALL use taskipy entrypoints (`uv run task test-unit`, `uv run task test-integration`, `uv run task test-e2e`, `uv run task test-bdd`, `uv run task test`, and related lane commands) instead of stale raw `pytest` examples. Its summary SHALL separate fast lane (unit + integration) from browser lane (e2e + BDD + visual), and SHALL call out BDD serial behavior when documenting browser execution.

#### Scenario: Commands use task wrappers

- **WHEN** a reader inspects the Commands block in `tests/PERFORMANCE.md`
- **THEN** taskipy entrypoints are shown instead of raw `pytest` commands

#### Scenario: Lanes remain separated

- **WHEN** a reader inspects the Summary or Lanes section in `tests/PERFORMANCE.md`
- **THEN** fast lane and browser lane are separated
- **AND** BDD serial behavior is stated where the browser lane is described

### Requirement: Audit manifest tracks every surviving test
The file `tests/AUDIT.md` SHALL exist and contain one row per
surviving test function (including parametrized instances). Each row
MUST include: test identifier (file::function), retention category
(`error-path`, `integration`, `spec-contract`, or `regression-guard`),
and justification text. The manifest is generated by
`scripts/generate_audit_manifest.py`.

#### Scenario: Manifest is present and complete
- **WHEN** `uv run pytest --collect-only -q` reports N tests
- **THEN** `tests/AUDIT.md` has at least N rows

#### Scenario: New test requires manifest update
- **WHEN** a developer adds a new test function in `tests/`
- **THEN** the same slice or PR MUST add a row to `tests/AUDIT.md`

#### Scenario: Test removed requires manifest update
- **WHEN** a developer removes a test function from `tests/`
- **THEN** the same slice or PR MUST remove the corresponding row from `tests/AUDIT.md`

### Requirement: Marker allow-lists must not overlap

A test file SHALL NOT appear in both `_INTEGRATION_PREFIXES` and `_UNIT_FILES` in `tests/conftest.py`. The marker logic checks `_INTEGRATION_PREFIXES` first; a dual-listed file is silently tagged `integration` even if its tests are pure functions, defeating the fast-lane split.

#### Scenario: Dual-listed file is silently tagged integration

- **WHEN** a file is listed in both `_INTEGRATION_PREFIXES` and `_UNIT_FILES`
- **THEN** the `pytest_collection_modifyitems` hook tags it `integration` because the integration check runs before the unit check
- **AND** the file's tests are excluded from `task test-unit`
- **AND** the overlap is a defect that MUST be resolved by removing the file from one list

#### Scenario: No overlap after fix

- **WHEN** a contributor inspects `tests/conftest.py`
- **THEN** the intersection of `_INTEGRATION_PREFIXES` entries and `_UNIT_FILES` entries is empty
- **AND** every test file in `tests/*.py` appears in at most one allow-list

### Requirement: T32 selective pruning remains versioned and auditable

Owner-approved selective pruning SHALL keep each pruned case discoverable in
its owning test file with stable node/case identity and an explicit
`t32_pruned` prioritization rationale. The blocking visual task SHALL exclude
only this named marker; it SHALL NOT delete the case, remove its suite, or
claim omitted execution as green coverage. Each record SHALL include category,
redundancy group, protected contract, replacement node IDs and lanes, measured
before/after evidence, owner, date, and record version. T32's approved record
is authoritative in `tests/AUDIT.md` and `openspec/roadmap.md`, dated
2026-08-19.

#### Scenario: Pruned case remains discoverable

- **WHEN** an operator collects `tests/visual/test_snapshots.py` without the
  blocking marker expression
- **THEN** each approved T32 node/case remains present with its stable ID
- **AND** its source test carries the `t32_pruned` rationale

#### Scenario: Blocking visual lane excludes only approved T32 cases

- **WHEN** `uv run task test-visual` runs
- **THEN** it excludes only `t32_pruned` cases
- **AND** canonical replacement coverage remains in the blocking lane
- **AND** no new skip, xfail, placeholder, whole-suite removal, or silent lane
  reduction is introduced

#### Scenario: T32 record has complete contract evidence

- **WHEN** review inspects `tests/AUDIT.md`
- **THEN** all 12 approved visual cases have node ID, category, group,
  protected contract, replacement node/lane, owner/date/version, and measured
  evidence
- **AND** the accepted blocking population/checksum remains reconciled

### Requirement: BDD harness remains deterministic during expanded-lane concurrency

The canonical BDD task SHALL complete its 51 collected scenarios deterministically
both in isolation and while `test-t32-expanded` runs concurrently. The BDD lane
SHALL remain serial without skipping, xfail-ing, deselecting, removing, or pruning
scenarios.

#### Scenario: Isolated BDD lane is green
- **WHEN** `uv run task test-bdd` runs from fresh test-server/DB state
- **THEN** all 51 BDD scenarios pass
- **AND** zero scenario fails with `net::ERR_CONNECTION_REFUSED` on port 8766

#### Scenario: Expanded lane does not invalidate BDD
- **WHEN** `uv run task test-bdd` and `uv run task test-t32-expanded` run concurrently
- **THEN** BDD reports 51 passed and zero failed
- **AND** expanded lane retains governed selected cases
- **AND** no BDD scenario is removed from collection or execution

#### Scenario: BDD refusal blocks delivery rather than being masked
- **WHEN** BDD loses its live server or port 8766 during execution
- **THEN** lane reports failure with server/process/port evidence
- **AND** no browser retry, skip, xfail, or lane reduction claims success

### Requirement: Selective pruning is versioned and contract-preserving

Any proposed removal or consolidation of test coverage under the duration
ceiling SHALL be recorded at stable pytest node/case granularity, including
parametrized instances. The record MUST classify each candidate as
`parametrized-case`, `example`, `snapshot`, or `redundant-low-value-assert`,
group overlapping candidates, name the protected requirement/scenario or
behavioral contract, identify replacement node IDs and lanes, and include
measured savings, owner, date, and record version. No whole suite or whole
bucket SHALL be treated as one removable candidate.

#### Scenario: Candidate has complete retention record

- **WHEN** a contributor proposes removing or consolidating a test node
- **THEN** the change record names exact node/case ID, category, redundancy
  group, protected contract, replacement coverage, lane, measured savings,
  owner, date, and version
- **AND** review can reconcile record against the audit manifest and lane
  population

#### Scenario: Parametrized case is classified individually

- **WHEN** only one instance of a parametrized test is proposed for removal
- **THEN** the record identifies that parametrized node instance rather than
  the containing function or suite
- **AND** remaining instances and replacement coverage stay explicit

#### Scenario: Redundant coverage lacks canonical replacement

- **WHEN** a candidate has no surviving node that owns the same protected
  contract
- **THEN** the pruning proposal is rejected
- **AND** it is not replaced with a skip, xfail, placeholder, or undocumented
  carve-out

### Requirement: Selective pruning cannot weaken the blocking delivery gate

Selective pruning SHALL NOT remove an entire suite, mask a failure, or be
decided during a timeout or a green run above the `<=300s` ceiling. Approved
cases MAY remain versioned with an explicit `t32_pruned` rationale and be
excluded only from the standard blocking lane after the owner records scope,
date, owner, schedule, and evidence. A later Apply MUST preserve protected
behavior, update versioned population/audit evidence, and prove canonical
`uv run task test` success within the PRD §4.13 ceiling.

#### Scenario: Apply uses recorded gate disposition

- **WHEN** a pruning record has owner-approved
  `gate_disposition: outside-blocking-standard-lane`
- **THEN** Apply keeps its source node/case versioned and excludes only the
  named marker from the standard blocking task
- **AND** manifest, lane, and replacement evidence remain explicit

#### Scenario: Owner records blocking-gate retention

- **WHEN** owner records dated approval that removed cases remain in the
  blocking canonical gate
- **THEN** any later Apply keeps those cases in that gate's required evidence
- **AND** the change still proves full-suite green and `<=300s`

#### Scenario: Owner records outside-gate execution

- **WHEN** owner records dated approval that removed cases may run outside the
  blocking gate
- **THEN** the record names schedule, responsible owner, execution command,
  and retained evidence
- **AND** no silent skip, xfail, lane deletion, or coverage claim replaces
  that evidence

#### Scenario: Timeout is not pruning authorization

- **WHEN** a canonical run exceeds 300 seconds, fails, or leaves unclean
  children
- **THEN** the run blocks delivery and triggers bottleneck investigation
- **AND** no case is removed or gate disposition chosen from that run alone

#### Scenario: Whole-suite removal is proposed

- **WHEN** a proposal removes or disables an entire suite or bucket to meet
  the ceiling
- **THEN** review rejects the proposal
- **AND** PRD §4.13 full-suite, lane, and coverage obligations remain active

### Requirement: Authorized T32 harness remediation preserves coverage

The owner-authorized 2026-08-19 T32 expansion SHALL permit only measured
harness scheduling, resource-isolation, or teardown remediation and stale audit
wording normalization. It SHALL preserve every versioned test, lane, marker,
skip, xfail, and coverage contract except the already approved 12
`t32_pruned` visual cases outside the standard blocking lane.

#### Scenario: Harness remediation meets delivery gate

- **WHEN** Apply changes directly linked test harness scheduling, isolation, or
  teardown
- **THEN** one canonical `uv run task test` run exits 0 with clean children and
  wall-clock duration at or below 300 seconds
- **AND** population, lane checksums, skip identities, and protected coverage
  remain reconciled

#### Scenario: Safe remediation cannot meet ceiling

- **WHEN** the bounded harness remediation cannot produce a green canonical run
  within 300 seconds
- **THEN** Apply stops and reports profiling evidence and exact blocker
- **AND** no test, lane, marker, skip, xfail, coverage contract, or timeout
  decision is weakened

### Requirement: Expanded T32 governance classifies and selects cases

Every collected node/case SHALL receive exactly one explicit importance level:
`critical`, `high`, `normal`, or `low`. Missing classification SHALL fail
collection or governance validation. Active node count SHALL remain a transparent
current-state report, not an immutable delivery contract.

If measured or prior-known preflight cost predicts a breach of the 300-second
ceiling, selection SHALL happen before blocking children launch and SHALL choose
only lowest-importance cases in deterministic importance/cost/node order. A
within-ceiling forecast SHALL select no new case. Selected cases remain
versioned, separately runnable, and recorded with rationale, owner/date,
protected contract, replacement coverage, and measured or prior-known cost.

#### Scenario: Classification coverage is complete
- **WHEN** governance validates collected nodes, including parametrized cases
- **THEN** every node has one importance marker
- **AND** an unclassified node fails the gate

#### Scenario: Preflight selection preserves expanded execution
- **WHEN** forecast exceeds the ceiling
- **THEN** only lowest-importance cases are selected before execution
- **AND** the named expanded lane can run selected cases without masking failure

#### Scenario: Already-disabled cases are not selected again

- **WHEN** pre-run governance evaluates current blocking nodes
- **THEN** cases already outside the standard lane are excluded from candidate
  selection
- **AND** selection uses only currently blocking, explicitly classified cases
- **AND** every selected case remains runnable in the named expanded lane
