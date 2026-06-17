# 1.4 E2E cascades — /assets retirement + PATCH path

## Reproduction
4 e2e tests listed in the proposal:
- `tests/e2e/test_s01_inline_edit.py::TestS01InlineEdit::test_inline_edit_asset_target`
- `::test_inline_edit_blocks_when_sum_neq_100`
- `::test_dashboard_displays_four_percentages_per_asset`
- `tests/e2e/test_s03_asset_crud.py::TestS03AssetCRUD::test_assets_route_redirects_to_dashboard`

Sandbox cannot start Playwright + uvicorn for the e2e suite (no
chromium binary installed in the sandbox). Capturing failure mode
from code inspection.

## Diagnosis
Two patterns observed:

1. **`test_s03_asset_crud.py::test_assets_route_redirects_to_dashboard`**
   - Calls `page.goto(f"{live_url}/assets")` and asserts the URL no
     longer contains `/assets`. This is exactly what the §3.3
     redirect fix delivers. **Auto-resolves.**

2. **`test_s01_inline_edit.py::*`** — `_create_n_assets` does:
   ```python
   page.click(SELECTORS["nav_assets"])
   page.wait_for_url(re.compile(r"/assets$"))
   ```
   `SELECTORS["nav_assets"]` is NOT defined anywhere — it was
   removed when the dashboard replaced the page. The click will
   raise `KeyError: 'nav_assets'` immediately. Same for
   `SELECTORS["asset_editor_name"]`, `["asset_editor_class"]`,
   `["asset_editor_add"]`, `["asset_row"]` — none of these are in
   the S04 `SELECTORS` dict.

   These tests **cannot** be fixed by the §3.1/§3.3 changes alone;
   they reference a removed UI surface. The intended replacement
   is the dashboard-based inline form (the `POST /api/assets`
   path used by `test_s03_asset_crud.py::_create_seed_assets`).

## Decision
- `test_s03_asset_crud.py::test_assets_route_redirects_to_dashboard`
  → auto-resolves with §3.3.
- `test_s01_inline_edit.py::*` (3 tests) → still broken after
  §3.3. Need to rewrite `_create_n_assets` to use the dashboard
  inline form (mirror `_create_seed_assets` from test_s03).

  Decision boundary: the proposal §3.4 says "these should resolve
  automatically once §3.1 / §3.3 land; if not, reproduce under
  the same protocol as §1 and localise per §1.5". They do NOT
  auto-resolve. Localising per §1.5 shows the missing selectors
  — the test code is the divergence.

  Per D2 (no caller/spec evidence for the old nav-based flow),
  the fix is a **test edit**: rewrite `_create_n_assets` to use
  the dashboard inline form (which IS what the test's
  `_create_seed_classes` does for classes — same pattern).

## E2e sandbox note
E2e tests cannot be verified locally (no chromium). The unit/integration
fix will be validated; e2e cascades will be confirmed via CI or a
host with playwright installed. Per task 1.4 note and the proposal's
R4 mitigation, this is acceptable scope.