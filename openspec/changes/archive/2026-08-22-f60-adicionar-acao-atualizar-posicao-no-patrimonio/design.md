## Context

F59 is Applied and owns the server boundary consumed here:

- `POST /api/myprofit/sync` returns `202 {job_id, status:"queued"}` for the
  active real profile.
- `GET /api/myprofit/sync/{job_id}` returns `queued`, `running`, `succeeded`,
  `failed`, or `expired`; only `succeeded` may contain a preview.
- A successful preview has the same keys as manual upload:
  `preview_id`, `auto_matched`, `unmatched`, and `asset_classes`.
- Failed/expired responses contain safe error data and `preview: null`.
- Família is rejected by F59 before credential, connector, browser, file, or
  preview side effects.

F60 adds only the Patrimônio browser boundary. Existing manual CSV upload,
classification, explicit commit, snapshot, audit, and page navigation behavior
remain authoritative. No F59 route, connector, model, migration, or worker
implementation is redesigned.

## Code map

### Templates and client flow

- `src/omaha/templates/_patrimonio_actions.html`
  - `section[data-testid="patrimonio-actions"]`: current Alpine scope and
    action strip; `Importar CSV`, `Novo ativo`, and `Nova classe` triggers.
    F60 revision changes the pair order to sync immediately left of import and
    replaces the inline status paragraph with a notification outlet.
  - Current outer `{% if view == 'profile' %}` hides all actions in Família;
    F60 must make only the new sync affordance visible/read-only there.
- `src/omaha/templates/patrimonio.html`
  - Shell sets `view` and `read_only`, includes `_patrimonio_actions.html`,
    and includes `_patrimonio_add_asset_modal.html`; preserve thin-shell and
    include-only organization.
- `src/omaha/templates/_patrimonio_add_asset_modal.html` (directly required
  Alpine code)
  - `Alpine.store('importModal')`: `openModal`, `resetState`, `clearPreview`,
    `uploadFile`, and `commit` currently own manual preview hydration and
    explicit commit.
  - The repeated response-to-assignments logic inside `uploadFile` is the
    shared seam for a new programmatic F59 preview handoff.
  - `importModal.openPreview` / `closeModal`: source-aware review handoff and
    cancel reset; manual upload close behavior must remain unchanged.
  - `patrimonioSync`: current lifecycle state machine and message strings; F60
    revision routes lifecycle copy through notification cards and resets
    success styling after sync-origin review cancellation.
- `src/omaha/static/app.css`
  - `.patrimonio-actions` / `.patrimonio-action-btn`: current action-strip
    layout and typography; sibling parity and adjacency are fixed here.
  - New notification outlet/card selectors: fixed bottom-corner placement,
    stacking, timer-safe focus treatment, and responsive width.
  - Existing `.btn:disabled`, focus, error, responsive, and read-only rules:
    preserve token usage, contrast, and mobile wrapping while adding sync-state
    modifiers.

### Server context and API boundary

- `src/omaha/routes/pages.py`
  - `_common_context`: F59 already exposes sanitized `myprofit_sync` and
    `myprofit_sync_error` for the active real profile and suppresses detail in
    Família. F60 consumes this context for initial page-safe error display; it
    must not start jobs or poll from a GET.
  - `_render_patrimonio`: resolves `view`/`read_only` and includes the action
    partial; preserve family aggregate and cross-profile rendering.
- `src/omaha/routes/imports.py`
  - `_require_sync_profile`, `start_myprofit_sync`, and
    `get_myprofit_sync_status`: F59's exact start/poll contract and Família
    guard; F60 calls these endpoints and does not alter their behavior.
  - `MyProfitSyncService.status_for_profile`: terminal status and preview
    serializer consumed by the client; only a compatible successful payload
    reaches the review handoff.
  - `_build_preview_response`: canonical payload shape; do not duplicate or
    change it.

### Existing tests and specs

- `tests/test_rebalance_page.py` and `tests/e2e/test_rebalance_page.py`:
  existing Patrimônio action-strip and Alpine-scope regressions.
- `tests/e2e/test_import_modal.py` and
  `tests/e2e/test_import_user_journey.py`: existing review/modal behavior and
  explicit commit path.
- `tests/test_myprofit_sync_jobs.py`: F59 server contract; read as an oracle,
  do not broaden with browser tests or connector doubles.
- `tests/conftest.py::_INTEGRATION_PREFIXES`: explicit allow-list required for
  any new DB/TestClient test module.
- `openspec/specs/import-modal/spec.md` and
  `openspec/specs/cross-profile-sharing/spec.md`: stable manual-review and
  Família contracts extended by F60 deltas.

## Current relevant flow

1. Authenticated `GET /patrimonio` resolves active profile/view in
   `pages.py`, builds sanitized common context, and renders the shell.
2. In a real profile, `_patrimonio_actions.html` renders the action strip with
   `Atualizar posição` immediately left of `Importar CSV`; the sync button
   calls `$store.patrimonioSync.start()` and import calls
   `$store.importModal.openModal()`.
3. Manual file selection calls `importModal.uploadFile()`, which POSTs the
   file to `/api/import/preview`, stores the response, initializes assignments,
   and changes modal step to review.
4. The review modal remains open while the operator edits assignments. Its
   `commit()` calls `/api/import/commit`; successful commit reloads the page.
5. F60's new action starts F59 with `POST /api/myprofit/sync`, retains its
   `job_id`, and polls `GET /api/myprofit/sync/{job_id}` using a visible loading
   state. Each lifecycle copy is emitted as a bottom-corner notification card;
   no page GET, redirect, or hidden polling loop is introduced.
6. `succeeded + preview` goes through the same import-store hydration and
   opens existing step 2. Success styling may remain visible while review is
   open, but sync-origin `Cancelar` invokes the source reset, dismisses its
   notification, and returns the action to idle. `failed`, `expired`, start
   errors, poll errors, and malformed success payloads stop on Patrimônio with
   the modal closed and safe error notification.

Boundary conditions: duplicate activation is blocked; polling stops at every
terminal state; safe error messages never expose credentials, paths, raw
exceptions, CSV bytes, or URLs; no asset/position/class mutation occurs before
the existing explicit commit; Família cannot issue client or server sync
requests; browser tests use intercepted F59 HTTP responses, never MyProfit,
Playwright connector, credentials, network navigation, or production DB.

## Goals / Non-Goals

**Goals:**

- Pair `Atualizar posição` with `Importar CSV` for real profiles.
- Make all five requested UI states observable and accessible.
- Consume F59 start/status/preview contracts without navigation.
- Reuse existing import review and assignment initialization.
- Keep errors page-local and keep Família visible but disabled/read-only.
- Provide focused route/render/browser evidence plus an owner-approved visual
  browser artifact after Apply and before Review, following the mandatory
  `refresh-for-test` receipt.

**Non-Goals:**

- No F59 backend, connector, migration, job lifecycle, or error-contract edits.
- No new modal, standalone review page, automatic commit, inferred class
  assignment, snapshot, audit, asset, position, or class mutation.
- No navigation to `/import`, `/import/review`, or a refreshed dashboard on
  start/success/failure.
- No invisible polling, retry policy beyond one bounded poll schedule, live
  MyProfit calls, connector tests, external service tests, seed changes,
  production DB work, or `refresh-for-test` during Propose.

## Decisions

### 1. Keep F59 as the only server contract

Use the exact F59 endpoints and status values. Do not add a F60 proxy route or
change response shape. This prevents client/server drift and keeps Família and
profile ownership enforcement server-side.

Alternative rejected: adding a dashboard-specific endpoint. It would duplicate
F59 authorization/error behavior and create two job contracts.

### 2. Add one visible Alpine action state machine

Add a narrowly scoped action component/store next to the existing
`patrimonio-actions` scope. State is explicit: `idle`, `loading`, `success`,
`error`, and `disabled`; state is reflected in a stable data attribute or
modifier class and a live status node. Start uses `fetch`, then schedules
bounded `setTimeout` polling so each response controls the next request. The
button is disabled from start until terminal handling completes.

Alternative rejected: `setInterval` or page reload. Both permit overlapping
requests or hide the job lifecycle and would violate no-navigation feedback.

### 3. Extract shared preview hydration, do not duplicate it

Refactor the existing `importModal.uploadFile()` success path into one private
store method (exact name chosen during Apply from current store conventions).
The method sets `previewId`, rows, classes, assignments, and review step. Manual
upload and F59 success call it. F59 success then opens the existing modal only
after payload shape validation. No commit call is part of hydration.

Alternative rejected: copying assignment initialization into the action. That
would let manual and sync review drift, especially for trade flags and dynamic
class bindings covered by PRD §4.4/§4.5.

### 4. Render Família control without weakening read-only enforcement

The sync button is rendered in Família as a native disabled control with
accessible read-only labeling. Its click handler is absent or guarded in that
view. Existing mutation actions can retain their current hidden/disabled
behavior. F59 remains the authoritative server guard for direct requests.

Alternative rejected: hiding the new button in Família. Roadmap fidelity ledger
requires the action to remain visible as a disabled/read-only control.

### 5. Use existing F59 page-safe context, no new GET side effect

The action partial may render the latest sanitized `myprofit_sync` error already
provided by `_common_context`. `pages.py` must not start, poll, or open a modal.
If current context is sufficient, no functional edit is made to `pages.py`; any
edit must be limited to passing the already-safe state into the action markup.

Alternative rejected: polling from page load. F60 starts only from explicit user
activation and must not surprise the operator or run in Família.

## Implementation Decisions

### Apply preflight: retain F59 page context and modal boundary

- Context: inspection confirmed that F59 already exposes sanitized
  `myprofit_sync`/`myprofit_sync_error` context for real profiles, while the
  Patrimônio shell remains a thin include-only boundary. The existing import
  store owns all preview assignment initialization and the F59 routes already
  provide the exact start/status contract.
- Decision: leave `pages.py`, `patrimonio.html`, and `imports.py` behavior
  unchanged. Render the real-profile action and Família read-only affordance
  in `_patrimonio_actions.html`; add the sync state machine beside the existing
  Alpine `importModal` store and extract one shared preview hydration method in
  `_patrimonio_add_asset_modal.html`.
- Impact: no new GET side effect, proxy route, preview serializer, or commit
  path. F59 backend/job semantics remain owned by F59; F60 only consumes its
  public browser contract.
- Evidence: mapped source inspection before edits found `_common_context` safe
  error serialization at `src/omaha/routes/pages.py:149-231`, exact F59 routes
  at `src/omaha/routes/imports.py:818-863`, and duplicated manual preview
  hydration at `_patrimonio_add_asset_modal.html:1812-1884`.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/templates/_patrimonio_actions.html::patrimonio-actions` | Real-profile-only strip with manual/import/create actions | Strip includes `Atualizar posição` beside `Importar CSV`; real profile binds action state machine; Família renders new control disabled/read-only while existing mutators remain protected | Expose operator control and preserve Família visibility contract |
| `src/omaha/templates/patrimonio.html::shell` | Includes actions with `view`/`read_only` context but no sync-specific state contract | Keep thin shell and ensure action partial receives existing context; no section markup or modal structure moves | Preserve R04 partial boundary and server-rendered page contract |
| `src/omaha/templates/_patrimonio_add_asset_modal.html::importModal` | Manual upload owns inline preview-to-assignment hydration | Extract shared hydration method; expose only existing review opening path for F59 success | Avoid duplicated assignment logic and preserve manual commit |
| `src/omaha/static/app.css::.patrimonio-actions` / button states | Generic action row and generic disabled style | Add token-based loading/success/error/disabled/read-only sync modifiers and responsive feedback | Make five states visible without changing unrelated components |
| `src/omaha/routes/pages.py::_common_context` / `_render_patrimonio` | F59 already provides safe latest sync error context; page GET has no sync side effect | Consume existing context in action markup; edit only if a minimal explicit state binding is required, with no new query or mutation | Keep page-safe errors and no hidden polling |
| `src/omaha/routes/imports.py::start_myprofit_sync`, `get_myprofit_sync_status`, `_build_preview_response` | F59 exact start/status/preview contract | F60 client consumes unchanged endpoints, states, and payload keys; no backend behavior change | Prevent F59 regression and keep one authoritative API |
| `tests/test_patrimonio_sync_action.py` | No F60 server-rendering assertions | Add real-profile/Família markup, initial error, and no-side-effect boundary tests; classify explicit integration prefix | Prove rendered contract without browser or connector |
| `tests/e2e/test_patrimonio_sync_action.py` | No F60 browser workflow | Intercept F59 start/poll responses and prove no navigation, all terminal states, success modal handoff, failure no-modal, duplicate guard, and Família disabled | Independent browser oracle for client choreography |
| `tests/e2e/test_import_modal.py` | Manual upload/review only | Add compatible programmatic preview handoff regression if not fully isolated in new F60 e2e module | Pin reuse of existing modal and explicit commit |
| `tests/conftest.py::_INTEGRATION_PREFIXES` | New F60 TestClient path unclassified | Add exact new test basename/prefix only if its tests use DB/TestClient | Preserve explicit marker allow-list |

No `src/omaha/routes/imports.py` implementation, connector, migration, seed,
asset/position data, production DB, or unrelated test changes are authorized by
this map.

## Risks / Trade-offs

- **Preview hydration drift** → one shared import-store method, existing
  `import-modal` selectors, and payload-key assertions for both entry paths.
- **Duplicate starts or stale poll responses** → action-local request token,
  disabled loading state, one scheduled poll at a time, and terminal-state
  stop assertions.
- **Modal opens on unsafe terminal data** → require `status === "succeeded"`
  plus all four preview keys; otherwise show error and keep modal closed.
- **Family read-only regression** → native disabled markup test plus intercepted
  network assertion and existing F59 server guard tests left unchanged.
- **Visual clutter beside existing actions** → owner visual gate checks exact
  adjacency, hierarchy, shared typography/dimensions/alignment, icon placement,
  spacing, state contrast, mobile wrap, and no new modal.
- **Stale page error copy** → use F59 sanitized context only; never render raw
  job fields or exceptions.
- **Notification timer hides actionable feedback** → 8-second timer, pause on
  hover/focus, manual close, `aria-live` announcement, no focus theft, and no
  removal while a descendant has focus.
- **Success highlight survives review cancellation** → mark preview origin as
  `patrimonio-sync`; only that origin calls `patrimonioSync.resetAfterReview()`
  from `Cancelar`/close, leaving manual import semantics untouched.
- **Existing action regressions** → preserve current testids, Alpine scope,
  manual upload behavior, and existing CSS tokens; changed-file audit rejects
  unrelated rewrites.

## Migration Plan

No database migration or data migration. Apply in this order:

1. Enter Apply under the owner-authorized F60 process exception. Implement the
   markup/state contract and shared import-store hydration.
2. Add token-based CSS state presentation.
3. Add focused server-rendering and browser-interception tests; update the
   explicit marker allow-list only when a new DB/TestClient file requires it.
4. Run focused taskipy commands and lint. Do not call F59 connector or mutate
   production DB. If rollback is needed, remove only F60 UI/client/tests/spec
   changes; F59 routes and job data remain untouched.
5. Invoke mandatory `refresh-for-test` and record its delivery receipt.
6. Produce browser-rendered visual evidence, obtain owner validation/approval,
   and record it in this dossier. Review, `Applied`, archive, and commit remain
   blocked until that approval is recorded in `design.md`.

## Owner visual-approval gate (mandatory post-Apply, pre-Review)

F60 may enter `Applying` under the explicit owner-authorized process exception.
After implementation and the mandatory `refresh-for-test` delivery receipt,
Apply SHALL produce browser-rendered visual evidence and pause for owner
validation/approval before Review starts:

- required browser artifact:
  `tests/visual/artifacts/f60-atualizar-posicao-patrimonio.png`, captured from
  the refreshed seeded dashboard with intercepted F59 responses. It SHALL
  render action adjacency beside `Importar CSV`, idle/loading/success/error/
  disabled states, Família disabled/read-only treatment, safe error feedback,
  no navigation, and the existing review-modal handoff. Supplement with
  additional browser-rendered state screenshots or a trace when one image
  cannot show every state.

Owner approval is exact: owner confirms artifact path/checksum and receipt,
action adjacency/hierarchy, idle/loading/success/error/disabled presentations,
Família disabled/read-only, safe errors, no-navigation behavior, and existing
review modal handoff. Missing refresh receipt, missing artifact, missing
approval, or a visual mismatch is `BLOCKED`. Review SHALL NOT start, and the
slice SHALL NOT move to `Applied` or archive, until the owner decision is
recorded in `design.md`. This Propose revision does not create or run that
artifact.

## Test strategy

- Server/render tests: `tests/test_patrimonio_sync_action.py`,
  `tests/test_rebalance_page.py`, and existing F59 route tests as regression
  oracles. Test only rendered HTML, context, and exact F59 endpoint shapes.
- Browser tests: `tests/e2e/test_patrimonio_sync_action.py` plus the existing
  import modal journey. Route interception supplies queued/running/success,
  failed/expired, malformed-success, and start-error responses; no connector,
  credential, external network, or production DB is used.
- Browser visual gate: after implementation, invoke `refresh-for-test`, retain
  its mandatory delivery receipt, render the required states from intercepted
  F59 responses, and obtain owner approval before Review. Propose runs no
  browser, server refresh, DB task, or visual artifact command.
- Marker rule: any new DB/TestClient module is explicitly added to
  `_INTEGRATION_PREFIXES`; no wildcard/pattern shortcut.
- Focused implementation commands:
  `uv run task test-file tests/test_patrimonio_sync_action.py`,
  `uv run task test-file tests/test_rebalance_page.py`,
  `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`,
  `uv run task test-file tests/e2e/test_import_modal.py`, and
  `uv run task lint`.
- Canonical `uv run task test` remains a review-owned gate. Under current
  `maintenance-suspended` policy, review records it as
  `NOT RUN — maintenance-suspended`; focused product tests remain mandatory.
- Propose runs no product tests, no browser, no server refresh, no DB task, and
  no `refresh-for-test`.

## Acceptance evidence

- HTML oracle proves exact button label/testid, same action strip adjacency,
  preserved existing testids/Alpine scope, and visible Família disabled state.
- Browser oracle proves POST start + GET polling sequence, no URL/navigation
  change, loading duplicate suppression, terminal state stop, success opening
  existing review at step 2, and no auto-commit.
- Browser oracle proves failed, expired, malformed-success, and start/poll
  errors stay on page with no modal; Família emits zero client requests.
- Payload oracle proves F59 preview keys hydrate existing assignments and
  manual explicit commit remains sole mutation path.
- Visual oracle is the owner-approved browser-rendered artifact at the exact
  path above, with the mandatory `refresh-for-test` receipt; acceptance records
  owner decision after Apply and before Review.
- Changed-file audit contains only F60 UI/client/test/spec artifacts; no F59
  backend/connector, seed, migration, production DB, or unrelated rewrite.

## Open Questions

None blocking for Apply under the owner-authorized exception. Owner validation
and approval of the post-Apply browser-rendered artifact, after the mandatory
`refresh-for-test` receipt, is required before Review; the decision must be
recorded in `design.md`. Endpoint names, lifecycle values, preview keys, manual
commit boundary, and Família semantics are fixed by F59 and this dossier.

## Owner visual-validation revision — 2026-08-22

### Code map and current boundary

- `src/omaha/templates/_patrimonio_actions.html::section[data-testid="patrimonio-actions"]`
  currently renders real-profile controls in `Importar CSV`, `Atualizar
  posição`, `Novo ativo`, `Nova classe` order. It binds the sync store and
  renders `p[data-testid="dashboard-sync-status"]` inline. Revision target:
  `Atualizar posição` immediately left of `Importar CSV`, with a notification
  outlet replacing that paragraph.
- `src/omaha/templates/_patrimonio_add_asset_modal.html::Alpine.store('patrimonioSync')`
  currently stores lifecycle copy in `message`, including the three owner-
  identified strings, and applies `patrimonio-actions--sync-success` until a
  later action or page lifecycle changes it.
- `src/omaha/templates/_patrimonio_add_asset_modal.html::Alpine.store('importModal')`
  currently calls `resetState()` from `closeModal()` and opens a preview through
  `openPreview(data)`. Neither function currently records whether preview came
  from manual upload or F59 sync; this is the cancel-reset seam.
- `src/omaha/static/app.css::.btn`, `.patrimonio-actions`,
  `.patrimonio-action-btn`, and `.patrimonio-sync-btn` currently provide shared
  button typography/padding/border/radius plus a sync-only `min-width` and
  success highlight. The revision removes sync-only geometry and makes state
  styling obey shared button vocabulary.
- `src/omaha/static/app.css::.modal-overlay` is `z-index: 1000`; notification
  cards must remain below it while visible and must not cover the review modal.
- `tests/e2e/test_patrimonio_sync_action.py` currently asserts inline status
  text and success styling. `tests/e2e/test_import_modal.py` is the regression
  boundary for manual review/cancel. `tests/e2e/selectors.py` is the central
  selector inventory and must own any new notification/close selectors.
- `openspec/specs/iconography-tokens/spec.md` and `DESIGN.md §Iconography`
  currently catalog 11 Material Symbols Outlined ligatures and reject new
  names without a change. F60's delta adds one catalog entry: `sync`.

### Revised input → transformation → output flow

1. Server renders action controls. Real profile renders sync then import in one
   `.patrimonio-actions` flex row; Família keeps only its disabled/read-only
   sync control and does not render a notification outlet with sync behavior.
2. Alpine initializes one notification card with exact idle copy. Card lives
   in a fixed bottom-corner live region, starts an 8,000 ms timer, and exposes
   a manual close control. Closing or expiry removes card only; it does not
   alter the action state unless it is the sync-origin review reset.
3. Start changes action state to `loading`, sets `aria-busy="true"`, disables
   activation, and replaces lifecycle card copy with exact loading copy. The
   card timer is paused while hovered or focused; polling remains bounded and
   visible through button state even if card is manually closed.
4. Safe start/poll/terminal errors replace current card with safe PT-BR error
   card. Raw credentials, paths, exceptions, CSV bytes, URLs, and F59 detail
   remain excluded.
5. Valid success replaces card with exact success copy, keeps success styling
   only while sync-origin review is open, then calls existing `openPreview`
   without commit or navigation.
6. `Cancelar` in the existing review modal calls existing reset behavior and,
   only for `previewOrigin === 'patrimonio-sync'`, invokes
   `patrimonioSync.resetAfterReview()`. That method cancels timers, removes
   success notification, sets state to `idle`, clears `aria-busy`, and removes
   success/highlight classes. Manual upload close never calls it.

### Implementation decisions

1. **Order and parity.** Render sync before import in source order and visual
   order. Use the same `btn patrimonio-action-btn` class and the existing
   shared button values: Inter/inherited `font: inherit`, `0.85rem`, weight
   `500`, `0.4rem 0.75rem` padding, `6px` radius, 1px border, shared
   `align-items: center`, hover, `:focus-visible`, and disabled language. Remove
   `.patrimonio-sync-btn { min-width: 10.5rem; }`; keep only behavior/state
   hooks. Acceptance compares computed font family/size/weight/line-height,
   height, padding, border, radius, baseline alignment, and focus ring against
   `dashboard-import-btn`; content-driven width may differ because labels
   differ, but no sync-only dimension is allowed.
2. **Icon selection.** Use `<span class="icon icon--md" aria-hidden="true">sync</span>`.
   `sync` is semantically correct because action starts a profile-scoped
   synchronization and delivers refreshed positions for review; `refresh`
   would imply page/cache reload. Exact source is the existing Material Symbols
   Outlined Google Fonts ligature system loaded by
   `https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined`.
   Icon inherits button `currentColor`, remains 20px, and sits immediately
   before `Atualizar posição`. Add `sync` to the catalog through this F60
   delta; Apply must update the stable icon catalog/design assertion as part of
   this directly affected contract, not introduce an ad-hoc SVG or emoji.
3. **Notification outlet.** Render one Alpine-managed outlet with
   `data-testid="patrimonio-notifications"` and cards with stable IDs. Place
   it at `inset-inline-end: 1rem; inset-block-end: 1rem`, width
   `min(24rem, calc(100vw - 2rem))`, above page content but below modal
   (`z-index: 900`). On screens up to 480px use `0.75rem` edges and
   `calc(100vw - 1.5rem)`. Cards stack newest first with 8px gap, max three;
   inserting a fourth removes oldest. Current F60 lifecycle emits one active
   card at a time by replacing prior lifecycle copy, preventing idle/loading/
   success duplication.
4. **Accessible timing and focus.** Every card auto-dismisses after exactly
   8,000 ms from insertion. Timer pauses on `:hover`, `:focus-within`, and
   hidden-document state; a focused card never disappears until focus leaves.
   Each card has a `type="button"` close control with accessible name
   `Fechar notificação`, shared visible focus ring, and at least 24px target;
   no notification steals focus. Status/loading/success use `role="status"`
   and `aria-live="polite"`; safe error uses `role="alert"` and
   `aria-live="assertive"`; `aria-atomic="true"` ensures whole-copy
   announcement. On sync-origin modal open, focus moves into the existing
   review modal; on `Cancelar`, focus returns to `dashboard-sync-btn` when it
   remains available. Manual close/expiry does not move focus.
5. **Cancel reset.** Carry a source marker only for `openPreview(preview,
   'patrimonio-sync')`. `closeModal()` handles both `Cancelar` and existing
   close control, resets source marker, and invokes sync reset only for that
   marker. No green/highlighted class, success data state, success notification,
   or `aria-busy` may remain after cancel. Existing manual upload preview and
   explicit `/api/import/commit` remain unchanged.
6. **Notification ownership.** Keep lifecycle cards in the existing
   `patrimonioSync` Alpine store rather than adding a global toast dependency.
   Store owns exact 8,000 ms timers, hover/focus/document-visibility pauses,
   max-three bounded retention, role/live-region mapping, and manual close;
   template owns only outlet/card semantics. This preserves one F60 boundary
   and lets sync-origin cancellation clear all transient presentation.
   Evidence: the action partial has no `dashboard-sync-status` paragraph and
   focused rendered-contract/iconography tests passed after the revision.
7. **Sibling geometry.** Remove `.patrimonio-sync-btn` minimum width and leave
   button geometry to shared `.btn`/`.patrimonio-action-btn` rules. State color
   modifiers remain limited to loading/success/error semantics; success is
   removed by `resetAfterReview()` after sync-origin modal close. Evidence:
   static CSS inspection plus rendered action order/icon/state assertions.

### Revised change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `_patrimonio_actions.html::patrimonio-actions` | Import then sync; inline `p` status; sync has no icon | Sync immediately left of import; `sync` Material Symbols icon; notification outlet replaces inline status; shared sibling markup | Owner-required order, icon source, and visual parity |
| `_patrimonio_add_asset_modal.html::patrimonioSync` | `message` owns inline lifecycle strings; success style persists until unrelated reset | Notification store/outlet owns lifecycle cards and timers; state remains observable; `resetAfterReview()` clears success presentation | Remove page-inline copy and prevent persistent green style |
| `_patrimonio_add_asset_modal.html::importModal` | `openPreview`/`closeModal` have no origin marker | Sync-origin preview marker; Cancelar/close invokes scoped sync reset and returns focus | Preserve manual modal path while fixing sync cancel |
| `app.css::.patrimonio-actions`, `.patrimonio-sync-btn`, new notification selectors | Sync-only `min-width`, success green highlight, no card styles | Shared button geometry/state language; transient success; fixed bottom-corner cards with responsive stack/focus styles | Match sibling actions and accessible notification behavior |
| `tests/e2e/selectors.py` | No notification selectors | Central selectors for outlet/card/close and any cancel assertion | Keep selector-pinning contract |
| `tests/e2e/test_patrimonio_sync_action.py` | Asserts inline strings and success state only | Asserts exact card copy, icon/order, 8s/paused/manual close behavior, parity hooks, and no success styling after Cancelar | Independent browser oracle for owner feedback |
| `tests/e2e/test_import_modal.py` | Manual review/cancel regression only | Add sync-origin programmatic handoff cancel regression without changing manual semantics | Prove source-scoped reset |
| `openspec/changes/f60.../specs/iconography-tokens/spec.md` | No F60 icon delta | Add `sync` catalog requirement and ligature/source scenario | Stable icon contract currently rejects out-of-catalog names |

### Explicit non-goals and preserved invariants

- No F59 route/job/connector/backend change, no F59 test change, no navigation,
  no retry policy expansion, no alternative modal, no auto-commit, no seed,
  migration, asset/position mutation, production DB, or Família enablement.
- No global toast framework, external dependency, page-wide notification
  rewrite, or change to unrelated inline errors. F60 owns one bounded outlet.
- Existing manual import's source-less `openPreview`, `closeModal`, assignment
  hydration, explicit confirmation, and reload-after-commit remain authoritative.
- Família remains native-disabled/read-only; no sync request, poll, modal, or
  sync notification is emitted from Família.

## Execution Evidence

Apply completed implementation and focused validation. `tests/e2e/test_patrimonio_sync_action.py`
now owns seven intercepted-F59 browser scenarios: state markers, queued → running
→ succeeded review handoff, duplicate suppression, failed/expired/malformed
terminal states, and Família disabled behavior. It emits the required artifact
plus loading/error/Família supplements under `tests/visual/artifacts/`.

Validation receipts:

- `uv run task test-file tests/test_patrimonio_sync_action.py tests/test_rebalance_page.py`
  → 30 passed, 12 solver warnings.
- `T29_RUN_ID=f60-e2e-run-20260822-04 T29_DB_RECEIPT_LANE=e2e uv run task test-file tests/e2e/test_patrimonio_sync_action.py`
  → 7 passed in 27.72s.
- `T29_RUN_ID=f60-visual-verify-20260822-01 T29_DB_RECEIPT_LANE=visual uv run task test-visual`
  → 8 passed, 12 deselected in 54.82s.
- `uv run task lint` → all hooks passed.
- `rtk git diff --check` → passed.
- Exact change validation → 1 passed; stable-spec validation → 71 passed,
  informational long-requirement notices only.

Artifact checksums:

| Artifact | SHA-256 |
|---|---|
| `tests/visual/artifacts/f60-atualizar-posicao-patrimonio.png` | `5fc286fb1da05df200d26b469aa34558478f52ba76a3784d8b3948ff35da6756` |
| `tests/visual/artifacts/f60-atualizar-posicao-loading.png` | `f9de0ce85df430ba5db9144f762dacdc14a707d9199497b390d8c99bf206181a` |
| `tests/visual/artifacts/f60-atualizar-posicao-error.png` | `3036237a96ca0c8caf9af586058fbc0b4bd5681337b7f68ba07c6ef64f70ea5d` |
| `tests/visual/artifacts/f60-atualizar-posicao-family.png` | `6791f3c9444bb9bae80ca974105721e96e4bb08c2b47f17a8c87dfe87b8ce950` |

Refresh preflight used `bash scripts/print_lan_url.sh` and obtained
`http://192.168.1.4:8000`; read-only `/healthz` succeeded. Current local DB was
left untouched at `11 classes / 89 assets / 88 positions`. Required restart was
blocked safely: PID `893`, PGID `893` was pre-existing/foreign, running from
`/app` as `fastapi ... src/omaha/main.py` on port `8000`. Ownership protocol
forbids killing or adopting it. Isolated e2e/visual runners used owned ports
`8765`/`8768` and exact current-run test DB paths, all cleaned with receipts.

Owner visual approval is intentionally absent. Review, `Applied`, archive, and
commit remain blocked until owner confirms artifact checksums and all required
states after a valid current-source LAN refresh.

### Delivery-only follow-up — owner-authorized Compose stop and current-source refresh — 2026-08-22

- Context: prior refresh was blocked by a foreign listener. Owner then
  authorized exactly `docker compose -f docker-compose.yml stop web`, limited
  to this repository's `web` service/container `omaha-web-1`, to release TCP
  8000. No other service or resource operation was authorized.
- Decision: reconfirm Compose project `omaha`, working directory
  `/home/juca/github/omaha`, service `web`, container `omaha-web-1`, and its
  `8000:8000` publication before issuing the exact stop. After successful
  stop and bounded port-release verification, launch only current source with
  LAN bind `0.0.0.0:8000`; preserve runtime for owner visual validation.
- Impact: no source/test rerun, F59/backend/connector change, external sync,
  full suite, destructive reset, production DB operation, Compose removal, or
  other service stop. Existing browser artifacts remain owner-validation
  evidence; Review/archive/commit remain blocked.
- Evidence: Compose config resolved only `web`; inspect resolved container ID
  `63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028` and repo
  cwd. Exact stop returned success; container exited 0; post-stop `ss` had no
  TCP 8000 listener. Current-source PID `115075`/PGID `115072` serves from
  `/home/juca/github/omaha`; LAN receipt returned healthy health, authenticated
  session redirect, seeded dashboard, and F60 action markup. Exact ownership
  ledger and bounded temporary cleanup are recorded in `tasks.md`.
- Owner decision: visual approval still pending. Owner must validate the
  listed artifact checksums and all F60 checklist items before Review.

### Delivery-only follow-up — SIGKILL registration — 2026-08-22

Run `f60-refresh-followup-20260822-02` registered at
`2026-08-22T10:15:34-03:00`. Owner authorization is limited to one exact
`SIGKILL` for PID `893`, contingent on immediate reconfirmation of the known
`/app/.venv/bin/fastapi run --host 0.0.0.0 --port 8000 src/omaha/main.py`
identity, PGID/SID `893`, cwd `/app`, and port-8000 ownership. No group,
parent/child, process-name, or broad port cleanup is permitted. Refresh and
browser evidence will use only current `/home/juca/github/omaha` source after
port release; no source/test rerun or destructive DB operation is part of this
follow-up.

### Delivery-only follow-up — safe stop — 2026-08-22

At `2026-08-22T10:16:29-03:00`, immediate reconfirmation found PID `893`
absent: no `ps` command, PGID/SID, or cwd. TCP `8000` remained listening on
`0.0.0.0` and `[::]`, but `ss -ltnp 'sport = :8000'` exposed no `pid=893`;
the bounded `fuser -v 8000/tcp` observation exposed no owner at
`2026-08-22T10:16:40-03:00`. Identity changed/vanished before action, so exact
`kill -KILL 893` was **not issued**. No other PID, group, parent/child, or port
operation was attempted. Refresh-for-test and browser evidence were correctly
not launched. Result: `BLOCKED_FOREIGN_RESOURCE`; owner decision required:
provide isolated runner/environment with TCP `8000` free, without authorizing
new host cleanup.

### Delivery-only follow-up — 2026-08-22

Owner authorized terminating only confirmed foreign listener PID 893 rooted at
`/app` on port 8000. Exact pre-termination evidence recorded before action:
`ps` showed `/app/.venv/bin/python /app/.venv/bin/fastapi run --host 0.0.0.0
--port 8000 src/omaha/main.py`, cwd `/app`, PGID/SID 893; `/proc/893/net/tcp`
showed `0.0.0.0:1F40` LISTEN inode `8759`, and PID 893 fd 12 held
`socket:[8759]`. No broad process, process-group, or port discovery/cleanup was
performed.

Bounded action `kill -TERM 893` returned exit code 0 at
`2026-08-22T10:12:18-03:00`, but exact `kill -0 893` one second later
succeeded and `ps` still reported PID 893 in `Dsl` state with the same command.
No retry, `SIGKILL`, group termination, port cleanup, adoption, or refresh was
attempted. Current-source LAN receipt and browser visual evidence remain
blocked; follow-up result is `BLOCKED_FOREIGN_RESOURCE`. Full ownership ledger
and cleanup result live in `tasks.md` under `Delivery-only follow-up
pre-termination ledger`.

### Delivery-only follow-up — owner-authorized PID retry — 2026-08-22

- Context: R42 startup correction is now present, and owner authorization
  covers only prior F60-owned PID `115075` after immediate identity
  reconfirmation. The retry is delivery-only; no runtime/test source changes
  or F59 connector activity are authorized.
- Decision: verify PID `115075` command, cwd, LAN bind, and exact TCP `8000`
  listener ownership first. If all match, send one `SIGTERM` to that PID only,
  verify PID absence and port release, then launch current `/home/juca/omaha`
  source with `0.0.0.0:8000` for the mandatory refresh receipt. Never act on a
  process group, process name, or port without exact ownership evidence.
- Impact: refresh may preserve only current-run server for owner visual
  validation; no DB reset, production mutation, E2E/Playwright/browser test,
  MyProfit sync, review, archive, commit, or push.
- Evidence: precheck at `2026-08-22T11:41:37-03:00` matched PID `115075`,
  cwd `/home/juca/github/omaha`, command
  `/home/juca/github/omaha/.venv/bin/python /home/juca/github/omaha/.venv/bin/uvicorn
  omaha.main:app --host 0.0.0.0 --port 8000`, and `0.0.0.0:8000` listener.
  Exact `kill -TERM 115075` returned `0` at `2026-08-22T11:41:45-03:00`;
  bounded verification at `2026-08-22T11:41:46-03:00` found PID absent and no
  TCP `8000` listener.

### Current-source delivery receipt — owner visual validation pending

- Refresh run `f60-current-source-refresh-20260822-02` now serves current
  `/home/juca/github/omaha` source at LAN URL `http://192.168.1.4:8000`.
  PID `135793`, PGID/SID `135789` (observed only), exact LAN bind
  `0.0.0.0:8000`; server log is
  `/tmp/f60-current-source-refresh-20260822-02-uvicorn.log`.
- Read-only smoke passed: health `200`/`ok`, login `303`, profile select `303`,
  dashboard `200`, Família select `303`, Família dashboard `200`, profile
  restored `303`; DB remained `11 classes / 89 assets / 88 positions`, with
  seeded `RF Din` marker count `5`. No DB reset, destructive route, MyProfit
  sync, browser automation, or auto-commit occurred.
- New current-source receipt artifact is
  `tests/visual/artifacts/f60-current-source-refresh-20260822-02-receipt.json`,
  SHA-256
  `7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949`.
  Current HTML/CSS evidence records sync-before-import order, `sync` ligature,
  shared action class and geometry hooks, notification outlet/lifecycle cards,
  and Família disabled/read-only markup. Existing state supplements remain
  checksum-verified in `tests/visual/artifacts/` for dashboard, loading, error,
  and Família states.
- Before the owner decision recorded below, visual approval remained required
  for button order, icon, style parity, toast cards,
  idle/loading/success/error/disabled states, Família treatment, safe errors,
  no navigation, review handoff, and Cancelar reset. This historical gate is
  now satisfied; Review is next.

## Owner visual approval — 2026-08-22

- Owner decision: **`F60 approved`**, reported after live browser validation at
  the current-source refresh URL `http://192.168.1.4:8000`.
- Current-source receipt:
  `tests/visual/artifacts/f60-current-source-refresh-20260822-02-receipt.json`
  (SHA-256
  `7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949`).
- Approved checklist:
  - `Atualizar posição` appears immediately left of `Importar CSV`, with the
    `sync` icon and sibling action order preserved.
  - Sync action typography, dimensions, alignment, icon treatment, and state
    style match `Importar CSV`.
  - Idle/loading/success/error/disabled feedback uses notification cards with
    safe lifecycle/error presentation.
  - `Cancelar`/review close resets sync success styling, notification, and
    transient action state.
  - Família keeps `Atualizar posição` visible but disabled/read-only.
  - Successful sync hands off to the existing review window; no navigation and
    no automatic commit occur.
- Owner-approval gate is satisfied. **Review is next gate**; no `Applied`,
  archive, commit, or push decision is recorded here.

## Implementation Decisions — R1 remediation

### Lifecycle replacement overrides interaction retention

- Context: Review R1 found `showNotification()` retained hovered, focused, or
  visibility-paused cards, so an interacted idle/loading card could block the
  next lifecycle card or leave stale copy beside success/error feedback.
- Decision: `showNotification()` calls the existing `removeAllNotifications()`
  before inserting every new lifecycle card. That method cancels each prior
  timer and removes each prior card, including interacted cards. The ordinary
  `dismissNotification(id)` path remains non-forcing for focused cards, so a
  focused card still cannot disappear from timeout/manual dismissal when no
  newer lifecycle event replaces it.
- Impact: F60 lifecycle replacement is always single-card and starts a fresh
  8-second timer; no global toast or manual-import behavior changes.
- Evidence: R1-F01 review lines 732–752 and focused local browser acceptance
  covering focused/hovered idle/loading replacement, success/error roles, and
  ordinary focused-card dismissal protection.
