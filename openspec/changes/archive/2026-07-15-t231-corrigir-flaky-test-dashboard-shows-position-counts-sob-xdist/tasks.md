## 1. Fix flaky test under xdist

- [x] 1.1 Add `pytestmark = pytest.mark.xdist_group("serial")` to `tests/test_imports_routes.py` (after existing imports, before test functions)
- [x] 1.2 Verify `task test-integration-parallel` passes (all tests in module green under xdist)
- [x] 1.3 Verify `task test-integration` still passes (no regression in serial mode)
