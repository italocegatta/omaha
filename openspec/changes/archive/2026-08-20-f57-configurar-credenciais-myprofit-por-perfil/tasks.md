## 1. Configuration model and profile resolver

- [x] 1.1 `src/omaha/config.py::Settings`: add separate Italo/Ana email, password, and destination environment fields named exactly `MYPROFIT_ITALO_*` and `MYPROFIT_ANA_*`; preserve existing `.env` precedence, `SECRET_KEY` enforcement, quote settings, and test-mode behavior. Acceptance: each profile loads its own synthetic values and missing/incomplete values fail closed. Test file/scenario: `tests/test_f57_myprofit_profile_config.py` Italo/Ana isolation and incomplete-config scenarios. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py`. Independent oracle: inspect `Settings.model_fields` and instantiate with isolated `monkeypatch` environment; no network or DB access.
- [x] 1.2 `src/omaha/config.py::MyProfitProfileConfig` and resolver/error symbols: implement typed profile resolution from active `Profile`, reject Família sentinel before prefix lookup, reject unknown/ambiguous profiles, and expose only non-secret routing/config data to future connector. Preserve cross-profile viewing and existing auth/session contracts. Acceptance: Italo maps only Italo variables, Ana maps only Ana variables, Família returns stable family-read-only failure, and incomplete config never falls back. Test file/scenario: same file, `test_italo_uses_italo_values`, `test_ana_uses_ana_values`, `test_family_rejected_before_lookup`, `test_unknown_profile_rejected`. Focused command: `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_family_rejected_before_lookup`. Independent oracle: fake external-client spy has zero calls and resolver output contains expected profile key only.

## 2. Secret and placeholder safety

- [x] 2.1 `src/omaha/config.py` secret representation and diagnostic paths: wrap password material with secret-safe type, redact credential/destination values from repr and safe errors, and avoid logging raw settings/env payloads. Preserve useful field/reason identifiers without exposing values. Acceptance: synthetic password, email, destination, and raw env payload do not appear in diagnostic text. Test file/scenario: `tests/test_f57_myprofit_profile_config.py::test_secret_sanitization`. Focused command: `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_secret_sanitization`. Independent oracle: assert each synthetic marker is absent from `repr`, raised error text, and captured log records.
- [x] 2.2 `.env.example`: add six separate false placeholders (`MYPROFIT_ITALO_EMAIL`, `MYPROFIT_ITALO_PASSWORD`, `MYPROFIT_ITALO_DESTINATION`, and Ana equivalents) using reserved invalid/example values; do not add real credentials or alter `ADMIN_PASSWORD=distendidos`. Acceptance: placeholders are distinct by profile, clearly non-production, and resolver treats them as disabled/invalid rather than live credentials. Test file/scenario: `tests/test_f57_myprofit_profile_config.py::test_env_example_placeholders_are_false`. Focused command: `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_env_example_placeholders_are_false`. Independent oracle: parse `.env.example` without importing app and assert exact variable set, reserved invalid markers, and no credential-like live values.

## 3. Documentation and stable contracts

- [x] 3.1 `README.md` Quick start/configuration guidance: document ignored `.env`, separate Italo/Ana variables, placeholder replacement, secret non-logging, and Família synchronization block. Preserve network bind instructions, shared password contract, and read-only DB/testing guidance. Acceptance: README contains no real or synthetic credential values beyond explicit non-production placeholder explanation. Test file/scenario: documentation scan in `tests/test_f57_myprofit_profile_config.py::test_docs_do_not_contain_secrets`. Focused command: `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_docs_do_not_contain_secrets`. Independent oracle: text scan checks required variable names and rejects known fake/real secret markers.
- [x] 3.2 `openspec/specs/myprofit-profile-credentials/spec.md` delta: implement every ADDED requirement and scenario in active change, including Italo, Ana, Família rejection, sanitization, and offline fake-value behavior. Preserve future connector boundary: no HTTP, Playwright, job, CSV, UI, or E2E work. Acceptance: spec scenarios map one-to-one to focused tests and resolver behavior. Test/validation file: change delta plus `tests/test_f57_myprofit_profile_config.py`. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py`. Independent oracle: `openspec validate --change f57-configurar-credenciais-myprofit-por-perfil --strict` reports no spec errors.
- [x] 3.3 `openspec/specs/cross-profile-sharing/spec.md` delta: extend existing Família read-only contract to MyProfit synchronization without changing existing dashboard, profile-switcher, or mutation behavior. Acceptance: family guard is required before credential lookup/external access and uses sanitized family-read-only semantics. Test file/scenario: `tests/test_f57_myprofit_profile_config.py::test_family_rejected_before_lookup`. Focused command: `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_family_rejected_before_lookup`. Independent oracle: fake lookup/client spies remain at zero calls; delta validates against stable spec structure.

## 4. Offline acceptance validation

- [x] 4.1 `tests/test_f57_myprofit_profile_config.py`: add pure tests with isolated `monkeypatch` fake values covering Italo, Ana, Família rejection, secret sanitization, false `.env.example` placeholders, and zero external calls. Preserve explicit test-lane classification and do not touch production DB. Acceptance: all F57 scenarios pass offline with no MyProfit/Playwright/HTTP invocation. Focused command: `uv run task test-file tests/test_f57_myprofit_profile_config.py`. Independent oracle: test module has no network client import/call and external spy count remains zero.
- [x] 4.2 Proposal gate validation: run only OpenSpec artifact/status validation after all artifacts exist; record command, result, and artifact paths in `design.md`/final report. Acceptance: proposal, design, tasks, and both delta specs exist; change status is complete/apply-ready; no application files changed and no implementation tests run. Focused command: `openspec validate --change f57-configurar-credenciais-myprofit-por-perfil --strict` (artifact gate, not taskipy test). Independent oracle: `git status --short` lists only the new F57 change dossier paths.

## Test strategy

- Pure pytest module: `tests/test_f57_myprofit_profile_config.py`.
- Synthetic environment values only; no `.env` mutation, production DB access,
  HTTP, Playwright, MyProfit, background job, CSV, UI, or E2E execution.
- Focused implementation command: `uv run task test-file tests/test_f57_myprofit_profile_config.py`.
- Focused single-scenario command: `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_family_rejected_before_lookup`.
- Proposal-gate command: `openspec validate --change f57-configurar-credenciais-myprofit-por-perfil --strict`.
- Acceptance evidence: independent fake-client spy remains unused; synthetic
  secrets are absent from repr/errors/logs; Italo/Ana values never cross;
  Família fails closed; placeholders remain false.

## Proposal Gate Evidence

Recorded:

- `openspec status --change f57-configurar-credenciais-myprofit-por-perfil --json`
  → `isComplete: true`; all four required artifact classes are `done`.
- `openspec validate f57-configurar-credenciais-myprofit-por-perfil --type change --strict --json`
  → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json` → valid, 68/68 stable specs
  passed, 0 failures; informational long-requirement notices are pre-existing.
- `rtk git diff --check -- openspec/changes/f57-configurar-credenciais-myprofit-por-perfil`
  → clean.
- `rtk git status --short --untracked-files=all -- openspec/changes/f57-configurar-credenciais-myprofit-por-perfil`
  → only `.openspec.yaml`, proposal/design/tasks, and two F57 delta specs;
  no application files changed.
- Tests run: none. This is proposal-only; no implementation test, network
  call, credential change, migration, or production DB operation occurred.

## Execution Evidence

### Initial apply pass

- **1.1 complete:** `src/omaha/config.py::Settings` now exposes exact,
  optional `MYPROFIT_ITALO_*` and `MYPROFIT_ANA_*` fields. The F57 unit module
  verifies `Settings.model_fields`, isolated environment loading, profile
  isolation, and incomplete-config failure. No changes to `auth.py`,
  `models.py`, `.env` precedence, `SECRET_KEY`, quote settings, or test-mode
  detection.
- **1.2 complete:** `config.py::MyProfitProfileConfig`,
  `MyProfitConfigurationError`, and `resolve_myprofit_profile_config` implement
  Italo/Ana mapping, Ana aliases, unknown/ambiguous guards, and sentinel-first
  `household_read_only` rejection. Family-focused test passes with zero
  external calls.
- **2.1 complete:** `SecretStr` wraps password material; settings, resolved
  config, and domain errors redact values. Secret-focused test passes with no
  synthetic email/password/destination markers in diagnostics or logs.
- **2.2 complete:** `.env.example` contains six distinct reserved invalid
  placeholders; resolver rejects copied placeholders. Placeholder-focused test
  passes.
- **3.1 complete:** `README.md` documents ignored `.env`, separate profile
  variables, placeholder replacement, no secret logging, and Família sync
  blocking while preserving network/password guidance. Documentation scan
  passes.
- **3.2/3.3 complete:** Existing F57 delta requirements are implemented by
  resolver/tests without editing proposal or delta scope. Change and stable
  specs validate; no connector, job, UI, CSV, or E2E behavior was added.
- **4.1 complete:** Pure unit module added at
  `tests/test_f57_myprofit_profile_config.py`; no network, Playwright, HTTP, or
  production DB access.
- **4.2 complete:** Proposal artifacts were validated before implementation;
  apply validation was rerun after implementation. Installed CLI rejects the
  dossier's older `--change` spelling; supported equivalent is recorded below.

### Focused validation receipts

- `uv run task test-file tests/test_f57_myprofit_profile_config.py` → **9 passed**.
- `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_family_rejected_before_lookup` → **1 passed**.
- `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_secret_sanitization` → **1 passed**.
- `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_env_example_placeholders_are_false` → **1 passed**.
- `uv run task test-one tests/test_f57_myprofit_profile_config.py::test_docs_do_not_contain_secrets` → **1 passed**.
- `openspec validate f57-configurar-credenciais-myprofit-por-perfil --type change --strict` → **valid**.
- `openspec validate --specs --strict` → **68 passed, 0 failed**.
- `rtk git diff --check` → **clean**.
- No DB mutation, migration, external call, real credential, or MyProfit access performed.

### Refresh-for-test receipt

- Restart command used taskipy `uv run task serve-prod` with bind
  `0.0.0.0`; workspace launch could not claim port 8000 because an existing
  externally managed `/app/.venv/bin/fastapi` process (PID 1241) already owns
  it. No unrelated process was killed.
- URL: `bash scripts/print_lan_url.sh` → `http://192.168.1.4:8000`.
- Healthz: `curl -fsS "$URL/healthz"` → `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- Read-only DB receipt: Italo-visible database reported `11 classes`, `89 assets`,
  `88 positions`; no reset, seed, migration, or other DB mutation ran.
- Dashboard smoke: read-only login/profile selection and `GET /` returned
  `dashboard_rf_din_matches 5`.
- Existing server health and seeded state verified; review should confirm
  workspace process restart before browser validation if runtime reload is
  required.

## Review Findings

### Review R1

Scope audit: proposal scope pass; design decisions pass; task completion 9/9
pass; MyProfit profile isolation requirements/scenarios pass; Família
read-only guard requirements/scenarios pass; secret sanitization pass;
offline-test boundary pass; `.env.example` placeholder contract pass; README
guidance and preserved password/network/testing guidance pass; changed-symbol
and preserved-invariant audit pass; excluded F58-F60/T31, migrations, DB, and
real MyProfit access boundaries pass; apply focused-test evidence, delivery
receipt, and external port/PID note pass; OpenSpec artifact/spec health pass;
scope assessability pass.

Full suite: `uv run task test` -> green; unit, integration, audit, e2e, bdd,
and visual lanes each exited 0; external wall-clock `262.45s` (task-reported
`262.01s`); duration limit `300s`; cleanup complete, no failed child remained.
Per-test timing was not emitted; lane receipts were available. Test gate
passed.

OpenSpec verification: `openspec validate
f57-configurar-credenciais-myprofit-por-perfil --type change --strict --json`
-> valid, 1/1 passed, 0 issues. `openspec validate --specs --strict --json`
-> valid, 68/68 passed, 0 failed; informational long-requirement notices
pre-existing. `openspec status --change
f57-configurar-credenciais-myprofit-por-perfil --json` -> complete, 9/9
tasks, all dossier artifacts present.

Verdict: APPROVED

Findings: none.
