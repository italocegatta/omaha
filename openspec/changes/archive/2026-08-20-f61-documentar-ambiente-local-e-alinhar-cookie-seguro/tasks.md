## 1. Operator documentation

- [x] 1.1 `.env.example` application configuration block: add exact
  `OMAHA_ENV=development` with comments describing exact case-sensitive
  `production` versus local/non-production defaults. Preserve all existing
  false MyProfit placeholders, `ADMIN_PASSWORD=distendidos`, and secret warning.
  Acceptance: template contains one development mode entry, no real secrets,
  and no F57 credential/destination changes. Test file/scenario:
  `tests/test_auth.py::test_environment_mode_documentation` (planned scan of
  `.env.example`). Focused command: `uv run task test-file tests/test_auth.py`.
  Independent oracle: parse `.env.example` as text and assert exact mode line,
  required preserved password, and absence of real credential material.

- [x] 1.2 `README.md` Quick start lines 18-41: document copied ignored `.env`,
  exact `OMAHA_ENV=development`, exact case-sensitive production behavior, and
  retain `uv run task serve` plus `0.0.0.0` guidance. Do not redefine MyProfit
  destinations or expose `.env` values. Acceptance: README satisfies the new
  mode scenarios while existing `readme-freshness` content remains unchanged.
  Test file/scenario: `tests/test_auth.py::test_environment_mode_documentation`.
  Focused command: `uv run task test-file tests/test_auth.py`. Independent
  oracle: required literals are present; forbidden real-secret and excluded
  F57/F58-F60/T31 terms are absent from changed documentation.

## 2. Runtime source alignment

- [x] 2.1 `src/omaha/main.py::create_app` session middleware option: replace
  only the direct `os.environ.get("OMAHA_ENV")` check with exact comparison of
  loaded `settings.OMAHA_ENV`. Preserve cookie name, secret key, `same_site`,
  middleware order, routes, and logging setup. Acceptance: `.env`-loaded
  production settings produce `https_only=True`; loaded development and any
  non-exact production value produce `False`; no second environment lookup
  remains in cookie configuration. Test file/scenarios:
  `tests/test_auth.py::test_session_cookie_mode_uses_loaded_settings`,
  `::test_session_cookie_does_not_follow_later_process_environment_change`.
  Focused command: `uv run task test-file tests/test_auth.py`. Independent
  oracle: inspect `app.user_middleware` exact `https_only` boolean and monkeypatch
  process environment after settings load; no repository `.env` is opened.

- [x] 2.2 Preserve `src/omaha/config.py::Settings` and
  `Settings.effective_log_format` behavior while making its contract explicit
  in tests: process environment overrides temporary `.env` before load, exact
  development selects text, exact production selects JSON, and explicit
  `LOG_FORMAT` wins only for logs. Acceptance: no new normalization, setting,
  or secret-handling change. Test file/scenarios:
  `tests/test_auth.py::test_environment_mode_load_precedence_and_log_defaults`,
  `::test_explicit_log_format_does_not_change_cookie_mode`. Focused command:
  `uv run task test-file tests/test_auth.py`. Independent oracle: instantiate
  `Settings(_env_file=tmp_path / ".env")` with synthetic values and assert exact
  `OMAHA_ENV`, `effective_log_format`, and middleware option.

## 3. Regression coverage

- [x] 3.1 `tests/test_auth.py`: add isolated scenarios for temporary `.env`
  loading, process-environment precedence, post-load process drift, exact
  `development`, exact `production`, case-sensitive `Production`, explicit log
  override, and documentation. Keep existing auth/session assertions and test
  fixture boundaries; do not read actual `.env`, mutate production DB, add
  network calls, or add masked-pass constructs. Acceptance: every runtime-mode
  delta scenario has an exact assertion and existing auth tests remain intact.
  Test file/scenario: this module, named scenarios above. Focused command:
  `uv run task test-file tests/test_auth.py`. Independent oracle: all focused
  tests pass with no external client, real credential, or production DB access.

## 4. Stable contracts

- [x] 4.1 `specs/runtime-environment-mode/spec.md`: add requirements and
  scenarios for one loaded settings source, exact production/development and
  fallback semantics, `.env`/process precedence, later process drift, and
  explicit log-format precedence. Preserve non-goals: no broad config cleanup,
  no formatter rewrite, no cookie attribute redesign. Acceptance: each
  scenario maps to a planned focused test and implementation symbol.
  Test file/scenario: `tests/test_auth.py` mode scenarios. Focused command:
  `uv run task test-file tests/test_auth.py`. Independent oracle:
  `openspec validate --specs --strict` accepts delta structure and no unrelated
  stable spec is modified.

- [x] 4.2 `specs/readme-freshness/spec.md`: modify only README requirement to
  require local `OMAHA_ENV=development` guidance and exact production meaning;
  preserve all existing freshness scenarios. Acceptance: delta is limited to
  documentation contract and contains no F57 credential or MyProfit destination
  semantics. Test file/scenario: documentation scenario in
  `tests/test_auth.py`. Focused command: `uv run task test-file tests/test_auth.py`.
  Independent oracle: `openspec validate --specs --strict` passes and the
  stable README contract remains otherwise unchanged.

## 5. Proposal gate validation

- [x] 5.1 Validate only this OpenSpec dossier after all artifacts exist:
  `openspec validate f61-documentar-ambiente-local-e-alinhar-cookie-seguro --type change --strict`.
  Acceptance: proposal, design, tasks, and both delta specs validate; no
  implementation tests run. Test file/scenario: N/A, artifact gate only.
  Focused command: `uv run task test-unit` is explicitly **not run** at proposal
  gate. Independent oracle: change validator reports zero errors.

- [x] 5.2 Validate stable specs and scope:
  `openspec validate --specs --strict`, `openspec status --change
  f61-documentar-ambiente-local-e-alinhar-cookie-seguro --json`, and
  `rtk git diff --check --
  openspec/changes/f61-documentar-ambiente-local-e-alinhar-cookie-seguro`.
  Acceptance: stable-spec validation is green, status reports all required
  artifacts complete/apply-ready, whitespace is clean, and only this dossier
  is changed. Test file/scenario: N/A, artifact gate only. Focused command:
  no taskipy test command; OpenSpec validation commands above are canonical for
  this proposal gate. Independent oracle: `git status --short` shows only the
  exact F61 change paths and no runtime/docs/tests files.

## Test strategy

- Runtime regression file: `tests/test_auth.py`; existing integration marker
  remains sufficient, so no new allow-list entry is planned.
- Configuration tests use `tmp_path` env files and `monkeypatch` process
  overrides with synthetic non-secret values. They never read repository `.env`.
- Focused implementation command: `uv run task test-file tests/test_auth.py`.
- Focused single scenario command for apply: `uv run task test-one
  tests/test_auth.py::test_session_cookie_mode_uses_loaded_settings`.
- Proposal gate intentionally runs no pytest/taskipy implementation test.
- Review, not proposal/apply, owns one full `uv run task test` run; no full suite
  is claimed here.

## Execution Evidence

### Initial apply pass

- **1.1 complete:** `.env.example` now contains one exact
  `OMAHA_ENV=development` entry with case-sensitive production and restart
  guidance. Existing `ADMIN_PASSWORD=distendidos` and F57 false placeholders
  remain unchanged.
- **1.2 complete:** README Quick start documents copied ignored `.env`, local
  development mode, exact production behavior, plain-HTTP fallback, required
  server restart after `.env` edits, `uv run task serve`, and `0.0.0.0`.
- **2.1 complete:** `src/omaha/main.py::create_app` now derives only
  `SessionMiddleware.kwargs["https_only"]` from loaded `settings.OMAHA_ENV`.
  Cookie name, secret, SameSite, middleware order, routes, and logging setup
  remain unchanged.
- **2.2 complete:** `src/omaha/config.py::Settings` and
  `Settings.effective_log_format` were preserved. Tests prove existing
  process-over-file precedence and explicit `LOG_FORMAT` precedence.
- **3.1 complete:** `tests/test_auth.py` adds exact assertions for temporary
  `.env` loading, development/production/unknown/case-sensitive modes,
  process override, later process drift, explicit log override, and docs.
  Existing auth/session tests remain intact.
- **4.1/4.2 complete:** F61 delta specs were pre-existing approved artifacts;
  implementation maps every scenario to focused tests and no stable spec or
  unrelated capability was edited.

### Focused validation receipts

- `uv run task test-file tests/test_auth.py` → **15 passed**.
- `uv run task test-one tests/test_auth.py::test_session_cookie_mode_uses_loaded_settings`
  → **4 passed** (parameterized exact-mode scenarios).
- `openspec validate f61-documentar-ambiente-local-e-alinhar-cookie-seguro
  --type change --strict --json` → **valid, 1/1 passed, 0 failures**.
- `openspec validate --specs --strict --json` → **valid, 69/69 passed, 0
  failures**; existing informational long-requirement notices remain.
- `openspec status --change f61-documentar-ambiente-local-e-alinhar-cookie-seguro
  --json` → **isComplete: true**; all dossier artifacts done.
- `rtk git diff --check` → **clean**.
- No repository `.env` was opened. No database mutation, migration, external
  service, or credential access performed.

### Refresh-for-test receipt

- `bash scripts/print_lan_url.sh` → `http://192.168.1.4:8000`.
- Restart attempted with detached `uv run uvicorn omaha.main:app
  --host 0.0.0.0 --port 8000`; environment-managed FastAPI process reclaimed
  port 8000 after local launcher bind contention. Final read-only health check
  returned `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- DB left untouched per PRD §4.12: **11 classes / 89 assets / 88 positions**.
  No reset, clear, seed, migration, or destructive route executed.
- Read-only auth/dashboard smoke: login `303`, profile select `303`, page
  `200`, seeded `RF Din` count **5**.
- Final environment-managed server PID: **419701** (`fastapi run`, port 8000).

## Acceptance evidence required before Apply handoff

- Exact `development` and exact case-sensitive `production` behavior recorded
  for default logs and session-cookie Secure flag.
- `.env`-loaded settings and process-environment precedence/drift scenarios pass
  without opening actual `.env`.
- Existing auth cookie/session behavior remains green.
- Change validation and stable-spec validation results are recorded in
  `design.md`; changed-file scope contains only F61 dossier at this gate.
- No implementation, runtime docs, tests, database, secrets, F57, F58-F60, or
  T31 work is performed during proposal.

## Review Findings

### Review R1
Scope audit: proposal requirements pass; design decisions pass; tasks 1.1–5.2
pass by implementation/dossier evidence; runtime-environment-mode requirements
and six scenarios pass by `src/omaha/main.py:187-193` and
`tests/test_auth.py:72-188`; readme-freshness requirement and three scenarios
pass by `.env.example:12-16`, `README.md:22-44`, and existing README contract
evidence; excluded scope (config mechanism, formatter, DB, secrets, F57,
F58-F60, T31) pass by diff and dossier evidence; full-suite acceptance is not
assessable because canonical runner terminated with lane/process failures.
Full suite: `uv run task test` -> RED/indeterminate, 854.89 seconds measured
by runner, cleanup incomplete/failed (unit, integration, audit, BDD, and visual
lanes reported `process PID not found`; E2E terminated with exit 241; parent
returned exit 124). Duration limit: 300 seconds. Test gate: not passed.
Verdict: BLOCKED

#### R1-F01 — Canonical full-suite runner failed before suite completion
Status: blocked
Requirement/task: Test strategy review gate in tasks.md:117-119; PRD
§4.13; review test gate.
Evidence: `uv run task test` started all six lanes but did not produce completed
pytest summaries. `reports/test-profile/20260820T122938-integration.log:32`
and `audit.log:42-107` show `process PID not found` followed by taskipy
`psutil.NoSuchProcess`; `bdd.log:13-38` shows the same PID failure and
Playwright `write EPIPE`; `e2e.log:14` stops at an in-progress test; visual
`visual.log:30` stops at `process PID not found`; command returned `124` after
854.89 seconds, above 300-second ceiling. Failure is **Unknown/environmental**:
logs show runner/child lifecycle failure, not a F61 assertion, and no complete
per-test result exists to attribute to this slice.
Required change: provide clean runner/process state capable of completing
`uv run task test` with all child lanes cleaned up and complete per-test
summaries; preserve all tests, skips, and coverage. Do not alter F61 runtime,
README, `.env.example`, or test implementation based on this receipt.
Excluded scope: no F61 code fix, test relaxation, test masking, lane removal,
DB reset, or coverage reduction authorized by this finding.
Acceptance: one canonical `uv run task test` run completes with exit 0,
all lane child processes cleaned up, complete summaries for unit, integration,
audit, e2e, bdd, and visual lanes, and wall-clock duration <=300 seconds;
then re-audit F61 without rerunning unrelated commands as substitutes.
Late finding reason: N/A; initial review.

### Review R2
Scope audit: proposal requirements pass; design decisions pass; tasks 1.1–5.2
pass with 9/9 complete; runtime-environment-mode requirement and six scenarios
pass by `src/omaha/main.py:187-193` and `tests/test_auth.py:72-188`;
readme-freshness requirement and three scenarios pass by `.env.example:12-16`,
`README.md:22-44`, and focused documentation assertions; preserved invariants
(exact mode matching, loaded-settings source, cookie attributes, logging
precedence, family password, `0.0.0.0`, taskipy, `.env` secrecy, DB/F57/F58-F60/
T31 boundaries) pass; changed-symbol and scope audit pass; test coverage and
regression risk pass; no area not assessable.
Full suite: `uv run task test` -> GREEN, exit 0, 249.43 seconds measured
externally from process start through child cleanup, cleanup clean (post-run
process check found no pytest/Playwright/full-suite/test-profile children).
Lane evidence: unit, integration, audit, e2e, bdd, and visual all exit 0;
e2e 51 passed, bdd 51 passed, audit 40 passed, visual 8 passed. Duration limit:
300 seconds. Test gate passed. Failure classification: none; no red tests.
Verdict: APPROVED

No open findings. R1-F01 resolved by clean-runner completion evidence; no F61
implementation repair performed.
