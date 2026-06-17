## ADDED Requirements

### Requirement: Unit tests use structural assertions
A unit test SHALL assert exact values (or `pytest.approx` for floats),
specific exception types, or specific regex shapes. It SHALL NOT
rely on `assert "x" in container` when the container holds rich
content where `"x"` could occur coincidentally (HTML reports,
JSON payloads, multi-line log lines).

#### Scenario: Color contrast ratio is asserted exactly
- **WHEN** a unit test checks `contrast_ratio("#ffffff", "#000000")`
- **THEN** the assertion compares against the exact WCAG 2.1 ratio
  (21.0) using `pytest.approx`, not `assert result > 20.0`

#### Scenario: HTML substring match uses a structural anchor
- **WHEN** a unit test verifies an HTML report contains a count
- **THEN** the assertion matches a structural element (e.g.
  `<span class="summary-count">2</span>`), not a bare substring
  `"2" in html`

### Requirement: Unit tests do not assert dataclass / library / stdlib behavior
A unit test SHALL NOT assert `isinstance(x, SomeDataclass)`,
`pytest.raises(Exception)` on a frozen dataclass, or
`isinstance(result, tuple)` for a function whose return annotation
is `tuple`. These re-test Python, not the code under audit.

#### Scenario: Frozen dataclass check uses the concrete exception type
- **WHEN** a unit test confirms `TokenInventoryRow` is frozen
- **THEN** the assertion uses
  `pytest.raises(dataclasses.FrozenInstanceError)`, not the
  catch-all `pytest.raises(Exception)`

#### Scenario: Return type is asserted via runtime contract, not isinstance
- **WHEN** a unit test wants to confirm `aa_status` returns
  `(float, str)`
- **THEN** the test unpacks and asserts on `result[0]` and
  `result[1]` with concrete values — it SHALL NOT use
  `isinstance(result, tuple)` or `isinstance(result[0], float)`

### Requirement: Unit tests for pure modules do not depend on production files outside `src/`
A unit test SHALL import a `Path` to a fixture (inline string, tmp
file, or test-owned asset) rather than reading production CSS,
templates, or app config. The single exception is one test per
capability that proves the production asset is well-formed; that
test SHALL be marked `@pytest.mark.integration` so it can be
excluded from fast unit runs.

#### Scenario: Audit parser test uses an inline CSS string
- **WHEN** a unit test exercises `parse_stylesheet`
- **THEN** the test writes the CSS to `tmp_path` (or builds a
  `Stylesheet` directly via `tinycss2.parse_stylesheet`) and
  SHALL NOT `skipif(not APP_CSS_PATH.exists())`

#### Scenario: Production-asset well-formedness is a marked integration test
- **WHEN** a test exists to verify `src/omaha/static/app.css`
  parses cleanly
- **THEN** it carries `@pytest.mark.integration` and lives outside
  the unit-test discovery path or is filtered via the
  `[tool.pytest.ini_options] markers` config

### Requirement: Parametrize near-identical assertions
The project MUST collapse any two or more tests that differ only by their inputs and expected
outputs into a single `@pytest.mark.parametrize`-driven test. The collapsed test MUST
keep every input/expected pair from the originals so coverage is
not lost.

#### Scenario: AA status thresholds share one test
- **WHEN** a unit test would assert `aa_status(4.5) == "Passa"`
  and a separate test would assert `aa_status(3.0, is_large=True) == "Passa"`
- **THEN** both live in a single
  `@pytest.mark.parametrize("ratio,is_large,expected", [...])`
  function

#### Scenario: Render-page smoke is one parametrized test
- **WHEN** eight tests of the form
  `test_render_<template>` only assert `isinstance(html, str) and len(html) > 0`
- **THEN** they collapse to one parametrized test that asserts
  the rendered HTML contains a template-specific anchor (e.g.
  the page title or a known CSS class) for each template

### Requirement: Production code refactors ship with this change
Three production refactors MUST land in the same change as the test
cleanup because the tests masked them.

#### Scenario: Dead `parse_stylesheet` is removed
- **WHEN** the change is applied
- **THEN** `src/omaha/audit/css_parser.py` contains exactly one
  `def parse_stylesheet(...)` definition (the one with the
  path-traversal guard at `:210`)

#### Scenario: Registry builder is the canonical one
- **WHEN** the change is applied
- **THEN** `src/omaha/audit/inventory.py` imports
  `_build_registry` from `omaha.audit.css_parser` and the
  duplicate `_build_registry_from_stylesheet` is removed

#### Scenario: `composite_over` validates backdrop before short-circuit
- **WHEN** `composite_over("not-a-color", "#ffffff")` is called
- **THEN** the function raises `ValueError` (or returns the
  invalid foreground unchanged consistently with `apply_brightness`),
  and `composite_over("#ff0000", "bad-color")` raises rather
  than silently returning `"#ff0000"`

### Requirement: Test markers split unit from integration
`pyproject.toml` MUST declare two pytest markers — `unit` and
`integration`. Unit tests in `tests/` carry `@pytest.mark.unit`
(applied automatically via the `pytestmark` module-level pattern
or via `pyproject.toml`'s `[tool.pytest.ini_options] markers` plus
`testpaths` configuration). The existing `task test-unit`
command runs only unit tests; `task test` runs everything.

#### Scenario: Marker configuration is present
- **WHEN** the change is applied
- **THEN** `[tool.pytest.ini_options]` in `pyproject.toml`
  contains `markers = ["unit: pure-function tests, no DB no HTTP", "integration: tests requiring DB, TestClient, or external services"]`

#### Scenario: Unit subset is runnable alone
- **WHEN** `uv run pytest -m unit` is invoked
- **THEN** every test in the unit subset runs without booting
  `omaha.main.app` and without migrating a SQLite database
