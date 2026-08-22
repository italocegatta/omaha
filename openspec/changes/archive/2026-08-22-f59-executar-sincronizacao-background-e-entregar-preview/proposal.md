## Why

F58 now provides an isolated, offline-testable MyProfit CSV connector, but no
safe request boundary runs it or hands its result to the existing import review.
F59 supplies that boundary before F60 adds the dashboard action: a profile-scoped
background job with observable state, failure feedback, and a successful preview
payload without committing portfolio data.

## What Changes

- Add one asynchronous MyProfit synchronization job boundary for each real
  profile, with start and polling endpoints and explicit `queued`, `running`,
  `succeeded`, `failed`, and `expired` states.
- Persist job ownership and lifecycle metadata by profile; enforce one active
  job per profile, allow independent real profiles to run concurrently within a
  bounded application-wide limit, and reject Família before credential or
  connector access.
- Give every job isolated temporary CSV/file paths, remove them on success,
  failure, expiry, shutdown, and cleanup retry, and never expose file contents
  or credentials in status/error responses.
- Convert a successful connector download through the existing parser and
  `/api/import/preview` response builder, returning the existing preview shape
  and `preview_id` for `$store.importModal` review. No automatic commit.
- Expose sanitized login/download errors as page-safe job error state; failed
  jobs return no preview and do not open or mutate the import modal.
- Preserve profile isolation, Família read-only semantics, manual class review,
  explicit import confirmation, pre-commit snapshot, post-commit audit, and
  production-DB protection.

## Capabilities

### New Capabilities

- `myprofit-sync-job`: profile-isolated asynchronous synchronization lifecycle,
  polling contract, bounded concurrency, file cleanup, expiry, and preview
  handoff.

### Modified Capabilities

- `import-modal`: successful programmatic MyProfit handoff uses the existing
  preview/review payload, while failed synchronization remains an error state
  with no modal opening and commit remains manual.
- `cross-profile-sharing`: Família read-only contract covers the job start and
  polling boundary before credential, browser, network, or file access.

## Impact

- Runtime: `src/omaha/routes/imports.py`, `src/omaha/routes/pages.py`,
  `src/omaha/main.py`, `src/omaha/csv_import.py`, `src/omaha/models.py`, plus
  the directly necessary Alembic migration and focused tests.
- API: new authenticated start/status endpoints; existing
  `POST /api/import/preview`, `GET /api/import/preview/{preview_id}`, and
  `POST /api/import/commit` wire shapes remain compatible.
- Storage: one job lifecycle table and short-lived per-job file metadata; no
  asset/position seed changes and no production data mutation during sync.
- Tests: lean focused coverage of essential internal boundaries only: persisted
  job state and concurrency, expiry/owned-file cleanup, profile/Família
  authorization, internal CSV-to-existing-preview handoff, page-safe error and
  no-modal state, and DB-mutation safety where the sync path can affect it.
  Use temporary DB/path fixtures and synthetic internal inputs. No F59 test
  exercises, fakes, mocks, launches, logs into, downloads from, or otherwise
  involves MyProfit/Playwright connector behavior.

## Owner-approved validation boundary

This amendment changes validation scope only. Production behavior remains the
profile-scoped background job, F58 connector handoff, preview reuse, cleanup,
expiry, Família guard, and manual commit safety described above.

Focused F59 tests SHALL cover only these high-value internal boundaries:

- job lifecycle state, per-profile reservation, bounded concurrency, expiry,
  and cleanup of job-owned paths;
- active-profile and Família authorization before scheduling, lookup, or file
  side effects;
- direct internal CSV bytes → existing parser/preview response handoff;
- normalized error → page/job state with `preview: null` and no modal/commit
  side effect;
- DB-mutation safety: no asset/position/commit/snapshot/audit mutation during
  sync preview creation, where affected.

Explicit exclusions: no test may exercise, fake, mock, launch, log into,
download from, or otherwise involve `MyProfitConnector`, Playwright, browser,
network, credentials, or MyProfit service behavior. Connector coverage remains
owned by F58/T31. Existing repository quality rules, including applicable
focused regression tests and the canonical full-suite delivery policy, remain
unchanged; this proposal gate runs no product tests or runtime refresh.
