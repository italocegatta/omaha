## Code map

- `.env.example` lines 1-32: ignored local configuration template. It has
  secret, database, quote, and F57 placeholder entries but no `OMAHA_ENV` entry.
- `README.md` lines 18-41, Quick start: copies `.env.example`, explains local
  values, and invokes `uv run task serve`; this is the operator entry point
  where local mode must be explicit. `README.md` lines 63-140 document taskipy
  usage and must retain `task serve` as canonical command.
- `src/omaha/config.py::Settings.model_config`, `Settings.OMAHA_ENV`,
  `Settings.LOG_FORMAT`, and `Settings.effective_log_format`: Pydantic Settings
  loads environment variables with `.env` fallback; effective log format is
  JSON only for exact `OMAHA_ENV == "production"` unless explicit
  `LOG_FORMAT` is `json` or `text`, and text otherwise. `settings` is eagerly
  built at module import.
- `src/omaha/main.py::create_app`: lines 177-193 build `SessionMiddleware`.
  Current `https_only=os.environ.get("OMAHA_ENV") == "production"` bypasses
  loaded `.env` settings. Lines 266-274 already configure logging from
  `settings.LOG_LEVEL` and `settings.effective_log_format`, showing intended
  loaded-settings ownership.
- `src/omaha/logging_config.py::configure_logging`: maps `json` to the JSON
  formatter and all other values to text. No change is proposed; it is the
  downstream behavior used to define the cookie/log alignment contract.
- `tests/test_auth.py`: existing TestClient auth/session contract. It already
  asserts successful login sets `omaha_session` and runs in the test harness
  that forces development mode. Add focused middleware/config assertions here
  so the existing auth boundary protects secure-cookie behavior without a new
  test-marker allow-list entry.
- `tests/support/db.py::make_test_env` and setup helpers: explicitly force
  `OMAHA_ENV=development` for isolated test subprocesses. Preserve this test
  isolation behavior; do not read or mutate the real `.env`.

## Current relevant flow

1. Process starts `task serve`/uvicorn and imports `omaha.config`.
2. `Settings` reads process environment first and `.env` through
   `SettingsConfigDict(env_file=".env")`; `settings` is instantiated once.
3. Logging consumes `settings.effective_log_format`. With no explicit
   `LOG_FORMAT`, exact `production` yields JSON and every other value yields
   text.
4. `create_app()` builds `SessionMiddleware` with the loaded secret key, but
   currently computes `https_only` from `os.environ`. A value present only in
   `.env` is therefore absent from this second lookup.
5. Starlette emits the `Secure` cookie attribute when `https_only=True`.

Boundary conditions:

- Mode comparison is exact and case-sensitive; no trimming, case-folding, or
  aliasing is introduced.
- Exact `production` means secure cookie and default JSON logging.
- Exact `development` means non-secure cookie and default text logging.
- Any other mode remains non-production fallback: non-secure cookie and default
  text logging. Explicit valid `LOG_FORMAT` remains higher precedence for logs.
- Process environment overrides a same-named `.env` value through existing
  Pydantic Settings precedence; the cookie must consume resulting `settings`,
  not independently inspect process environment.

## Implementation Decisions

- Replace only the `os.environ` mode lookup in `create_app()` with the already
  loaded `settings.OMAHA_ENV` comparison. Keep `SessionMiddleware` name,
  secret, SameSite policy, middleware order, and all route behavior unchanged.
- Add `OMAHA_ENV=development` to `.env.example` near other application-mode
  settings, with comment stating exact `production` is reserved for the
  TLS-terminated production stack and other values use non-production defaults.
- Add matching README Quick start guidance. Keep real secrets absent, preserve
  `ADMIN_PASSWORD=distendidos`, and do not duplicate F57 credentials or define
  any MyProfit destination semantics.
- Test loaded configuration with a temporary env file passed to `Settings`.
  Test process-environment override separately with `monkeypatch`; never open
  the repository `.env` and never expose values from it.
- Test cookie middleware options and `Settings.effective_log_format` directly,
  plus existing auth cookie-setting behavior. Use exact booleans/strings, not
  loose substring or threshold assertions.

### Initial apply discovery

- **Context:** `create_app()` imports one eager `settings` object from
  `omaha.config`; rebuilding settings or adding a factory parameter would
  exceed F61's one-option substitution.
- **Decision:** use `settings.OMAHA_ENV` directly for `https_only`, and patch
  `omaha.main.settings` only in focused tests when exercising synthetic
  temporary `.env` files. This keeps production loading, middleware order,
  and route composition unchanged.
- **Impact:** a later process-environment mutation cannot change an already
  constructed app's cookie policy; tests can independently prove `.env`
  loading and process-overrides without opening repository `.env`.
- **Evidence:** preflight inspection of `src/omaha/main.py::create_app`,
  `src/omaha/config.py::Settings`, and Starlette `app.user_middleware`
  confirmed `kwargs["https_only"]` is the exact middleware option boundary.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `.env.example` application config | No `OMAHA_ENV` entry | Document `OMAHA_ENV=development` and exact mode meaning | Remove local setup drift |
| `README.md` Quick start | Copies `.env` without environment-mode guidance | States local development mode and production/non-production distinction | Make `task serve` behavior predictable |
| `src/omaha/main.py::create_app` | `https_only=os.environ.get("OMAHA_ENV") == "production"` | `https_only=settings.OMAHA_ENV == "production"` | Honor `.env` loaded by Settings and match logging source |
| `tests/test_auth.py` | Auth tests do not cover mode source or Secure attribute | Add temporary-`.env`, process-override, exact production/development, and log-format scenarios | Lock regression boundary |
| `specs/runtime-environment-mode/spec.md` | No stable mode-consistency contract | Add exact mode, precedence, cookie, and logging requirements | Durable implementation oracle |
| `specs/readme-freshness/spec.md` | README requirements omit local mode | Modify README requirement to include `OMAHA_ENV=development` and mode guidance | Durable documentation oracle |

`src/omaha/config.py`, `src/omaha/logging_config.py`, and
`tests/support/db.py` are preserved implementation dependencies, not intended
change targets.

## Risks and preserved patterns

- Risk: changing mode normalization could silently make misspelled production
  deployments secure or JSON-formatted. Preserve exact comparison and document
  non-production fallback instead.
- Risk: rebuilding or rebinding global settings in tests could leak state across
  TestClient tests. Use isolated monkeypatch teardown and temporary `Settings`
  instances; preserve existing fixture setup.
- Risk: middleware order changes could alter session/access logging. Make one
  option-source substitution only.
- Preserve taskipy commands (`uv run task ...`), explicit test-lane rules,
  family password invariant, network bind guidance, `.env` secrecy, and all
  F57 boundaries.
- No migration, DB seed/reset, auth flow redesign, cookie name/SameSite change,
  logging formatter change, secret validation change, MyProfit connector, or
  production deployment change.

## Proposal-gate evidence

- `openspec validate f61-documentar-ambiente-local-e-alinhar-cookie-seguro --type change --strict --json`
  → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json`
  → valid, 69/69 stable specs passed, 0 failures. Existing informational
  long-requirement notices remain; no F61 failure reported.
- `openspec status --change f61-documentar-ambiente-local-e-alinhar-cookie-seguro --json`
  → `isComplete: true`; proposal, design, specs, and tasks are all `done`.
- `rtk git diff --check -- openspec/changes/f61-documentar-ambiente-local-e-alinhar-cookie-seguro`
  → clean.
- `rtk git status --short --untracked-files=all`
  → only `.openspec.yaml`, proposal, design, tasks, and the two F61 delta specs
  under the exact change directory; no runtime/docs/tests files changed.
- Tests run: none. Proposal gate ran no taskipy/pytest implementation tests,
  no server, no database operation, no actual `.env` read, no secret access,
  and no external service call.

## Apply Validation

- `uv run task test-file tests/test_auth.py` → 15 passed.
- `uv run task test-one tests/test_auth.py::test_session_cookie_mode_uses_loaded_settings`
  → 4 passed (production, development, case-sensitive, and fallback modes).
- Change validation → valid, 1/1 passed; stable-spec validation → valid, 69/69
  passed; `rtk git diff --check` → clean.
- Refresh receipt completed with LAN URL `http://192.168.1.4:8000`, healthz OK,
  read-only dashboard smoke `200` with 5 `RF Din` matches, and DB left
  untouched at 11 classes / 89 assets / 88 positions per PRD §4.12.
