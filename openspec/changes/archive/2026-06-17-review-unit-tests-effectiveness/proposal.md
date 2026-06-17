## Why

The unit-test suite under `tests/` (~152 tests across 9 files) carries a
high volume of false positives, tautologies, dataclass-shape checks, and
tests that exercise the stdlib or third-party libraries instead of the
code under audit. The audit pass currently passes 152 + 3 skip — but a
read of the assertions shows many tests would still pass if the
production code regressed in ways the tests claim to prevent. Worse, a
small inventory of dead code and a duplicated `parse_stylesheet`
definition in `src/omaha/audit/css_parser.py:111` and `:210` were found
incidentally during the review — both invisible to the current suite.

We want **fewer tests that catch more real bugs**, not a larger suite.
A unit test must fail loudly when the code it covers actually breaks.

## What Changes

- **Remove** tests that assert tautologies, dataclass shapes, module
  importability, stdlib behavior, or `assert "x" in html` substring
  matches with no surrounding structural check.
- **Parametrize** near-identical assertions into single
  `@pytest.mark.parametrize` tests (`aa_status`, `apply_brightness`,
  `composite_over`, `AuditContextFactory.context_for`, `TestRenderPage`,
  `TestFindInteractive`, `TestRenderReport`).
- **Isolate** tests that depend on `src/omaha/static/app.css` and the
  real `templates/` dir so they use inline fixtures instead of
  silently skipping when those files move.
- **Move** `TestGenerateReport.test_generate_report_*` and
  `TestCLI.test_cli_writes_report` (in `test_audit_report.py`) plus
  the 3 `TestClient`-using tests in `test_t06_logging.py` into a new
  `tests/audit_integration/` (or analogous) file so the unit suite
  stops importing the live `omaha.main.app` and `app.css`.
- **Fix three production bugs uncovered by the review:**
  1. `src/omaha/audit/css_parser.py:111` — `parse_stylesheet`
     is defined twice; the first definition (no path-traversal
     guard) is dead code. Remove the dead copy.
  2. `src/omaha/audit/inventory.py:433` —
     `_build_registry_from_stylesheet` is a verbatim duplicate of
     `_build_registry` in `css_parser.py:274`. Re-export the
     canonical version.
  3. `src/omaha/audit/color_resolver.py:100-120` —
     `composite_over` short-circuits on `alpha >= 1.0` before
     validating the backdrop, so `composite_over("#ff0000",
     "bad-color")` silently returns `"#ff0000"`. Validate backdrop
     first (or remove the short-circuit and let sRGB conversion
     raise on bad input).
- **Mark each unit test** so it cannot accidentally become
  integration-flavored again — by failing fast when
  `omaha.config.settings` requires a DB or when an
  `app.css`-relative path is missing.

**BREAKING**: This change reduces test count by roughly 50% (~152 →
~75). Anyone who relied on a deleted test name to detect a regression
will need to look at the surviving parametrized test cases. CI
runtime for the unit subset should drop by 20–30%.

## Capabilities

### New Capabilities

- `unit-test-effectiveness`: A documented contract for what counts as
  a unit test in this project, with the assertion patterns we
  accept (structural assertions, exact value comparisons, explicit
  failure messages) and the patterns we reject (tautologies,
  dataclass-shape checks, stdlib assertions, substring soup).

### Modified Capabilities

None — no existing spec describes unit-test behavior. The work is
internal to `tests/` and `src/omaha/audit/`.

## Impact

- `tests/test_audit_color_resolver.py` — rewrite with parametrize.
- `tests/test_audit_css_parser.py` — rewrite, drop dead
  `_SMALL_FIXTURE_RULES`.
- `tests/test_audit_inventory.py` — rewrite, drop
  `test_render_*`/`test_finds_elements_in_*` redundancy, parametrize
  the rest.
- `tests/test_audit_report.py` — split into unit and integration.
  Move `TestGenerateReport` and `test_cli_writes_report` to
  `tests/audit_integration/test_report_pipeline.py`.
- `tests/test_phase02_tokens.py` — keep one app.css-bound test
  (the DESIGN.md contract sweep), parametrize the rest with
  inline fixtures.
- `tests/test_t06_logging.py` — split pure (formatter + configure)
  from integration (middleware via TestClient).
- `tests/test_t01_smoke.py` — **delete**.
- `src/omaha/audit/css_parser.py:111` — delete the dead
  `parse_stylesheet` definition.
- `src/omaha/audit/inventory.py:433` — replace
  `_build_registry_from_stylesheet` with import of `_build_registry`.
- `src/omaha/audit/color_resolver.py:100-120` — fix `composite_over`
  short-circuit.
- `pyproject.toml` — add `[tool.pytest.ini_options] markers` for
  `unit` and `integration` so we can split runs cleanly.
