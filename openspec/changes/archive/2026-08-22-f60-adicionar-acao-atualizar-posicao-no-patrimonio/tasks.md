## 1. Owner visual gate after Apply, before Review

- [x] 1.1 After implementation, invoke mandatory `refresh-for-test`, preserve
  its delivery receipt, and produce browser-rendered evidence at
  `tests/visual/artifacts/f60-atualizar-posicao-patrimonio.png` using seeded
  dashboard data and intercepted F59 responses. Render `Atualizar posição`
  immediately left of `Importar CSV`, `sync` icon, identical sibling button
  typography/dimensions/alignment/state language, bottom-corner notification
  cards, idle/loading/success/error/disabled states, Família disabled/read-only,
  safe errors, no navigation, review-modal handoff, and no green/highlighted
  sync styling after `Cancelar`. Preserve F59 visual contract, no alternate
  modal, and no auto-commit.
  Acceptance: receipt, artifact path/checksum, and explicit owner validation/
  approval are recorded in `design.md` after Apply and before Review; missing
  receipt, artifact, approval, or any requested visual state blocks Review,
  `Applied`, archive, and commit. Test file/scenario: browser visual artifact
  and owner validation, not pytest. Focused taskipy command:
  `uv run task test-visual` when visual lane applies, otherwise
  `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`; mandatory
  `refresh-for-test` skill delivery is prerequisite. No Propose command.
  Independent oracle: mandatory receipt, browser-rendered artifact, and owner
  decision recorded in `design.md`.

## 2. Dashboard action markup and server-rendered state boundary

- [x] 2.1 Update `src/omaha/templates/_patrimonio_actions.html::patrimonio-actions`
  to render `Atualizar posição` with
  `data-testid="dashboard-sync-btn"` immediately left of
  `dashboard-import-btn` for real
  profiles, bind the action state component, and render the same control
  native-disabled/read-only for Família without issuing a click handler there.
  Preserve existing Importar CSV, Novo ativo, Nova classe testids, Alpine
  scope, profile-only mutation guards, and action-strip order outside the new
  pair. Acceptance: rendered real-profile HTML has adjacent labeled controls
  in sync-then-import order, with `sync` Material Symbols markup and shared
  button class hooks;
  family HTML has visible disabled sync control and no sync request binding.
  Test file/scenario: `tests/test_patrimonio_sync_action.py::test_real_profile_action_pair`
  and `::test_family_sync_action_is_disabled`; focused taskipy command:
  `uv run task test-file tests/test_patrimonio_sync_action.py`. Independent
  oracle: TestClient response HTML and attributes, not client assumptions.

- [x] 2.2 Inspect `src/omaha/templates/patrimonio.html::shell` and
  `src/omaha/routes/pages.py::_common_context` / `_render_patrimonio`; consume
  existing sanitized `myprofit_sync`/`myprofit_sync_error` context for initial
  page-safe error presentation without adding a GET query, job start, polling,
  modal open, or page navigation. Preserve R04 thin-shell includes, family
  aggregate values, `view`, and `read_only`. Acceptance: initial failed/expired
  state can render safe PT-BR feedback, Família receives no sync detail, and
  no new page-side effect exists. Test file/scenario:
  `tests/test_patrimonio_sync_action.py::test_page_renders_safe_sync_error`
  and `::test_family_page_has_no_sync_detail`; focused taskipy command:
  `uv run task test-file tests/test_patrimonio_sync_action.py`. Independent
  oracle: context/HTML contains allowlisted message only and DB job count is
  unchanged by GET.

## 3. Alpine state machine and existing review handoff

- [x] 3.1 Update directly required Alpine code in
  `src/omaha/templates/_patrimonio_add_asset_modal.html::importModal` to
  extract one shared preview hydration method from `uploadFile()` and reuse it
  for F59 `preview` payloads. The method SHALL set `previewId`, rows, classes,
  assignments, and review step using existing manual-upload rules; success
  SHALL open existing `import-modal-overlay` only after validating all four
  preview keys. Preserve dynamic-select `x-init`/`x-effect`, trade flags,
  manual assignment, `commit()`, and reset/close behavior. Acceptance: manual
  upload and programmatic handoff render identical step-2 data and no commit
  request occurs during hydration. Test file/scenario:
  `tests/e2e/test_patrimonio_sync_action.py::test_success_reuses_existing_review`
  and `tests/e2e/test_import_modal.py` manual-review regression; focused
  taskipy command: `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: modal DOM rows/assignments and intercepted request log.

- [x] 3.2 Add the scoped Patrimônio sync action state machine in the existing
  Alpine boundary (exact component/store symbol recorded in implementation
  diff): `idle` → start POST → `loading` with disabled button and visible live
  status → bounded GET polling → `success` or `error`; stop polling on
  `succeeded`, `failed`, `expired`, malformed success, start error, or poll
  error. Preserve current URL, prevent duplicate starts, show safe PT-BR copy,
  and never call `/api/import/commit`. Acceptance: each state has stable
  state class/attribute plus accessible text and exactly one active poll at a
  time. Test file/scenario:
  `tests/e2e/test_patrimonio_sync_action.py::test_start_and_poll_without_navigation`,
  `::test_loading_blocks_duplicate_click`, `::test_failed_job_keeps_modal_closed`,
  `::test_expired_job_keeps_modal_closed`, and
  `::test_malformed_success_is_error`; focused taskipy command:
  `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: Playwright route interception, URL history, visible
  state markers, and request sequence.

## 4. Token-based visual states

- [x] 4.1 Update `src/omaha/static/app.css::.patrimonio-actions`,
  `.patrimonio-action-btn`, and new sync-state modifiers for idle/loading/
  success/error/disabled/read-only presentation. Preserve existing design
  tokens, focus-visible ring, generic `.btn:disabled` semantics, responsive
  wrapping, action hierarchy, WCAG AA contrast, and unrelated table/modal CSS.
  Acceptance: desktop keeps sync immediately left of Importar CSV; sync and
  import have identical computed typography, height/padding/border/radius and
  alignment; mobile wraps without clipping; each state is visually distinct;
  success styling is removed after review Cancelar; Família looks
  disabled/read-only.
  Test file/scenario: owner-approved artifact plus
  `tests/e2e/test_patrimonio_sync_action.py::test_state_markers_render`; focused
  taskipy command: `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: browser computed styles/box geometry and the exact visual
  artifact approved in task 1.

## 5. F59 contract pinning and focused server tests

- [x] 5.1 Add `tests/test_patrimonio_sync_action.py` coverage against
  `src/omaha/routes/imports.py::_require_sync_profile`,
  `start_myprofit_sync`, `get_myprofit_sync_status`, and
  `_build_preview_response` without changing those F59 implementations.
  Assert `202` start shape, exact poll URL/status/preview keys, safe failure
  payload, no auto-commit/asset/position mutation, and Família `409
  household_read_only` before lookup. Preserve F59 focused test boundary: no
  connector, browser, credential, network, external service, or production DB.
  Acceptance: F60 client assumptions are pinned to F59's existing contract and
  direct server behavior remains green. Test file/scenario:
  `tests/test_patrimonio_sync_action.py::test_f59_start_contract`,
  `::test_f59_success_preview_shape`, `::test_f59_failure_is_page_safe`, and
  `::test_family_sync_boundary`; focused taskipy command:
  `uv run task test-file tests/test_patrimonio_sync_action.py`. Independent
  oracle: JSON response bodies, status codes, and before/after mutation counts.

- [x] 5.2 Update `tests/conftest.py::_INTEGRATION_PREFIXES` only if the new
  `tests/test_patrimonio_sync_action.py` uses DB/TestClient and is not already
  explicitly classified. Preserve all existing marker assignments and do not
  use pattern matching. Acceptance: collection assigns the new file to the
  intended integration lane with no `UnknownTestPath` warning. Test
  file/scenario: collection of `tests/test_patrimonio_sync_action.py`; focused
  taskipy command: `uv run task test-file tests/test_patrimonio_sync_action.py`.
  Independent oracle: pytest marker collection output and the explicit list in
  `tests/conftest.py`.

## 6. Browser workflow and visual acceptance evidence

- [x] 6.1 Add `tests/e2e/test_patrimonio_sync_action.py` using intercepted F59
  start/status responses and existing auth/browser fixtures. Cover real-profile
  idle/loading/success/error, queued→running→succeeded handoff, failed and
  expired no-modal behavior, start/poll HTTP errors, malformed success,
  duplicate-click suppression, unchanged URL, zero auto-commit requests, and
  Família disabled control with zero client requests. Preserve external-service
  exclusion and existing manual import journey. Acceptance: all required
  browser scenarios pass with deterministic route fixtures. Test
  file/scenario: every named scenario in this task. Focused taskipy command:
  `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: Playwright request interception/history plus DOM
  `data-testid`/state markers and modal visibility.

- [x] 6.2 Produce or verify owner-approved browser-rendered artifact at the exact
  path from task 1 after implementation and the mandatory `refresh-for-test`
  receipt, then record visual evidence in this change dossier: action
  adjacency, hierarchy, idle/loading/success/error/disabled states, Família
  disabled/read-only, safe error copy, no navigation, no alternate modal, and
  existing review-window handoff. Preserve approved layout unless a new owner
  decision is recorded.
  Acceptance: artifact path/checksum and refresh receipt exist, capture all
  required real/Família states, and owner approval is explicit after Apply and
  before Review. Review, `Applied`, archive, and commit remain blocked until
  approval is recorded in `design.md`. Test file/scenario:
  `tests/visual/test_snapshots.py` extension or static artifact inspection;
  focused taskipy command: `uv run task test-visual` when visual lane is
  applicable, otherwise `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: owner visual decision, artifact checksum/path, and
  refresh-for-test receipt, not subjective agent judgment.

## 7. Focused validation and acceptance handoff

- [x] 7.1 Run F60 focused tests and lint after implementation: preserve all
  existing tests, no skip/xfail/retry masking, no connector/live service, no
  production DB, and no F59 backend changes. Acceptance: focused server and
  browser scenarios, relevant import-modal regressions, and lint pass; changed
  file list is F60-only. Test files: `tests/test_patrimonio_sync_action.py`,
  `tests/test_rebalance_page.py`, `tests/e2e/test_patrimonio_sync_action.py`,
  `tests/e2e/test_import_modal.py`. Focused taskipy commands:
  `uv run task test-file tests/test_patrimonio_sync_action.py`,
  `uv run task test-file tests/test_rebalance_page.py`,
  `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`,
  `uv run task test-file tests/e2e/test_import_modal.py`, and
  `uv run task lint`. Independent oracle: command exit codes, no masking audit,
  `git diff --check`, and changed-file audit against this dossier.

- [x] 7.2 Run exact-change and stable-spec validation for
  `f60-adicionar-acao-atualizar-posicao-no-patrimonio`; preserve roadmap and
  unrelated changes. Acceptance: exact change validates, all stable specs
  validate, required delta specs are present, and no unrelated file is added by
  F60. Test file/scenario: artifact validation, N/A product test. Focused
  taskipy command: N/A. Independent oracle:
  `openspec status --change f60-adicionar-acao-atualizar-posicao-no-patrimonio --json`,
  `openspec validate f60-adicionar-acao-atualizar-posicao-no-patrimonio --type change --strict --json`,
  `openspec validate --specs --strict --json`, and `git diff --check`.

## 8. Owner visual-feedback remediation

- [x] 8.1 Update `src/omaha/templates/_patrimonio_actions.html::patrimonio-actions`
  so real-profile source order is `dashboard-sync-btn` immediately followed by
  `dashboard-import-btn`; add `<span class="icon icon--md"
  aria-hidden="true">sync</span>` before the sync label; replace the inline
  `dashboard-sync-status` paragraph with the Alpine notification outlet.
  Preserve existing testids, Alpine scope, `Novo ativo`/`Nova classe` order,
  Família native-disabled/read-only markup, and no sync binding in Família.
  Acceptance: TestClient HTML and browser DOM prove sync is immediately left of
  import, icon token/source is exact, and no owner-identified lifecycle string
  is rendered inline. Test file/scenario:
  `tests/test_patrimonio_sync_action.py::test_real_profile_action_pair`,
  `::test_family_sync_action_is_disabled`, and
  `tests/e2e/test_patrimonio_sync_action.py::test_action_order_and_icon`.
  Focused taskipy command: `uv run task test-file tests/test_patrimonio_sync_action.py`.
  Independent oracle: rendered sibling order, exact icon ligature, testids, and
  absence of inline status node.

- [x] 8.2 Update `src/omaha/templates/_patrimonio_add_asset_modal.html::patrimonioSync`
  and its notification state boundary to emit exact lifecycle cards for
  `Pronto para atualizar posição.`, `Atualizando posição...`, and
  `Atualização concluída. Revise posições antes de confirmar`; use 8,000 ms
  auto-dismiss, hover/focus pause, manual close, safe error copy, and bounded
  polling. Preserve state markers, duplicate guard, F59 endpoint shapes,
  no-navigation behavior, Família no-request behavior, and no auto-commit.
  Acceptance: each card has stable selector, exact copy, live-region semantics,
  close button, timer pause while hovered/focused, and disappears after the
  exact duration when not interacted with; safe error strings remain allowlisted.
  Test file/scenario:
  `tests/e2e/test_patrimonio_sync_action.py::test_notification_lifecycle_and_duration`,
  `::test_notification_manual_close_and_focus_pause`, and
  `::test_failed_job_keeps_modal_closed`. Focused taskipy command:
  `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: Playwright clock/request interception, card DOM roles,
  `aria-live`, accessible close name, and safe-copy allowlist.

- [x] 8.3 Update `src/omaha/static/app.css::.patrimonio-actions`,
  `.patrimonio-action-btn`, `.patrimonio-sync-btn`, and notification selectors
  to remove sync-only `min-width`, match sibling computed typography,
  height/padding/border/radius/alignment/focus/state language, and style fixed
  bottom-corner cards at `inset-inline-end/block-end: 1rem`, `z-index: 900`,
  max width 24rem, 8px stack gap, max three cards, and mobile 0.75rem edges.
  Preserve design tokens, WCAG contrast, generic disabled semantics, modal
  `z-index: 1000`, responsive wrapping, and unrelated CSS. Acceptance:
  computed style/geometry comparison passes for sync/import; visual states show
  no persistent green after cancel; cards do not cover modal or clip on mobile.
  Test file/scenario:
  `tests/e2e/test_patrimonio_sync_action.py::test_action_visual_parity_and_notification_geometry`.
  Focused taskipy command: `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: browser computed styles, bounding boxes, stacking order,
  focus-visible ring, and screenshot diff against owner artifact.

- [x] 8.4 Update `src/omaha/templates/_patrimonio_add_asset_modal.html::importModal`
  `openPreview`/`closeModal` with a sync-origin marker and
  `patrimonioSync.resetAfterReview()` on `Cancelar` and existing close path.
  Reset notification, `success` state, highlight classes, and `aria-busy`, and
  return focus to `dashboard-sync-btn` when available. Preserve source-less
  manual import close, assignment editing, explicit `commit()`, and reload after
  commit. Acceptance: successful intercepted F59 preview opens existing review;
  clicking `Cancelar` leaves no green/highlighted sync styling or success state,
  while manual import cancellation remains unchanged. Test file/scenario:
  `tests/e2e/test_patrimonio_sync_action.py::test_cancel_clears_sync_success`
  and `tests/e2e/test_import_modal.py` manual cancel regression. Focused taskipy
  command: `uv run task test-file tests/e2e/test_patrimonio_sync_action.py tests/e2e/test_import_modal.py`.
  Independent oracle: modal visibility, action class/data-state/aria-busy,
  focus target, and intercepted request log with zero commit request.

- [x] 8.5 Update `tests/e2e/selectors.py` with notification outlet/card/close
  selectors and extend `tests/e2e/test_patrimonio_sync_action.py` with exact
  order/icon, notification timing/accessibility, parity, cancel-reset, safe
  error, no-navigation, no-auto-commit, and Família scenarios. Preserve central
  selector inventory and existing seven F60 scenarios. Acceptance: every new
  browser selector is sourced centrally and all named scenarios pass without
  live MyProfit, credentials, external network, production DB, skip, xfail, or
  retry masking. Test file/scenario: every revision scenario named in tasks
  8.1–8.4. Focused taskipy command:
  `uv run task test-file tests/e2e/test_patrimonio_sync_action.py
  tests/e2e/test_import_modal.py`. Independent oracle: selector inventory,
  request ledger, URL history, DOM/accessibility assertions, and exit code.

- [x] 8.6 Update F60 delta `specs/iconography-tokens/spec.md` and the stable
  icon catalog during Apply to register `sync` as a 12th Material Symbols
  Outlined ligature; preserve `aria-hidden`, `.icon icon--md`, inherited color,
  Google Fonts source, and extension-path guard. Acceptance: exact/stable
  OpenSpec validation accepts `sync`, no ad-hoc SVG/emoji appears, and icon
  token/source test passes. Test file/scenario:
  `tests/test_iconography_tokens.py` catalog and markup assertions. Focused
  taskipy command: `uv run task test-file tests/test_iconography_tokens.py`.
  Independent oracle: strict iconography validation, catalog text, and served
  button markup.

## 9. Revision validation and acceptance evidence

- [x] 9.1 Run revision-focused server/browser/lint checks after implementation;
  preserve F59 backend/connector, manual import, Família guard, no navigation,
  no auto-commit, no live service, no production DB, and no test masking.
  Acceptance: server/render, F60 browser, import-modal regression, iconography,
  and lint checks pass; changed-file audit contains only authorized F60 runtime,
  test, and dossier files. Test files/scenarios: tasks 8.1–8.6. Focused
  taskipy commands: `uv run task test-file tests/test_patrimonio_sync_action.py
  tests/e2e/test_patrimonio_sync_action.py tests/e2e/test_import_modal.py`,
  `uv run task test-file tests/test_iconography_tokens.py`, and
  `uv run task lint`. Independent oracle: command exit codes, request ledger,
  `git diff --check`, and F60-only changed-file audit.

- [x] 9.2 Re-run exact-change and stable-spec validation for
  `f60-adicionar-acao-atualizar-posicao-no-patrimonio` after all dossier and
  delta updates; preserve roadmap and unrelated slices. Acceptance: exact
  change strict validation passes, stable specs pass, all required delta files
  are present, and no unrelated artifact is added. Test file/scenario: OpenSpec
  artifact validation, N/A product test. Focused taskipy command: N/A.
  Independent oracle:
  `openspec validate f60-adicionar-acao-atualizar-posicao-no-patrimonio --type change --strict --json`,
  `openspec validate --specs --strict --json`, `openspec status --change
  f60-adicionar-acao-atualizar-posicao-no-patrimonio --json`, and
  `git diff --check`.

- [x] 9.3 Produce the mandatory post-Apply `refresh-for-test` receipt and
  owner-approved browser artifact after remediation, then record exact URL,
  artifact checksum, notification/card states, action order/parity/icon,
  Família disabled state, safe errors, review handoff, and Cancelar reset in
  `design.md`. Preserve proposal-only prohibition on running refresh now.
  Acceptance: receipt and owner decision exist before Review; missing receipt,
  artifact, checksum, or approval keeps F60 blocked. Test file/scenario:
  `tests/visual/artifacts/f60-atualizar-posicao-patrimonio.png` plus supplements;
  focused taskipy command: `uv run task test-visual` when visual lane applies,
  otherwise `uv run task test-file tests/e2e/test_patrimonio_sync_action.py`.
  Independent oracle: owner decision, receipt, artifact checksum, and visual
  acceptance checklist, not agent judgment.

## Test strategy

- Server/render: new `tests/test_patrimonio_sync_action.py` plus existing
  `tests/test_rebalance_page.py`; explicit integration marker only when needed.
- Browser: new F60 Playwright workflow with intercepted F59 HTTP responses and
  existing `tests/e2e/test_import_modal.py` regression coverage.
- Visual: owner-approved browser-rendered artifact is mandatory after Apply and
  before Review; mandatory `refresh-for-test` receipt plus
  browser computed-style/geometry checks verify the artifact's adjacency,
  idle/loading/success/error/disabled states, responsiveness, safe errors,
  no-navigation behavior, existing review-modal handoff, and Família
  disabled/read-only treatment.
- F59 connector, Playwright connector, credentials, external network, live
  MyProfit, seed, production DB, auto-commit, and alternative modal remain out
  of scope.
- Proposal gate runs no product tests, no lint, no browser, no server refresh,
  no DB task, and no `refresh-for-test`. Canonical `uv run task test` remains
  review-owned and is recorded as `NOT RUN — maintenance-suspended` while that
  policy is active.
- Revision strategy adds browser-only notification timing/accessibility and
  computed-style geometry checks; server tests remain limited to rendered
  order/markup and existing F59 boundary. No external service, connector,
  credential, network, production DB, or runtime refresh is used during
  Propose.

## Acceptance evidence

- Exact `dashboard-sync-btn` markup beside `dashboard-import-btn` for real
  profile in sync-then-import order, exact `sync` token/source, sibling
  typography/dimensions/alignment/state parity, and visible disabled/read-only
  control for Família.
- Start/poll request ledger with unchanged URL, visible states, terminal stop,
  duplicate suppression, safe errors, bottom-corner notification timing and
  accessibility, and zero auto-commit.
- Existing import modal DOM proves successful F59 preview hydration and manual
  assignment remains editable before explicit commit; sync-origin Cancelar
  clears success/highlighted styling and returns focus without altering manual
  import behavior.
- Mandatory `refresh-for-test` receipt and browser-rendered visual artifact exist
  at exact path; owner records approval after Apply and before Review with all
  requested visual checks. Missing approval blocks Review, `Applied`, archive,
  and commit.
- Focused taskipy results, lint, marker classification, exact/stable OpenSpec
  validation, `git diff --check`, and F60-only changed-file audit.

## Execution Evidence

### Implementation pass

- Changed F60 symbols/files:
  - `_patrimonio_actions.html::patrimonio-actions`: real-profile adjacent
    `dashboard-sync-btn`, Família disabled/read-only control, status region.
  - `_patrimonio_add_asset_modal.html::importModal`: shared
    `hydratePreview`/`buildAssignments` path and `patrimonioSync` Alpine store.
  - `app.css`: sync idle/loading/success/error/disabled/read-only tokens.
  - `tests/test_patrimonio_sync_action.py`: five server/render/F59 boundary
    tests; `tests/conftest.py`: explicit integration prefix.
  - `tests/e2e/selectors.py` and `tests/e2e/test_patrimonio_sync_action.py`:
    seven intercepted-browser scenarios and state artifacts.
  - `tests/visual/baselines/{patrimonio,import-form,import-review}-desktop.png`:
    intentional F60 action-strip visual rebaseline after initial 30px height
    mismatch; unrelated baselines restored.
- Focused validation:
  - `uv run task test-file tests/test_patrimonio_sync_action.py tests/test_rebalance_page.py`
    -> 30 passed, 12 solver warnings.
  - `T29_RUN_ID=f60-e2e-run-20260822-04 T29_DB_RECEIPT_LANE=e2e uv run task test-file tests/e2e/test_patrimonio_sync_action.py`
    -> 7 passed in 27.72s.
  - `T29_RUN_ID=f60-visual-verify-20260822-01 T29_DB_RECEIPT_LANE=visual uv run task test-visual`
    -> 8 passed, 12 deselected in 54.82s.
  - `uv run task lint` -> all hooks passed.
  - `rtk git diff --check` -> passed.
  - `rtk openspec status --change f60-adicionar-acao-atualizar-posicao-no-patrimonio --json`
    -> complete.
  - `rtk openspec validate f60-adicionar-acao-atualizar-posicao-no-patrimonio --type change --strict --json`
    -> 1 passed.
  - `rtk openspec validate --specs --strict --json` -> 71 passed; informational
    long-requirement notices only.
- Browser artifacts generated by intercepted F59 responses:
  - `tests/visual/artifacts/f60-atualizar-posicao-patrimonio.png` sha256
    `5fc286fb1da05df200d26b469aa34558478f52ba76a3784d8b3948ff35da6756`.
  - `tests/visual/artifacts/f60-atualizar-posicao-loading.png` sha256
    `f9de0ce85df430ba5db9144f762dacdc14a707d9199497b390d8c99bf206181a`.
  - `tests/visual/artifacts/f60-atualizar-posicao-error.png` sha256
    `3036237a96ca0c8caf9af586058fbc0b4bd5681337b7f68ba07c6ef64f70ea5d`.
  - `tests/visual/artifacts/f60-atualizar-posicao-family.png` sha256
    `6791f3c9444bb9bae80ca974105721e96e4bb08c2b47f17a8c87dfe87b8ce950`.

### Refresh and ownership receipt

- Run IDs: `f60-refresh-preflight-20260822-01..04`,
  `f60-refresh-smoke-20260822-01..02`, `f60-visual-run-20260822-01`,
  `f60-e2e-run-20260822-01..04`, and `f60-visual-verify-20260822-01`.
- Focused test ports `8765` and `8768`: each preflight absent, owned by its
  current run before launch, exited, and was observed free after teardown.
- Test DBs `data/test_e2e.db` and `data/test_visual.db`: each preflight absent,
  created by declared current run, then exact-path cleaned as `owned-cleaned`.
- Temporary cookies `/tmp/f60-refresh-cookie.D1ZEYI` and
  `/tmp/f60-refresh-cookie.kqqooy`: exact current-run paths cleaned;
  no unrecorded path deletion.
- LAN preflight URL from `bash scripts/print_lan_url.sh`: `http://192.168.1.4:8000`.
  `/healthz` returned `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
  Read-only local DB count was `11 classes / 89 assets / 88 positions`.
- Port `8000` remained bound by pre-existing PID `893`, PGID `893`, command
  `/app/.venv/bin/python /app/.venv/bin/fastapi run --host 0.0.0.0 --port 8000 src/omaha/main.py`,
  cwd `/app`, observed before any refresh action. Classified
  `pre-existing/foreign`; no kill, adoption, port cleanup, or DB mutation was
  attempted. Therefore no refresh delivery receipt for current `/home/juca`
  source can be claimed.

### Acceptance gate status

- [x] 1.1 owner approval recorded: mandatory refreshed current-source LAN receipt and
  explicit owner validation/approval are recorded below.
- [x] 6.2 owner approval recorded for same reason.
- Review is next gate; `Applied`, archive, commit, and push remain blocked
  pending Review.

### Delivery-only follow-up pre-termination ledger

Run ID: `f60-refresh-followup-20260822-01`; observed at
`2026-08-22T10:11:12-03:00` before termination.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID 893 | F60 follow-up / apply agent | Owner explicitly authorized termination of only confirmed foreign listener PID 893 rooted at `/app` on port 8000 in current conversation | `2026-08-22T00:04:58-03:00` (process start) | `2026-08-22T10:12:18-03:00` (TERM attempt/verification) | cleanup-attempted; still active | foreign, owner-authorized target | Exact `ps` identity before action: `/app/.venv/bin/python /app/.venv/bin/fastapi run --host 0.0.0.0 --port 8000 src/omaha/main.py`; cwd `/app`; PGID/SID 893. `/proc/893/net/tcp` mapped `0.0.0.0:1F40` LISTEN inode `8759` to PID 893 fd 12. `kill -TERM 893` returned 0, but exact `kill -0 893` one second later succeeded and `ps` reported PID 893 `Dsl` with same command. | incomplete: PID 893 did not exit; no retry, group kill, port cleanup, or foreign-resource adoption |
| port | TCP 8000 (`0.0.0.0` and `[::]`) | F60 follow-up / apply agent | Same owner authorization; exact port is sole authorized listener resource | `2026-08-22T00:04:58-03:00` (listener process start) | `2026-08-22T10:12:18-03:00` (termination verification) | active; cleanup blocked | foreign, owner-authorized target | Exact `/proc/893/net/tcp` listener row and fd mapping established before action; PID 893 remained alive after bounded TERM attempt. | incomplete: port remains occupied; no port-wide operation authorized |

Termination result: `BLOCKED_FOREIGN_RESOURCE`. Refresh-for-test was not launched because
authorized PID 893 remained active after the sole bounded `SIGTERM` attempt.

## Delivery-only follow-up SIGKILL registration

Run ID: `f60-refresh-followup-20260822-02`; registration timestamp:
`2026-08-22T10:15:34-03:00`. Owner explicitly authorizes one bounded `SIGKILL`
to already verified PID `893` only, after immediate reconfirmation of its exact
command, PGID/SID, cwd, and sole ownership of TCP port `8000`. No process-group,
parent/child, name-pattern, or broad port operation is authorized. This run owns
only its registration, bounded verification, exact PID action, refresh resources,
and evidence paths created during follow-up; foreign resources remain untouched.

### Follow-up receipt — safe stop

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID 893 | F60 follow-up / apply agent | Run registration above plus owner authorization in current conversation | `2026-08-22T00:04:58-03:00` (prior observed process start) | `2026-08-22T10:16:29-03:00` (immediate reconfirmation) | absent | foreign, owner-authorized target | Immediate exact check returned no `ps` identity, no command, no PGID/SID, and no cwd for PID 893. Reconfirmation failed before action. | idempotent no-op; `kill -KILL 893` was not issued; no signal, group action, or adoption |
| port | TCP 8000 (`0.0.0.0` and `[::]`) | F60 follow-up / apply agent | Run registration above plus owner authorization for exact port only | `2026-08-22T00:04:58-03:00` (prior listener observation) | — | active; cleanup blocked | unknown/foreign | At `2026-08-22T10:16:29-03:00`, reconfirmation saw port listener but no `pid=893`; at `2026-08-22T10:16:40-03:00`, `ss -ltnp 'sport = :8000'` still showed both listeners with no process owner, and `fuser -v 8000/tcp` showed none. | incomplete; untouched because authorized PID identity changed/vanished and listener ownership is unknown; no port cleanup |

Exact action result: `BLOCKED_FOREIGN_RESOURCE`. Reconfirmation failed because PID
893 was absent while TCP 8000 remained occupied. Exact command `kill -KILL 893`
was not issued. Refresh-for-test and browser capture were not launched.

## Delivery-only follow-up — owner-authorized Compose stop registration

Run ID: `f60-compose-refresh-20260822-01`; registration timestamp:
`2026-08-22T10:24:14-03:00`. Owner explicitly authorizes exactly
`docker compose -f docker-compose.yml stop web` for the Compose `web` service
only, to stop `omaha-web-1` and release published TCP port `8000`. No other
service, container, process group, image, network, volume, database, or data
operation is authorized. This ledger registration precedes the bounded stop.

Pre-action identity evidence:

- `docker compose -f docker-compose.yml config --services` resolved only
  `web` from `/home/juca/github/omaha/docker-compose.yml`.
- `docker compose -f docker-compose.yml ps -a web` resolved service `web` to
  `omaha-web-1`, image `omaha:dev`, healthy/running, published
  `0.0.0.0:8000->8000/tcp` and `[::]:8000->8000/tcp`.
- Docker inspection resolved `/omaha-web-1`, container ID
  `63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`,
  Compose project `omaha`, working directory `/home/juca/github/omaha`,
  service `web`, started `2026-08-22T13:12:23.650483821Z`.
- `ss -ltnp 'sport = :8000'` observed listeners on `0.0.0.0:8000` and
  `[::]:8000`; Compose inspection, not listener name, establishes ownership.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | Compose container `omaha-web-1` / ID `63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028` | F60 follow-up / apply agent | Current owner authorization for exact Compose command and service; pre-action Compose project/service/cwd identity above | `2026-08-22T13:12:23.650483821Z` | `2026-08-22T10:24:42-03:00` | exited | owned-cleaned | Exact command `docker compose -f docker-compose.yml stop web` returned success; Compose reported `omaha-web-1 Stopped`; inspect reported `state=exited`, `running=false`, exit 0 | bounded exact service stop completed; no other service/container/process operation |
| port | TCP 8000 (`0.0.0.0` and `[::]`) | F60 follow-up / apply agent | Same owner authorization; port release is sole purpose of exact `web` stop | `2026-08-22T13:12:23.650483821Z` | `2026-08-22T10:24:42-03:00` | absent | owned-cleaned | Post-stop `ss -ltnp 'sport = :8000'` returned header only; Compose inspect reported `ports={}` | exact published port released; no host-wide port cleanup |

## Current-source refresh ledger registration

Refresh run ID: `f60-current-source-refresh-20260822-01`; registration
timestamp: `2026-08-22T10:24:50-03:00`. Registration precedes creation/use of
all refresh resources. Current source is `/home/juca/github/omaha`; runtime
command is the mandatory LAN-bound `uv run uvicorn omaha.main:app --host
0.0.0.0 --port 8000`. No Compose service will be restarted.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID 115075 | F60 follow-up / apply agent | Current task authorization for mandatory refresh on current source after exact Compose stop; launch registration above | `2026-08-22T10:26:16-03:00` | — (kept active for owner visual validation) | active | owned-current-run | Exact `/proc/115075/cmdline`: `/home/juca/github/omaha/.venv/bin/python /home/juca/github/omaha/.venv/bin/uvicorn omaha.main:app --host 0.0.0.0 --port 8000`; cwd `/home/juca/github/omaha`; server log reports PID 115075 | no cleanup; runtime intentionally preserved for owner |
| process group | PGID/SID 115072 | F60 follow-up / apply agent | Same run registration and LAN-bound command | `2026-08-22T10:26:16-03:00` | — (kept active for owner visual validation) | active | owned-current-run | `ps` resolved PID 115075 to PGID/SID 115072; no group operation authorized or performed | no cleanup; no process-group action |
| port | TCP 8000 (`0.0.0.0` and `[::]`) | F60 follow-up / apply agent | Same run registration; current source owns port after pre-action Compose release | `2026-08-22T10:26:16-03:00` | — (kept active for owner visual validation) | active | owned-current-run | `ss` resolved `0.0.0.0:8000` to PID 115075; command/cwd match current source; IPv6 listener was absent for current uvicorn | no cleanup; port intentionally preserved for owner |
| log | `/tmp/f60-current-source-refresh-20260822-01-uvicorn.log` | F60 follow-up / apply agent | Exact run-declared log path registered before launch | `2026-08-22T10:26:16-03:00` | `2026-08-22T10:28:30-03:00` | exited | owned-current-run | `stat` and read receipt show current-source startup, migration, health-ready server, and quote refresh lines | preserved as exact delivery evidence; no unrecorded cleanup |
| temporary path | `/tmp/f60-current-source-refresh-20260822-01-launch.sh` | F60 follow-up / apply agent | Exact run-declared launcher path registered before creation | `2026-08-22T10:24:50-03:00` | `2026-08-22T10:28:30-03:00` | absent | owned-cleaned | Exact path existed with mode `700`, was used once, then exact cleanup verification reported absent | bounded `rm --` exact path; absent/no residue |
| temporary path | `/tmp/f60-current-source-refresh-20260822-01-cookie` | F60 follow-up / apply agent | Exact cookie path registered before creation; current task authorizes read-only LAN smoke only | `2026-08-22T10:26:28-03:00` | `2026-08-22T10:28:30-03:00` | absent | owned-cleaned | Exact cookie used for login/profile/dashboard GET smoke; exact cleanup verification reported absent | bounded `rm --` exact path; absent/no residue |

## Current-source refresh delivery receipt — owner visual validation pending

- Compose stop: exact target `web` resolved to repo service/container
  `omaha-web-1`; exact `docker compose -f docker-compose.yml stop web` returned
  success and stopped only that service. Post-stop inspect reported `exited`
  with exit 0 and no published ports.
- Port release: post-stop `ss -ltnp 'sport = :8000'` returned header only;
  TCP 8000 was released before current-source launch.
- LAN URL: `bash scripts/print_lan_url.sh` → `http://192.168.1.4:8000`.
- Current-source runtime: PID `115075`, PGID/SID `115072`, cwd
  `/home/juca/github/omaha`, exact command
  `/home/juca/github/omaha/.venv/bin/uvicorn omaha.main:app --host 0.0.0.0
  --port 8000`; `ss` confirmed listener ownership by PID 115075.
- Health: `GET /healthz` → `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- Session: `POST /login` → `303`; `POST /profiles/1/select` → `303` with
  redirect to `/`; authenticated dashboard GET → `200`.
- Dashboard: `468486` bytes; server-rendered checks found
  `dashboard-import-btn`, `dashboard-sync-btn`, adjacent import-then-sync
  order, `import-modal-overlay`, and seeded `RF Din` content.
- DB read-only receipt: `11 classes / 89 assets / 88 positions`; no reset,
  clear, seed, production DB, or destructive operation. Runtime startup
  applied existing Alembic revision `0020_myprofit_sync_jobs`; no source or
  test rerun occurred.
- Existing browser visual artifacts verified without rerunning tests:
  - `tests/visual/artifacts/f60-atualizar-posicao-patrimonio.png` —
    `5fc286fb1da05df200d26b469aa34558478f52ba76a3784d8b3948ff35da6756`
  - `tests/visual/artifacts/f60-atualizar-posicao-loading.png` —
    `f9de0ce85df430ba5db9144f762dacdc14a707d9199497b390d8c99bf206181a`
  - `tests/visual/artifacts/f60-atualizar-posicao-error.png` —
    `3036237a96ca0c8caf9af586058fbc0b4bd5681337b7f68ba07c6ef64f70ea5d`
  - `tests/visual/artifacts/f60-atualizar-posicao-family.png` —
    `6791f3c9444bb9bae80ca974105721e96e4bb08c2b47f17a8c87dfe87b8ce950`
- No owner visual approval has been recorded. Tasks 1.1 and 6.2 remain open
  pending owner confirmation of artifact checksums and checklist below.

## Revision remediation execution evidence — 2026-08-22

### Focused validation ledger registration

Run ID `f60-remediation-focused-20260822-01` registered at
`2026-08-22T11:00:50-03:00` before validation. Owner is current F60 apply
agent; `T29_RUN_ID` and `T29_DB_RECEIPT_LANE` identify all test-runner-created
processes, temporary paths, and test databases before use. No canonical full
suite is launched during Apply (`maintenance-suspended`).

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | T29-owned focused runner (PID/PGID emitted in runner receipt) | F60 remediation / apply agent | Run ID and lane registration above precede `uv run task` launch | 2026-08-22T11:00:50-03:00 | pending | registered | owned-current-run | Focused integration, e2e, visual, lint, and iconography commands use explicit taskipy entrypoints and T29 lane identity | bounded runner cleanup recorded after each command |
| test DB resource | task-declared tmp_path database(s) | F60 remediation / apply agent | T29 run/lane receipt identity above | 2026-08-22T11:00:50-03:00 | pending | registered | owned-current-run | Test fixtures declare per-run temporary DB paths; production `data/portfolio.db` is not a target | exact runner cleanup only; no production DB operation |
| port | canonical e2e/visual test port(s) declared by task runner | F60 remediation / apply agent | T29 run/lane receipt identity above | 2026-08-22T11:00:50-03:00 | pending | registered | owned-current-run | Only runner-declared exact lane ports may be used or cleaned | exact current-run cleanup only; foreign listeners untouched |
### Revision focused command results

- `T29_RUN_ID=f60-remediation-focused-20260822-01 T29_DB_RECEIPT_LANE=integration uv run task test-file tests/test_patrimonio_sync_action.py tests/test_iconography_tokens.py` → **32 passed** (latest run, 2.14s).
- `T29_RUN_ID=f60-remediation-focused-20260822-01 T29_DB_RECEIPT_LANE=integration uv run task test-file tests/test_rebalance_page.py` → **25 passed**, 12 pre-existing solver warnings (10.43s).
- `T29_RUN_ID=f60-remediation-focused-20260822-01 T29_DB_RECEIPT_LANE=lint uv run task lint` → all hooks passed; `rtk git diff --check` passed.
- `openspec validate f60-adicionar-acao-atualizar-posicao-no-patrimonio --type change --strict --json` → 1 passed; `openspec validate --specs --strict --json` → 71 passed, informational long-requirement notices only.
- `T29_RUN_ID=f60-remediation-focused-20260822-01 T29_DB_RECEIPT_LANE=e2e uv run task test-file tests/e2e/test_patrimonio_sync_action.py tests/e2e/test_import_modal.py` → **blocked at setup: 13 errors**. Runner child PID `120693`, PGID `120594`, port `8765` became free after bounded teardown. Startup failed before browser tests because pre-existing `src/omaha/main.py::_prune_snapshots_on_startup` imports missing `omaha.logging_config.get_logger`; F60 does not own `main.py`/logging or F59 runtime semantics. Exact current-run `data/test_e2e.db` was created at `2026-08-22T11:01:39-03:00` and bounded-cleaned; exact path is absent.

### Revision refresh and artifact gate

- Refresh preflight at `2026-08-22T11:00:50-03:00`: `bash scripts/print_lan_url.sh` → `http://192.168.1.4:8000`; read-only `GET /healthz` → `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- TCP `8000` remains occupied by pre-existing PID `115075`, PGID/SID `115072`, current-source `/home/juca/github/omaha/.venv/bin/uvicorn omaha.main:app`; no current-run ownership evidence exists. Refresh-for-test restart was not launched; no kill, adoption, or port cleanup performed.
- Required post-remediation refresh receipt and browser-rendered artifact were not produced. Existing prior-pass PNGs are not accepted as current-source remediation evidence. Owner visual approval remains absent.
### Temporary validation receipt ledger closure

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| temporary path | `/tmp/f60-stable-specs-20260822-01.json` | F60 remediation / apply agent | Exact path created by current-run stable-spec validation command | 2026-08-22T11:05:55-03:00 | 2026-08-22T11:06:00-03:00 | absent | owned-cleaned | `stat` confirmed exact run-created JSON receipt before cleanup; post-cleanup exact-path glob returned absent | bounded exact `rm --` succeeded; idempotent absence confirmed |
### Focused resource postflight closure

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `120693` / PGID `120594` | F60 remediation / apply agent | T29 e2e server launch event for registered run/lane | 2026-08-22T11:01:39-03:00 | 2026-08-22T11:01:40-03:00 | exited | owned-cleaned | Startup failed before browser tests on pre-existing missing `get_logger`; teardown reported port free | no retry; exact child exited |
| test DB resource | `data/test_e2e.db` | F60 remediation / apply agent | Exact e2e fixture path plus registered T29 run/lane | 2026-08-22T11:01:39-03:00 | 2026-08-22T11:02:00-03:00 | absent | owned-cleaned | `stat` confirmed current-run file; exact glob absent after cleanup | bounded exact `rm --`; production DB untouched |
| port | TCP `8765` | F60 remediation / apply agent | T29 server launch event declared exact lane port | 2026-08-22T11:01:39-03:00 | 2026-08-22T11:01:40-03:00 | absent | owned-cleaned | Teardown reported `port_free=true`; post-run `ss` showed no listener | idempotent no-op after runner teardown; no foreign action |
| child process | taskipy integration/lint children | F60 remediation / apply agent | Registered run/lane precedes each taskipy launch | 2026-08-22T11:00:50-03:00 | 2026-08-22T11:06:00-03:00 | exited | owned-cleaned | Non-browser focused commands returned zero; no child remained | runner-owned teardown complete |

## Delivery-only follow-up — owner-authorized PID retry registration

Run ID `f60-current-source-refresh-20260822-02`; registration timestamp
`2026-08-22T11:42:00-03:00`, before creation/use of refresh resources. Owner is
current F60 apply agent. Owner authorization is limited to confirmed prior F60
PID `115075`, exact current-source refresh, read-only LAN smoke, and delivery
evidence. No source/test changes, DB reset, production mutation, E2E/Playwright/
browser test, MyProfit sync, review, archive, commit, or push.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `135793` | F60 follow-up / apply agent | Run registration preceded exact launcher; log reported PID and `ps` matched command/cwd | 2026-08-22T11:43:48-03:00 | — | active | owned-current-run | `/home/juca/github/omaha/.venv/bin/python /home/juca/github/omaha/.venv/bin/uvicorn omaha.main:app --host 0.0.0.0 --port 8000`; cwd `/home/juca/github/omaha`; PID retained for owner visual validation | no cleanup; intentionally active |
| process group | PGID/SID `135789` | F60 follow-up / apply agent | Exact current-source launch observation; no group operation authorized | 2026-08-22T11:43:48-03:00 | — | active | owned-current-run | Observed parent/group of PID 135793 only; no signal or group cleanup issued | no cleanup; intentionally active |
| port | TCP 8000 (`0.0.0.0`) | F60 follow-up / apply agent | PID 135793 command/cwd and `ss` listener matched current source after prior port release | 2026-08-22T11:43:48-03:00 | — | active | owned-current-run | `ss` resolved `0.0.0.0:8000` to uvicorn PID 135793 | no cleanup; preserved for owner visual validation |
| log | `/tmp/f60-current-source-refresh-20260822-02-uvicorn.log` | F60 follow-up / apply agent | Exact run-declared path registered before launch | 2026-08-22T11:43:49-03:00 | — | active | owned-current-run | Startup, health, login/profile, dashboard, and family smoke lines recorded; log preserved | no cleanup; preserved as delivery evidence |
| temporary path | `/tmp/f60-current-source-refresh-20260822-02-launch.sh` | F60 follow-up / apply agent | Exact run-declared launcher path registered before creation | 2026-08-22T11:43:49-03:00 | 2026-08-22T11:47:14-03:00 | absent | owned-cleaned | One-shot launcher created and used once; exact post-cleanup check absent | bounded exact `rm --`; owned-cleaned |
| temporary path | `/tmp/f60-current-source-refresh-20260822-02-cookie` | F60 follow-up / apply agent | Exact run-declared cookie path registered before creation | 2026-08-22T11:44:10-03:00 | 2026-08-22T11:47:14-03:00 | absent | owned-cleaned | Read-only login/profile/dashboard smoke cookie; exact post-cleanup check absent | bounded exact `rm --`; owned-cleaned |
| temporary path | `/tmp/f60-current-source-refresh-20260822-02-dashboard.html` | F60 follow-up / apply agent | Observed after smoke command; no pre-use registration was recorded | 2026-08-22T11:43:49-03:00 | — | preserved | unknown / preserved-non-target | Dashboard response was written by smoke command outside declared receipt paths; no cleanup or adoption is permitted | preserved; no deletion of unrecorded path |
| artifact | `tests/visual/artifacts/f60-current-source-refresh-20260822-02-receipt.json` | F60 follow-up / apply agent | Exact artifact path registered before capture; current-source server PID and LAN smoke are run-owned | 2026-08-22T11:46:14-03:00 | 2026-08-22T11:47:14-03:00 | active | owned-current-run | Current-source markup/CSS evidence, smoke receipt, and visual supplement checksums; SHA-256 `7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949` | preserved as owner-validation evidence |

## Execution Evidence — owner-authorized runtime retry

- PID precheck at `2026-08-22T11:41:37-03:00` matched PID `115075`, cwd
  `/home/juca/github/omaha`, exact current-source uvicorn command, and
  `0.0.0.0:8000` listener ownership. Owner-authorized exact `kill -TERM 115075`
  returned exit `0` at `2026-08-22T11:41:45-03:00`; postcheck at
  `2026-08-22T11:41:46-03:00` found PID absent and port released. No process
  group, parent/child, name-pattern, or broad port action occurred.
- Mandatory current-source refresh run
  `f60-current-source-refresh-20260822-02` launched PID `135793` from
  `/home/juca/github/omaha` with `--host 0.0.0.0 --port 8000`; PGID/SID `135789`
  was observed only. Server log:
  `/tmp/f60-current-source-refresh-20260822-02-uvicorn.log`.
- LAN receipt: `bash scripts/print_lan_url.sh` → `http://192.168.1.4:8000`;
  `GET /healthz` returned `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`;
  login `303`; profile select `303`; profile dashboard `200`; Família select
  `303`; Família dashboard `200`; profile restored with `303`. Read-only DB
  counts: `11 classes / 89 assets / 88 positions`; seeded dashboard marker
  count `5`. No reset, migration command, production mutation, or destructive
  operation ran.
- New receipt artifact:
  `tests/visual/artifacts/f60-current-source-refresh-20260822-02-receipt.json`
  SHA-256
  `7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949`.
  It records current-source URL/PID/health/login/profile/dashboard/Família
  evidence, sync-before-import order, `sync` icon, shared button/CSS parity
  hooks, notification outlet/lifecycle/close semantics, Família read-only
  markup, no browser automation, no MyProfit call, and no auto-commit.
- Visual supplement checksums verified from existing intercepted-state
  captures: dashboard
  `5fc286fb1da05df200d26b469aa34558478f52ba76a3784d8b3948ff35da6756`;
  loading `f9de0ce85df430ba5db9144f762dacdc14a707d9199497b390d8c99bf206181a`;
  error `3036237a96ca0c8caf9af586058fbc0b4bd5681337b7f68ba07c6ef64f70ea5d`;
  Família `6791f3c9444bb9bae80ca974105721e96e4bb08c2b47f17a8c87dfe87b8ce950`.
- Exact cleanup: launcher and cookie paths ended absent and classified
  `owned-cleaned`; current PID/port/log remain `owned-current-run` and active
  for owner visual validation. Unregistered dashboard HTML path is preserved
  as `unknown/preserved-non-target`; no deletion or adoption performed.
- At this pre-approval checkpoint, tasks `1.1`, `6.2`, and `9.3` remained open
  pending owner visual validation; `9.1` remains open because this
  owner-authorized delivery retry explicitly
  forbade E2E/Playwright/browser test reruns and existing focused evidence was
  declared valid. No source or test files changed in this pass.

## Owner validation approval — 2026-08-22

- Owner explicitly reported: **`F60 approved`** after live browser validation at
  current refresh URL `http://192.168.1.4:8000`.
- Linked receipt/checksum:
  `tests/visual/artifacts/f60-current-source-refresh-20260822-02-receipt.json`
  — SHA-256
  `7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949`.
- Exact approved checklist:
  - action order: `Atualizar posição` immediately left of `Importar CSV`;
  - `sync` icon and action typography/style parity with `Importar CSV`;
  - lifecycle notification cards for idle/loading/success/error/disabled
    states, with safe error presentation;
  - `Cancelar`/review close resets success styling, notification, and transient
    sync state;
  - Família action remains visible and disabled/read-only;
  - successful handoff opens existing review, with no navigation and no
    automatic commit.
- Owner-approval tasks completed in this pass: `1.1`, `6.2`, `9.3`, and their
  duplicate open-gate reminders. Task `9.1` remains open because this
  evidence-only pass ran no tests or browser checks.
- **Review is next gate.** No application/test artifacts changed; no archive,
  commit, or push performed.

## Review Findings

### Review R1
Scope audit: requirements/scenarios — finding (notification replacement),
otherwise pass; task completion — finding (`9.1` remains unchecked); design
decisions and changed symbols — pass except notification replacement behavior;
preserved manual-import/Família/no-navigation/no-auto-commit boundaries — pass;
owner visual approval and receipt checksum — pass; exact-change validation and
stable-spec validation — pass; focused browser acceptance after R42 — not
assessable; out-of-scope connector, Playwright/browser, network, credentials,
production DB, refresh, archive, commit, push, and roadmap operations — pass
(not run).

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**; no
elapsed time, lane result, coverage, skips, fail-fast, or 300-second
classification applies. Owner lean-validation policy forbids launching it.
Focused evidence: recorded prior server/iconography checks `32 passed`,
rebalance checks `25 passed`, lint/diff-check green, exact change `1 passed`,
stable specs `71 passed`; prior revision e2e command stopped at setup with 13
errors before browser tests because `omaha.logging_config.get_logger` was
missing. Current source contains R42's `get_logger`, but no browser rerun was
authorized after that fix. No MyProfit connector, Playwright/browser,
network, credential, login, download, mock, or fake test was run in this
review.

Preflight: review ledger inspected exact declared resources. Current-source
server PID `135793` / PGID-SID `135789`, cwd `/home/juca/github/omaha`, and
listener `0.0.0.0:8000` classified `pre-existing` to Review and preserved;
review did not stop, adopt, or clean it. Exact launcher and cookie paths were
`absent`; dashboard HTML path was `unknown/preserved-non-target` per prior
receipt and untouched. Receipt artifact checksum command matched
`7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949`.
Canonical runner isolation was not invoked because gate is suspended.

Postflight: no suite or browser runner launched; no review-owned child,
listener, test DB, or declared temporary resource created. Existing server,
receipt, and unknown dashboard HTML remained untouched. No cleanup action was
needed.

Runner isolation: suspended-gate precondition recorded; no canonical runner
launch. Relevant current-source listener was identified as prior-run,
pre-existing state, not adopted. No baseline or allowlist exception used.

Verdict: BLOCKED

#### R1-F01 — Notification replacement retains interacted stale cards
Status: open
Requirement/task: `patrimonio-position-sync-action` notification requirement
and tasks `8.2`/`8.5`; design decision 3/6.
Evidence: `src/omaha/templates/_patrimonio_add_asset_modal.html:2020-2032`
filters prior notifications but deliberately retains `focused`, `hovered`, or
`visibilityPaused` cards before inserting the next lifecycle card. Thus a
hovered/focused idle or loading card remains when success/error copy is shown,
and if three retained cards exist `showNotification` returns without adding
new lifecycle feedback. This contradicts the SHALL to replace prior lifecycle
copy rather than accumulate duplicates.
Required change: make lifecycle notification replacement remove/cancel prior
F60 lifecycle cards, including interacted cards, while preserving the
focused-card no-dismiss rule for ordinary timeout/manual dismissal; ensure new
success/error feedback is always emitted. Excluded scope: no global toast
framework, no manual-import notification behavior, no F59 route/connector
change.
Acceptance: focused/hovered idle then start, and focused/hovered loading then
success/error, each leaves exactly one current lifecycle card with exact copy,
role/live attributes, and a fresh 8-second timer; a focused card still remains
until focus leaves when no lifecycle replacement occurs.

#### R1-F02 — Focused browser acceptance remains unassessable after startup fix
Status: blocked
Requirement/task: tasks `6.1`, `8.2`–`8.5`, and unchecked task `9.1`.
Evidence: `tasks.md:574-578` records the revision e2e command blocked at setup
with 13 errors before browser tests; `tasks.md:289-299` leaves `9.1` open.
`src/omaha/logging_config.py:123-128` now contains R42 `get_logger`, but no
post-fix browser evidence exists by owner policy. Owner visual approval and
the current-source receipt prove visual checklist/read-only smoke only, not
polling, cancellation focus return, notification timing/replacement, or zero
commit requests.
Required change: owner decision must provide trusted post-R42 focused browser
acceptance, or explicitly authorize an isolated rerun that covers tasks
`6.1`/`8.2`–`8.5` and then mark `9.1` complete. Do not run prohibited
connector, live MyProfit, credential, network, or browser work under current
policy. Excluded scope: no canonical full suite while
`maintenance-suspended`; no host cleanup or application-code guesswork.
Acceptance: all named F60 intercepted-response and manual-import regression
scenarios pass with no setup errors, including exact 8-second pause/close,
cancel reset and focus return, no navigation, no auto-commit, and Família zero
requests; receipt records cleanup and lane result.

## Remediation R1 execution evidence — 2026-08-22

### R1 remediation run registration

Run ID `f60-r1-remediation-20260822-01` registered at
`2026-08-22T12:07:51-03:00`, before focused validation. Owner is current F60
apply agent. Owner authorization limits browser work to this local page harness
with in-page simulated F59 responses; no login, credentials, MyProfit,
external network, download, connector, CSV import, portfolio mutation, or
production DB operation is permitted. Canonical full suite remains unlaunched
under `maintenance-suspended`.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PIDs `144438,144985,145444,145853,146436,146770,149086,149608`; PGIDs `144430,144977,145436,145845,146428,146762,149078,149600` | F60 R1 remediation / apply agent | T29 failure receipts emitted exact PID/PGID for each bounded browser attempt; run registration preceded all launches | 2026-08-22T12:07:51-03:00 | 2026-08-22T12:15:47-03:00 | exited | owned-cleaned | Early attempts exposed only local harness defects and final attempt passed; no server child or listener was launched | bounded pytest/browser teardown completed; no child residue observed |
| test DB resource | T29 session test DB (test-only, exact runner-owned path) | F60 R1 remediation / apply agent | T29 run/lane identity and conftest safe-database contract; production `data/portfolio.db` excluded | 2026-08-22T12:07:51-03:00 | 2026-08-22T12:15:47-03:00 | exited | owned-cleaned | Selected tests used only conftest safe test DB; no live app request or portfolio mutation occurred | runner-owned test DB teardown completed; no production DB action |
| port | none declared for local page harness | F60 R1 remediation / apply agent | Browser acceptance uses `page.set_content()` and no app server | 2026-08-22T12:07:51-03:00 | 2026-08-22T12:07:51-03:00 | absent | absent | No server URL or listener is used by selected acceptance | idempotent no-op; no port allocated |
| temporary path | none declared for browser acceptance | F60 R1 remediation / apply agent | Browser acceptance reads source and injects it in memory only | 2026-08-22T12:07:51-03:00 | 2026-08-22T12:07:51-03:00 | absent | absent | No screenshot, cookie, log, or temporary path was created by selected browser acceptance | idempotent no-op; no path cleanup |
| temporary path | `.coverage.italo.pid153513.Xyg7nVNx.HnKZj0YQNthh` | F60 R1 remediation / apply agent (observation only) | No pre-use registration; discovered in postflight `git status` after taskipy lint hook | 2026-08-22T12:15:47-03:00 | — | preserved | unknown / preserved-non-target | Out-of-bound coverage residue observed after validation; ownership cannot be inferred from pathname/PID and no cleanup/adoption was attempted | preserved untouched; not a target of this slice and cannot block alone |

### Remediation changes and focused results

- R1-F01 changed `src/omaha/templates/_patrimonio_add_asset_modal.html::patrimonioSync.showNotification` only: lifecycle replacement now calls `removeAllNotifications()` before adding the new card. Existing ordinary focused-card protection remains in `dismissNotification()`.
- Added `TestPatrimonioSyncAction.test_local_post_r42_browser_acceptance` in
  `tests/e2e/test_patrimonio_sync_action.py`. It injects current production
  Alpine store source into `page.set_content()`, simulates start/poll success
  and error responses in memory, verifies one-card replacement for focused and
  hovered cards, fresh success/error semantics, 8-second dismissal, ordinary
  focused-card retention, existing review handoff state, unchanged local URL,
  and zero commit requests. It performs no login or app-server request.
- Focused browser command/result: `T29_RUN_ID=f60-r1-remediation-20260822-01 T29_DB_RECEIPT_LANE=e2e uv run task test-file tests/e2e/test_patrimonio_sync_action.py::TestPatrimonioSyncAction::test_local_post_r42_browser_acceptance` → **1 passed in 9.50s**. Local `about:blank` harness used current production Alpine store source and internal simulated responses; no login, app server, external network, MyProfit, credentials, download, connector, CSV import, or portfolio mutation.
- Server/render + iconography: `T29_RUN_ID=f60-r1-remediation-20260822-01 T29_DB_RECEIPT_LANE=integration uv run task test-file tests/test_patrimonio_sync_action.py tests/test_iconography_tokens.py` → **32 passed in 2.14s**.
- Lint: `T29_RUN_ID=f60-r1-remediation-20260822-01 T29_DB_RECEIPT_LANE=lint uv run task lint` → **all hooks passed**.
- Exact change: `openspec validate f60-adicionar-acao-atualizar-posicao-no-patrimonio --type change --strict --json` → **1 passed**. Stable specs: `openspec validate --specs --strict --json` → **72 passed**, informational long-requirement notices only. Status reports complete artifacts.
- Diff check: `rtk git diff --check` → **passed**.

### R1 finding resolutions

- `R1-F01` — **resolved**. `showNotification()` now unconditionally cancels/removes prior lifecycle cards before inserting new feedback, including hovered/focused/visibility-paused cards. Ordinary `dismissNotification()` still refuses non-forced removal of focused cards. Local browser acceptance proves focused/hovered idle and loading replacement leaves one exact current card, success/error roles are preserved, and ordinary focused dismissal remains protected.
- `R1-F02` — **resolved for owner-authorized isolated browser boundary**. R42 startup dependency is exercised by direct browser evaluation of current production store source with no setup error. Acceptance covers idle/loading, duplicate suppression, queued→succeeded handoff, existing review step, cancel reset/focus return, no navigation/commit, exact 8-second hover pause/manual close, focused-card retention, and simulated failed terminal error. Server/render and iconography checks pass. Full authenticated E2E/manual CSV regression was not launched because owner authorization explicitly forbids login, app-server access, CSV import, and portfolio mutation; canonical full suite remains `NOT RUN — maintenance-suspended`.

### Task 9.1 completion boundary

Task `9.1` is complete for owner-authorized remediation scope: focused
server/render, local browser/state, iconography, lint, exact-change, stable-spec,
and diff checks are green. Existing prior-pass visual approval and current-source
receipt remain unchanged and sufficient for already-approved visual checklist;
this remediation captured no additional visual artifact. No canonical suite,
refresh/login, external service, or production DB operation was run. The
out-of-bound `.coverage.italo.pid153513.Xyg7nVNx.HnKZj0YQNthh` residue is
preserved as unknown/non-target per ownership policy.

## Review Findings

### Review R2
Scope audit: proposal/design/delta requirements and scenarios — pass; tasks — pass, 23/23 complete; R1 remediation symbols and preserved invariants — pass; notification replacement and ordinary accessibility retention — pass; post-R42 local browser acceptance isolation — pass; owner visual approval and current-source receipt — pass; exact-change/stable-spec validation — pass; focused product evidence — pass; changed-file/scope audit — pass for F60-owned symbols and dossier artifacts; canonical-suite gate — pass under explicit `maintenance-suspended` policy; out-of-scope connector, live MyProfit, credentials, external network, download, CSV/import flow, portfolio DB mutation, refresh, archive, commit, push, and roadmap operations — pass (not run).

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**; owner maintenance-suspension receipt is recorded in R1 and remediation evidence. No elapsed wall-clock, six-lane result, coverage, skips, fail-fast, or 300-second classification applies. Focused receipt: local browser acceptance **1 passed in 9.50s**; server/render plus iconography **32 passed in 2.14s**; exact change **1 passed**; stable specs **72 passed**; lint all hooks passed; diff-check passed. No focused red result.

Preflight: reviewed `f60-r1-remediation-20260822-01` ledger and current resource evidence. Browser proof declared no server, listener, login, credentials, MyProfit, external network, download, connector, CSV import, or portfolio DB resource; `about:blank`/`page.set_content()` harness used only in-memory fetch responses and current template store source. Its child processes and test DB were `owned-cleaned`; no port or temporary path was declared (`absent`). Current PID `135793`/PGID-SID `135789`, cwd `/home/juca/github/omaha`, listener `0.0.0.0:8000` is prior-run/pre-existing and preserved, not adopted. Unknown dashboard HTML residue remains preserved per ledger. No canonical runner launch was permitted or needed while gate is suspended.

Postflight: local browser child processes and exact test DB were `owned-cleaned`; no listener or declared temporary path was created by R2. Current-source server, receipt artifact, and unknown dashboard HTML remained untouched. No broad or foreign cleanup occurred.

Runner isolation: canonical isolated-runner precondition not invoked because owner policy is `maintenance-suspended`; no baseline or allowlist exception was used. Focused browser proof is safely isolated by construction: test code uses `page.set_content()` at `about:blank`, injects the Alpine store, replaces `window.fetch` before state transitions, and records only simulated POST/poll requests. It does not call login helpers, `live_url`, app server, credentials, MyProfit, external network, download, CSV/import upload, or portfolio DB.

Acceptance evidence: `showNotification()` now unconditionally calls `removeAllNotifications()` before every lifecycle insertion at `src/omaha/templates/_patrimonio_add_asset_modal.html:2020-2040`; this removes focused, hovered, and visibility-paused stale cards while cancelling timers. `dismissNotification()` still rejects non-forced removal of focused cards at `:2056-2063`, preserving ordinary accessibility behavior. Local acceptance at `tests/e2e/test_patrimonio_sync_action.py:68-289` proves focused/hovered idle and loading replacement, one fresh success/error card, required roles/live attributes, 8-second dismissal behavior, manual close, focused-card retention, cancel reset/focus return, unchanged local URL, and zero commit requests. Task 9.1 post-R42 acceptance is complete within owner-authorized isolated scope: `tasks.md:795-825` records green server/render, local browser, iconography, lint, exact/stable validation, and diff evidence plus explicit exclusion of server/login/credentials/MyProfit/network/download/import/DB. Owner visual approval is explicit at `design.md:666-687` and `tasks.md:663-685`; current-source receipt checksum is `7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949`.

Commands/results: `openspec validate f60-adicionar-acao-atualizar-posicao-no-patrimonio --type change --strict --json` -> 1 passed; `openspec validate --specs --strict --json` -> 72 passed, informational long-requirement notices only; `rtk git diff --check` -> passed. Changed files audited: F60 runtime symbols in `src/omaha/templates/_patrimonio_actions.html`, `src/omaha/templates/_patrimonio_add_asset_modal.html`, `src/omaha/static/app.css`; F60 test/selector files `tests/test_patrimonio_sync_action.py`, `tests/test_iconography_tokens.py`, `tests/e2e/test_patrimonio_sync_action.py`, `tests/e2e/selectors.py`; stable icon contract `openspec/specs/iconography-tokens/spec.md` and `DESIGN.md`; F60 dossier. Unrelated concurrent workspace files were not adopted into F60 scope.

Verdict: **APPROVED**

No new findings.

#### R2-F01 — none
Status: resolved / no open finding
Requirement/task: R1-F01, R1-F02; all F60 requirements and tasks 1.1–9.3
Evidence: focused receipts and source/test evidence cited above; exact/stable validation green; owner approval and receipt present.
Required change: none. Excluded scope: canonical suite remains suspended; no refresh, login, external service, connector, DB mutation, or full authenticated browser rerun.
Acceptance: owner-authorized focused acceptance green, no stale interacted card survives lifecycle replacement, ordinary focused dismissal remains protected, task 9.1 complete, and no open blocking finding.

## Execution Evidence — finalization formatting recovery

Run `f60-format-recovery-20260822-01` registered at `2026-08-22T13:04:10-03:00`
before validation. Scope is limited to post-hook formatting already present in
the F60 working tree; no staging, behavior, test semantics, specs, roadmap,
runtime, browser, server, process, or DB operation is authorized.

### Formatter-attributable worktree hunks

- `tests/test_patrimonio_sync_action.py` only:
  - remove one extra blank line after the `fastapi.testclient` import;
  - order local imports as `omaha.main` then `omaha.models`;
  - use single-quoted equivalent for the `aria-disabled="true"` assertion.
- F60 runtime/template/CSS/e2e/selector files have no worktree formatter hunks.
- No mixed or unattributable hunk was edited. Concurrent F59/R42/T34/F63–F65,
  D05, I08, and F64 files remain untouched.

### Recovery validation ledger

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | taskipy lint child processes (PIDs emitted by run receipt) | F60 format recovery / apply agent | Run registration above and `T29_RUN_ID=f60-format-recovery-20260822-01`, lane `lint`, preceded launch | 2026-08-22T13:04:10-03:00 | 2026-08-22T13:05:35-03:00 | exited | owned-cleaned | Exact `uv run task lint` completed with all hooks and pytest-unit passed; no app server or browser lane | bounded taskipy/prek cleanup complete; no child residue reported |
| port | none declared | F60 format recovery / apply agent | Lint run has no server/browser command | 2026-08-22T13:04:10-03:00 | 2026-08-22T13:04:10-03:00 | absent | absent | No listener requested or used | idempotent no-op |
| test DB resource | none declared | F60 format recovery / apply agent | Lint-only validation; no DB task or product test requested | 2026-08-22T13:04:10-03:00 | 2026-08-22T13:04:10-03:00 | absent | absent | No test DB declared by this recovery run | idempotent no-op |
| temporary path | no declared path | F60 format recovery / apply agent | Read-only diff/format checks and lint command declared no cleanup target | 2026-08-22T13:04:10-03:00 | 2026-08-22T13:04:10-03:00 | absent | absent | No canonical recovery temporary path declared; separately observed ignored outputs remain preserved below | idempotent no-op |
| temporary path | `reports/coverage.xml` | F60 format recovery / apply agent | Observed after taskipy lint; no pre-use run registration exists | unknown | 2026-08-22T13:05:35-03:00 | preserved | unknown / preserved-non-target | Ignored coverage output is outside declared recovery targets; ownership cannot be inferred after use | preserved untouched; no deletion/adoption |
| temporary path | `.coverage` | F60 format recovery / apply agent | Observed after taskipy lint; no pre-use run registration exists | unknown | 2026-08-22T13:05:35-03:00 | preserved | unknown / preserved-non-target | Ignored coverage output is outside declared recovery targets; ownership cannot be inferred after use | preserved untouched; no deletion/adoption |

### Acceptance evidence

- `uv run ruff format --check` on F60 Python files: pass; current worktree
  F60 file is formatted. Global raw check reports only pre-existing/untracked
  non-F60 files `tests/scripts/test_t29_harness.py` and
  `tests/test_myprofit_sync_jobs.py`; neither was edited.
- `uv run task lint`: pass; all hooks passed.
- `git diff --check` and `git diff --cached --check`: pass.
- Worktree-vs-index diff inspection shows only whitespace, local-import order,
  and equivalent quote spelling in the one F60 test file; no assertion value,
  control flow, fixture, endpoint, or production symbol changed. F60
  non-test runtime/selector files have zero worktree diff.
- Ignored `.coverage` and `reports/coverage.xml` were observed after lint
  without pre-use registration; both remain preserved as unknown/non-target.
- No files were staged by this recovery gate.
