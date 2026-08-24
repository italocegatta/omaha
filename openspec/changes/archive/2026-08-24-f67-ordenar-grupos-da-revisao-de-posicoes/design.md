## Context

F65 already owns four mutually exclusive review states and deterministic row
ordering inside each state. D06 archived the surrounding sync/import surface
decisions without changing preview, review, confirmation, or timeout behavior.
F67 is one browser-visible ordering correction: section sequence must not depend
on payload key order, producer, or a local action's hydration timing.

### Code map

| File | Symbol/surface | Role in current flow |
|---|---|---|
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | Step 2 `template x-for="section in $store.importModal.triageSections"` | Renders each non-empty review section, count, table, row controls, hidden `broker_ticker`, and diff disclosures. Current section list is `new`, `changed`, `unchanged`, `absent`, so `Ausentes` renders last. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | `Alpine.store('importModal').triageSections` | Current client-side section metadata and labels. This is shared by manual upload, MyProfit handoff, and local/mock `openPreview` calls. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | `resetState`, `clearPreview`, `hydratePreview`, `openPreview`, `uploadFile`, `goBackToStep1` | Reset and hydration boundaries. `hydratePreview` accepts F65 payloads or falls back from legacy `auto_matched`/`unmatched`; `openPreview` serves sync/local actions; `uploadFile` serves manual CSV. |
| `src/omaha/routes/imports.py` | `_build_preview_response` | Canonical API serializer for `POST /api/import/preview`, `GET /api/import/preview/{preview_id}`, and MyProfit status preview. Builds `auto_matched`, `unmatched`, four `triage` groups, and deterministic within-group row order. |
| `src/omaha/routes/imports.py` | `_triage_sort_key`, `_build_absent_rows`, `_preview_rows_and_baseline` | Preserve accent/case-insensitive row ordering, `Ausentes` construction, F65 baseline/legacy envelope compatibility, and profile boundaries. |
| `src/omaha/routes/imports.py` | `preview_import`, `get_preview`, `MyProfitSyncService.status_for_profile` | API and sync handoff boundaries. They must keep response shape, TTL, sanitized errors, polling/job state, and no-mutation behavior unchanged. |
| `tests/test_import_preview.py` | `TestPostImportPreview` triage, absent, legacy, and baseline scenarios | API oracle for four-way classification, counts, rows, deterministic row order, compatibility arrays, legacy raw-list previews, and read-only preview behavior. |
| `tests/e2e/test_import_modal.py` | `test_import_modal_happy_path`, local `openPreview` scenarios | Browser oracle for section labels/counts, row membership, controls, empty sections, diff behavior, manual upload, sync-shaped/local payloads, and explicit commit. |

### Current relevant flow

1. **Input:** manual `selectFile` posts a CSV to `/api/import/preview`;
   successful MyProfit polling passes `payload.preview` to `openPreview`; local
   browser/mocked actions can call `openPreview` directly. API re-fetch uses
   `GET /api/import/preview/{preview_id}`.
2. **Transformation:** `_build_preview_response` rehydrates the persisted raw
   rows/baseline, matches active-profile assets, classifies incoming rows into
   `new`, `changed`, or `unchanged`, adds profile assets absent from the batch
   into `absent`, and sorts each group with `_triage_sort_key`. It preserves
   legacy arrays independently.
3. **Hydration:** `hydratePreview` stores compatibility arrays and, when
   present, the four F65 groups; if `triage` is absent, it maps `unmatched` to
   `new`, `auto_matched` to `changed`, and leaves `unchanged`/`absent` empty.
4. **Output:** Step 2 iterates `triageSections`, suppresses groups whose array
   is empty, renders count plus all eight production columns and controls, and
   keeps `broker_ticker` hidden for assignment/commit identity. Current output
   order follows `triageSections`, not a server-side cross-group sort.
5. **Boundaries:** preview generation is read-only; `Confirmar` remains sole
   commit boundary. Expired/malformed/foreign previews, Família guards,
   MyProfit polling, `pollDelay × maxPolls`, job expiry, sanitized error text,
   cancellation, and D06 removals are outside this visual ordering change.

### Boundary conditions

- A payload may contain any subset of the four groups; empty sections remain
  absent, with no placeholder or count.
- A mixed payload whose object-key order is arbitrary must still render in the
  fixed sequence `Novos` → `Ausentes` → `Alterados` → `Inalterados`.
- Legacy payloads without `triage` remain reviewable through existing fallback;
  fallback groups use the same fixed section metadata.
- Counts are lengths of hydrated group arrays. Rows and deterministic order
  within each group are not recomputed or reclassified by F67.
- Assignment controls, hidden ticker identity, diff cues/disclosures, zero and
  missing values, and all existing formatting remain unchanged.

## Goals / Non-Goals

**Goals:**

- Make one authoritative client section sequence for every review entry path.
- Prove mixed-batch browser order and API preservation together.
- Preserve F65 four-way classification, counts, rows, within-group sorting,
  controls, no-empty-section behavior, legacy compatibility, and D06 handoff.
- Carry explicit owner browser-rendering/mock approval as a prerequisite to
  Apply.

**Non-Goals:**

- No change to `_build_preview_response` classification, `_triage_sort_key`,
  `auto_matched`, `unmatched`, `asset_classes`, or API field values.
- No server-side cross-group sorting contract; JSON object key order is not the
  rendering source of truth.
- No timeout, polling, job expiry, connector, error, commit, DB, migration,
  seed, CSS, route, D06 archive, or local-storage behavior change.
- No changes to T36/F68, F63, T31, F65, F60, or F60-owned sync tests.
- No new review section, no empty placeholders, no client locale-dependent row
  sort, and no automatic commit.

## Decisions

### 1. Fixed order lives in `triageSections`

Change the existing metadata sequence to exactly `new`/`Novos`,
`absent`/`Ausentes`, `changed`/`Alterados`, `unchanged`/`Inalterados`.
The existing Step 2 loop already uses this metadata for labels, counts,
selectors, row keys, controls, and empty-section suppression. Reusing it makes
manual upload, sync handoff, local hydration, and legacy fallback converge
without duplicate order logic.

**Alternative rejected:** sort `Object.keys(triage)` or the group arrays in
Alpine. Payload key order is producer-dependent, and browser locale sorting
would risk changing F65's deterministic within-group order.

### 2. Keep API classification and row order unchanged

`imports.py` remains an inspected compatibility boundary, not an implementation
target unless focused evidence exposes a contract defect. `_build_preview_response`
continues to emit the four groups and sort rows inside each group. API tests
must assert the four keys/counts/rows and existing deterministic name/ticker
ordering, while browser tests assert cross-group rendering order from the fixed
client metadata.

**Alternative rejected:** reorder or reshape the response to make JSON key
order carry UI semantics. That would couple API producers to presentation and
could disturb legacy consumers without improving local hydration.

### 3. Legacy fallback uses same section sequence

Do not add synthetic `triage` to legacy payloads or alter compatibility arrays.
`hydratePreview` keeps current fallback data, while the shared `triageSections`
list guarantees its visible sections follow F67 order. This retains safe review
of pre-F65 payloads and avoids treating legacy `auto_matched` as proof of
unchanged state.

### 4. Owner approval blocks Apply

Before Apply, owner must approve a browser rendering or deterministic local
mixed-batch mock showing all four labels in order, absent empty groups, counts,
row membership, and preserved controls. Record artifact/mock path, exact
payload shape, rendered sequence, and approval timestamp in the Apply handoff.
Proposal records gate only; it does not claim approval or run refresh-for-test.

### 5. Delivery and timeout boundaries stay untouched

The change does not edit sync timers or messages. Apply must preserve
`pollDelay`, `maxPolls`, terminal/error handling, and D06-removal behavior. If
browser evidence reveals timeout or unrelated surface drift, stop and return
`BLOCKED_SCOPE_CHANGE` rather than expanding F67.

## Change map

| File/symbol | From → to | Reason |
|---|---|---|
| `src/omaha/templates/_patrimonio_add_asset_modal.html` — `importModal.triageSections` | `new`, `changed`, `unchanged`, `absent` → `new`, `absent`, `changed`, `unchanged` | One fixed rendering sequence for all hydrated previews. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` — Step 2 `x-for`/hydration paths | Existing iteration uses shared metadata → same iteration with reordered metadata; `hydratePreview`, `openPreview`, `uploadFile`, reset, controls, and empty filtering unchanged | Ensure every entry path inherits order without duplicate sorting or reclassification. |
| `src/omaha/routes/imports.py` — `_build_preview_response`, `_triage_sort_key`, preview routes/status | Existing four-way payload and per-group deterministic order → unchanged contract, verified by tests | Preserve F65 classification, counts, row values, compatibility, legacy envelope/raw-list handling, TTL, and job boundary. |
| `tests/test_import_preview.py` — triage/legacy API scenarios | Existing four-way and deterministic assertions → add mixed-batch key/count/row and compatibility regression assertions only | Independent oracle that API semantics remain stable; no production route change inferred from presentation order. |
| `tests/e2e/test_import_modal.py` — upload/local preview scenarios | Existing presence/count assertions → assert exact visible sequence for mixed F65 payload, hidden empty groups, legacy hydration, and preserved controls | Browser oracle for actual rendered order across manual, sync-shaped, and local paths. |
| `openspec/changes/f67-ordenar-grupos-da-revisao-de-posicoes/specs/import-modal/spec.md` | No fixed four-section sequence → modified Step 2 requirement and scenarios | Durable contract for owner-facing order and preserved review behavior. |

## Fidelity ledger

| Product wording | Concrete behavior | Source | Forbidden interpretation | Evidence |
|---|---|---|---|---|
| `Novos, Ausentes, Alterados, Inalterados` | Non-empty section headers render in exact sequence | `triageSections` + Step 2 `x-for` | Payload insertion order, alphabetical order across groups, or reclassification | Browser mixed-batch section-header list |
| Preserve F65 classification | Rows remain in server-provided `triage.new/changed/unchanged/absent` arrays | `_build_preview_response`, `hydratePreview` | Moving rows between groups to achieve sequence | API counts/membership plus browser row selectors |
| Counts | Header count equals hydrated group length | `triage[section.key].length` | Recomputed totals, compatibility-array counts, or hidden rows | API and browser count assertions |
| No empty sections | Section wrapper absent when group length is zero | Existing `x-if` | Empty heading, placeholder, or zero-count card | Browser locator count |
| Deterministic within-group order | Keep case/accent-insensitive name, ticker tie-break, raw fallback order | `_triage_sort_key` | Client locale sort or cross-group sort | API named-order assertions |
| Preserve rows and controls | Eight columns, class/trade/currency controls, hidden ticker, diff cues remain | Existing Step 2 markup | Ticker column, control removal, altered value formatting, automatic commit | Browser control/commit assertions |
| Legacy compatibility | Missing triage maps through existing fallback and renders ordered review | `hydratePreview` fallback | Fabricating unchanged/absent classification or dropping legacy arrays | Browser local legacy payload |
| D06/timeout preservation | D06 removals and sync timing/error surfaces unchanged | Archived D06 handoff; `patrimonioSync` | Reintroducing notifications, changing timeout, retrying indefinitely | Scope audit; existing sync tests remain untouched |

## Risks / Trade-offs

- **A future producer adds a fifth group** → Keep metadata as explicit four-state
  allow-list; focused tests fail rather than silently rendering unknown state.
- **A refactor sorts arrays in the browser** → Assert API order for rows and
  review implementation keeps no client-side row sort; preserve `_triage_sort_key`.
- **Legacy payload loses reviewability** → Exercise payload with only legacy
  arrays and assert existing assignments/commit boundary remain available.
- **Section reorder breaks selectors or controls** → Use mixed rows in every
  group and assert testids, counts, hidden ticker, assignments, and no commit
  before confirmation.
- **Owner sees stale browser bytes** → Apply must invoke `refresh-for-test` for
  runtime change and provide receipt before delivery; owner rendering approval
  remains a separate pre-Apply gate.
- **Scope expands into timeout or D06 cleanup** → Stop with
  `BLOCKED_SCOPE_CHANGE`; do not touch F68/T36/D06 archive or sync timers.

## Migration Plan

No data or schema migration. Apply reads this dossier, confirms recorded owner
approval, changes only listed runtime/test symbols, runs focused API/browser
checks and lint, then invokes `refresh-for-test` for browser-visible delivery.
Rollback is surgical: restore prior `triageSections` sequence and remove only
F67 tests/delta; do not alter archived D06, preview data, DB, or job state.

## Open Questions

- **Owner approval:** browser rendering or deterministic mock approval is open
  until owner records it. Without it, Apply is blocked.
- No product decision is open for group order; roadmap fixes exact sequence.
- No decision is open for timeout/polling; those remain T36/F68 scope.

## Implementation Decisions

- **Client metadata remains sole presentation authority.** Preflight and the
  green browser run confirmed manual upload, sync-shaped/local hydration, and
  legacy fallback all converge through `triageSections`; no API serializer or
  server cross-group sort was needed. Evidence: 8 passing F67 E2E tests and
  17 passing preview API tests, with `imports.py` unchanged.
- **Owner-authorized delivery cleanup is exact-resource bounded.** The
  continuation used explicit authorization for only `data/test_e2e.db` and
  Omaha PID/PGID `67046`/`67038`; `data/test_e2e_short_ttl.db` and
  `data/portfolio.db` stayed non-targets. Evidence: preflight command/identity
  match, exact-group restart, preserved production inode, and owned-cleaned
  test DB receipt in `tasks.md`.
