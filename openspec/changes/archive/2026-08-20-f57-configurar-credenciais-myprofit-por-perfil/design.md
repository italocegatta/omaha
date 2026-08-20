## Context

Current configuration is a single eager `Settings` instance in
`src/omaha/config.py`, loaded from environment and `.env`; it has no MyProfit
fields or profile resolver. `src/omaha/auth.py` already defines the active
profile boundary and treats `Profile.is_family_sentinel` as not-real for
profile-required flows. `src/omaha/models.py` stores the profile name and
sentinel flag without any MyProfit columns. `.env.example` and `README.md`
currently document only shared login/database and quote settings.

### Code map

- `src/omaha/config.py::Settings`, `_build_settings`, and module-level
  `settings`: current environment loading, eager validation, and safe place for
  profile-specific settings plus resolver types.
- `src/omaha/auth.py::get_active_profile` and
  `require_active_profile`: current session-to-`Profile` boundary; sentinel
  profiles are intentionally rejected by `require_active_profile`.
- `src/omaha/models.py::Profile.is_family_sentinel`, `Profile.name`, and
  `Profile.user`: current persisted identity used to distinguish Família from
  real profile rows; no schema change is needed.
- `.env.example`: current operator-facing environment template; it has no
  MyProfit variables.
- `README.md::Quick start` and configuration/testing guidance: current
  operator documentation and prohibition surface for secrets.
- Stable `openspec/specs/cross-profile-sharing/spec.md`: current Família
  aggregate/read-only contract. The delta extends its read-only boundary to
  MyProfit synchronization.
- Stable `openspec/specs/header-profile-switcher/spec.md` and
  `openspec/specs/profile-landing/spec.md`: current active-profile selection
  and login landing contracts. They remain unchanged; F57 consumes their
  active-profile semantics rather than changing them.
- Stable `openspec/specs/shared-test-support/spec.md`: current synthetic test
  environment convention. F57 tests remain pure and use isolated fake values;
  no worker DB or production DB path is needed.

### Current relevant flow

1. Process imports `omaha.config`; `Settings` reads environment first and
   `.env` second, then `_build_settings` enforces `SECRET_KEY` outside pytest.
2. Login/session flow stores `active_profile_id`; profile selection can point
   at any profile, including the Família sentinel for the aggregate view.
3. `get_active_profile`/`require_active_profile` expose a real `Profile` for
   profile-scoped flows, while the sentinel flag is the explicit Família
   boundary.
4. No MyProfit transformation, external client, synchronization route, CSV
   download, or background job exists in this slice. F57 ends at typed config
   resolution and a guard that F58 can call.

Boundary conditions: Italo and Ana must remain isolated; Família and unknown
profiles must not receive credentials; missing/incomplete values must fail
closed with sanitized diagnostics; fake values must never cause network access;
existing shared `ADMIN_PASSWORD`, DB defaults, auth, and profile persistence
must remain unchanged.

## Goals / Non-Goals

**Goals:**

- Add exact, separate `MYPROFIT_ITALO_*` and `MYPROFIT_ANA_*` settings for
  email, password, and opaque destination.
- Provide one typed resolver boundary for active profile selection.
- Fail closed for Família, unknown profiles, and incomplete configuration.
- Keep secrets out of repr, diagnostics, logs, docs, and tests.
- Document false `.env.example` placeholders and verify them offline.

**Non-Goals:**

- No Playwright/browser connector or MyProfit HTTP request.
- No background synchronization job, polling, UI action, CSV download/preview,
  import commit, or end-to-end test (F58-F60/T31 scope).
- No database column, migration, seed, profile rename, auth behavior, or
  production credential change.
- No secret rotation or modification of `ADMIN_PASSWORD=distendidos`.

## Decisions

### 1. Keep credential state in environment-backed settings

Add profile-specific fields to `Settings`, with `email`, `password`, and
`destination` grouped into a typed immutable value returned by a resolver.
Use `SecretStr` (or equivalent Pydantic secret type) for password material and
avoid logging the settings object. This preserves existing `.env` precedence,
startup validation, and deployment conventions without introducing DB storage.

Alternative rejected: storing credentials on `Profile` or in SQLite. That would
persist secrets in the portfolio database, require a migration, and violate the
environment-secret boundary needed by F58.

### 2. Resolve by real profile identity and reject sentinel first

Resolver accepts the active `Profile` boundary (or an equivalent profile
identity adapter) and checks `is_family_sentinel` before selecting an env
prefix. After trimming and case-folding `Profile.name`, `italo` maps to Italo;
`ana` and `ana livia` map to Ana. Any other non-sentinel name is rejected.
Missing or incomplete mappings raise stable domain errors with safe reason
codes; no fallback profile is allowed.

Alternative rejected: silently return `None` or fall back to Italo. A silent
fallback could synchronize wrong account; an explicit failure gives F58 a safe
pre-network guard.

### 3. Treat destination as opaque non-secret routing data

Destination is loaded separately per profile and passed as opaque configuration
to the future connector. F57 validates presence and rejects blank/known false
placeholders; it does not validate or contact a URL and does not define
connector navigation behavior. Password is secret-wrapped; all diagnostics
redact credential fields and destination details.

Alternative rejected: URL reachability validation during settings load. It
would make startup/network behavior nondeterministic and violate offline test
requirements.

### 4. Use false placeholders that cannot be mistaken for production values

`.env.example` will contain separate synthetic email/password/destination
placeholders for Italo and Ana, using reserved invalid/example values. Tests
will assert placeholders are distinct, non-production, and load only under
explicit fake-value overrides. README will state that operators must supply
real values in ignored `.env`, without printing or echoing them.

### 5. Keep active-profile and Família contracts unchanged

`auth.py` and `models.py` are read-only inputs to this design. Existing
cross-profile viewing remains allowed for real profiles; Família remains a
read-only aggregate. Only the stable cross-profile-sharing spec gains the
MyProfit synchronization prohibition. No auth dependency, profile row, or
database behavior changes.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/config.py::Settings` | No MyProfit settings | Separate Italo/Ana email, password, destination fields with safe types and defaults/validation | Environment-backed profile isolation |
| `src/omaha/config.py::MyProfit*` resolver/error symbols | No MyProfit resolver | Typed profile config plus fail-closed real-profile resolver and Família/unknown/incomplete guards | Stable pre-connector boundary for F58 |
| `.env.example` | No MyProfit entries | Six separate false placeholders under `MYPROFIT_ITALO_*`/`MYPROFIT_ANA_*` | Operator contract without real credentials |
| `README.md::Quick start` / configuration guidance | No MyProfit setup or secret warning | Explain ignored `.env`, per-profile variables, false placeholders, Família block, and no secret logging | Safe deployment documentation |
| `src/omaha/auth.py::get_active_profile`, `require_active_profile` | Existing session and sentinel semantics | No behavior change; resolver consumes same boundary | Preserve authentication/profile contracts |
| `src/omaha/models.py::Profile` | Existing name/sentinel persistence | No schema or seed change | Avoid DB secret storage and preserve Família sentinel |
| `tests/test_f57_myprofit_profile_config.py` | No F57 coverage | Pure tests for Italo, Ana, Família rejection, sanitization, and offline fake values | Acceptance evidence without network/DB |

## Risks / Trade-offs

- **[Wrong profile mapping]** Cross-profile viewing means viewer identity is
  not active-profile identity → resolve from active `Profile`, never logged-in
  `User`, and test Ana/Italo isolation explicitly.
- **[Secret leakage through diagnostics]** Pydantic or logging may stringify
  values → use secret-safe password type, sanitized domain errors, and tests
  asserting synthetic markers are absent from repr/error output.
- **[Placeholder interpreted as live config]** Example values may be copied
  unchanged → use reserved invalid domains/tokens and fail closed for known
  placeholders; document replacement in ignored `.env`.
- **[Future connector bypasses guard]** F58 might read raw settings directly →
  expose one resolver/guard as connector input and make tasks/spec require
  connector calls through it.
- **[Profile naming drift]** Persisted names are user-facing → keep mapping
  normalization/aliases explicit in the resolver and reject ambiguous names;
  do not broaden mapping silently.

## Migration Plan

No database migration or production DB operation. Deploy configuration code and
docs with empty/default-safe settings; operators add real values only to their
ignored `.env`. Rollback removes the resolver and env entries without touching
portfolio rows. F58 must consume this contract before enabling synchronization.

## Implementation Decisions

### 1. Keep resolver independent from database and auth imports

- **Context:** F57 must remain offline and must not change `auth.py`,
  `models.py`, or database behavior. The active `Profile` row already exposes
  the two resolver inputs needed here: `name` and `is_family_sentinel`.
- **Decision:** `config.py` accepts that narrow profile boundary through a
  structural protocol. It checks the Família sentinel before name mapping and
  resolves only canonical Italo/Ana aliases.
- **Impact:** F58 receives one typed `MyProfitProfileConfig` boundary without
  any DB lookup, network client, Playwright import, or credential fallback.
- **Evidence:** `tests/test_f57_myprofit_profile_config.py` uses isolated
  `SimpleNamespace` profiles; family rejection passes with zero external-call
  spy count.

### 2. Fail closed at resolution, not application startup

- **Context:** Existing `_build_settings` must preserve `.env` precedence,
  `SECRET_KEY` enforcement, quote settings, and pytest detection. Operators
  need the app to start before optional MyProfit credentials are configured.
- **Decision:** Six MyProfit settings are optional environment-backed fields;
  resolver rejects missing, blank, and reserved placeholder values with stable
  reason codes. Password uses `SecretStr`; settings and resolved config have
  redacted representations for diagnostics.
- **Impact:** Incomplete or copied `.env.example` values cannot reach a future
  connector, while existing startup behavior remains unchanged.
- **Evidence:** Focused F57 tests pass for profile isolation, incomplete
  configuration, placeholder rejection, and marker absence from repr/logs.

### 3. Preserve existing Família wire semantics

- **Context:** `auth.py` already defines the read-only wire reason as
  `household_read_only`, despite the user-facing profile being named Família.
- **Decision:** MyProfit resolver uses that existing stable reason and performs
  the sentinel guard before any profile prefix or credential field lookup.
- **Impact:** Future synchronization can reuse the existing family-read-only
  contract without changing auth/session or mutation behavior.
- **Evidence:** `test_family_rejected_before_lookup` passes and both F57 delta
  specs validate successfully.

## Resolved Boundary Decisions

- Ana profile identity accepts both persisted labels documented by current
  code/docs (`Ana` and `Ana Livia`) after normalization; all other labels are
  rejected rather than guessed.
- Destination remains opaque routing data in F57. F57 validates only
  non-blank/non-placeholder input; F58 owns URL/path navigation semantics.

## Proposal Gate Evidence

Recorded after artifact creation:

- `openspec status --change f57-configurar-credenciais-myprofit-por-perfil --json`
  → `isComplete: true`; proposal, design, specs, and tasks all `done`.
- `openspec validate f57-configurar-credenciais-myprofit-por-perfil --type change --strict --json`
  → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json` → valid, 68/68 stable specs
  passed, 0 failures; existing informational long-requirement notices only.
- `rtk git diff --check -- openspec/changes/f57-configurar-credenciais-myprofit-por-perfil`
  → clean.
- `rtk git status --short --untracked-files=all -- openspec/changes/f57-configurar-credenciais-myprofit-por-perfil`
  → only F57 dossier files are untracked; no application files changed.

No implementation tests, MyProfit calls, credential changes, migrations, or
production DB operations were run in this proposal gate.
