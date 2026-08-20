## Why

`Settings` already loads `OMAHA_ENV` from the process environment or ignored
`.env`, and logging already consumes that loaded value. Session-cookie security
still reads `os.environ` directly, so `task serve` can run with production
settings from `.env` while emitting a non-secure cookie. Local setup also does
not tell operators which environment mode is expected.

## What Changes

- Document `OMAHA_ENV=development` in `.env.example` and the README Quick start.
- Make `create_app()` derive `SessionMiddleware.https_only` from loaded
  `settings.OMAHA_ENV`, not a second process-environment lookup.
- Preserve exact, case-sensitive mode semantics: exact `production` enables
  secure cookies and default JSON logs; exact `development` disables secure
  cookies and uses default text logs.
- Preserve current fallback behavior for other mode strings: non-production
  cookie/text behavior, while explicit `LOG_FORMAT=json|text` still wins for
  logs.
- Add focused regression coverage for temporary `.env` loading, process
  environment precedence, cookie mode, and log mode.
- Update stable OpenSpec contracts for environment-mode consistency and README
  local-environment documentation.

## Capabilities

### New Capabilities

- `runtime-environment-mode`: one loaded `OMAHA_ENV` source for default logging
  and session-cookie security, with exact case-sensitive production behavior.

### Modified Capabilities

- `readme-freshness`: require documented local `OMAHA_ENV=development` setup
  and the production/non-production mode distinction.

## Impact

- `.env.example` and `README.md`: operator-facing local configuration guidance.
- `src/omaha/main.py`: session middleware configuration only.
- `src/omaha/config.py`: inspected as the existing settings/logging source;
  no new settings field or `.env` loading mechanism is proposed.
- `tests/test_auth.py`: focused regression scenarios using temporary settings
  files and isolated environment overrides.
- `openspec/specs/`: one new capability delta and one README delta.

No real `.env` read, credential change, MyProfit destination change, database
operation, F57 reopening, connector work, F58-F60 work, or T31 work is included.
