## Context

F57 archived a profile-scoped configuration boundary in
`src/omaha/config.py`, but its `destination` field is false product surface:
MyProfit uses one known destination, `StockDetail.aspx`, and no per-profile
selector or modulator is required. F58 absorbs that small removal before adding
browser automation. The historical F48 PoC was removed from the repository;
the durable implementation source is `~/myprofit/cloak_download.py` plus its
`~/myprofit/requirements.txt`. No `.env` file is read or copied.

### Code map

- `src/omaha/config.py::MyProfitProfileConfig`, `_resolve_values`,
  `_FALSE_MYPROFIT_VALUES`, `Settings`, `resolve_myprofit_profile_config`,
  `MyProfitConfigurationError`: current environment-backed credential shape,
  profile mapping, Família-first guard, placeholder validation, and redacted
  diagnostics consumed by the future connector.
- `src/omaha/auth.py::get_active_profile`,
  `require_active_profile`, `HouseholdReadOnlyError`: existing session/profile
  boundary and stable `household_read_only` semantics. F58 does not change it;
  connector input must preserve its sentinel-first behavior.
- `src/omaha/models.py::Profile.name` and
  `Profile.is_family_sentinel`: persisted identity inputs used by the resolver;
  no schema or seed change is allowed.
- `src/omaha/csv_import.py::parse_positions`: existing parser remains the later
  preview consumer. F58 returns downloaded bytes and does not call parser or
  import routes, so F59 can choose preview transformation explicitly.
- `src/omaha/routes/imports.py::post_import` and `post_confirm`: current
  upload/preview/commit flow. It is an integration boundary to preserve, not a
  F58 edit point.
- `src/omaha/quotes/provider/protocol.py` and `stub.py`: local pattern for a
  narrow `Protocol`, immutable result shape, and deterministic fake provider;
  the new connector follows this injection style.
- `~/myprofit/cloak_download.py::STOCK_DETAIL_URL`, `_path_from_project`,
  `first_visible`, `dismiss_two_factor_prompt`, `export_file`, and `main`:
  observed Playwright flow. F58 carries over `launch_persistent_context`,
  login field discovery, optional `Mais tarde`/`Later`, `Export` → `CSV`, and
  `expect_download`, while replacing process-global paths/printing with a
  library boundary and cleanup.
- `~/myprofit/requirements.txt`: observed dependency baseline:
  `cloakbrowser==0.5.8`, `playwright==1.62.0`, `python-dotenv==1.2.3`.
  Omaha already owns environment loading through Pydantic; `python-dotenv` is
  not copied as an unnecessary connector dependency.
- `tests/test_f57_myprofit_profile_config.py`: existing pure F57 contract tests
  that must be narrowed from six fields to four and retain profile isolation,
  sanitization, placeholder, and Família assertions.
- `tests/test_auth.py::test_environment_mode_documentation`: coupled README
  assertion currently names destination and must assert email/password only.
- `tests/conftest.py::_UNIT_FILES`: explicit unit-lane allow-list. New
  `tests/test_myprofit_connector.py` must be registered here; it may not import
  TestClient, DB, or live network clients.
- `pyproject.toml` dependency groups and taskipy tasks, plus `uv.lock`: runtime
  dependency/lock surface; use taskipy commands for verification.

### Current relevant flow

1. Importing `omaha.config` builds eager `Settings` from process environment
   before `.env`, with pytest-only `SECRET_KEY` relaxation. Optional F57
   MyProfit fields do not block startup.
2. A caller supplies active `Profile` to
   `resolve_myprofit_profile_config`. `_profile_key` rejects the Família
   sentinel before profile-prefix lookup, normalizes Italo/Ana aliases, and
   rejects unknown profiles. `_resolve_values` currently requires email,
   password, and destination, rejects false placeholders, and returns
   `MyProfitProfileConfig` with `SecretStr` password.
3. F58 changes that transformation to email + password only. Resolver output
   becomes the sole credential input to connector; no raw settings lookup may
   happen after connector launch begins.
4. Concrete connector receives a real-profile boundary (or resolver-compatible
   profile), resolves credentials, creates an isolated temporary persistent
   browser profile and temporary download directory, launches the injected
   `cloakbrowser` context, opens the MyProfit login page, fills credentials,
   submits once, handles optional 2FA setup defer, navigates directly to
   `STOCK_DETAIL_URL`, opens Export, selects CSV under `expect_download`, reads
   bytes, and returns filename + bytes.
5. `finally` closes page/context and removes temporary profile/download paths.
   No FastAPI route, `Session`, `ImportPreview`, `Asset`, `Position`, parser,
   job, or external database operation is in this flow.

Boundary conditions: Família fails before credential resolution and browser
launch; missing/blank/placeholder credentials fail closed; credentials never
appear in logs/errors/repr; no destination variable is accepted; login,
navigation, optional prompt, export-menu, export-option, and download each have
bounded timeouts; browser/site errors become stage-labelled sanitized domain
errors; no actual MyProfit call is made by tests.

## Goals / Non-Goals

**Goals:**

- Remove all F57-derived destination contract and references without reopening
  or editing F57 archive.
- Define one injectable connector interface and one Playwright implementation
  for direct `StockDetail.aspx` CSV download.
- Preserve isolated Italo/Ana email/password resolution and Família guard.
- Make credential sanitization, timeout behavior, cleanup, and failure stages
  testable with fake browser/page/download doubles.
- Keep tests deterministic/offline and connector output free of DB concerns.

**Non-Goals:**

- No `.env` inspection, secret migration, credential rotation, or live MyProfit
  call during proposal or implementation tests.
- No destination selector, profile-dependent URL, browser fingerprint
  modulation, CAPTCHA/2FA bypass, or automated real 2FA enrollment.
- No CSV parsing/preview, background synchronization, polling, import commit,
  FastAPI route, button, template, Alpine state, or E2E workflow (F59/F60/T31).
- No ORM/model/migration/seed/database mutation and no production DB access.

## Decisions

### 1. Remove destination before connector work

Delete destination fields from `Settings` and `MyProfitProfileConfig`, remove
the resolver argument/validation and false-value markers, and update docs/tests
and both affected spec deltas. Keep `MyProfitProfileConfig.email` and
`SecretStr password`; preserve `household_read_only`, `unknown_profile`,
`incomplete_configuration`, and `placeholder_configuration` behavior for the
remaining credential pair. Alternative rejected: leave a deprecated field in
place; that preserves false routing surface and lets future callers infer a
selector contract that owner explicitly denied.

### 2. Connector consumes guarded profile configuration

Expose a narrow `MyProfitConnector` protocol with a synchronous
`download_positions_csv(profile) -> MyProfitCsvDownload` operation, where the
result contains only sanitized filename and CSV bytes. The concrete
`PlaywrightMyProfitConnector` calls the existing resolver before constructing
any browser object. It never accepts a destination argument. This keeps the
Família guard in front of external access and gives F59 a replaceable fake
boundary. Alternative rejected: put Playwright calls in a route or job now;
that couples F58 to F59 lifecycle, HTTP state, and preview persistence.

### 3. Reuse observed POC navigation, with direct fixed destination

Use fixed `STOCK_DETAIL_URL =
"https://myprofitweb.com/App/StockDetail.aspx"`. Login starts at the observed
MyProfit login page, fills the POC's visible email/password fields, and submits
one login action. After bounded post-login settling, the connector probes for
the optional visible `Mais tarde` or `Later` control and clicks it once when
present. Absence is accepted; a real second-factor challenge or unconfirmed
authenticated state is not bypassed and becomes a sanitized authentication
failure. Then it goes directly to `StockDetail.aspx`, opens
`button[aria-label="Export"]`, selects exact `CSV`, and wraps the selection in
Playwright `expect_download`.

This matches the POC's observed behavior without copying its configurable
`APP_URL`, destination, persistent local profile, debug screenshots, prints,
or `.env` loading. Historical F48 selector notes may inform fake-page tests,
but no unobserved selector or external automation step is invented.

### 4. Use temporary resources and explicit timeout policy

Create a fresh `TemporaryDirectory` for each connector call and use separate
profile/download children. Launch persistent context with `accept_downloads`;
read the download into memory after sanitizing `suggested_filename` with
`Path(...).name`, then return it. Close context in `finally`; temporary roots
remove profile state and downloaded file even on timeout or Playwright error.

Expose immutable timeout settings with POC-derived defaults: navigation 45s,
login settle 5s, optional 2FA probe 30s maximum, Export button 30s, CSV option
10s, and download 45s. Tests inject smaller values and fake clocks/pages where
needed. Alternative rejected: reuse a persistent project profile or fixed
`downloads/` directory; it leaks cookies/financial files across calls and
breaks test isolation.

### 5. Sanitize at connector boundary

Define `MyProfitConnectorError` carrying only stable stage/code (for example
`credentials`, `login`, `two_factor`, `navigation`, `export`, `download`,
`cleanup`). Catch Playwright/timeout/resource errors, never interpolate raw
exception text, URL form values, email, password, page content, screenshot,
trace, or downloaded bytes into logs/errors. Missing credentials are rejected
by existing resolver before launcher invocation. Download result is returned
only after non-empty bytes are read; no payload is logged.

### 6. Dependencies and test seam

Promote Playwright to runtime dependency at the POC-compatible version range
and add `cloakbrowser==0.5.8`; update `uv.lock` with project tooling. Keep
`python-dotenv` out because `Settings` already owns `.env` precedence. Inject
the launcher/context factory and use fake page/download/context doubles in
`tests/test_myprofit_connector.py`; no test imports TestClient or invokes a
real browser/domain. Alternative rejected: monkeypatch global Playwright
internals only; an explicit launcher seam proves Família and failure paths
without external side effects.

## Implementation Decisions

### Initial apply discovery

- **Context:** F58 requires fixed login flow but the active dossier only named
  the login page generically. Archived F48 spec/task evidence records the
  observed entry `https://myprofitweb.com/Login.aspx`, selectors `#email`,
  `#password`, `#buttonLogin`, and CSV selector
  `a.dropdown-item[data-type="csv"]`.
- **Decision:** use those observed selectors as fixed connector constants,
  while retaining F58's exact `button[aria-label="Export"]` and `CSV` contract;
  no caller-provided URL, destination, selector, or environment override is
  introduced.
- **Impact:** fake-page tests can assert deterministic login/export order and
  direct StockDetail navigation without live MyProfit access. Connector keeps
  F48's observed behavior but omits its `.env`, prints, screenshots, parser,
  persistent profile, and temporary-file leakage.
- **Evidence:** archived F48 `specs/myprofit-position-csv-poc/spec.md` lines
  24-26 and 55-58; `~/myprofit/cloak_download.py` lines 108-214.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/config.py::MyProfitProfileConfig` | email, password, destination | email + secret password only | Remove false routing contract |
| `src/omaha/config.py::_resolve_values`, resolver, false markers | Requires/validates six profile fields including destination | Resolves only four email/password fields; same profile/family/secret guards | Preserve credential safety while eliminating destination |
| `.env.example` | Four credential fields plus two destination placeholders | Four false email/password placeholders | Operator contract matches connector |
| `README.md` Quick start | Documents destination variables | Documents email/password only and fixed connector destination behavior without exposing URL config | Remove stale setup burden |
| `tests/test_f57_myprofit_profile_config.py` | Six-field F57 assertions and destination sanitization | Four-field offline assertions and credential-only sanitization | Keep historical test file aligned without touching archive |
| `tests/test_auth.py::test_environment_mode_documentation` | Requires destination name | Requires password name only; no destination reference | Coupled documentation contract |
| `openspec/specs/myprofit-profile-credentials/spec.md` delta | Stable requirement returns/mentions destination | Stable requirement returns only email/password and forbids destination config | Correct F57-derived contract |
| `openspec/specs/cross-profile-sharing/spec.md` delta | Família MyProfit guard not explicit in stable spec | Guard precedes resolver/browser/request/download | Preserve read-only boundary |
| `src/omaha/myprofit/__init__.py` | No connector package | Public connector/result/error exports | Narrow package surface |
| `src/omaha/myprofit/connector.py` | No MyProfit runtime connector | Protocol, result, timeout policy, Playwright implementation, sanitized errors | Direct StockDetail download boundary |
| `tests/test_myprofit_connector.py` | No connector tests | Pure fake/offline coverage for credentials, Família, flow, 2FA, timeout, cleanup, errors | Testable without MyProfit/DB |
| `tests/conftest.py::_UNIT_FILES` | New test path absent | Explicitly list connector unit file | Preserve test marker allow-list rule |
| `pyproject.toml`, `uv.lock` | Playwright dev-only; no cloakbrowser | Runtime Playwright + POC-compatible cloakbrowser lock | Install connector dependency reproducibly |

## Risks / Trade-offs

- **[MyProfit markup or anti-automation changes]** → centralize observed
  selectors and convert failures to stage-specific sanitized errors; do not
  bypass site controls. Live calibration remains opt-in and owner-observed.
- **[Optional 2FA prompt differs from actual challenge]** → click only visible
  `Mais tarde`/`Later`; absence is allowed after authenticated-state check;
  actual challenge fails closed rather than being automated or bypassed.
- **[Credential leakage through Playwright exceptions or artifacts]** → no raw
  exception text/logs, no screenshots/traces, secret-safe config, and tests
  assert synthetic markers never enter diagnostics.
- **[Temporary browser/download cleanup failure]** → nested `try/finally`,
  bounded close, stage-only cleanup error, and tests assert fake context close
  plus temporary path removal on success/failure.
- **[Connector accidentally mutates application state]** → module has no DB,
  FastAPI, route, or import-preview dependency; tests spy on parser/DB/network
  boundaries and assert zero calls.
- **[Dependency drift]** → pin cloakbrowser to POC version, use explicit
  Playwright range, lock via `uv`, and run focused unit/lint/package checks.

## Migration Plan

1. Apply destination removal and adjust offline F57/coupled documentation tests.
2. Add connector package, dependency lock changes, pure fake-browser tests,
   and new stable/delta requirements.
3. Run focused taskipy tests and lint; inspect changed-file scope. No migration,
   seed, server refresh, DB reset, or external connector invocation is needed.
4. Rollback is code/config/docs removal only; no database or credential data was
   written. Operators with old ignored `.env` files may leave stale destination
   keys locally, but Omaha must ignore them through `extra="ignore"` and must not
   read or validate them.

## Open Questions

- None blocking proposal. Accepted behavior is: optional setup prompt may be
  deferred with visible `Mais tarde`/`Later`; no prompt is valid; actual 2FA,
  CAPTCHA, or unclear authentication is a sanitized fail-closed result. Any
  future selector change requires owner-observed evidence and a later scope.

## Proposal Gate Evidence

- Source inspection completed for roadmap F58, archived F57/F48 artifacts,
  `~/myprofit/cloak_download.py`, `~/myprofit/requirements.txt`, current
  config/docs/tests, connector patterns, taskipy, PRD/config rules.
- No `.env` file was read or copied; no MyProfit request, browser launch, DB
  mutation, implementation, or test execution occurred during proposal.

Validation results after all F58 artifacts were created:

- `openspec status --change f58-integrar-automacao-playwright-myprofit --json`
  → `isComplete: true`; proposal, design, three delta specs, and tasks are
  all `done`; `applyRequires: ["tasks"]` satisfied.
- `openspec validate f58-integrar-automacao-playwright-myprofit --type change
  --strict --json` → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json` → valid, 70/70 stable specs
  passed, 0 failures. Existing informational long-requirement notices only.
- `rtk git diff --check --
  openspec/changes/f58-integrar-automacao-playwright-myprofit` → clean.
- `rtk git status --short --untracked-files=all` → pre-existing
  `openspec/roadmap.md` modification plus only the new F58 dossier files
  (`.openspec.yaml`, proposal, design, tasks, and three delta specs); no
  application files changed.
- Tests run: none. Proposal-only gate performed no taskipy test, lint, install,
  browser, network, credential, migration, seed, or database operation.
