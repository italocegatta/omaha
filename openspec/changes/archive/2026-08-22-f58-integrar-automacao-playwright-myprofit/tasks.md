## 1. Remove F57-derived destination contract

- [x] 1.1 `src/omaha/config.py::MyProfitProfileConfig`, `_resolve_values`, `_FALSE_MYPROFIT_VALUES`, `Settings`, `resolve_myprofit_profile_config`: remove both `MYPROFIT_<PROFILE>_DESTINATION` fields/property/argument/placeholder checks and destination repr text; retain only Italo/Ana email/password, `SecretStr`, profile isolation, Família-first `household_read_only`, unknown/incomplete/placeholder guards, `.env` precedence, `SECRET_KEY`, quote settings, and test-mode behavior. Acceptance: `Settings.model_fields` contains exactly four MyProfit credential fields, legacy destination env values are ignored, resolved config has no destination attribute, and Família never reads any credential field. Test file/scenario: `tests/test_f57_myprofit_profile_config.py` field-set, profile-isolation, destination-ignored, incomplete, and `test_family_rejected_before_lookup`. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py`. Independent oracle: inspect model fields and a fake profile/config; no browser, HTTP, parser, DB, or external spy call occurs.

- [x] 1.2 `tests/test_f57_myprofit_profile_config.py`: narrow existing F57 pure tests from six fields to four; remove destination markers/assertions and add a legacy-destination-ignored case while preserving synthetic email/password sanitization, Italo/Ana non-fallback, Família rejection, false placeholder, and no-external-call assertions. Acceptance: tests prove no destination contract remains and no synthetic email/password marker enters diagnostics. Test file/scenario: same file, all F57 scenarios. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py`. Independent oracle: parse `.env.example`/`Settings.model_fields`; destination names and values are absent from application-facing assertions and fake lookup count remains zero.

- [x] 1.3 `.env.example`, `README.md`, `tests/test_auth.py::test_environment_mode_documentation`: delete destination variables, comments, and coupled assertions; retain false per-profile email/password placeholders, ignored `.env` guidance, `ADMIN_PASSWORD=distendidos`, `OMAHA_ENV`, `0.0.0.0`, and Família read-only/no-secret language. Acceptance: docs mention only four MyProfit credential names, no `MYPROFIT_*_DESTINATION`, no real values, and auth documentation test remains green. Test file/scenario: `tests/test_f57_myprofit_profile_config.py::test_env_example_placeholders_are_false`, `::test_docs_do_not_contain_secrets`, `tests/test_auth.py::test_environment_mode_documentation`. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py` then `uv run task test-one tests/test_auth.py::test_environment_mode_documentation`. Independent oracle: repository text scan finds zero destination variable references outside active F58 dossier/history and preserves required family/password/network markers.

## 2. Add connector boundary and runtime dependencies

- [x] 2.1 `src/omaha/myprofit/connector.py` and `src/omaha/myprofit/__init__.py`: add `MyProfitConnector` protocol, immutable `MyProfitCsvDownload` result, timeout configuration, sanitized `MyProfitConnectorError`, fixed `STOCK_DETAIL_URL`, and `PlaywrightMyProfitConnector.download_positions_csv(profile)`; resolve profile credentials before `launch_persistent_context`, reject Família before launcher call, use temporary profile/download roots, and close/remove all resources in `finally`. Acceptance: public interface has no destination argument, no DB/FastAPI/import dependency, result contains basename + bytes only, and success/failure paths expose only stage/code errors. Test file/scenario: `tests/test_myprofit_connector.py` fake launcher flow, family guard, missing credentials, timeout, cleanup, and sanitized-error scenarios. Focused command: `uv run task test-file tests/test_myprofit_connector.py`. Independent oracle: fake launcher/network/DB/parser spies show zero calls before guard or on failure; temporary root does not exist after return/error.

- [x] 2.2 `src/omaha/myprofit/connector.py`: implement POC-observed browser flow using fixed login entry, visible email/password filling, one submit, bounded optional visible `Mais tarde`/`Later` dismissal, authenticated-state check, direct `StockDetail.aspx` navigation, `button[aria-label="Export"]`, exact `CSV`, and `expect_download`; do not copy POC `.env` loading, prints, screenshots, debug traces, persistent local profile, or destination selector. Acceptance: fake page records ordered login → optional defer/check → fixed StockDetail → Export → CSV → download calls; absent optional prompt proceeds only with authenticated state; unconfirmed 2FA/CAPTCHA stops before export. Test file/scenario: `tests/test_myprofit_connector.py::test_download_flow`, `::test_two_factor_defer`, `::test_missing_two_factor_prompt`, `::test_unconfirmed_authentication_fails`. Focused command: `uv run task test-file tests/test_myprofit_connector.py`. Independent oracle: recorded fake-page call list contains exact fixed URL and no environment destination value; no live browser/domain request occurs.

- [x] 2.3 `pyproject.toml` dependency declarations and `uv.lock`: add POC-compatible runtime `cloakbrowser==0.5.8`, promote/raise Playwright runtime dependency to the supported 1.62-compatible range, remove duplicate incompatible dev declaration if needed, and regenerate lock through uv without adding `python-dotenv` solely for connector use. Preserve all existing app/dev dependencies and task definitions. Acceptance: clean `uv sync` resolves imports used by connector and lock has one coherent Playwright requirement plus cloakbrowser. Test file/scenario: package import smoke embedded in connector unit test and lock/dependency inspection. Focused command: `uv run task install` then `uv run task test-file tests/test_myprofit_connector.py`. Independent oracle: `pyproject.toml`/`uv.lock` dependency graph has no unresolved connector import and no new dotenv-based config path.

- [x] 2.4 `tests/conftest.py::_UNIT_FILES`: register `tests/test_myprofit_connector.py` in explicit unit allow-list, preserving the rule that connector tests are pure and do not use TestClient/DB. Acceptance: focused unit collection marks connector module `unit` without `UnknownTestPath`; no integration prefix is added. Test file/scenario: collection of new connector module. Focused command: `uv run task test-one tests/test_myprofit_connector.py::test_download_flow`. Independent oracle: pytest collection marker report and module imports show no DB/TestClient fixture.

## 3. Specify and verify stable contracts

- [x] 3.1 `openspec/changes/f58-integrar-automacao-playwright-myprofit/specs/myprofit-profile-credentials/spec.md`: modify F57-derived stable requirements to describe four email/password fields only, no destination property/validation/selector/modulator, preserved profile isolation and secret sanitization, plus destination-ignored scenario. Acceptance: every removed destination behavior and preserved credential/family behavior maps to a test in `tests/test_f57_myprofit_profile_config.py`. Test file/scenario: delta spec plus F57 focused tests. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py`. Independent oracle: `openspec validate f58-integrar-automacao-playwright-myprofit --type change --strict` accepts delta syntax and stable spec references no destination contract after sync interpretation.

- [x] 3.2 `openspec/changes/f58-integrar-automacao-playwright-myprofit/specs/cross-profile-sharing/spec.md`: add Família connector guard requiring rejection before credential resolution, browser/context construction, navigation, or download with `household_read_only`. Preserve all existing dashboard/profile/mutation behavior. Acceptance: family fake launcher and credential lookup remain unused; no auth/model/DB change is introduced. Test file/scenario: `tests/test_f57_myprofit_profile_config.py::test_family_rejected_before_lookup` and `tests/test_myprofit_connector.py::test_family_rejected_before_launcher`. Focused command: `uv run task test-one tests/test_myprofit_connector.py::test_family_rejected_before_launcher`. Independent oracle: zero-call spies plus strict delta validation.

- [x] 3.3 `openspec/changes/f58-integrar-automacao-playwright-myprofit/specs/myprofit-position-csv-connector/spec.md`: add connector requirements for protocol/result, fixed direct StockDetail flow, optional 2FA defer without bypass, explicit timeout stages, credential sanitization, temporary cleanup, offline fakes, and no DB/parser/preview mutation. Acceptance: each scenario has a named pure test and explicitly excludes F59/F60/T31 routes/jobs/UI. Test file/scenario: `tests/test_myprofit_connector.py` full module. Focused command: `uv run task test-file tests/test_myprofit_connector.py`. Independent oracle: strict change validation reports no missing capability/spec artifact and test spies remain offline.

## 4. Proposal and implementation acceptance gates

- [x] 4.1 `tests/test_myprofit_connector.py` and modified F57 tests: run only synthetic/fake unit scenarios for credential isolation, Família-first rejection, login/download call order, optional 2FA behavior, fixed URL/export selectors, sanitized failures, timeout handling, basename safety, and temporary resource cleanup. Preserve no-network/no-DB/no-parser behavior. Acceptance: focused tests pass with zero MyProfit requests, zero browser launches, zero production DB access, and no secret markers in diagnostics. Test files/scenarios: `tests/test_f57_myprofit_profile_config.py`, `tests/test_myprofit_connector.py`. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py` and `uv run task test-file tests/test_myprofit_connector.py`. Independent oracle: fake launcher/request/DB/parser counters remain zero outside intended in-process doubles; `git status` shows no DB artifacts.

- [x] 4.2 All changed Python/docs/artifacts in F58: run repository lint and inspect scope; do not run refresh-for-test, db-reset, server, E2E/BDD, or any live connector command. Preserve unrelated roadmap/F57 archive and do not create F59/F60/T31 artifacts. Acceptance: lint passes, diff has only F58 dossier plus implementation files listed by design, and no `.env`/financial/browser artifacts are changed. Test file/scenario: repository lint and changed-file audit. Focused command: `uv run task lint`. Independent oracle: `rtk git status --short --untracked-files=all` and `rtk git diff --check` show no unrelated or secret files.

- [x] 4.3 F58 change directory and stable specs: after proposal artifacts exist, run artifact/status/spec validation only and record outputs in `design.md` and final report; implementation tests remain unrun at proposal gate. Acceptance: `proposal.md`, `design.md`, `tasks.md`, and all three delta specs exist; change is complete/apply-ready; stable specs validate; no application files are changed during proposal. Test file/scenario: OpenSpec artifact gate, not pytest. Focused command: `openspec status --change f58-integrar-automacao-playwright-myprofit --json`, `openspec validate f58-integrar-automacao-playwright-myprofit --type change --strict --json`, and `openspec validate --specs --strict --json`. Independent oracle: `rtk git status --short --untracked-files=all -- openspec/changes/f58-integrar-automacao-playwright-myprofit` lists only dossier paths and `git status` confirms pre-existing roadmap modification is untouched.

## Test strategy

- Pure unit tests only: `tests/test_f57_myprofit_profile_config.py` for the
  destination-removal/config contract and `tests/test_myprofit_connector.py`
  for fake Playwright connector behavior.
- Fake launcher/context/page/locator/download objects; synthetic credentials
  via explicit settings/monkeypatch only. Never read or copy actual `.env`.
- No MyProfit HTTP/domain access, real browser launch, FastAPI TestClient,
  parser invocation, DB session, migration, seed, production DB, route, job,
  preview, UI, E2E, BDD, or refresh-for-test operation.
- Focused taskipy commands:
  `uv run task test-file tests/test_f57_myprofit_profile_config.py`,
  `uv run task test-file tests/test_myprofit_connector.py`,
  `uv run task test-one tests/test_myprofit_connector.py::test_download_flow`,
  and `uv run task lint`.
- Proposal-only validation commands:
  `openspec status --change f58-integrar-automacao-playwright-myprofit --json`,
  `openspec validate f58-integrar-automacao-playwright-myprofit --type change
  --strict --json`, and `openspec validate --specs --strict --json`.
- Acceptance evidence: four credential fields only; destination references
  absent from active config/docs/tests; Família launcher count zero; fake call
  order reaches fixed StockDetail and Export → CSV; 2FA unknown state fails
  closed; timeout errors are stage-only; temporary paths are removed; no DB or
  external calls; change/stable OpenSpec validation passes.

## Preflight Boundaries

- **Captured before implementation:** `rtk git diff HEAD~1` showed pre-existing
  F61 work in `.env.example`, `README.md`, `src/omaha/main.py`,
  `tests/test_auth.py`, `openspec/specs/readme-freshness/spec.md`,
  `openspec/specs/runtime-environment-mode/spec.md`, and the archived F61
  dossier; it also showed the pre-existing `openspec/roadmap.md` lifecycle
  update plus the untracked F58 dossier. These files/hunks are not F58-owned
  except the explicitly mapped `.env.example`, `README.md`, and
  `tests/test_auth.py` destination assertions/lines.
- **Boundary preserved:** no edits to `openspec/roadmap.md`, archived F57/F48/F61
  dossiers, `src/omaha/main.py`, auth/models/routes, database, seed, or local
  `.env`.

## Execution Evidence

### Initial apply pass

- **1.1/1.2 complete:** `src/omaha/config.py` now exposes exactly four
  `MYPROFIT_*` credential fields. Destination fields, resolver argument,
  false markers, repr text, and resolved property are absent. F57 tests cover
  legacy env-key ignoring, profile isolation, incomplete/placeholder guards,
  `SecretStr`, sanitization, and Família-first rejection. Changed symbols:
  `MyProfitProfileConfig`, `_resolve_values`, `_FALSE_MYPROFIT_VALUES`,
  `Settings`, `resolve_myprofit_profile_config`.
- **1.3 complete:** `.env.example`, `README.md`, and the coupled auth
  documentation assertion now list only four email/password names while
  preserving `ADMIN_PASSWORD=distendidos`, `OMAHA_ENV`, `0.0.0.0`, ignored
  `.env`, and Família read-only guidance. No local `.env` was read or staged.
- **2.1/2.2 complete:** added `src/omaha/myprofit/connector.py` and package
  exports. `PlaywrightMyProfitConnector` resolves credentials before launcher,
  rejects Família before resolver/launcher, uses temporary browser/download
  roots, fixed `LOGIN_URL` and `STOCK_DETAIL_URL`, visible login selectors,
  bounded optional `Mais tarde`/`Later`, authentication confirmation, Export →
  exact CSV → `expect_download`, basename sanitization, in-memory bytes, and
  sanitized stage/code errors. Context close and temporary-root removal run in
  `finally`. No FastAPI, DB, parser, route, job, or UI imports.
- **2.3/2.4 complete:** `cloakbrowser==0.5.8` and runtime
  `playwright>=1.62,<1.63` added to `pyproject.toml`; dev duplicate removed;
  `uv.lock` regenerated by `uv run task install`; connector test registered in
  `_UNIT_FILES`. No `python-dotenv` added.
- **3.1/3.2/3.3 complete:** active F58 deltas retained/validated; stable
  `openspec/specs/myprofit-profile-credentials/spec.md` now describes four
  credential fields, ignored legacy destination keys, and no routing surface.
  Família connector guard and direct CSV connector contracts remain explicit.
- **4.1 complete:** `tests/test_f57_myprofit_profile_config.py` → 10 passed;
  `tests/test_myprofit_connector.py` → 9 passed; exact focused smoke
  `uv run task test-one tests/test_myprofit_connector.py::test_download_flow`
  → 1 passed. All browser/network/parser/DB behavior uses in-process fakes;
  no MyProfit request or production DB mutation occurred.
- **4.2 complete:** `uv run task lint` → passed. `rtk git diff --check` →
  clean. Changed-file audit shows only declared F58 implementation/docs/specs,
  plus pre-existing roadmap/F61 boundaries; no `.env`, financial, browser, or
  F59/F60/T31 artifact changes.
- **4.3 complete:** `openspec status --change
  f58-integrar-automacao-playwright-myprofit --json` → complete;
  `openspec validate f58-integrar-automacao-playwright-myprofit --type change
  --strict --json` → 1/1 passed, 0 issues; `openspec validate --specs --strict
  --json` → 70/70 passed, 0 failed. Informational long-requirement notices
  remain pre-existing.

### Focused validation receipts

- `uv run task install` → resolved/installed project with cloakbrowser and one
  runtime Playwright requirement.
- `uv run task test-file tests/test_f57_myprofit_profile_config.py` → 10 passed.
- `uv run task test-one tests/test_auth.py::test_environment_mode_documentation`
  → 1 passed.
- `uv run task test-file tests/test_myprofit_connector.py` → 9 passed.
- `uv run task test-one tests/test_myprofit_connector.py::test_download_flow`
  → 1 passed.
- `uv run task lint` → all prek/ruff/hygiene checks passed.
- No live connector command, browser install/launch, MyProfit request, route,
  migration, seed, destructive DB task, or local `.env` read/copy was run.

### Refresh-for-test receipt

- Runtime refresh attempted with detached `uv run uvicorn omaha.main:app
  --host 0.0.0.0 --port 8000`; port 8000 was already owned by an externally
  managed process, so no unrelated process was killed. New process exited after
  reporting address-in-use. No DB reset/seed/migration ran.
- `bash scripts/print_lan_url.sh` → `http://192.168.1.4:8000`.
- Read-only health smoke → `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- Read-only DB receipt → `11 classes`, `89 assets`, `88 positions`.
- Dashboard smoke with synthetic known family password and Italo login →
  rendered page contained `RF Din` 5 times. No `.env` was inspected or staged.

## Review Findings

### Review R1
Scope audit: proposal scope **pass**; design decisions **pass**; tasks 13/13
complete **pass**; destination-contract removal in active config/docs/tests and
stable spec **pass** (legacy keys remain documented only as ignored inputs);
Italo/Ana credential isolation and `SecretStr` **pass**; Família-first guard
before resolver/launcher **pass**; connector protocol/result and fixed
StockDetail/export flow **pass**; fake/offline/no DB/no live network boundary
**pass**; temporary cleanup and basename handling **pass** for covered paths;
dependency/lock and explicit unit allow-list **pass**; F57 archive and F59/F60/T31
boundaries **pass**; preserved password/network/config/test invariants **pass**;
apply evidence and delivery receipt **pass**; complete scope assessability
**pass**. Timeout interaction implementation **finding**. Full-suite gate
**finding/blocker**.

Full suite: `uv run task test` -> **red**, runner receipt elapsed **218.40s**
(external `/usr/bin/time`: **218.67s**), duration limit **300s**, cleanup
`clean_children: true`, no child survivors. Unit 498 passed/2 skipped; audit
40 passed; visual exited 0; BDD had 2 failures; integration and e2e were
terminated by runner after first lane failure (exit 241). Test gate failed;
verdict **BLOCKED**.

Verdict: **BLOCKED**

#### R1-F01 — Full suite red from unresolved local browser-server failures
Status: blocked
Requirement/task: PRD §4.13; F58 task 4.1 full delivery acceptance
Evidence: `reports/test-profile/20260820T142212-bdd.log:25-26,63-203` —
`test_manual_add_4_assets_unequal[Italo]` and
`test_derived_recomputes_on_class_patch[Ana]` fail at
`tests/bdd/step_defs/_workflows.py:273` / `tests/support/browser.py:200` with
`Page.goto: net::ERR_ABORTED` for `http://127.0.0.1:8766/`; no F58 symbol or
file appears in either traceback. `reports/test-profile/20260820T142212-run.json:4-7,3244`
records 218.401s, under ceiling, cleanup true, but nonzero BDD lane and
integration/e2e sibling termination.
Required change: owner must resolve or explicitly classify local test-server
failure, then obtain one clean green `uv run task test` receipt before F58 may
enter owner validation; do not route this unknown/environmental failure to
Apply guessing at F58 code. Preserve all tests, lanes, skips, and coverage;
do not mask, skip, or rerun full suite in this review.
Acceptance: same full suite exits 0, all six lane receipts exit 0, cleanup is
true, and wall-clock remains <=300s; record diagnosis for both named BDD nodes
and collateral integration/e2e termination.

#### R1-F02 — Playwright interaction calls lack configured stage timeouts
Status: open
Requirement/task: F58 delta `myprofit-position-csv-connector`, Requirement
“Connector SHALL bound failures and clean resources”; tasks 2.2 and 4.1
Evidence: `src/omaha/myprofit/connector.py:163-167` calls `fill`/`submit.click`
without timeout; `:178-179` calls optional defer `click` without timeout;
`:205-206` export `click` without timeout; `:226-227` CSV `click` is inside
`expect_download` timeout but click itself has no configured timeout. Only
preceding waits and navigation receive values from `MyProfitConnectorTimeouts`.
Required change: pass explicit configured timeout values to every Playwright
credential fill/submit/defer/export/CSV interaction, or revise contract with
owner-approved rationale; add fake assertions proving those values are used.
Excluded scope: no route, job, parser, preview, UI, live browser, or F59/F60/T31
work.
Acceptance: fake-page tests assert each interaction receives its stage timeout;
an injected timeout at each interaction raises sanitized stage/code error and
still closes context/removes temporary roots.

OpenSpec verification: `openspec status --change
f58-integrar-automacao-playwright-myprofit --json` -> complete, all artifacts
present, 13/13 tasks complete. `openspec validate
f58-integrar-automacao-playwright-myprofit --type change --strict --json` ->
valid, 1/1 passed, 0 issues. `openspec validate --specs --strict --json` ->
valid, 70/70 passed, 0 failed; informational long-requirement notices only.

Changed files (review evidence only): `.env.example`, `README.md`,
`openspec/specs/myprofit-profile-credentials/spec.md`, `pyproject.toml`,
`src/omaha/config.py`, `src/omaha/myprofit/__init__.py`,
`src/omaha/myprofit/connector.py`, `tests/conftest.py`, `tests/test_auth.py`,
`tests/test_f57_myprofit_profile_config.py`, `tests/test_myprofit_connector.py`,
`uv.lock`, plus F58 dossier files. Pre-existing `openspec/roadmap.md` remains
outside F58 review ownership. No `.env` read/exposed; no production DB mutation.

Blocker / owner decision: **BLOCKED** by R1-F01. Owner must provide clean
environment diagnosis and green full-suite receipt. R1-F02 remains open for
implementation remediation after blocker resolution; F58 cannot enter owner
validation or unblock F59 yet.

### Review R2
Scope audit: proposal **pass**; design decisions **pass**; tasks 13/13
complete **pass**; destination-contract removal and stable credential specs
**pass**; Italo/Ana isolation and `SecretStr` **pass**; Família-first guard
**pass**; connector protocol/result and fixed StockDetail/export flow **pass**;
offline fake/no DB/no live network boundary **pass**; temporary cleanup and
basename handling **pass** for covered paths; dependency/lock and unit
allow-list **pass**; F57 archive and F59/F60/T31 boundaries **pass**; PRD
§4.1-§4.9 and §4.11-§4.14 invariants **pass**; clean-runner precondition
**pass**; R1-F01 environment blocker **resolved**; explicit Playwright
interaction timeouts **finding**; complete scope assessability **pass**.

Full suite: `uv run task test` -> **green**, external wall-clock **252.01s**
(runner receipt **251.33s**), duration limit **300s**, cleanup **clean** (all
six lane exit codes 0, reconciliation `ok: true`, no pytest/Playwright/uvicorn
or task-test child remained after command). Unit 498 passed/2 skipped; audit
40 passed; BDD 51 passed; integration, e2e, and visual exited 0. Test gate
passed. No failures to classify.

Verdict: **CHANGES_REQUESTED**

#### R1-F01 — Full suite red from unresolved local browser-server failures
Status: resolved
Requirement/task: PRD §4.13; F58 task 4.1 full delivery acceptance
Evidence: `reports/test-profile/20260820T143745-run.json:4-7,3435-3464`
records elapsed 251.3299s, all six lane exit codes 0, reconciliation `ok: true`,
and `reports/test-profile/20260820T143745-bdd.log:11-63` records 51 passed;
post-run process inspection found no pytest/Playwright/uvicorn/task-test child.
Required change: none for this finding; clean-runner prerequisite established
without implementation/config/test/harness edits.
Acceptance: satisfied by this single green full-suite receipt at <=300s with
cleanup complete.

#### R1-F02 — Playwright interaction calls lack configured stage timeouts
Status: open
Requirement/task: F58 delta `myprofit-position-csv-connector`, Requirement
“Connector SHALL bound failures and clean resources”; tasks 2.2 and 4.1
Evidence: `src/omaha/myprofit/connector.py:163-167` calls credential
`fill`/submit `click` without `timeout`; `:178` calls optional defer `click`
without `timeout`; `:205-206` calls Export `click` without `timeout`; and
`:226-227` calls CSV `click` inside `expect_download(timeout=...)` but passes no
timeout to the click itself. Configured values currently apply only to waits,
navigation, probe polling, and download capture. Full suite green does not
invalidate this contract gap because fake tests do not assert interaction
timeout arguments.
Required change: pass explicit configured stage timeout values to every
Playwright credential fill/submit/defer/export/CSV interaction, or obtain
owner-approved contract revision; extend offline fakes/assertions to verify
each value and injected timeout at each interaction still produces sanitized
stage/code error with context close and temporary-root removal.
Excluded scope: no route, job, parser, preview, UI, live browser, harness,
environment repair, or F59/F60/T31 work.
Acceptance: fake-page tests assert timeout received by each listed interaction;
timeout injection covers each interaction; all cleanup and sanitized-error
assertions pass, followed by a new review gate suite (not run in R2).

OpenSpec verification: `openspec validate
f58-integrar-automacao-playwright-myprofit --type change --strict --json` ->
valid, 1/1 passed, 0 issues. `openspec validate --specs --strict --json` ->
valid, 70/70 passed, 0 failed; informational long-requirement notices only.

Changed files (review evidence only): `.env.example`, `README.md`,
`openspec/specs/myprofit-profile-credentials/spec.md`, `pyproject.toml`,
`src/omaha/config.py`, `src/omaha/myprofit/__init__.py`,
`src/omaha/myprofit/connector.py`, `tests/conftest.py`, `tests/test_auth.py`,
`tests/test_f57_myprofit_profile_config.py`, `tests/test_myprofit_connector.py`,
`uv.lock`, plus F58 dossier files. Pre-existing `openspec/roadmap.md` remains
outside F58 ownership. Review modified only this `tasks.md` record.

Blocker / owner decision: **CHANGES_REQUESTED** by open R1-F02. Owner/apply
must make bounded timeout remediation and focused acceptance evidence before
owner validation; do not archive, sync, commit, push, or route environmental
repair to Apply.

### Review R3 — remediation 1/2
Scope audit: proposal **pass**; design decisions **pass**; tasks 13/13
complete **pass**; destination-contract removal and stable credential specs
**pass**; Italo/Ana isolation and `SecretStr` **pass**; Família-first guard
**pass**; connector protocol/result and fixed StockDetail/export flow **pass**;
offline fake/no DB/no live network boundary **pass**; temporary cleanup and
basename handling **pass** for covered paths; dependency/lock and unit
allow-list **pass**; F57 archive and F59/F60/T31/D05/I08/T33 boundaries
**pass**; PRD §4 invariants in F58 scope **pass**; changed-file scope
assessment **pass**; explicit interaction timeout coverage **finding**;
runner isolation **finding**; complete scope assessability **pass**.

Full suite: `uv run task test` -> **not launched**; duration **N/A**;
duration limit **300s**; cleanup **N/A (no suite process created)**. Unit,
integration, audit integration, e2e, bdd, and visual lanes: **not run**.
Coverage and tests/skips: **N/A**. Fail-fast disposition: **not applicable;
launch blocked before runner**. No F58 test failure was observed, so no test
failure classification applies. The prior R2 receipt remains green at
251.33s runner / 252.01s external, but is not reused as this review's suite.
The <=300s gate is **not assessable** for R3.

Preflight: per-run ledger inspected at `2026-08-20T20:30:08-03:00`.
`resource_kind=port`, `resource_id=8000`, `owner=unknown`,
`owner_evidence=none`, `classification=unknown/pre-existing`; `ss` showed
listeners on `0.0.0.0:8000` and `[::]:8000`. Relevant test processes and
`/tmp/omaha-myprofit-*` were absent. Trusted ownership preflight **failed**;
no adoption, kill, free, delete, allowlist, or suite launch performed.

Postflight: ledger inspected at `2026-08-20T20:31:01-03:00`. Port 8000
remained `unknown/pre-existing`, cleanup `not attempted by policy`; relevant
test processes and MyProfit temporary roots absent. The inventory command's
own transient shell/Python PIDs were current-run inspection resources and
ended with command; no suite child existed. Runner isolation **failed** due
to unowned listener; no baseline or foreign-resource exception used.

OpenSpec verification: `openspec status --change
f58-integrar-automacao-playwright-myprofit --json` -> complete, 13/13 tasks;
`openspec validate f58-integrar-automacao-playwright-myprofit --type change
--strict --json` -> valid, 1/1 passed, 0 issues; `openspec validate --specs
--strict --json` -> valid, 70/70 passed, 0 failed; informational long
requirement notices only.

Changed/unrelated files: remediation diff is limited to
`src/omaha/myprofit/connector.py` and `tests/test_myprofit_connector.py`;
focused evidence records 15 passed and lint passed. Whole F58 scope remains
limited to dossier, connector package, mapped config/docs/spec/test/dependency
files. Current working-tree changes in `src/omaha/csv_import.py`,
`tests/bdd/step_defs/_workflows.py`, `tests/test_real_csv_flow.py`, visual
baselines, and other non-F58 paths are excluded as unrelated/pre-existing;
`openspec/roadmap.md` remains untouched by this review. No unrelated file was
edited by R3.

Verdict: **BLOCKED**

#### R1-F02 — Playwright stage timeout remains unbounded at zero
Status: open
Requirement/task: F58 delta `myprofit-position-csv-connector`, Requirement
“Connector SHALL bound failures and clean resources”; tasks 2.2 and 4.1
Evidence: `src/omaha/myprofit/connector.py:50-60` rejects negative timeout
values but accepts zero; Playwright treats `timeout=0` as no timeout. The
remediation test deliberately configures and accepts
`two_factor_probe_ms=0`/defer `click(timeout=0)` at
`tests/test_myprofit_connector.py:207-213,343-344`, so explicit argument is
present but not bounded. Other interaction arguments now carry configured
values; this remaining zero-value path prevents R1-F02 closure.
Required change: enforce strictly positive timeout values for every stage (or
otherwise guarantee a finite lower bound), use positive timeout values in
fake tests, and retain assertions/injected-timeout coverage for email fill,
password fill, submit click, defer click, Export click, and CSV click with
cleanup and sanitized stage/code errors. Excluded scope: no route, job,
parser, preview, UI, live browser, harness, environment repair, or
F59/F60/T31 work.
Acceptance: focused connector tests prove each interaction receives a finite
positive timeout and each injected interaction timeout closes context/removes
temporary roots; then a fresh green canonical full-suite receipt is produced
on an isolated runner.

#### R3-F01 — Canonical suite blocked by unowned port residue
Status: blocked
Requirement/task: PRD §4.13; review test gate runner-isolation precondition.
Evidence: R3 preflight ledger at `2026-08-20T20:30:08-03:00` recorded port
8000 as `owner=unknown`, `owner_evidence=none`, `classification=unknown/pre-existing`;
`ss -ltnp` showed listeners on `0.0.0.0:8000` and `[::]:8000`. R3 postflight
at `2026-08-20T20:31:01-03:00` showed same residue. No suite command was
launched.
Required change: owner must provide isolated runner with no unknown,
pre-existing, foreign, contradictory, or incomplete relevant resources, and
record ownership evidence in one per-run ledger before launching exactly one
`uv run task test`. Do not kill, adopt, free, delete, mask, or allowlist port
8000 residue.
Acceptance: trusted preflight passes; one canonical full suite runs through
child cleanup with six lane receipts, coverage/tests/skips, fail-fast
disposition, and elapsed wall-clock; all lanes exit 0 within 300s.

### Remediation pass 1 — R1-F02

Resolution status: implementation remediated; pending review confirmation.

- **Changed files/symbols:** `src/omaha/myprofit/connector.py::_download_from_page`
  now passes explicit configured timeouts to email/password `fill`, login
  `submit.click`, optional defer `click`, Export `click`, and CSV `click` inside
  `expect_download`; authentication and optional-prompt `is_visible` probes also
  receive bounded timeout values. `::_find_two_factor_defer` computes remaining
  probe budget before each bounded visibility probe. No destination, profile
  credentials, Família guard, route/job/UI, DB, parser, secret, or harness
  behavior changed.
- **Changed tests/symbols:** `tests/test_myprofit_connector.py::FakeLocator`,
  `FakePage`, `test_download_flow`, `test_two_factor_defer`, and new
  `test_each_playwright_interaction_uses_stage_timeout_and_cleans_up` assert
  configured values for email fill, password fill, submit click, defer click,
  Export click, and CSV click. Parameterized timeout injection proves each
  interaction maps to its sanitized stage/`timeout` error and removes its
  temporary root.
- **First remediation validation ledger:** run
  `f58-r1-f02-apply-20260820-200941`; `resource_kind=child_process`,
  `resource_id=PID:517556`, `owner=F58/R1-F02/apply`,
  `owner_evidence=wrapper registration before taskipy`,
  `started_at=2026-08-20T20:09:41-03:00`,
  `ended_at=2026-08-20T20:09:42-03:00`, `status=exited`,
  `classification=owned-cleaned`, `evidence=pytest completed with 8 failed /
  7 passed; no pytest/Playwright child or /tmp/omaha-myprofit-* residue`,
  `cleanup_result=natural process exit plus connector finally cleanup`.
  Command `uv run task test-file tests/test_myprofit_connector.py` failed
  during remediation because `_find_two_factor_defer` used `remaining_ms`
  before assignment; fixed in same scoped pass.
- **Focused validation ledger:** run
  `f58-r1-f02-apply-20260820-201019`; `resource_kind=child_process`,
  `resource_id=PID:517701`, `owner=F58/R1-F02/apply`,
  `owner_evidence=wrapper registration before taskipy`,
  `started_at=2026-08-20T20:10:19-03:00`,
  `ended_at=2026-08-20T20:10:20-03:00`, `status=exited`,
  `classification=owned-cleaned`, `evidence=15 passed in 0.21s; no
  pytest/Playwright/task child and no /tmp/omaha-myprofit-* residue`,
  `cleanup_result=natural process exit, connector finally cleanup, idempotent
  no-op for absent residue`.
- **Focused test assertion follow-up ledger:** run
  `f58-r1-f02-apply-20260820-202816`; `resource_kind=child_process`,
  `resource_id=PID:520334`, `owner=F58/R1-F02/apply`,
  `owner_evidence=wrapper registration before taskipy`,
  `started_at=2026-08-20T20:28:16-03:00`,
  `ended_at=2026-08-20T20:28:17-03:00`, `status=exited`,
  `classification=owned-cleaned`, `evidence=15 passed in 0.23s; every
  injected interaction timeout asserted context closure and no temporary-root
  residue`, `cleanup_result=natural process exit, connector finally cleanup,
  idempotent no-op for absent residue`.
- **Lint validation ledger:** run `f58-r1-f02-lint-20260820-202451`;
  `resource_kind=child_process`, `resource_id=PID:518574`,
  `owner=F58/R1-F02/apply`, `owner_evidence=wrapper registration before
  taskipy`, `started_at=2026-08-20T20:24:51-03:00`,
  `ended_at=2026-08-20T20:24:54-03:00`, `status=exited`,
  `classification=owned-cleaned`, `evidence=all prek/ruff/hygiene/unit hooks
  passed`, `cleanup_result=natural process exit; no test/runtime residue`.
- **Refresh-for-test receipt:** run
  `f58-r1-f02-refresh-20260820-202359`, owner
  `F58/R1-F02/apply-refresh`. Port ledger:
  `resource_kind=port`, `resource_id=8000`, `owner=F58/R1-F02/apply-refresh`,
  `owner_evidence=ss and healthz inventory before launch`,
  `started_at=2026-08-20T20:23:59-03:00`, `ended_at=2026-08-20T20:24:01-03:00`,
  `status=active`, `classification=unknown/pre-existing`,
  `evidence=already listening with no attributable owner`,
  `cleanup_result=not attempted by policy`. Existing health was read-only
  `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
  New uvicorn ledger entry: `resource_kind=child_process`,
  `resource_id=PID:518444` (wrapper PID `518438`),
  `owner=F58/R1-F02/apply-refresh`,
  `owner_evidence=wrapper registration before launch`,
  `started_at=2026-08-20T20:23:59-03:00`,
  `ended_at=2026-08-20T20:24:01-03:00`, `status=exited`,
  `classification=owned-cleaned`,
  `evidence=uvicorn address-in-use and bounded shutdown`,
  `cleanup_result=natural shutdown; no foreign process killed/adopted`.
  LAN URL
  `http://192.168.1.4:8000`; read-only DB counts `11 classes / 89 assets /
  88 positions`; dashboard probe observed `RF Din` count `5`, while login POST
  returned HTTP 405, so no fresh-server/auth claim is made. Cookie
  `/tmp/f58-r1-f02-refresh-20260820-202359-cookie` was registered before curl
  at `2026-08-20T20:24:36-03:00`, then exactly removed at
  `2026-08-20T20:24:36-03:00`; classification `owned-cleaned`, cleanup
  `exact-current-run-cookie-removed`.
- **Diff-scope confirmation:** remediation changes are limited to explicit
  Playwright interaction timeout arguments, bounded visibility probe timing,
  and connector fake/assertion coverage in the two files above. No unrelated
  F58 file was edited in this pass; pre-existing worktree changes and
  `openspec/roadmap.md` remain outside this slice.

### Remediation pass 2/2 — owner-authorized parity repair preflight

- **Pre-edit diff boundary:** captured `git diff HEAD~1` before editing. The
  target `src/omaha/myprofit/connector.py` and
  `tests/test_myprofit_connector.py` are untracked F58 files, so they have no
  `HEAD~1` patch; `HEAD~1` contains unrelated/pre-existing changes in F61,
  I08, D05, F57-derived config/docs/specs, runner/test harness, CSV/BDD,
  visual baselines, and `uv.lock`. The active F58 dossier is also untracked.
  Existing `openspec/roadmap.md`, `src/omaha/csv_import.py`,
  `tests/bdd/step_defs/_workflows.py`, `tests/test_real_csv_flow.py`, visual
  baselines, and all other non-target worktree paths are outside this pass.
- **Authorized repair boundary:** only `connector.py`,
  `test_myprofit_connector.py`, and this evidence section may change. No
  config, dependency, route, job, UI, parser, spec, runner, port, process, or
  database work is authorized.

### Remediation pass 2/2 — execution evidence

- **Implementation:** `src/omaha/myprofit/connector.py` now rejects every
  non-positive `MyProfitConnectorTimeouts` field before connector/browser use;
  `_first_visible` performs bounded fallback discovery across observed login
  selectors; `_find_two_factor_defer` covers role/button-filter/role-button/text
  fallbacks with bounded probes; Export uses the first locator and exact CSV
  uses the last locator. Changed symbols: `MyProfitConnectorTimeouts`,
  `_download_from_page`, `_find_two_factor_defer`, `_first_visible`, and login
  selector constants. Existing fixed URL, profile isolation, Família-first
  guard, temporary cleanup, sanitized errors, and destination-free boundary
  remain unchanged.
- **Tests:** `tests/test_myprofit_connector.py` fake doubles now model selector
  fallback and duplicate locator collections. Added coverage proves alternate
  login controls, alternate 2FA button-filter control, first Export, last exact
  CSV, and zero/negative rejection for every configurable timeout. Existing
  interaction-timeout injection still proves sanitized stage errors, context
  close, and temporary-root cleanup. No network, browser, parser, or DB call is
  used.
- **Focused test ledger:** run
  `f58-r1-f02-rem2-test-20260820-204840`; `resource_kind=child_process`,
  `resource_id=PID:523304`, `owner=F58/R1-F02/apply/remediation-2`,
  `owner_evidence=wrapper-registration-before-taskipy`,
  `started_at=2026-08-20T20:48:40-03:00`,
  `ended_at=2026-08-20T20:48:43-03:00`, `status=exited`,
  `classification=owned-cleaned`, `evidence=30 passed in 0.35s`,
  `cleanup_result=natural-process-exit`; no Playwright child or
  `/tmp/omaha-myprofit-*` residue remained. Earlier run
  `f58-r1-f02-rem2-test-20260820-204824` had 29 passed/1 failed because fake
  hidden fallback controls reported visible; test double corrected in the
  same authorized file, then rerun passed. No product failure remained.
- **Lint ledger:** run `f58-r1-f02-rem2-lint-20260820-204852`;
  `resource_kind=child_process`, `resource_id=PID:523341`,
  `owner=F58/R1-F02/apply/remediation-2`,
  `owner_evidence=wrapper-registration-before-taskipy`,
  `started_at=2026-08-20T20:48:52-03:00`,
  `ended_at=2026-08-20T20:49:12-03:00`, `status=exited`,
  `classification=owned-cleaned`, `evidence=all prek/ruff/hygiene/unit hooks
  passed`, `cleanup_result=natural-process-exit`.
- **Refresh receipt:** runtime refresh preflight run
  `f58-r1-f02-rem2-refresh-20260820-205003` recorded
  `resource_kind=port`, `resource_id=8000`,
  `owner=F58/R1-F02/apply/remediation-2-refresh`,
  `owner_evidence=preflight-inventory-before-use`,
  `started_at=2026-08-20T20:50:03-03:00`, `ended_at=2026-08-20T20:50:26-03:00`,
  `status=active`, `classification=unknown/pre-existing`,
  `evidence=ss showed listeners on 0.0.0.0:8000 and [::]:8000 with no
  attributable owner`, `cleanup_result=not-attempted-by-policy`,
  `residue=listener-remains`. No launch, kill, adoption, free, delete, or
  allowlist action occurred. Read-only smoke used LAN URL
  `http://192.168.1.4:8000`; health returned `{"status":"ok","db":"ok",
  "service":"omaha","version":"0.1.0"}` and DB counts were `11 classes`,
  `89 assets`, `88 positions`. Dashboard GET returned login HTML because
  existing server session was unauthenticated; follow-up run
  `f58-r1-f02-rem2-refresh-dashboard-20260820-205037` confirmed 4251 bytes,
  login marker present, and no app-shell marker. Wrapper resources exited
  naturally as `owned-cleaned`; no temporary path was created. Initial smoke's
  dashboard parser used unavailable `python` and produced curl pipe error;
  bounded follow-up used `python3` and passed. Refresh could not restart server
  under isolation policy.
- **Scope proof:** current remediation functional edits are limited to
  `src/omaha/myprofit/connector.py` and `tests/test_myprofit_connector.py`;
  this evidence is the only F58 dossier edit. `git diff HEAD~1` boundary and
  pre-existing unrelated worktree paths remain recorded above. No canonical
  full suite was run by apply; review owns its isolated-run gate.

### Review R4 — remediation 2/2 final
Scope audit: proposal **pass**; design decisions **pass**; tasks 13/13
complete **pass**; connector bounded login/2FA fallback discovery **pass**;
strictly-positive timeout validation before browser use **pass**; first Export
and last exact CSV selection **pass**; destination-free profile isolation and
`SecretStr` credential handling **pass**; Família-first guard **pass**;
sanitized errors and temporary cleanup **pass**; offline fake/no DB/no live
network boundary **pass**; dependency/lock and explicit unit allow-list
**pass**; F57 archive and F59/F60/D05/I08/T33 boundaries **pass**; preserved
PRD §4 invariants in F58 scope **pass**; changed-file/unrelated-file audit
**pass**; exact F58 spec coverage **pass**; runner isolation **finding**;
full-suite acceptance **not assessable** because trusted preflight failed;
complete scope assessability otherwise **pass**.

Full suite: canonical command `uv run task test` -> **not launched**;
elapsed wall-clock **N/A**; duration limit **300s**; cleanup **N/A (no suite
process created)**. Unit, integration, audit integration, e2e, bdd, and visual
lanes: **not run**. Coverage and tests/skips: **N/A**. Fail-fast disposition:
**not applicable; launch blocked before runner**. No test failure observed;
failure classification **N/A**. Prior green R2 receipt is not reused. The
<=300s classification is **not assessable**.

Preflight: per-run ledger inspected at `2026-08-20T20:53:45-03:00` and
`2026-08-20T20:53:39-03:00`. Ledger fields: `resource_kind=listener`,
`resource_id=tcp:8000`, `owner=unknown`, `owner_evidence=none`,
`started_at=not-current-run`, `ended_at=N/A`, `status=observed`,
`classification=unknown/pre-existing`, `evidence=ss showed listeners on
0.0.0.0:8000 and [::]:8000 with no attributable PID/owner`,
`cleanup_result=not attempted by policy`. `/tmp/pytest-of-juca` and
`/tmp/playwright_chromiumdev_profile-bs0UW8` were pre-existing resources with
no current-run ownership evidence; no current-run uvicorn/pytest/Playwright
process was observed. Trusted ownership preflight **failed**. No kill,
adoption, free, delete, mask, or allowlist action occurred.

Postflight: ledger inspected at `2026-08-20T20:54:30-03:00`; port 8000 and
pre-existing test/browser temporary roots remained
`unknown/pre-existing`; no suite process existed, so no cleanup was attempted.
Inspection shell/Python processes ended naturally. Runner isolation **failed**;
no baseline or foreign-resource exception used.

OpenSpec verification: `openspec status --change
f58-integrar-automacao-playwright-myprofit --json` -> complete, 13/13 tasks;
`openspec validate f58-integrar-automacao-playwright-myprofit --type change
--strict --json` -> valid, 1/1 passed, 0 issues; `openspec validate --specs
--strict --json` -> valid, **70/70** passed, 0 failed; informational
long-requirement notices only.

Changed/unrelated files: remediation functional edits remain limited to
`src/omaha/myprofit/connector.py` and `tests/test_myprofit_connector.py`;
current unrelated worktree changes in CSV/BDD/visual/runner and
`openspec/roadmap.md` remain excluded and untouched by this review. No
unrelated file change attributable to F58 remediation was found. Review
evidence is appended only here in F58 `tasks.md`.

Verdict: **BLOCKED**

#### R4-F01 — Canonical suite blocked by unowned runner residue
Status: blocked
Requirement/task: PRD §4.13; F58 task 4.1 full delivery acceptance; review
test-gate isolated-runner precondition
Evidence: per-run ledger above; `ss -ltnp '( sport = :8000 )'` showed listeners
on `0.0.0.0:8000` and `[::]:8000`, without attributable owner/PID. Pre-existing
`/tmp/pytest-of-juca` and `/tmp/playwright_chromiumdev_profile-bs0UW8` likewise
lacked current-run ownership evidence. No canonical suite command was launched.
Required change: owner must provide isolated runner with no unknown,
pre-existing, foreign, contradictory, or incomplete relevant resources, then
run exactly one `uv run task test` and record child cleanup, six lane results,
coverage/tests/skips, fail-fast disposition, and elapsed wall-clock. Do not
kill, adopt, free, delete, mask, or allowlist residue. No third remediation
pass or code repair is requested; remediation limit 2/2 reached and owner
decision is required.
Excluded scope: F59/F60, URL/env configuration, browser fingerprint or
persistent profiles, DB/parser/UI/jobs, F57 archive, and D05/I08/T33
runner/harness work.
Acceptance: trusted preflight passes; one canonical suite exits 0 across all
six lanes, with cleanup receipt and elapsed wall-clock <=300s. Until then F58
cannot enter Applied or owner delivery validation.

### Review R5 — final canonical review after remediation 2/2
Scope audit: proposal **pass**; design decisions **pass**; tasks 13/13
complete **pass**; connector bounded interaction/fallback behavior **pass**;
strictly-positive timeout validation **pass**; fixed StockDetail/export flow
**pass**; destination-free credential isolation and `SecretStr` **pass**;
Família-first guard **pass**; sanitized errors and temporary cleanup **pass**;
offline fake/no DB/no live network boundary **pass**; dependency/lock and unit
allow-list **pass**; F57 archive and F59/F60/D05/I08/T33 boundaries **pass**;
PRD §4 invariants in F58 scope **pass**; changed-file/unrelated-file audit
**pass**; exact F58 delta coverage **pass**; stable/change spec validation
**pass**; runner isolation **finding**; full-suite acceptance **not
assessable**; complete scope assessability **pass** except canonical test gate.

Spec verification: `openspec validate
f58-integrar-automacao-playwright-myprofit --type change --strict --json` ->
valid, 1/1 passed, 0 issues. `openspec validate --specs --strict --json` ->
valid, 70/70 passed, 0 failed; informational long-requirement notices only.

Server identity/stop receipt: owner authorization received before stop. Exact
pre-stop inventory identified Omaha container `63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`,
`/omaha-web-1`, running PID `419701`, PGID `419701`, command
`/app/.venv/bin/python /app/.venv/bin/fastapi run --host 0.0.0.0 --port 8000
src/omaha/main.py`; host listeners were exact docker-proxy PIDs `419748` and
`419754`, PGID `346`, forwarding `0.0.0.0:8000`/`[::]:8000` to container
`172.19.0.2:8000`. Container inspect independently confirmed published port
8000 and Omaha image `omaha:dev`; no name-pattern or broad port cleanup used.
Controlled command `sudo -n docker stop --timeout 30 omaha-web-1` stopped only
that confirmed container; post-stop port inventory was empty and container
state was exited.

Preflight: per-run ledger at `2026-08-20T21:22:29-03:00`; fields recorded:
`resource_kind=listener/container/test-temp`, `resource_id=tcp:8000 /
omaha-web-1 / /tmp/pytest-of-juca /tmp/playwright_chromiumdev_profile-bs0UW8`,
`owner=F58 final review` for controlled stop and `owner=unknown` for existing
test-temp roots, `owner_evidence=owner authorization plus PID/PGID/command/
port/container inspection` for server and `none for pre-existing temp roots`,
`started_at=2026-08-20T21:22:29-03:00` for inventory, `ended_at=N/A`,
`status=stopped for server; observed for temp roots`,
`classification=owned-current-run` for authorized stop lane and
`unknown/pre-existing` for both temp roots, `evidence=post-stop port empty;
glob inventory found both roots`, `cleanup_result=server stopped by exact
container command; temp cleanup not attempted by policy`. Trusted preflight
**failed**. No adoption, deletion, killing, freeing, masking, or allowlisting
of pre-existing residue occurred. Runner isolation precondition failed; no
foreign-resource or baseline exception used.

Full suite: canonical command `uv run task test` -> **not launched**; elapsed
wall-clock **N/A**; duration limit **300s**; cleanup **N/A (no suite process
created)**. Unit, integration, audit integration, e2e, bdd, and visual lanes:
**not run**. Coverage and tests/skips: **N/A**. Fail-fast disposition: **not
applicable; launch blocked before runner**. No test failure observed, so no
failure classification applies. The <=300s classification is **not
assessable**. Exactly zero canonical suite attempts were made in R5.

Postflight/restart receipt: exact current-run restart command
`sudo -n docker start omaha-web-1`; new container PID `528309`, PGID `528309`,
host docker-proxy PIDs `528352` and `528359`; port listeners restored on
`0.0.0.0:8000` and `[::]:8000`. Initial immediate health probe reset during
startup; read-only retry after 3 seconds returned
`{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
LAN URL: `http://192.168.1.4:8000`. Final postflight at
`2026-08-20T21:23:05-03:00`: Omaha container/listeners
`owned-current-run`; `/tmp/pytest-of-juca` and
`/tmp/playwright_chromiumdev_profile-bs0UW8` remained
`unknown/pre-existing`, cleanup **not attempted by policy**. No production DB
operation was issued; no reset, seed, clear, or standalone migration command
was run. Existing container startup emitted its configured Alembic startup
step; no schema change was observed or requested.

Verdict: **BLOCKED**

#### R5-F01 — Canonical suite blocked by pre-existing test resources
Status: blocked
Requirement/task: PRD §4.13; F58 task 4.1 full delivery acceptance; review
test-gate isolated-runner precondition; R4-F01
Evidence: R5 preflight found pre-existing `/tmp/pytest-of-juca` and
`/tmp/playwright_chromiumdev_profile-bs0UW8` without current-run ownership
evidence. Protocol requires no unknown, pre-existing, foreign, contradictory,
or incomplete relevant resource before launch. Therefore `uv run task test`
was not run; six lane receipt, coverage, and <=300s result are unavailable.
Required change: owner must provide isolated runner with no relevant unowned
test-temporary resources, then authorize one fresh canonical review attempt;
preserve all tests, lanes, skips, and coverage. Do not delete/adopt/kill/free
residue, do not request third remediation, and do not alter F58 code.
Excluded scope: F59/F60, URL/env configuration, UI/jobs/DB/parser, F57
archive, D05/I08/T33, and unknown host residue.
Acceptance: trusted preflight ledger classifies every relevant resource as
owned-current-run, absent, or owned-cleaned with PID/PGID/port/temp evidence;
one `uv run task test` exits 0 across unit, integration, audit integration,
e2e, bdd, and visual lanes; cleanup is trusted; elapsed wall-clock <=300s.
Late finding reason: R5 is final gate after remediation 2/2; this is unresolved
R4-F01 runner isolation, not new implementation scope.

### Review R6 — resumed final gate after Omaha LAN restoration
Scope audit: proposal **pass**; design decisions **pass**; tasks 13/13
complete **pass**; connector bounded interaction/fallback behavior **pass**;
strictly-positive timeout validation **pass**; fixed StockDetail/export flow
**pass**; destination-free credential isolation and `SecretStr` **pass**;
Família-first guard **pass**; sanitized errors and temporary cleanup **pass**;
offline fake/no DB/no live network boundary **pass**; dependency/lock and unit
allow-list **pass**; F57 archive and F59/F60/D05/I08/T33 boundaries **pass**;
PRD §4 invariants in F58 scope **pass**; changed-file/unrelated-file audit
**pass**; exact F58 delta coverage **pass**; stable/change spec validation
**pass**; service restoration **pass**; runner isolation preflight **pass**;
full-suite test gate **finding**; complete scope assessability **pass**.

Restoration receipt: pre-restore inventory at `2026-08-20T21:43:33-03:00`
identified only confirmed Omaha container `63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`,
`/omaha-web-1`, image `omaha:dev`, exited, published `8000/tcp`, configured
command `alembic upgrade head && exec fastapi run --host 0.0.0.0 --port 8000
src/omaha/main.py`; host port inventory was empty. No other container/resource
was touched. Exact restore command `sudo -n docker start omaha-web-1` ran at
`2026-08-20T21:43:44-03:00`; container became running with PID/PGID
`533067`, `docker top` command `/app/.venv/bin/python /app/.venv/bin/fastapi
run --host 0.0.0.0 --port 8000 src/omaha/main.py`, and listeners were
`0.0.0.0:8000` and `[::]:8000`. Read-only health
`http://192.168.1.4:8000/healthz` returned
`{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`
at `2026-08-20T21:43:54-03:00`. No DB reset, seed, clear, standalone
migration, code edit, or other-resource action occurred.

Preflight: per-run ledger inspected after restoration at
`2026-08-20T21:44:17-03:00`; `resource_kind=container/process/listener/test-temp`,
`resource_id=omaha-web-1/PID:533067/PGID:533067/tcp:8000,8765-8768,
/tmp/pytest-of-juca,/tmp/playwright_chromiumdev_profile-bs0UW8,
/tmp/omaha-myprofit-*`, `owner=F58 final review` for restored Omaha service and
`owner=none` for absent test resources, `owner_evidence=exact container
inspect plus docker top plus ss; absent-resource inventory`, `started_at=`
`2026-08-20T21:43:44-03:00` for service, `ended_at=N/A`, `status=running /
absent`, `classification=owned-current-run / absent`, `evidence=container
identity and command match Omaha; only tcp:8000 listener; no test processes,
8765-8768 listeners, Playwright roots, or MyProfit roots`,
`cleanup_result=service intentionally left running; no test resource cleanup
needed`. Trusted preflight passed; no foreign, unknown, pre-existing,
contradictory, or incomplete relevant state was adopted or repaired. Prior R5
receipt explicitly recorded zero canonical-suite attempts, so this R6 launch
was eligible and was the sole R6 `uv run task test` attempt.

Full suite: canonical command `uv run task test` -> **red**;
external wall-clock `159.67s`; runner receipt
`reports/test-profile/20260820T214446-run.json` elapsed `158.7663s`, duration
limit **300s**, duration exceeded **false**, cleanup reported complete and all
owned lane children were stopped/reaped. Six lane receipt: unit exit **241**,
integration exit **1**, audit integration exit **241**, e2e exit **143**, bdd
exit **143**, visual exit **1**. Unit/audit/e2e/bdd were fail-fast sibling
stops after `fail-fast:visual`; integration reached four selected admin tests
before `process PID not found (pid=533637)` at
`reports/test-profile/20260820T214446-integration.log:12-16`; visual collected
eight tests and all eight errored because isolated server `127.0.0.1:8768`
never became ready after its process exited, with no server output, at
`reports/test-profile/20260820T214446-visual.log:39-135`; no F58 symbol appears
in either failure. Available receipt reconciliation: expected manifest 1032,
actual nodes 117, expected skips 2, actual skips 0, `skip_mismatch=true`,
`ok=false`; coverage report unavailable. Post-run inventory at
`2026-08-20T21:48:07-03:00` found no pytest/Playwright/task-test processes and
no 8765-8768 listeners; Omaha remained running on 8000. `/tmp/pytest-of-juca`
was absent preflight but existed after suite, created during this run; runner
receipt says cleanup complete while postflight observed this current-run root,
so cleanup receipt is not fully trusted. No broad or foreign cleanup occurred.
Test gate failed; failures classify as **unknown/environmental** (integration
PID race and visual isolated-server startup), with e2e/bdd/unit/audit collateral
termination, not F58 code failures. Elapsed time was within 300s but cannot
override red tests or cleanup-receipt uncertainty.

Postflight: ledger end `2026-08-20T21:48:07-03:00`; Omaha
`owned-current-run` and healthy, test child processes and test ports absent,
current-run pytest root observed, classification `owned-current-run`,
`cleanup_result=lane children cleaned; root cleanup discrepancy recorded`; no
foreign/pre-existing resources were touched. Runner isolation after suite is
not fully trusted because runner receipt and filesystem inventory disagree.

Runner isolation: pre-launch precondition **passed** after exact Omaha service
restore; relevant listener/process/test-temp inventory had no unowned state.
Postflight cleanup receipt **not assessable as fully trusted** because
`/tmp/pytest-of-juca` remained after runner reported complete cleanup.

Verdict: **BLOCKED**

#### R6-F01 — Canonical suite red from unrelated runner/server failures
Status: blocked
Requirement/task: PRD §4.13; F58 task 4.1 full delivery acceptance; R5-F01
acceptance
Evidence: `reports/test-profile/20260820T214446-integration.log:12-16`
shows `process PID not found (pid=533637)` during
`test_admin_restore_404_for_missing_snapshot`; integration exit 1.
`reports/test-profile/20260820T214446-visual.log:39-135` shows all eight visual
nodes erroring because `127.0.0.1:8768` never became ready and server output is
empty; visual exit 1. Unit/audit exit 241 and e2e/bdd exit 143 are explicitly
collateral fail-fast stops in `reports/test-profile/20260820T214446-run.json`.
No F58 symbol/path appears in failure evidence.
Required change: owner must diagnose and resolve or explicitly classify both
local runner failures, then obtain owner-authorized isolated review handling;
do not modify F58 code, tests, DB, or unrelated runner/server resources, and
do not run another full suite in this review. Preserve all tests, lanes, skips,
coverage, fail-fast behavior, and 300-second ceiling.
Acceptance: owner decision records disposition for PID race and visual server
startup; a later authorized review records one trusted green canonical suite
with six lane exits 0, coverage/tests/skips/reconciliation, trusted cleanup,
and elapsed wall-clock <=300s.

#### R6-F02 — Full-suite cleanup receipt contradicts postflight inventory
Status: blocked
Requirement/task: PRD §4.13; review test-gate postflight protocol
Evidence: `reports/test-profile/20260820T214446-run.json:5-7,81-82` reports
runner cleanup complete and no lane residue, but preflight at
`2026-08-20T21:44:31-03:00` showed no `/tmp/pytest-of-juca` and postflight at
`2026-08-20T21:48:07-03:00` showed `/tmp/pytest-of-juca` created at 21:45.
Receipt cannot prove complete current-run temporary cleanup.
Required change: owner must provide trusted runner/postflight evidence that
current-run temporary resources are reconciled without deleting, adopting, or
cleaning foreign residue; no F58 implementation change requested.
Acceptance: future review receipt classifies every lane temp resource as
owned-cleaned or absent, reconciles runner receipt with postflight inventory,
and preserves all tests and coverage.
Late finding reason: R6 is resumed after R5 service restoration; discrepancy
became observable only after this canonical suite attempt.

### Review R7 — maintenance-suspended final gate
Scope audit: proposal **pass**; design decisions **pass**; tasks 13/13 complete
**pass**; destination-free connector/configuration **pass**; Italo/Ana
per-profile email/password isolation and `SecretStr` **pass**; Família-first
block before credential lookup/launcher **pass**; bounded positive login,
2FA, Export, CSV, and download interaction timeouts **pass**; bounded login
selector and 2FA fallback discovery **pass**; first Export and last exact CSV
locator selection **pass**; fixed StockDetail navigation **pass**; sanitized
stage/code errors **pass**; temporary profile/download cleanup **pass** for
success and covered failure paths; offline fake boundary with no DB/parser/
network/live browser **pass**; dependency/lock and unit allow-list **pass**;
stable and change spec coverage/validation **pass**; F57 archive and
F59/F60/T34/I10 scope boundaries **pass**; preserved PRD invariants in F58
scope **pass**; changed-file audit **pass**; complete scope assessability
**pass**.

Focused evidence: `uv run task test-file tests/test_myprofit_connector.py` ->
**30 passed** (`f58-r1-f02-rem2-test-20260820-204840`); prior F57 config file
-> **10 passed**; auth documentation -> **1 passed**; `uv run task lint` ->
**passed**. Evidence records owned-cleaned task processes, no Playwright
child, no MyProfit request, no DB/parser call, and no
`/tmp/omaha-myprofit-*` residue. No focused failure remains. Coverage was not
collected by focused receipts.

Full suite: canonical `uv run task test` -> **NOT RUN —
maintenance-suspended**. Unit, integration, audit integration, e2e, bdd, and
visual lanes: **NOT RUN — maintenance-suspended**. Coverage and tests/skips:
**N/A for canonical suite**; focused counts above retained. Fail-fast:
**not applicable**. Canonical elapsed wall-clock: **N/A**; 300-second
classification: **NOT ASSESSED by policy, not a failure**.

Preflight: canonical ownership/runner preflight **not executed by policy**;
maintenance-suspended gate forbids full-suite launch and process/DB cleanup.
No resource was adopted, killed, freed, deleted, masked, or allowlisted.
Prior R6 runner findings are superseded by T34/I10 maintenance-suspended
policy, not treated as F58 failures.

Postflight: canonical postflight **N/A — no suite launched**; no suite
resources or cleanup receipt claimed. Focused validation receipts retain their
per-run ownership, natural process exit, connector `finally` cleanup, and
absence of MyProfit temporary roots.

Runner isolation: canonical isolated-runner precondition **not applicable
under maintenance-suspended policy**; no canonical runner was launched.

Verdict: **APPROVED**

No open findings. R6-F01/R6-F02 are policy-superseded canonical-runner
findings; no implementation remediation or new scope requested. F58 may exit
Applying for owner validation; archive/commit/push remain excluded.
