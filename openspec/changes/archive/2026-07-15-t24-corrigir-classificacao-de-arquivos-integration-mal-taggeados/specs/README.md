# No delta specs for T24

This change is a compliance fix: two test files are added to
`_INTEGRATION_PREFIXES` so their markers match their actual
behavior (TestClient + DB).

No spec requirements are added, modified, or removed. The
existing requirements in `unit-test-effectiveness` and
`test-suite-quality` already mandate this classification.
