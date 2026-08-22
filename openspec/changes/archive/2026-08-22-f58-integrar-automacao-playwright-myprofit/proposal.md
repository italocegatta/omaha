## Why

F57 left profile-specific `destination` configuration that has no selector or
modulator role; keeping it would make connector configuration misleading. Omaha
now needs one guarded, offline-testable Playwright boundary that logs into
MyProfit and returns the downloaded position CSV without creating a route, job,
preview, or database mutation.

## What Changes

- **BREAKING** Remove `MYPROFIT_ITALO_DESTINATION` and
  `MYPROFIT_ANA_DESTINATION` from the environment contract, `Settings`,
  `MyProfitProfileConfig`, resolver validation, README, `.env.example`, F57
  tests, and F57-derived stable/delta requirements. Preserve only isolated
  profile email/password and the Família guard.
- Add a dedicated Playwright connector interface and concrete implementation
  for direct `https://myprofitweb.com/App/StockDetail.aspx` navigation.
- Reuse POC flow: temporary persistent browser context, email/password login,
  bounded optional `Mais tarde`/`Later` 2FA setup dismissal, Export → CSV, and
  Playwright download capture.
- Return CSV bytes/filename through an in-process result; sanitize operational
  errors, enforce explicit timeouts, and always clean temporary profile,
  download, and browser resources.
- Keep connector tests fake/offline. Família must fail before credential lookup
  or browser launch. No database session, import preview, route, background
  job, UI action, or external call belongs to this slice.
- Add only connector dependencies needed by the POC (`playwright` and
  `cloakbrowser`) and update the lockfile through the repository toolchain.

## Capabilities

### New Capabilities

- `myprofit-position-csv-connector`: guarded Playwright login/download contract
  for a direct MyProfit StockDetail CSV, with sanitized failures and offline
  test doubles.

### Modified Capabilities

- `myprofit-profile-credentials`: remove destination from profile configuration
  while retaining email/password isolation, secret safety, and fail-closed
  resolution.
- `cross-profile-sharing`: require the Família read-only guard before connector
  credential resolution, browser launch, request, or download.

## Impact

- Configuration/docs/tests: `src/omaha/config.py`, `.env.example`, `README.md`,
  `tests/test_f57_myprofit_profile_config.py`, `tests/test_auth.py`.
- New connector module and pure tests under `src/omaha/myprofit/` and
  `tests/test_myprofit_connector.py`; `tests/conftest.py` receives the explicit
  unit-file registration only.
- Packaging: `pyproject.toml` and `uv.lock`.
- No ORM, Alembic, seed, FastAPI route, import-preview, UI, production DB, or
  F57 archive changes. F59/F60/T31 remain out of scope.
