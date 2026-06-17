# test-suite-quality Specification

## Purpose
TBD - created by archiving change test-architecture-marker-and-dedup. Update Purpose after archive.
## Requirements
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

