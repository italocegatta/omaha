## Test strategy and acceptance evidence

- Contract tests stay split by boundary: pure source/contrast assertions in
  `tests/test_production_favicon.py`; browser discovery and in-memory 16px/32px
  raster checks in `tests/e2e/test_production_favicon.py`.
- `tests/conftest.py::_UNIT_FILES` must explicitly allow the new pure test
  file; no DB/TestClient fixture belongs in that file. E2E uses existing
  isolated `live_url`/`page` fixtures and creates no preview server or
  committed preview artifact.
- Focused taskipy commands:
  `uv run task test-unit -- tests/test_production_favicon.py -q` and
  `uv run task test-e2e -- tests/e2e/test_production_favicon.py -q`.
- Acceptance evidence: source assertions, successful `/static/favicon.svg`
  browser request, exactly one shared head link on `/login` and one inherited
  application page, non-empty teal-on-dark 16px and 32px raster samples,
  contrast calculation at or above 4.5:1, `git diff --check`, and owner
  validation of actual 16px/32px browser rendering after review and before
  finalize.
- Canonical full suite is not run at proposal gate. Apply/review must follow
  repository maintenance-suspended policy and record applicable focused
  evidence only.

## 1. Written direction gate

- [x] 1.1 **Owner-approved written direction — `openspec/changes/f64-favicon-de-producao-do-omaha/tasks.md` evidence:** use approved direction “O” geométrico com trilhos de ledger, teal sobre fundo escuro, próprio e legível em 16px as pre-Apply gate. No mock, static preview, browser preview example, preview server, or preview file is required. Preserve scope and stop with `BLOCKED` if written direction approval is absent. Acceptance: Apply may start under this direction and only exact production scope remains: `src/omaha/static/favicon.svg` and `src/omaha/templates/base.html`; no branding redesign, alternatives, or manifest/PWA. Test file/scenario: N/A, owner decision. Focused taskipy command: N/A (manual gate). Independent oracle: owner decision recorded in this change dossier.

## 2. Production SVG asset

- [x] 2.1 **`src/omaha/static/favicon.svg` — new root SVG asset:** create one self-contained `viewBox="0 0 32 32"` asset with opaque dark canvas mapped to DESIGN.md `--bg` and integer-aligned filled teal ledger rails mapped to `--accent`, forming one unmistakable geometric “O”; omit text, emoji, gradients, animation, external references, and alternate marks. Preserve behavior: existing `/static` mount and middleware remain the serving boundary. Acceptance: asset is standalone, unclipped, readable at 16px, structurally clear at 32px, and selected colors measure at least 4.5:1 contrast. Test file/scenario: `tests/test_production_favicon.py::test_favicon_svg_structure_and_palette`. Focused taskipy command: `uv run task test-unit -- tests/test_production_favicon.py -q`. Independent oracle: XML parse plus explicit viewBox/forbidden-content/geometry/color and contrast assertions.

## 3. Shared head integration

- [x] 3.1 **`src/omaha/templates/base.html:<head>` — favicon discovery link:** add exactly one `<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">` alongside existing head links; do not move or duplicate `head_extra`, stylesheet, font, Alpine, or page behavior. Preserve behavior: every child template inherits current shared head and page-specific head additions remain additive. Acceptance: source has one exact F64 link, no child template adds another favicon, and rendered `/login` plus authenticated application page expose same link. Test file/scenario: `tests/test_production_favicon.py::test_base_head_has_single_favicon_link` and `tests/e2e/test_production_favicon.py::test_shared_head_discovers_favicon`. Focused taskipy command: `uv run task test-unit -- tests/test_production_favicon.py -q` plus `uv run task test-e2e -- tests/e2e/test_production_favicon.py -q`. Independent oracle: parsed HTML/link count and browser DOM/request assertions.

## 4. Focused contract tests

- [x] 4.1 **`tests/test_production_favicon.py` and `tests/conftest.py::_UNIT_FILES` — pure contract coverage:** add source-only tests for SVG root/viewBox, dark/teal encoded colors, no text/emoji/gradient/animation/external reference, minimum contrast, exact link uniqueness, and the existing static path contract; add only the new test basename to the explicit unit allow-list. Preserve behavior: test file performs no DB mutation, TestClient startup, or production request. Acceptance: focused unit command passes with no `UnknownTestPath` warning and fails on missing/duplicate/wrong favicon wiring. Test file/scenarios: `test_favicon_svg_structure_and_palette`, `test_base_head_has_single_favicon_link`, `test_base_extenders_do_not_add_favicon_candidates`. Focused taskipy command: `uv run task test-unit -- tests/test_production_favicon.py -q`. Independent oracle: pytest assertions over exact repository files and explicit allow-list classification.

- [x] 4.2 **`tests/e2e/test_production_favicon.py` — browser discovery and raster evidence:** use existing isolated `live_url` and `page` fixtures to load `/login`, assert one head icon link, request `/static/favicon.svg`, rasterize it in memory at 16px and 32px, and assert dark background plus visible teal pixels/mark bounds; do not add preview server, screenshot baseline, or committed preview file. Preserve behavior: E2E remains isolated from `data/portfolio.db` and uses no destructive route. Acceptance: during Apply, browser proves discovery and successful static serving at both sizes; owner validation after review and before finalize remains mandatory because pixel heuristics do not replace visual validation. Test file/scenario: `test_shared_head_discovers_favicon` with 16px and 32px raster assertions. Focused taskipy command: `uv run task test-e2e -- tests/e2e/test_production_favicon.py -q`. Independent oracle: Chromium DOM, response status/content type, and in-memory pixel sample assertions.

## 5. Scoped verification handoff

- [x] 5.1 **Change-boundary verification — exact runtime files plus declared test support only:** run both focused taskipy commands, then `git diff --check` and inspect `git status --short`/diff for only `src/omaha/static/favicon.svg`, `src/omaha/templates/base.html`, `tests/test_production_favicon.py`, `tests/e2e/test_production_favicon.py`, `tests/conftest.py`, and this change folder. Preserve behavior: no roadmap, DESIGN.md, app.css, manifest, route, middleware, or unrelated docs change. Acceptance: focused tests pass, no generated preview files exist, and diff is whitespace-clean. Test file/scenario: all F64 scenarios. Focused taskipy command: `uv run task test-unit -- tests/test_production_favicon.py -q && uv run task test-e2e -- tests/e2e/test_production_favicon.py -q`. Independent oracle: test output plus exact file allow-list and `git diff --check`.

- [x] 5.2 **Owner post-review validation — `openspec/changes/f64-favicon-de-producao-do-omaha/tasks.md` evidence:** after review approval and before finalize, owner validates actual browser rendering at 16px and 32px against approved written direction and records result in this change dossier. Preserve behavior: Apply focused browser evidence remains mandatory, while heuristics and written direction do not replace owner validation. Acceptance: finalize is blocked until both rendered sizes are explicitly validated; no preview server or committed preview file is created. Test file/scenario: N/A, manual owner validation. Focused taskipy command: N/A (manual validation). Independent oracle: owner validation record naming 16px and 32px actual browser rendering.

## Execution Evidence

### Initial Apply — 2026-08-22

- **Tasks 2.1, 3.1, 4.1, 4.2:** completed. Changed
  `src/omaha/static/favicon.svg`, one line in
  `src/omaha/templates/base.html`, `tests/test_production_favicon.py`,
  `tests/e2e/test_production_favicon.py`, and one `_UNIT_FILES` entry in
  `tests/conftest.py`. Existing unrelated `base.html` comment and
  `tests/conftest.py` integration entries were preserved.
- **Unit:**
  `uv run task test-unit -- tests/test_production_favicon.py -q` -> **3 passed**.
  First attempt exposed a test-regex defect: required SVG namespace matched
  broad `https?://` forbidden-content assertion. Test assertion was narrowed
  to external-reference attributes; rerun passed.
- **Browser-focused E2E:**
  `uv run pytest tests/e2e/test_production_favicon.py -q -s --no-cov` -> **1 passed**.
  Chromium loaded `/login` and inherited authenticated `/`; static response
  returned `200 image/svg+xml`. Raster evidence: 16px background
  `[48, 52, 70, 255]`, 68 teal pixels, bounds `[2, 2, 13, 13]`; 32px same
  background, 284 teal pixels, bounds `[4, 4, 27, 27]`.
- **Required taskipy E2E command:**
  `uv run task test-e2e -- tests/e2e/test_production_favicon.py -q` was
  attempted exactly. Task definition hard-codes `tests/e2e`, so it collected
  60 E2E nodes and stopped at pre-existing F60 failure
  `tests/e2e/test_patrimonio_sync_action.py::TestPatrimonioSyncAction::test_state_markers_render`
  (`"Pronto para atualizar posição.\n\nclose"` vs expected text). The scoped
  F64 command above passed; no F64 test failure remains.
- **Boundary:** `rtk git diff --check` -> **pass**. No preview, manifest,
  baseline, route, middleware, palette, roadmap, or unrelated F64 runtime
  file was created. Exact F64 paths are limited to the two runtime files, two
  new tests, the declared unit allow-list entry, and this change dossier.

### Validation ownership ledger

| resource_kind | resource_id | owner / owner_evidence | started_at / ended_at | status / classification | evidence / cleanup_result |
|---|---|---|---|---|---|
| child process + process group | unit runner PID/PGID `136970/136970` | F64-apply / `f64-unit-20260822-144816` registration before launch | `14:48:16Z` / `14:48:20Z` | exited / owned-current-run | 3 unit tests passed; process exited normally; no residue |
| child process + process group | E2E task runner PID/PGID `137131/137131` | F64-apply / `f64-e2e-20260822-144843` registration before launch | `14:48:43Z` / timeout at `14:50:43Z` | exited / owned-current-run | over-collected E2E run hit pre-existing F60 failure; listener absent after bounded run; no foreign action |
| test DB | `/home/juca/github/omaha/data/test_e2e.db` | F64-apply / exact `T29_DB_TARGET` receipt for `f64-e2e-focused-20260822-145128` | `14:51:28Z` / `14:51:38Z` | cleanup-attempted / owned-cleaned | E2E-only DB; exact cleanup removed path |
| test DB | `/home/juca/github/omaha/data/test_e2e_short_ttl.db` | F64-apply / exact `T29_DB_TARGET` receipt for `f64-e2e-focused-20260822-145128` | `14:51:28Z` / `14:51:38Z` | cleanup-attempted / owned-cleaned | E2E-only fixture DB; exact cleanup removed path |
| port | `8765` / PGID `138489`, child PID `138703` | F64-apply / `T29_SERVER_EVENT` launch receipt for focused run | `14:51:31Z` / `14:51:37Z` | cleanup-attempted / owned-cleaned | server `return_code=-15`, `port_free=true`; bounded fixture teardown |
| log | `/home/juca/github/omaha/tmp/uvicorn-logs/e2e-live-url-fk0942yj.log` | F64-apply / focused-run server launch receipt | `14:51:31Z` / `14:51:38Z` | cleanup-attempted / owned-cleaned | exact current-run log removed |
| temporary path | `/tmp/pytest-of-juca/pytest-77` | F64-apply / exact `T29_TEMP_ROOT` receipt for focused run | `14:51:28Z` / `14:51:38Z` | cleanup-attempted / owned-cleaned | exact declared runner temp root removed |
| process + listener | PID `135793`, PGID `135789`, port `8000` | not F64-owned / no current-run registration; observed before refresh | `11:43:48Z` / not ended | active / pre-existing + unknown ownership | pre-existing uvicorn occupied `0.0.0.0:8000`; preserved untouched; cleanup result safe no-op, no adoption or kill |

### Refresh-for-test receipt

- **Preflight:** `bash scripts/print_lan_url.sh` -> `http://192.168.1.4:8000`.
- **Blocked restart:** port `8000` was already occupied before F64 refresh by
  pre-existing uvicorn PID `135793`, PGID `135789`, started `Sat Aug 22 11:43:48
  2026`. No F64 ledger registration or ownership evidence exists for it;
  process was classified `pre-existing/unknown` and left untouched. No kill,
  adoption, or port cleanup performed.
- **Read-only smoke against existing server:** `/healthz` returned
  `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`;
  LAN `/login` exposed one F64 link; LAN `/static/favicon.svg` returned `200`,
  `image/svg+xml`, `Cache-Control: no-cache`.
- **DB state:** read-only counts `asset_classes=11`, `assets=89`,
  `positions=88`; no reset, seed, clear, migration, or destructive route was
  run.

## Review Findings

### Review R1

Scope audit: requirements pass; scenarios pass; tasks 7/7 complete; design decisions pass; changed-symbol audit pass; preserved static mount, middleware, inherited head, and additive `head_extra` pass; focused test evidence pass; owner visual validation pass; exact diff allow-list pass; no-test-deletion/no-coverage-reduction pass; refresh receipt pass with pre-existing port occupant preserved; canonical full-suite not assessable by policy only (`maintenance-suspended`).

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**; no elapsed duration, six-lane result, coverage, skip, or fail-fast result claimed. Focused evidence: `uv run task test-unit -- tests/test_production_favicon.py -q` -> 3 passed; `uv run pytest tests/e2e/test_production_favicon.py -q -s --no-cov` -> 1 passed. Browser evidence: `/login` and authenticated `/` each exposed one exact link; `/static/favicon.svg` returned `200 image/svg+xml`; 16px raster had 68 teal pixels and bounds `[2, 2, 13, 13]`; 32px raster had 284 teal pixels and bounds `[4, 4, 27, 27]`; both backgrounds `[48, 52, 70, 255]`. Product behavior tests green. No skipped or deleted F64 tests.

Preflight: review run `f64-review-r1-20260822`; owner `F64-review`, owner evidence `review process + dossier handoff`; timestamps recorded at review start/end. Ledger classifications: process/listener `0.0.0.0:8000`, PID `135793`, PGID `135789` = `pre-existing` with `unknown` ownership, preserved; canonical suite process, test DB, and declared canonical temporary paths = `absent` because suite was not launched; focused E2E runner resources = apply receipt `owned-cleaned` (`136970/136970` unit, `138489`/`138703` E2E server, exact test DB/temp/log paths). Decision: no canonical launch; no adoption, kill, deletion, masking, or allowlist exception.

Postflight: no review-owned canonical process/listener/test DB/temp resource existed; pre-existing `8000` listener remained untouched. Apply focused-run receipt records process exit and exact bounded cleanup for `data/test_e2e.db`, `data/test_e2e_short_ttl.db`, port `8765`, E2E log, and declared temp root as `owned-cleaned`. Decision: cleanup trusted for recorded focused evidence; no foreign-resource action.

Runner isolation: canonical isolated-runner precondition not exercised because owner-authorized maintenance suspension prohibits canonical launch. Focused E2E used isolated fixture resources and recorded bounded cleanup. Refresh LAN server isolation was blocked by pre-existing/unknown `8000` uvicorn, safely preserved; read-only health/static/DB smoke passed.

Diff/spec checks: F64 runtime changes are limited to new `src/omaha/static/favicon.svg` and one exact link in `src/omaha/templates/base.html`; declared test support is `tests/test_production_favicon.py`, `tests/e2e/test_production_favicon.py`, and `_UNIT_FILES` entry in `tests/conftest.py`. Unrelated existing `base.html` comment and `tests/conftest.py` integration entries remain preserved, not attributed to F64. `git diff --check` passed. No route, middleware, palette, manifest/PWA, roadmap, preview, or baseline change. Specs, proposal, design, tasks, and implementation agree.

Owner validation: owner explicitly reported actual browser rendering validated at both 16px and 32px against approved geometric ledger-rail “O” direction. No preview server/file created. Task 5.2 is complete.

Verdict: **APPROVED**

Finding IDs: none. No blocking findings.

## Remediation 1/2 Execution Evidence

- **Finding F64-finalization-E501:** reformatted only the long JavaScript
  condition in `tests/e2e/test_production_favicon.py`; staged the existing
  Ruff-format-only changes in `tests/test_production_favicon.py`. Assertions,
  test flow, and production files were unchanged.
- **Unit:**
  `uv run task test-unit -- tests/test_production_favicon.py -q` -> **3
  passed**. Ownership rerun `f64-remediation-unit-20260822-151400` used child
  PID/PGID `148930/148930`, registered before release, exited `0` at
  `2026-08-22T15:13:56Z`; no process residue. Harness emitted no exact test-DB
  receipt, so no DB discovery or cleanup was attempted.
- **E2E preflight:** `data/test_e2e.db` was present before launch without a
  current-run receipt or ownership evidence; ports `8765` and `8767` were
  free. The focused E2E command was not launched because its fixture
  unconditionally deletes that path. Resource classified
  `pre-existing/unknown`; preserved untouched. `data/test_e2e_short_ttl.db`
  was absent. Existing port `8000` listener was out-of-bound/non-target and
  preserved.
- **Boundary:** `uv run ruff check tests/e2e/test_production_favicon.py
  tests/test_production_favicon.py`, `uv run ruff format --check
  tests/e2e/test_production_favicon.py tests/test_production_favicon.py`,
  `git diff --check`, and `git diff --cached --check` passed. Test files are
  fully staged with no unstaged split. No production behavior changed.

### Remediation ownership ledger

| resource_kind | resource_id | owner / owner_evidence | started_at / ended_at | status / classification | evidence / cleanup_result |
|---|---|---|---|---|---|
| child process + process group | PID/PGID `148930/148930` | F64 apply remediation / `f64-remediation-unit-20260822-151400`; child stopped immediately after creation before test release | `2026-08-22T15:13:51Z` / `2026-08-22T15:13:56Z` | exited / owned-cleaned | 3 unit tests passed; process exited `0`; no residue observed; bounded cleanup idempotent no-op |
| test DB | `unknown (unit harness emitted no exact path)` | F64 apply remediation / run `f64-remediation-unit-20260822-151400`; no path receipt emitted | `2026-08-22T15:13:51Z` / not ended | blocked / unknown | test-only DB identity unavailable; no discovery, adoption, deletion, or cleanup attempted |
| test DB | `data/test_e2e.db` | no current-run registration; preflight observation only | pre-existing / not ended | present / pre-existing, unknown ownership | focused E2E not launched; preserved; no adoption or deletion |
| port | `8765`, `8767` | no current-run listener | preflight / not applicable | absent / absent | no launch; no cleanup required |

**Remediation stop:** focused E2E evidence remains pending. Safe continuation
requires isolated runner with declared test DB boundary absent or current-run
owned; foreign/pre-existing DB must remain untouched.
