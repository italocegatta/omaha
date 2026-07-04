## ADDED Requirements

### Requirement: Central selector inventory
The e2e test suite SHALL source all `data-testid` / `aria-*` /
role-based selectors from a single Python module
(`tests/e2e/selectors.py`) so that UI changes surface as a single
inventory update rather than hidden per-file rot.

#### Scenario: Selector import path exists
- **WHEN** a test author needs a UI element's selector
- **THEN** `from tests.e2e.selectors import SELECTORS` resolves and
  the import has no `pytest` dependency

#### Scenario: Test files use the central map
- **WHEN** the test file declares any `data-testid` / `aria-*`
  string for an authed surface
- **THEN** the string is referenced through `SELECTORS[...]` and
  not inlined in the test body

### Requirement: Selector inventory smoke test
The e2e suite SHALL include a smoke test
(`tests/e2e/test_selector_inventory.py`) that walks every entry in
the central inventory against a live `/patrimonio` render and
confirms each named element resolves within 2 seconds.

#### Scenario: Every inventory entry resolves on /patrimonio
- **WHEN** the smoke test runs against a populated dashboard
- **THEN** `page.locator(SELECTORS[k]).count()` is `>= 1` for
  every key `k` in the inventory

#### Scenario: Missing testid surfaces as a failure
- **WHEN** an inventory entry names a `data-testid` that no
  template renders
- **THEN** the smoke test fails with a message naming the missing
  testid and its expected file location

### Requirement: patrimonio-actions Alpine scope regression test
The e2e suite SHALL include a regression test asserting that
`[data-testid="patrimonio-actions"]` carries an `x-data` attribute.
This locks in the F02 fix from commit `1755dd0` against silent
re-regression.

#### Scenario: patrimonio-actions has x-data
- **WHEN** the test loads `/patrimonio` for any profile
- **THEN** `page.locator('[data-testid="patrimonio-actions"]')
  .get_attribute('x-data')` is non-null

#### Scenario: Each action button toggles its modal store
- **WHEN** the test clicks each of the three buttons in
  `patrimonio-actions` in sequence
- **THEN** the corresponding `Alpine.store('X').open` transitions
  from `False` to `True` and the modal overlay becomes visible