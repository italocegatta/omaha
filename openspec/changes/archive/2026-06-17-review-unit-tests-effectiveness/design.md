## Context

The Omaha unit-test surface is concentrated in nine files under
`tests/` (no `tests/e2e/`, no `tests/integration/`). Almost every
"unit" test currently imports the same session-scoped test database
that the route tests use, because the conftest in `tests/conftest.py`
boots a real `omaha.main.app`, runs alembic, and seeds the DB once
per pytest session. Only the four `test_audit_*.py` files plus
`test_phase02_tokens.py`, `test_t01_asset_target.py`, `test_t01_smoke.py`,
and `test_t02_csv_import.py` exercise pure code paths. Even those
are coupled to `src/omaha/static/app.css` via `skipif(not
APP_CSS_PATH.exists())` guards.

The audit tooling (`omaha.audit.*`) is the densest target. It has
its own dependencies (`coloraide`, `tinycss2`, `beautifulsoup4`,
`jinja2`), no DB or FastAPI dependencies, and a small public API
that we want to lock down tightly. Today the tests don't lock
down much — many assertions would still pass if the underlying
math went wrong.

Three production refactors land in this change because the
existing tests didn't catch them:

1. `parse_stylesheet` defined twice in `css_parser.py`.
2. `_build_registry_from_stylesheet` duplicated in `inventory.py`.
3. `composite_over` short-circuits without validating the backdrop.

These are documented in the proposal and are not optional — the
test rewrite is incomplete without them, because the new
`composite_over` validation tests would fail without the fix.

## Goals / Non-Goals

**Goals:**

- Replace tautological / dataclass / library assertions with
  structural ones that catch real regressions.
- Collapse near-identical tests into `@pytest.mark.parametrize`
  blocks while preserving every input/expected pair.
- Make every unit test runnable without `omaha.config.settings`
  resolving to a DB-backed URL (i.e., without the conftest's
  session-scoped DB fixture).
- Make every unit test runnable when `src/omaha/static/app.css`
  is missing, by moving the one or two "well-formedness" tests
  out of the unit set.
- Fix the three production bugs uncovered during review in the
  same change.
- Add `unit` and `integration` pytest markers so the
  `task test-unit` shortcut actually excludes everything that
  needs a DB / HTTP / docker.

**Non-Goals:**

- Touching route tests, e2e tests, or anything under `tests/e2e/`.
  Those have their own coverage contract and the user explicitly
  scoped them out.
- Adding new public-API surface to `omaha.audit.*` — the goal is
  to test what exists, not extend it.
- Rewriting `audit/cli.py` or `audit/report.py`'s rendering logic.
  We change what they emit only insofar as the bug fixes above
  require (the `parse_stylesheet` dedupe is invisible externally;
  the registry dedupe is invisible externally; the
  `composite_over` validation is a behavior tightening that the
  affected callers already handle via the `ValueError` path).
- Setting coverage gates (`--cov-fail-under`). The prek pipeline
  already runs coverage in `task coverage`; gating is a
  separate decision.

## Decisions

### D1: Single `specs/unit-test-effectiveness/spec.md` with assertion-style requirements

We could have split the spec per file under review, but the
shared theme (assertion patterns) cuts across files. One spec
with six requirements is easier to evolve than seven. The spec
names the patterns (`structural`, `exact value`,
`@pytest.mark.parametrize`), not the test files, so new tests
written later must conform without us having to update the spec.

### D2: Production refactors ship in the same change

Alternative: file them as separate OpenSpec changes. We chose
the joint change because:

- The test rewrite would land `composite_over` validation tests
  that fail against the current implementation; landing them
  without the fix would either (a) fail CI immediately or (b)
  require a temporary `xfail` marker that we'd forget to remove.
- The `parse_stylesheet` dedupe is a 9-line delete; splitting it
  into its own change costs more in OpenSpec overhead than the
  refactor itself.
- The registry dedupe is similarly small.

If any of the three feels too risky in practice during
implementation, we split it. Otherwise the joint change is cheaper.

### D3: Integration tests move into `tests/audit_integration/`

Alternative A: keep everything in `tests/` and use markers only.
Alternative B: move integration-flavored tests to a new directory.

We chose B for three reasons:

1. `task test-unit` already does `--ignore=tests/e2e`. Adding
   `--ignore=tests/audit_integration` keeps the existing
   contract — the new directory is opt-in by default.
2. CI currently runs `task test` (full suite) and `task test-e2e`.
   A new `task test-integration` (or a marker-based
   `-m "not e2e"`) gives operators an obvious middle ground.
3. The conftest in `tests/conftest.py` is the source of the
   session-scoped DB fixture that pollutes the unit-test
   surface. Moving the integration tests out lets the unit
   subset pick up a slimmer conftest (or a `conftest.py`
   inside `tests/audit_integration/`).

### D4: Inline CSS fixtures, not `tests/fixtures/*.css`

The audit parser tests currently depend on
`src/omaha/static/app.css`. The cleanest fix is a `textwrap.dedent`
inline string in each test, the same pattern `test_audit_css_parser.py`
already uses for `FIXTURE_CSS`. We do not introduce a new
`tests/fixtures/audit/*.css` directory because the fixtures are
tiny and test-local. If a fixture grows past ~30 lines, we
revisit.

### D5: Marker registration via `pyproject.toml` only — no `pytest.ini`

The project already uses `[tool.pytest.ini_options]` in
`pyproject.toml`. Adding `markers = ["unit", "integration"]` keeps
config in one place and matches the ruff-and-prek convention.

### D6: `composite_over` validation: raise, don't return

Alternative: keep the silent passthrough for backwards
compatibility. We chose raise because:

- The only caller is `audit/inventory.py:state_color_pairs`,
  which already wraps the call in a `try/except Exception`
  block (line 567-578). A `ValueError` there is swallowed by
  the existing except path; behavior at the caller is
  unchanged.
- Silent passthrough makes the function non-total — a caller
  that doesn't know to check for the unchanged input gets a
  bad color propagated. The audit report can therefore include
  garbage ratios silently.

The fix is the validate-backdrop-first reordering, not a new
contract. The `apply_brightness` function is left alone (it
already returns the input unchanged on `ValueError`).

## Risks / Trade-offs

- **R1**: A test deleted in this change was the only one catching
  a regression that nobody noticed yet. → Mitigation: the
  archive step in `opsx-archive-change` keeps the old test
  files in git history; the parametrize sweeps preserve every
  (input, expected) pair from the originals.

- **R2**: Tightening `composite_over` to raise on invalid
  backdrop breaks a call site we don't know about. → Mitigation:
  `audit/inventory.py:state_color_pairs` is the only internal
  caller and it already swallows exceptions. We grep for
  `composite_over` in the codebase to confirm no other callers
  before landing the change.

- **R3**: Parametrizing the audit tests hides which case failed
  in noisy CI output. → Mitigation: pytest's `-v` mode prints
  the parametrize id (`aa_status[4.5-false-Passa]`) which is
  more diagnostic than the current `test_aa_status_normal_pass`.

- **R4**: The new `tests/audit_integration/` directory changes
  the test-collection surface, which CI must know about. →
  Mitigation: the change updates `task` definitions in
  `pyproject.toml` (`test`, `test-unit`, `test-integration`)
  in the same PR.

- **R5**: We add `unit` and `integration` markers but never
  retroactively mark existing tests in files outside the audit
  scope (which the user excluded). → Mitigation: the spec
  applies prospectively; pre-existing integration tests keep
  running via `task test` until they migrate naturally.

## Migration Plan

1. Land the three production refactors first (separate small
   commits in the same PR). Verify `task test` still passes.
2. Land the new marker config in `pyproject.toml`. Verify
   `uv run pytest -m unit` runs only the unit subset.
3. Rewrite the audit unit tests file by file, in this order:
   `test_audit_color_resolver.py`, `test_audit_css_parser.py`,
   `test_audit_inventory.py`, `test_audit_report.py`,
   `test_phase02_tokens.py`, `test_t06_logging.py`.
4. Delete `test_t01_smoke.py`.
5. Move integration-flavored tests from `test_audit_report.py`
   and `test_t06_logging.py` to `tests/audit_integration/`.
6. Update `task test-unit`, `task test-integration`, `task test`
   in `pyproject.toml` to reflect the new layout.
7. Run `uv run task check` to confirm CI gate passes.
8. Archive the change.

Rollback strategy: revert the merge commit. Because the change
deletes tests but does not change shipped behavior (the three
production fixes are bug-tightenings, not API changes), rolling
back is safe — operators on a deploy between the merge and
archive would simply lose the test hardening with no runtime
impact.

## Open Questions

- **OQ1**: Do we want a `tests/audit_integration/conftest.py`
  that loads the existing session-scoped DB fixture, or do we
  move the conftest's `_omaha_test_env` into the new directory
  and split it from the route tests? (Currently the route tests
  use the same fixture — moving the conftest might break
  unrelated tests.)

- **OQ2**: The `audit_color_resolver.py`'s `apply_brightness`
  function has the same silent-passthrough behavior as the
  `composite_over` fix. Do we tighten it for symmetry, or
  leave it alone since no test currently exercises the bad path?

- **OQ3**: Should the unit-vs-integration split also apply to
  `test_t02_csv_import.py`'s `test_match_positions_43_5_split`
  (which depends on `tests/fixtures/sample_broker.csv`)? It's
  currently a unit test, but the fixture file is a production
  asset-like dependency.
