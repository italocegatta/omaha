## Why

MyProfit automation needs credentials and destination selected from active
portfolio profile, not one shared process-wide credential pair. F57 establishes
that boundary before F58 adds browser automation, preventing Família aggregate
from ever being treated as a real MyProfit account and keeping secrets outside
logs, tests, and documentation.

## What Changes

- Add profile-scoped MyProfit configuration for real Italo and Ana profiles.
- Add separate `MYPROFIT_ITALO_*` and `MYPROFIT_ANA_*` environment variables for
  email, password, and destination.
- Resolve only real profiles; reject Família before any synchronization or
  external-client invocation.
- Use secret-safe password representation and sanitized error/log boundaries.
- Document false, non-production placeholders in `.env.example` and explain
  profile selection in `README.md`.
- Add offline tests using synthetic values only; tests SHALL never call
  MyProfit, Playwright, or any network endpoint.

## Capabilities

### New Capabilities

- `myprofit-profile-credentials`: profile-specific MyProfit credential and
  destination resolution, secret sanitization, and offline configuration
  behavior.

### Modified Capabilities

- `cross-profile-sharing`: extend Família read-only behavior so a MyProfit
  synchronization request is rejected before credential use or network access.

## Impact

- `src/omaha/config.py`: settings fields, typed profile mapping, and guarded
  resolver consumed by the future connector.
- `.env.example`: separate false-value placeholders for Italo and Ana.
- `README.md`: operator configuration guidance without real credentials.
- `src/omaha/auth.py` and `src/omaha/models.py`: preserve existing active-profile
  and Família-sentinel semantics used by the resolver; no auth or DB schema
  change is proposed.
- Tests: new pure/offline configuration coverage with fake values and no
  production DB access.
- No MyProfit HTTP client, Playwright connector, background job, CSV
  import/preview, UI action, or end-to-end workflow is included.
