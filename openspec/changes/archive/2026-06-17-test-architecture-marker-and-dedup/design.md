# Design: Test architecture marker + dedup + false-positive patterns

## Context

The Omaha test suite has 41 test files (~150 tests) split across
unit, integration, and e2e layers. A deep audit (recorded in
`openspec/changes/test-architecture-marker-and-dedup/proposal.md`)
found four structural problems that produce a misleading green
signal:

1. The path-based marker rule in `tests/conftest.py:137-156` tags
   ~25 DB+TestClient files as `unit`, defeating the purpose of
   `task test-integration`.
2. Three "retire" stub files duplicate redirect assertions that
   already exist in the main route tests, and two T0* files
   duplicate assertions from S0* files.
3. Three S0* module docstrings describe a 422-rejecting contract
   that the actual tests do not enforce (the contract moved to
   "allocation is informational" but the docstrings were never
   rewritten).
4. Three false-positive-bait patterns in the e2e suite (loose
   thresholds, screenshot-only gate, all-`None` parametrization)
   let real regressions pass.

This design covers the technical approach for each fix. Production
code (`src/omaha/**`) is not touched. No new external dependencies.

## Goals / Non-Goals

**Goals:**
- `task test-integration` runs the full DB+TestClient family
  (S02/S03/S04 + T0* routes + T04 e2e + T06 + T99) and only that.
- `task test-unit` runs pure-function tests (parsers, validators,
  audit logic) and only that — no alembic subprocess, no TestClient
  boot, no Playwright.
- Every behavior assertion in the suite has exactly one canonical
  home; retire-stubs are gone.
- Module docstrings describe what the file actually tests.
- Loose thresholds (S06) and weak gates (S05 visual) are tightened
  to exact-equality assertions backed by the parser / DOM.
- Parametrized blocks that have no positive case gain one.

**Non-Goals:**
- No new test framework, no pytest plugin, no custom matcher.
- No pixel-diff against a baseline (the S05 visual gate is
  strengthened structurally; baseline image capture stays).
- No coverage tool reconfiguration. Existing coverage thresholds are
  unchanged.
- No `tests/audit_integration/` directory creation (the existing
  marker rule already reserves that path; it just does not yet
  exist on disk).
- No production refactors.

## Decisions

### D1. Explicit path list in `pytest_collection_modifyitems` (not pattern matching)

The current implementation uses three branches with
`"/tests/e2e/" in path` and `"/tests/audit_integration/" in path`,
then everything-else → `unit`. This is too coarse: a file in
`tests/test_t02_assets_routes.py` clearly hits DB+TestClient, but
falls into the `unit` default.

We replace this with an explicit allow-list of integration paths.
The `set` of integration prefixes is:

```
{
    "tests/e2e/",                                  # carve-out: no marker
    "tests/audit_integration/",                    # carve-out: integration
    "tests/s02_", "tests/s03_", "tests/s04_",      # S02/S03/S04 route families
    "tests/test_t02_",
    "tests/test_t03_auth.py",
    "tests/test_t03_pages_routes.py",
    "tests/test_t03_imports_routes.py",
    "tests/test_t03_assets_e2e.py",
    "tests/test_t03_classes_e2e.py",
    "tests/test_t04_e2e.py",
    "tests/test_t06_",
    "tests/test_t99_",
}
```

Each integration file matches if `path.startswith(prefix)`. Files
in `tests/e2e/` are explicitly skipped (no marker added) so the
Playwright suite stays filtered by path. Files in
`tests/audit_integration/` get `integration` explicitly. Everything
else in `tests/*.py` gets `unit`. Module-level `pytestmark` wins
over the rule (already supported).

**Alternatives considered:**
- *Per-file `pytestmark` declarations*: explicit but requires editing
  ~25 files instead of one. More diff, same outcome.
- *Glob pattern* (`fnmatch`): brittle when filenames change; the
  explicit prefix list survives renames within a family.
- *Convention-over-config via test class hierarchy*: too invasive,
  requires restructuring every file.

### D2. File deletion for retire-stubs, not inline removal

The three retire-stub files (`test_s02_t07_classes_retire.py`,
`test_s03_t05_assets_retire.py`, `test_s04_t09_import_retire.py`)
each contain exactly one or two assertions that already exist in
the main route files. We delete the retire files outright. The
canonical home stays where it is today:

| Assertion | Canonical home |
|---|---|
| `GET /classes → 302 → /` | `tests/test_t02_classes_routes.py::test_get_classes_redirects_to_dashboard` |
| `GET /assets → 302 → /` | `tests/e2e/test_s03_asset_crud.py::test_assets_route_redirects_to_dashboard` |
| `GET /import → 302 → /` | `tests/test_t03_imports_routes.py::test_get_import_redirects_to_dashboard` |
| `GET /import/review → 302 → /` | `tests/test_t03_imports_routes.py::test_review_redirects_to_dashboard` |

For `test_t03_pages_routes.py`, we do **not** add a `GET /assets`
redirect test (the e2e already covers it). The retire-stub file
exists solely to keep a TestClient-level smoke; the e2e covers it
at the browser level. Keeping both was redundant.

For T0* ≡ S0* duplicates inside the main route files
(`test_t02_classes_routes.py::test_get_classes_redirects_to_dashboard`,
`test_t03_classes_e2e.py::test_snapshot_replaces_pre_existing`,
`test_t03_imports_routes.py::test_review_redirects_to_dashboard`),
we keep the S0* or T0* version per the table above and delete the
duplicate.

**Alternatives considered:**
- *Comment out instead of delete*: leaves dead code; future agent
  re-enables it; clutters the file. Git history preserves the
  removed assertion if anyone needs it.
- *Move assertions to a single "redirects" file*: requires a new
  file and renames test ids; more churn than value.

### D3. Tighten S06 thresholds by deriving expected counts from the parser

The current `test_s06_full_journey.py` accepts `mismatch_ratio <
0.15`, `wrong_assignments < 5`, and `row_count >= 10`. These are
loose percentages that mask regressions affecting a minority of
rows.

We change the test to derive the expected counts from the parser
output. The flow:

1. Parse `tests/fixtures/posicao_italo.csv` once at test setup.
2. Capture the exact parsed-row count, the exact set of
   `broker_ticker → category` pairs, and the exact set of
   `broker_ticker → expected_class` pairs (the latter from a
   curated map that mirrors the test author's intent).
3. After `commit`, iterate every committed `Position` row and
   assert `asset_class.name == _EXPECTED_CLASS[ticker]` with
   exact equality — zero mismatches allowed.

The `_EXPECTED_CLASS` dict (lines 178-227 today) is kept and
expanded where the parser output disagrees with the current
hardcoded map (some tickers may map to different classes if the
matcher was updated). The mismatch counter and the loose
thresholds disappear.

### D4. S05 visual gate: structural assertions before the screenshot

`test_s05_visual_gate.py` today asserts only
`screenshot_path.stat().st_size > 1024`. An empty page with
whitespace can exceed 1KB. We change the test to:

1. Wait for `[data-testid="class-summary-row"]` count == 3.
2. Assert `[data-testid="dashboard-asset-row"]` count >= 1.
3. Assert `R$` is present in `<main>` text (proves BRL formatting
   fired).
4. Then capture the screenshot and assert it exists.

The screenshot file is still saved for the human visual review; the
1KB size check is removed.

**Alternatives considered:**
- *Pixel diff against an M001 baseline*: requires committing a
  binary baseline + a perceptual diff library. Out of scope; can
  be a follow-up.
- *Drop the screenshot entirely*: loses the human artifact. The
  screenshot stays; it just no longer carries the gate weight.

### D5. Positive parametrization for `TestSuggestClassId`

`test_s04_t04_real_csv_flow.py::TestSuggestClassId` parametrizes 9
real CSV categories, all with `expected_id = None`. This is
false-positive bait: deleting `suggest_class_id` would not break
the test. The fix is to seed the test with at least one class
whose normalized name matches a CSV category, then parametrize a
`(category, expected_id)` pair with a concrete id.

Concretely: the test creates the three default classes plus one
extra class whose name normalizes to match a CSV category
(e.g. add `"Internacional"` so the CSV row `"Internacional"` rows
match it). The parametrize block gets one new entry like
`("Internacional", 4)` and the existing nine `None` entries stay.
The `expected_id` for the new case is the integer class id
returned by the seed helper.

### D6. Docstring rewrite — not removal

The three stale docstrings (`test_s02_t01_classes_patch.py`,
`test_s02_t02_classes_post.py`, `test_s03_t01_assets_post.py`)
are rewritten to describe the actual assertions. The new text is
shorter and points at the specific tests by name. We do not
remove the docstrings — they carry the per-class sum gate context
("Allocation is NEVER blocked by sum-to-100") that the tests now
verify.

## Risks / Trade-offs

- **[R1] Marker rule rename risk** — Some operator's local branch
  might have additional `tests/test_*` files that hit DB+TestClient
  and were relying on the silent-`unit` default. *Mitigation*: the
  explicit list is grep-able; the PR description lists every file
  that changes marker. `task test-unit` output is captured in the
  PR description for comparison.
- **[R2] Deleting duplicate tests hides regressions** — If a
  retire-stub test diverges from its canonical twin (e.g. one
  starts testing redirect + auth-free, the other stays redirect-
  only), deleting the retire-stub removes that extra coverage.
  *Mitigation*: every retire-stub is byte-equivalent to its
  canonical twin today; the deletion is a pure prune.
- **[R3] Tightening S06 may surface a latent bug** — The
  `mismatch_ratio < 0.15` was probably set because the test author
  saw edge cases in real data. Tightening to `== 0` may fail today
  on a real edge. *Mitigation*: the test runs in CI before merge;
  if it fails, the test author investigates the actual mismatch
  (which is a real bug worth fixing) or expands `_EXPECTED_CLASS`
  to include the edge case (which is a documentation fix).
- **[R4] Visual gate weakening risk** — Removing the 1KB size
  check loses the "is the page literally empty?" gate. *Mitigation*:
  the structural pre-assertions (3 class sections + asset rows +
  `R$` present) are strictly stronger than "file > 1KB".
- **[R5] Positive parametrization adds maintenance** — When the
  CSV fixture gains a new category, the new test class name must
  be added or the positive case breaks. *Mitigation*: the
  fixture is small and the test author already maintains
  `_AUTO_MATCH_NAMES`; one more entry in the same dictionary is
  the same churn.
- **[R6] Path-list drift** — A future slice might add a new test
  family with a new prefix (e.g. `tests/test_t10_*.py`) that hits
  DB. The explicit list won't pick it up; the file silently becomes
  `unit`. *Mitigation*: the docstring on the conftest function and
  the PR template reminder ("did you add the new path to the
  marker rule?") address this; long-term, a pytest plugin could
  derive the list from a glob, but that's out of scope.

## Migration Plan

1. **Apply the spec changes**: rewrite
   `tests/conftest.py::pytest_collection_modifyitems` with the
   explicit path list (D1).
2. **Run the test matrix once**:
   `task test-unit && task test-integration && task test-e2e`.
   Compare to pre-change run; capture the diff for the PR
   description.
3. **Delete retire-stubs** (D2): three files removed in a single
   commit so the diff is reviewable.
4. **Delete T0* ≡ S0* duplicates**: remove the three duplicate
   assertions. Re-run `task test-integration` to confirm coverage
   unchanged.
5. **Tighten S06** (D3): rewrite the loose assertions. Run the
   test; if it fails on a real edge, expand `_EXPECTED_CLASS` or
   investigate the underlying mismatch.
6. **Tighten S05 visual gate** (D4): add structural pre-assertions.
   Capture the new screenshot; visually inspect for parity with the
   previous screenshot.
7. **Add positive parametrization to `TestSuggestClassId`** (D5):
   add a fourth class to the seed and one positive parametrize
   entry.
8. **Rewrite the three stale docstrings** (D6).
9. **Update `pyproject.toml:99-101`** task help text to reflect the
   corrected marker rule.
10. **Re-run the full matrix** one more time. Commit. Open PR.

**Rollback**: the change touches only `tests/**` and
`pyproject.toml:99-101`. `git revert` reverts cleanly. No DB
migration, no production deploy.

## Open Questions

- **OQ1**: Does `tests/audit_integration/` exist anywhere? `find`
  reports no such directory. The marker rule reserves the path for
  future tests; if no such tests are planned, the path entry in the
  rule is dead code. *Suggested resolution*: leave the entry (it
  costs nothing) and document it as the convention for future
  audit-pipeline tests.
- **OQ2**: Should the marker rule's path list live in
  `pyproject.toml` (under `[tool.pytest.ini_options]`) instead of
  hardcoded in `conftest.py`? Pros: visible to ops without reading
  Python. Cons: requires a custom pytest hook to read the config
  list, since `pytest_collection_modifyitems` does not have a
  built-in path-list mechanism. *Suggested resolution*: keep in
  `conftest.py` for now; revisit if ops asks.
- **OQ3**: Should the marker rule emit a warning (not an error)
  when a new `tests/test_*.py` file lands without an explicit
  marker? *Suggested resolution*: yes, add a `pytest.warns` call
  for any file that is not in either the integration allow-list or
  the e2e carve-out. Cheap, catches future drift.
