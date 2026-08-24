## 1. Apply prerequisite: owner visual-rendering approval

- [x] 1.1 Before touching runtime code, record the exact owner decision in
  `design.md` using the exact static artifact
  `openspec/changes/f65-triagem-de-ativos-por-estado-no-preview-de-posicao/visual-prototype.html`
  and checksum; review every checklist item in the matching `design.md`
  section: exact `Novos`/`Alterados`/`Inalterados` labels and fixture counts,
  one-section-only membership, deterministic name/ticker order, incoming
  values, persistent changed cue, hover/focus prior-value disclosure with
  label/unit/sign, 1200px desktop cap, full-width/readable mobile constraint,
   absence of any standalone manual-import panel/card/footer or duplicate CTA,
   existing `Importar CSV` entry/upload, preserved Cancelar/Confirmar hierarchy,
   and disabled/read-only Família context. Also verify every triage section
   visibly preserves exact current columns `Nome`, `Qtde`, `Preço médio`,
   `Total atual`, `Classe`, `Compra`, `Venda`, `Moeda`; class binding,
   suggestion/color/pending state; Compra/Venda toggles; and Moeda select.
   Verify `broker_ticker` remains only as hidden assignment key with no visible
   ticker or `Ativo / ticker` heading. Preserve proposal-only
   prohibition on browser/server/DB work. Acceptance: owner record exists
  directly below the checklist in `design.md`, uses `APPROVED`, names owner and
  UTC timestamp, and includes artifact path/checksum; missing, partial, or
  rejected approval blocks Apply. Test file/scenario:
  `visual-prototype.html` manual review; no pytest. Focused taskipy command:
  N/A. Independent oracle: exact owner decision plus artifact checksum and
  checklist completion.

- [x] 1.2 Verify visual artifact remains review-only and matches manual-import
  boundary before handoff: file is self-contained with inline CSS and
  deterministic fixture content, has no live data/network/DB/MyProfit/endpoint
  dependency, and contains no standalone `Importação manual` panel/card,
  explanatory footer, `.manual-note` style, or `Importar manualmente` CTA.
  Existing `Cancelar` and `Confirmar importação` actions remain visible as
  static evidence only. Do not add implementation work or alter F65 behavior
  scope. Acceptance: changed-file audit contains only F65 dossier artifacts;
   source inspection proves forbidden block/selectors are absent; static file
   has no external/live-data hook; each of the three tables has all eight
   columns and row controls; visible source has no ticker value/heading while
   hidden assignment keys remain; `design.md` records owner decision location.
   Test file/scenario: `visual-prototype.html` source inspection. Focused
   taskipy command: N/A. Independent oracle: exact artifact path, forbidden
   string/selector audit, and `git diff --check`.

- [x] 1.3 Recheck revised static evidence after any dossier edit: compute
  SHA-256 for
  `openspec/changes/f65-triagem-de-ativos-por-estado-no-preview-de-posicao/visual-prototype.html`,
  record exact digest in `design.md` and this task's evidence, and ensure the
  digest is computed from final file bytes. Preserve no owner approval claim;
  owner visual decision remains the next gate. Acceptance: digest is stable on
  immediate repeat and the prototype source still proves eight columns/control
  inventory in `Novos`, `Alterados`, and `Inalterados`. Test file/scenario:
  `visual-prototype.html` static inspection. Focused taskipy command: N/A.
  Independent oracle: repeated `sha256sum` output and exact source audit.
  Current recorded digest:
  `6a2540a74067051eaacb1988af26cfba33d8ab075a6f6d76fe2373ea8f8002e6`.

## 2. Server baseline and triage response

- [x] 2.1 Update `src/omaha/routes/imports.py::preview_from_blob`,
  `_raw_to_dict`, and `_dict_to_raw` to capture additive per-row pre-preview
  Asset metadata and same-Asset/exact-ticker Position state in existing
  `ImportPreview.raw_json`, while accepting legacy raw-list JSON without a
  baseline. Preserve parser fields, profile scoping, preview TTL, broker
  totals, and zero Asset/Position mutation. Acceptance: baseline records are
  stable after later DB edits, legacy previews still rehydrate, and preview
  persistence counts/shape remain compatible. Test file/scenario:
  `tests/test_import_preview.py::TestPostImportPreview::test_preview_persists_preview`
  plus new baseline/legacy scenarios. Focused taskipy command:
  `uv run task test-file tests/test_import_preview.py`. Independent oracle:
  temporary test DB before/after counts and raw JSON inspection prove captured
  baseline without production DB or commit/snapshot/audit side effects.

- [x] 2.2 Implement `src/omaha/routes/imports.py::_build_preview_response`
  triage serializer: classify each row exactly once using baseline Asset
  identity, Position existence, exact Decimal/null equality, exact trimmed
  Asset metadata equality, and compatibility fallback; emit additive
  `triage.new/changed/unchanged` rows with `changed_fields` containing field
  id, PT-BR label, unit, sign, incoming value, and previous value/display.
  Preserve unchanged top-level `auto_matched`, `unmatched`, `asset_classes`,
  `invested`, `current_value`, trade flags, suggested classes, and existing
  matcher meaning. Acceptance: no `auto_matched` row is assumed unchanged;
  new/changed/unchanged sets are disjoint and exhaustive; missing Position,
  missing-vs-zero totals, equal Decimal scales, metadata differences, and
  legacy previews follow design rules; no commit/snapshot/audit occurs. Test
  file/scenario: `tests/test_import_preview.py` new mixed-state, equality,
  diff-payload, compatibility, and no-mutation scenarios. Focused taskipy
  command: `uv run task test-file tests/test_import_preview.py`. Independent
  oracle: response JSON assertions plus Asset/Position/db_mutations counts and
  baseline fixture prove classification source and exact payload.

- [x] 2.3 Add server-side deterministic ordering in
  `src/omaha/routes/imports.py::_build_preview_response` for every triage
  group: Unicode accent-insensitive/case-insensitive name, missing name last,
  normalized broker ticker tie-break, raw values final tie-break. Preserve
  broker input order in legacy compatibility arrays. Acceptance: same input
  permutations produce identical triage order while legacy arrays remain
  compatible. Test file/scenario: `tests/test_import_preview.py` accent/case,
  missing-name, and ticker-tie scenarios. Focused taskipy command:
  `uv run task test-file tests/test_import_preview.py`. Independent oracle:
  exact ordered name/ticker lists from JSON under permuted input rows.

## 3. Alpine review model and three state sections

- [x] 3.1 Update `src/omaha/templates/_patrimonio_add_asset_modal.html::Alpine.store('importModal')`
  `resetState`, `clearPreview`, `hydratePreview`, and `buildAssignments` to
  accept additive triage groups, retain a safe legacy fallback from
  `auto_matched`/`unmatched`, and keep every row addressable by
  `broker_ticker`. Preserve manual upload, F59 `openPreview`, class
   assignment initialization, trade-control defaults, dynamic select
   `$nextTick`/`x-effect`, preview expiry/reupload, profile ownership, Família
   guard, and explicit `commit()`. Acceptance:
  both payload variants reach Step 2 without JS errors and assignment payload
  remains unchanged. Test file/scenario:
  `tests/e2e/test_import_modal.py::TestS04ImportModal::test_newer_file_selection_ignores_stale_preview_response`
  plus new legacy/additive hydration scenario. Focused taskipy command:
  `uv run task test-file tests/e2e/test_import_modal.py`. Independent oracle:
  browser Alpine store state, row keys, and intercepted request log show no
  commit during hydration.

- [x] 3.2 Replace Step 2 markup in
  `src/omaha/templates/_patrimonio_add_asset_modal.html` with conditional
  `Novos`, `Alterados`, and `Inalterados` sections and counts, rendering each
  triage row once while preserving existing class selects, trade toggles,
   currency binding, row testids, Confirmar/Cancelar, and incoming value cells.
   Every section must retain `Nome`, `Qtde`, `Preço médio`, `Total atual`,
   `Classe`, `Compra`, `Venda`, and `Moeda`; ticker remains hidden while
   `broker_ticker` continues to key assignments. Responsive overflow may scroll
   horizontally but must not hide any listed column/control.
   Do not add any standalone manual-import panel/card/footer or duplicate
   `Importar manualmente` CTA; existing modal actions remain the manual commit
   control.
  Hide zero-length sections with no empty placeholder. Acceptance: mixed,
  single-group, and empty-group payloads render correct section/count/order;
  existing assignment and commit journey remains functional. Test
  file/scenario: `tests/e2e/test_import_modal.py::TestS04ImportModal::test_import_modal_happy_path`
  plus new three-section/empty-section scenarios. Focused taskipy command:
  `uv run task test-file tests/e2e/test_import_modal.py`. Independent oracle:
  rendered DOM section counts, unique row membership, incoming cell text, and
  POST `/api/import/commit` only after Confirmar.

- [x] 3.3 Add changed-field rendering in the same Step 2 template: incoming
  value remains default; each `changed_fields` item renders persistent cue and
  focusable disclosure with accessible label/description, unit, sign, and
  prior value; unchanged/new fields have no prior-value decoration. Preserve
  existing BRL/quantity formatters and null/zero display semantics. Acceptance:
  pointer hover and keyboard focus reveal identical prior text, screen-reader
  naming includes field label/unit/sign, and disclosure does not depend on
  `title`. Test file/scenario: `tests/e2e/test_import_modal.py` new changed
  numeric/metadata and keyboard-focus scenarios. Focused taskipy command:
  `uv run task test-file tests/e2e/test_import_modal.py`. Independent oracle:
  Playwright DOM/accessibility snapshot before/after hover and Tab focus.

## 4. Modal sizing and visual language

- [x] 4.1 Update `src/omaha/static/app.css::.modal-panel--wide` from 1100px
  to 1200px and extend `.import-review-section*`,
  `.import-review-table*`, and new diff selectors using existing tokens for
  three state headers/counts, changed cue, hover/focus disclosure, wrapping,
  and readable mobile behavior. Preserve `.modal-panel` shell, modal z-index,
  existing class-cell colors/focus rings, no page-wide layout, and full-width
  mobile rule at <=768px. Acceptance: computed desktop max-width is 1200px;
  mobile panel is full width; changed disclosure is visible on hover/focus;
  unchanged rows have no diff decoration. Test file/scenario:
  `tests/e2e/test_import_modal.py` new computed-style/viewport and disclosure
  scenarios. Focused taskipy command:
  `uv run task test-file tests/e2e/test_import_modal.py`. Independent oracle:
  browser computed styles, bounding boxes, responsive screenshot/DOM, and
  focus-visible state.

## 5. Focused validation and delivery handoff

- [x] 5.1 Run focused API regression after all server/template changes:
  `tests/test_import_preview.py` must cover response compatibility, baseline
  source, three-way classification, typed equality, ordering, totals, and no
   mutation; `tests/e2e/test_import_modal.py` must cover existing manual commit,
   three sections, empty sections, incoming values, sorting, hover/focus
   disclosure, mobile sizing, and absence of any standalone manual-import
   panel or duplicate CTA. Preserve no skip/xfail/retry, no connector or
   external service, no production DB, and no F63 edits. Acceptance: both
  focused command results are green and changed-file audit is F65-only.
  Test files/scenarios: the two files above. Focused taskipy commands:
  `uv run task test-file tests/test_import_preview.py` and
  `uv run task test-file tests/e2e/test_import_modal.py`. Independent oracle:
  exit codes, request ledger, response/DOM assertions, and `git diff --check`.

- [x] 5.2 Run `uv run task lint` and exact artifact checks after implementation;
  preserve current maintenance-suspended canonical policy (do not claim full
  suite green during Propose/Apply). Acceptance: lint passes, exact F65
  OpenSpec change and all stable specs validate strictly, no unrelated files
  changed, and no product tests are run during this Propose gate. Test
  file/scenario: N/A for artifact gate; product files remain the focused
  oracles in 5.1. Focused taskipy command: `uv run task lint`. Independent
  oracle: exact/stable OpenSpec validator output, `git diff --check`, and
  changed-file audit.

- [x] 5.3 After Apply touches routes/templates/CSS, invoke mandatory
  `refresh-for-test` and record its delivery receipt plus current-source
  browser rendering before Review. Preserve no destructive DB reset without
  explicit authorization, LAN bind `0.0.0.0`, and exact owned-resource
  cleanup. Acceptance: refresh receipt, health/session smoke, triage visual
  evidence, and owner-approved rendering are recorded; this task is not run
  during Propose. Test file/scenario: visual artifact and delivery receipt.
  Focused taskipy command: N/A; use the `refresh-for-test` skill. Independent
  oracle: mandatory receipt, exact artifact/checksum, and owner decision.

## Test strategy

- Server/API: `tests/test_import_preview.py` with temporary test DB state and
  deterministic synthetic preview rows. Covers baseline capture, legacy
  fallback, all three classifications, Asset/Position equality, Decimal/null
  rules, sorting, compatibility keys, broker totals, and no mutation.
- Browser: `tests/e2e/test_import_modal.py` with existing isolated fixtures;
  covers manual and additive payload hydration, three sections/counts,
  empty-section omission, incoming display, sorted rows, hover/focus
  disclosure, responsive sizing, explicit commit, and no new standalone
  manual-import panel/CTA. No MyProfit connector, external network,
  credentials, or production DB.
- Static artifact: `visual-prototype.html` source inspection covers removal of
  the standalone manual-import block, preservation of existing modal action
  hierarchy, and additive eight-column inventory in every triage section. It
  also proves visible ticker absence plus hidden `broker_ticker` assignment
  keys, class binding/suggestion/color/pending state, trade toggles, currency
  selects, and responsive horizontal-scroll annotation. No browser/server/DB
  run during Propose.
- Focused commands: `uv run task test-file tests/test_import_preview.py`,
  `uv run task test-file tests/e2e/test_import_modal.py`, and
  `uv run task lint` after Apply. No product tests, browser, server, DB task,
  or `refresh-for-test` during Propose.
- Canonical `uv run task test` remains Review-owned and, under current
  `maintenance-suspended`, must be recorded as `NOT RUN — maintenance-suspended`
  rather than represented as green.

## Execution Evidence

- Apply preflight: owner visual approval recorded in `design.md` directly below
  the prototype checklist. Final prototype bytes produced the approved SHA-256
  `6a2540a74067051eaacb1988af26cfba33d8ab075a6f6d76fe2373ea8f8002e6` twice.
  Static inspection confirmed inline-only CSS/fixture content, no live hooks,
  no standalone manual-import panel/footer/CTA, all eight columns and controls
  in each triage table, no visible ticker text, and hidden `broker_ticker`
  assignment inputs. `git diff --check` passed for dossier edits.
- Pre-existing worktree boundary: `openspec/roadmap.md` modification and
  untracked `openspec/changes/f63-hover-e-cabecalho-sticky-na-tabela-de-rebalanceamento/`
  belong to other work and are not owned by F65.
- Implementation complete for tasks 2.1–4.1. Changed symbols/files:
  `imports.py::_capture_preview_baseline`, `_preview_rows_and_baseline`,
  `_build_preview_response`, `_build_changed_fields`, and triage ordering;
  modal `importModal` hydration/assignment/diff helpers plus generic Step 2
  triage sections; import modal CSS width, state headers, overflow, and
  hover/focus disclosure; focused API and E2E assertions in the two mapped test
  files. Compatibility arrays and commit assignment wire shape remain intact.
- Focused validation completed: `uv run task test-file tests/test_import_preview.py`
  -> 14 passed (`f65-final-api-20260822T204700Z`); `uv run task test-file
  tests/e2e/test_import_modal.py` -> 5 passed (`f65-apply-e2e-20260822T203900Z`);
  `uv run task lint` -> passed (`f65-final-lint-20260822T204800Z`); `openspec validate
  f65-triagem-de-ativos-por-estado-no-preview-de-posicao --type change --strict`
  -> valid; `openspec validate --specs --strict` -> 75 passed; `git diff
  --check` -> passed (`f65-final-artifacts-20260822T204900Z`). One initial API assertion and two stale input-order E2E
  assumptions were corrected to the approved equal-field/no-resort contract;
  final focused results are green.
- Validation ownership ledger: `f65-apply-api-20260822T203200Z` PID/PGID
  `219181` exited with focused assertion failure; `f65-apply-api-20260822T203600Z`
  PID/PGID `219353` exited 0; `f65-apply-e2e-20260822T203700Z` PID/PGID
  `219468` exited with stale-selector assertion; `f65-apply-e2e-20260822T203800Z`
  PID/PGID `220244` exited with stale-order assertion; `f65-apply-e2e-20260822T203900Z`
  PID/PGID `220967` exited 0; `f65-apply-lint-20260822T204000Z` PID/PGID
  `221614` exited after formatter modifications (owned files only);
  `f65-apply-lint-20260822T204100Z` PID/PGID `222877` exited 0;
  `f65-apply-artifacts-20260822T204200Z` PID/PGID `224104` exited 0. Each
  shell/process-group entry was run-created by F65, started and ended at the
  timestamps printed in its receipt, and exited naturally; cleanup was exact
  idempotent no-op, no foreign resource was touched. Focused test DBs were
  test-only harness resources; production DB was not targeted.
- Final receipt additions: `f65-final-api-20260822T204700Z` PID/PGID
  `225308`, `f65-final-lint-20260822T204800Z` PID/PGID `225405`, and
  `f65-final-artifacts-20260822T204900Z` PID/PGID `226514`; each had
  run-created F65 ownership evidence, exited naturally, and ended
  `owned-cleaned` with exact no-op cleanup.
- Delivery receipt (refresh-for-test): `f65-refresh-20260822T204500Z`.
  URL `http://192.168.1.4:8000` from `bash scripts/print_lan_url.sh`;
  `/healthz` returned `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`;
  read-only DB inspection reported pre-existing `11 classes / 89 assets / 88
  positions` (no `db-reset`, `db-clear-assets`, or migration run because owner
  gave no destructive authorization); dashboard smoke found `RF Din` 5 times.
  Server resource was registered before launch at exact PID/PGID `224819`,
  command `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`, then
  exact owned process-group TERM cleanup ended `owned-cleaned`; no foreign
  process/listener was present in preflight. Cookie path
  `/tmp/f65-refresh-cookie-204500` was registered before use and ended absent
  after exact cleanup. Current-source triage browser evidence is the focused
  E2E green result: three-section/count assertions, hidden-key row lookup,
  incoming/diff cue, keyboard prior-value disclosure, explicit commit journey,
  and computed `1200px` panel cap.
- Canonical review isolation: apply did not launch full canonical suite
  (`maintenance-suspended`, review-owned). Preflight had no relevant unowned
  process/listener; focused test DBs were harness-declared test-only resources
  and exited with their runners. Existing out-of-bound `/tmp` observations
  were preserved/non-target; no foreign resource was adopted, killed, freed,
  or deleted.

## Acceptance evidence

- Response JSON proves `triage` groups are mutually exclusive/exhaustive,
  baseline-sourced, typed-equality-correct, sorted, diff-complete, and additive
  to `auto_matched`/`unmatched`.
- Browser DOM proves exact PT-BR section labels/counts, no empty sections,
  incoming values, stable assignments, accessible hover/focus prior values,
  1200px/full-width modal behavior, every current column/control in every
  section, hidden ticker assignment identity, and no standalone manual-import
  panel/card/footer or duplicate CTA.
- Existing commit path proves no mutation before explicit confirmation and
  retains snapshot/audit/Família protections.
- Focused taskipy results, lint, exact/stable OpenSpec validation,
  `git diff --check`, F65-only changed-file audit, post-Apply refresh receipt,
  and mandatory owner visual approval are recorded before Review.

## Review Findings

### Review R1
Scope audit: requirements pass; scenarios pass; tasks 13/13 pass; design decisions pass; changed symbols pass; preserved invariants (preview non-mutation, explicit commit, snapshot/audit, Família guard, profile/TTL ownership, broker totals) pass; focused tests pass; scope boundaries pass; compatibility constraints pass; no test deletion/masking detected. No area not assessable.

Full suite: `NOT RUN — maintenance-suspended` (owner-authorized I10 suspension in `openspec/PRD.md` §4.13; review must not launch canonical suite). Focused product evidence: `uv run task test-file tests/test_import_preview.py` -> 14 passed; `uv run task test-file tests/e2e/test_import_modal.py` -> 5 passed; `uv run task lint` -> passed. No focused red result.

Preflight: apply ownership ledgers and delivery receipt reviewed. F65 run-created PID/PGID/test-harness resources had owner evidence, natural exit, exact cleanup, and `owned-cleaned` classification; refresh server PID/PGID `224819` and cookie boundary had exact ownership and `owned-cleaned` cleanup. No relevant unowned process/listener/test DB remained. Out-of-bound `/tmp` observations were recorded `preserved/non-target`. Decision: trusted evidence; no canonical suite launch required under suspension.

Postflight: no review suite launched, so no review-run child cleanup was required. Apply focused-run and refresh postflight records end timestamps, exact cleanup results, and `owned-cleaned` classifications; no foreign resource was touched. Decision: postflight evidence sufficient for suspended gate.

Runner isolation: relevant process/listener/test-temp inventory from apply/refresh receipts shows no unowned state at handoff; declared focused test resources were test-only harness resources and cleaned. No baseline or allowlist exception used.

Verdict: APPROVED

No blocking findings.

### Review R3
Scope audit: proposal requirements pass; relevant delta-spec requirements and
scenarios pass; tasks 13/13 pass; durable design and remediation-3 decision pass;
changed symbols pass; preserved invariants pass; focused product evidence pass;
scope boundary pass for owner-authorized final visual correction; no unrelated
diff attributed; no test deletion, skip, xfail, retry, masking, or coverage
reduction detected; no area not assessable.

Follow-up audit: `src/omaha/static/app.css` adds only
`.import-review-table-wrap { padding-bottom: 2rem; }` for remediation 3/3.
`tests/e2e/test_import_modal.py` adds only bounded rectangle assertions for the
existing formatted-money disclosure. Disclosure remains `position: absolute`,
previous value remains overlay-only and readable at table bottom, incoming text
remains primary, and no cell reflow/layout change is introduced. No template,
route, data, classification, color, control, or unrelated behavior changed in
this follow-up.

Full suite: `uv run task test` -> `NOT RUN — maintenance-suspended` under
owner-authorized I10 state in `openspec/PRD.md` §4.13. Applicable focused
product evidence: `uv run task test-one
tests/e2e/test_import_modal.py::TestS04ImportModal::test_changed_money_disclosure_is_formatted_overlay`
-> 1 passed in 9.40s (`f65-remediation3-e2e-20260822T235540Z`); `uv run task
lint` -> passed; `git diff --check` -> passed; exact change validation ->
valid; stable spec validation -> 75 passed. Focused evidence is green. Six
canonical lane results, coverage, skips, fail-fast disposition, and canonical
duration are not applicable while suspension remains active.

Preflight: surgical remediation-3 ledger reviewed before standards/spec audit.
Focused process group, disposable test DB, port 8765, log, and isolation plugin
classify `owned-cleaned`/`absent` with exact owner evidence and bounded cleanup.
Owner-authorized delivery process group `282052/282048`, listener `0.0.0.0:8000`,
and `/tmp/opencode/f65-remediation3-server.log` classify `owned-current-run`
under explicit local delivery authorization; no foreign or unknown relevant
resource was adopted or cleaned. Decision: trusted review evidence; suspension
forbids canonical launch.

Postflight: focused process/temp/test-DB resources ended naturally and classify
`owned-cleaned` or `absent`; delivery listener/log remain intentionally active
and owner-authorized. No review suite launched, so no canonical child cleanup
exists. Decision: postflight sufficient under suspension.

Runner isolation: pass for applicable focused evidence; no unowned relevant
process, listener, test DB, or declared temporary resource observed. Canonical
isolated-runner precondition was not exercised because maintenance suspension
explicitly prohibits `uv run task test`; no baseline or allowlist exception used.

Verdict: APPROVED

No blocking findings.

## Surgical remediation 3/3 — owner-validation execution evidence

- Owner-authorized scope: final visual correction only. Before editing,
  captured `git diff HEAD~1 --` and `git status --short --branch`. Existing
  F65 hunks were preserved in `src/omaha/routes/imports.py`,
  `src/omaha/templates/_patrimonio_add_asset_modal.html`,
  `src/omaha/static/app.css`, `tests/test_import_preview.py`, and
  `tests/e2e/test_import_modal.py`. Pre-existing non-F65 boundaries were
  modified `openspec/PRD.md`, modified `openspec/roadmap.md`, deleted T34
  dossier files under `openspec/changes/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58/`,
  untracked F63 dossier, untracked F65 dossier, and untracked import-review
  dossier. No boundary was reverted or edited.
- Surgical correction: only `.import-review-table-wrap` in
  `src/omaha/static/app.css` gained `padding-bottom: 2rem`. This provides
  bounded clearance for the absolutely positioned prior-value disclosure
  below the final table row while retaining non-flow overlay behavior and
  unchanged cell text/column layout. `tests/e2e/test_import_modal.py` gained
  only rectangle assertions proving disclosure top/bottom remain inside both
  `.import-review-table-wrap` and `.modal-panel` after focus at the table
  boundary.
- Focused browser validation:
  `uv run task test-one tests/e2e/test_import_modal.py::TestS04ImportModal::test_changed_money_disclosure_is_formatted_overlay`
  -> 1 passed in 9.40s (`f65-remediation3-e2e-20260822T235540Z`), using exact
  disposable DB `/tmp/opencode/f65-remediation3-e2e-db.sqlite`; incoming
  `R$ 3.250` remained unchanged and prior `R$ 116.616` stayed readable on
  hover/focus inside table and modal bounds. No test was skipped, weakened,
  xfailed, retried, or deleted.
- `uv run task lint` -> passed
  (`f65-remediation3-lint-20260822T235900Z`); `git diff --check` -> passed
  (`f65-remediation3-diffcheck-20260822T235900Z`). No template, route, data,
  classification, or unrelated file changed in this pass.
- Final post-receipt `git diff --check` -> passed
  (`f65-remediation3-final-diffcheck-20260823T000500Z`).

### Surgical remediation 3/3 ownership ledger

| resource_kind | resource_id | owner / owner_evidence | started_at / ended_at | status / classification | evidence / cleanup_result |
|---|---|---|---|---|---|
| process group | PID/PGID `279884/279884` | `f65-remediation3-e2e-20260822T235540Z`; run-created exact focused command registration | `2026-08-22T23:56:00Z` / `2026-08-22T23:56:22Z` | exited / owned-cleaned | E2E exited 0; exact bounded no-op cleanup |
| test DB resource | `/tmp/opencode/f65-remediation3-e2e-db.sqlite` | same E2E run; exact path absent before launch and created by isolated fixture | `2026-08-22T23:55:40Z` / `2026-08-22T23:56:22Z` | absent / owned-cleaned | test-only disposable DB; exact `rm -f` cleanup; absent afterward |
| port | `127.0.0.1:8765` | same E2E run; port absent before launch | `2026-08-22T23:55:40Z` / `2026-08-22T23:56:22Z` | absent / absent | server teardown reported port free; no foreign listener touched |
| log | `/home/juca/github/omaha/tmp/uvicorn-logs/e2e-live-url-k0ii6jjf.log` | same E2E run; run-created server log from exact server event | `2026-08-22T23:56:00Z` / `2026-08-22T23:56:22Z` | absent / owned-cleaned | exact log removed after receipt capture |
| temporary path | `/tmp/opencode/f65-remediation3-isolated.py` | same E2E run; run-created isolation plugin | `2026-08-22T23:55:40Z` / `2026-08-22T23:56:22Z` | absent / owned-cleaned | exact plugin removed; no broad temp cleanup |
| process group | PID/PGID `280457/280457` | `f65-remediation3-lint-20260822T235900Z`; run-created exact lint command registration | `2026-08-22T23:57:35Z` / `2026-08-22T23:58:15Z` | exited / owned-cleaned | lint exited 0; exact no-op cleanup |
| process group | PID/PGID `281318/281318` | `f65-remediation3-diffcheck-20260822T235900Z`; run-created exact artifact command registration | `2026-08-22T23:58:15Z` / `2026-08-22T23:58:15Z` | exited / owned-cleaned | `git diff --check` exited 0; exact no-op cleanup |
| test DB resource | `data/portfolio.db` | owner-authorized exact `uv run task db-migrate` | `2026-08-22T23:59:14Z` / `2026-08-22T23:59:15Z` | exited / owned-current-run | rc 0; persistent local-dev DB retained, no cleanup |
| test DB resource | `data/portfolio.db` | owner-authorized exact `uv run task db-seed` | `2026-08-22T23:59:22Z` / `2026-08-22T23:59:23Z` | exited / owned-current-run | rc 0, seed skipped existing users; persistent local-dev DB retained |
| process group | PID/PGID `277274/277270` | `f65-remediation3-refresh-20260823T000000Z`; exact known Omaha listener and owner-authorized bounded replacement | `2026-08-22T23:59:49Z` / `2026-08-23T00:00:00Z` | absent / pre-existing | exact preflight matched `0.0.0.0:8000`; later absence recorded as lifecycle race, no foreign adoption; no broad kill |
| port | `0.0.0.0:8000` | same refresh run; exact preflight listener match then run-created replacement | `2026-08-22T23:59:49Z` / active | active / owned-current-run | newest Omaha listener `PID/PGID 282052/282048`; intentionally preserved for delivery |
| process group | PID/PGID `282052/282048` | same refresh run; run-created exact `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000` launch | `2026-08-23T00:00:00Z` / active | active / owned-current-run | startup complete; quote refresh `refreshed=1`; intentionally left running |
| log | `/tmp/opencode/f65-remediation3-server.log` | same refresh run; exact path registered before launch | `2026-08-22T23:59:49Z` / active | active / owned-current-run | startup/health/visual evidence retained with delivery server |
| temporary path | `/tmp/opencode/f65-remediation3-refresh-cookie` | same refresh run; exact path registered before use | `2026-08-22T23:59:49Z` / `2026-08-23T00:01:03Z` | absent / owned-cleaned | exact cookie removed; idempotent bounded cleanup |
| temporary path | `/tmp/opencode/f65-remediation3-refresh-launch.sh` | same refresh run; exact launcher path registered before use | `2026-08-22T23:59:49Z` / `2026-08-23T00:01:03Z` | absent / owned-cleaned | exact launcher removed; no unrecorded file deletion |

The first launcher attempt failed shell parsing before process execution; its
script was corrected in the exact owned temporary path. The subsequent exact
preflight found port 8000 absent, so no unknown process was adopted; the
newest Omaha listener was then started and verified. Pre-existing
`data/test_e2e.db` was preserved; `data/test_e2e_short_ttl.db`, ports 8765 and
8767 were absent after focused validation. No foreign or production resource
was touched.

### Surgical remediation 3/3 delivery receipt

- Owner-authorized startup operations: `uv run task db-migrate` rc 0;
  `uv run task db-seed` rc 0 with `seed skipped: 3 user(s) already present`;
  server startup executed Alembic startup checks and quote refresh
  `refreshed=1`. No reset, clear, commit, snapshot, or production DB command.
- URL: `http://192.168.1.4:8000` from `bash scripts/print_lan_url.sh`.
- Health: `/healthz` -> `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- DB before/after: `11 classes / 90 assets / 88 positions` both sides;
  after profile counts `Italo 6/47/46`, `Ana 5/43/42`, `Família 0/0/0`
  (`classes/assets/positions`).
- Dashboard smoke: `RF Din` count `5`.
- F65 current-source smoke: `Revisar posições` count `1`,
  `import-review-section` count `2`, `import-diff-disclosure` count `4`.
- Delivery server: `0.0.0.0:8000`, PID/PGID `282052/282048`, newest worktree
  active and intentionally preserved.

### Surgical remediation 3/3 canonical review isolation

Focused E2E used exact disposable test DB and ports 8765/8767 only; all exited
and were bounded-cleaned. Pre-existing `data/test_e2e.db` stayed untouched.
No unowned relevant process, listener, test DB, or declared temporary resource
remains except intentionally active owner-authorized delivery PID/PGID and log
on port 8000. Canonical `uv run task test` was not launched because I10 is
`maintenance-suspended`; review owns canonical verification. No baseline or
allowlist exception was used.

## Surgical owner-authorized follow-up — pre-edit boundary

- Before this follow-up edit, captured `git diff HEAD~1 --` and
  `git status --short --branch`. The relevant pre-existing diff boundary was
  the F65 implementation already present in
  `src/omaha/routes/imports.py`,
  `src/omaha/templates/_patrimonio_add_asset_modal.html`,
  `src/omaha/static/app.css`, `tests/test_import_preview.py`, and
  `tests/e2e/test_import_modal.py`: baseline capture/triage response, the
  three-section modal, 1200px/diff CSS, and their focused tests. Existing
  unrelated worktree boundary was `openspec/roadmap.md`, untracked F63 dossier,
  and untracked import-review dossier. These hunks and files are preserved;
  follow-up edits are limited to the owner-authorized F65 correction below.

## Surgical owner-authorized follow-up — execution evidence

- Changed symbols/files: `_build_absent_rows` and additive `triage.absent` in
  `src/omaha/routes/imports.py`; modal copy, four-section hydration, absent
  read-only rendering, and assignment exclusion in
  `src/omaha/templates/_patrimonio_add_asset_modal.html`; absent section and
  non-help disclosure cursor in `src/omaha/static/app.css`; API absent/profile
  scope/no-commit assertions in `tests/test_import_preview.py`; modal copy,
  hover/focus disclosure, and absent confirmation-wire assertions in
  `tests/e2e/test_import_modal.py`. Existing F65 hunks remain intact.
- `uv run task test-file tests/test_import_preview.py` -> 15 passed in 5.53s
  (`f65-followup-api-20260822T210000Z`). Receipt rerun with
  `PYTEST_ADDOPTS=-s` -> 15 passed in 4.58s
  (`f65-followup-api-receipt-20260822T214000Z`), exact test DB receipt
  `/tmp/omaha-conftest-safe-8rej03oe/portfolio.db`, exact temp receipt
  `/tmp/pytest-of-juca/pytest-139`; both runners exited naturally and owned
  resources were absent afterward.
- E2E attempt `uv run task test-file tests/e2e/test_import_modal.py` under
  isolated-run registration `f65-followup-e2e-isolated-20260822T214500Z`
  returned 1 failed / 5 passed. Failure is test assertion drift in the new
  selector: `.modal-title` matched three hidden modal headings; the requested
  review heading itself rendered `Revisar posições`. The run's helper
  `sitecustomize` failed before collection because `tests` was unavailable to
  Python startup, so the fixture used its original `data/test_e2e.db` target.
- Safety incident/blocker: preflight found pre-existing
  `data/test_e2e.db` (size 159744, mtime 2026-08-22 17:38:50 -0300), while
  ports 8765/8767 and `data/test_e2e_short_ttl.db` were absent. The E2E fixture
  deleted/recreated that pre-existing test DB during the failed attempt. It is
  test-only but not current-run-owned; no restore, deletion, adoption, or
  masking action was taken. Exact current-run server PID/PGID `241027`/`240919`
  exited with `-15`, port 8765 was free afterward. Exact run log
  `/home/juca/github/omaha/tmp/uvicorn-logs/e2e-live-url-fbps9cuq.log` and
  pytest path `/tmp/pytest-of-juca/pytest-140` are preserved pending owner
  isolation decision. The temporary helper `/tmp/opencode/sitecustomize.py`
  was exact current-run-owned and removed with bounded cleanup.
- No lint or refresh-for-test was run after this blocker. No production DB was
  targeted. Canonical full suite remains `NOT RUN — maintenance-suspended`.

## Surgical remediation 1/2 — execution evidence

- Pre-edit boundary captured with `git diff HEAD~1 --` before this pass. It
  contained existing F65 implementation hunks in exactly the five runtime/test
  files authorized by owner: `src/omaha/routes/imports.py`,
  `src/omaha/templates/_patrimonio_add_asset_modal.html`,
  `src/omaha/static/app.css`, `tests/test_import_preview.py`, and
  `tests/e2e/test_import_modal.py`. Existing non-F65 boundaries were
  `openspec/roadmap.md`, untracked F63 dossier, and untracked import-review
  dossier; all remain untouched. This pass also owns only F65 `design.md` and
  `tasks.md` documentation updates.
- Required corrections implemented: normalized-name `Ausentes` membership;
  ETH-style same-name/different-ticker regression and no-mutation confirmation;
  review-modal-scoped title selector; in-flow prior-value disclosure visible
  on hover/focus; no `?` or fabricated prior value; and visual treatment B
  neutral rows with semantic header/border edges and stronger focus ring.
- Changed symbols/files: `_build_absent_rows` and `triage["absent"]` in
  `src/omaha/routes/imports.py`; review disclosure/state styles in
  `src/omaha/static/app.css`; scoped title and exact prior-value assertions in
  `tests/e2e/test_import_modal.py`; normalized-name ETH regression in
  `tests/test_import_preview.py`; implementation decisions in `design.md`.
- Focused remediation validation: first API run
  `f65-remediation-api-20260822T` failed 9 tests with `NameError` because the
  new direct normalized-name call lacked its import; this was corrected in
  `imports.py`. Rerun `uv run task test-file tests/test_import_preview.py` ->
  16 passed in 4.92s (`f65-remediation-api-20260822T2217Z`). E2E first run
  `f65-remediation-e2e-20260822T2215Z` proved the scoped title selector and
  exposed disclosure visibility failure; CSS was corrected to use modal-field
  hover/focus-within. Second run exposed only an over-specific expected prior
  text (`Qtde` had valid `Não havia posição`); test was corrected. Final
  `uv run task test-file tests/e2e/test_import_modal.py` -> 6 passed in 33.12s
  (`f65-remediation-e2e-20260822T2219Z`). `uv run task lint` -> passed
  (`f65-remediation-lint-20260822T2219Z`); `git diff --check` -> passed
  (`f65-remediation-artifacts-20260822T2220Z`).
- Focused-run ownership ledger: API process group PID/PGID `248682` started
  `2026-08-22T22:14:06Z`, exited `2026-08-22T22:14:13Z`, owned-current-run
  and `owned-cleaned` via exact idempotent no-op. Final E2E process group was
  run-created and exited naturally; exact task-runner resources for runs
  `f65-remediation-e2e-20260822T2215Z`, `...2218Z`, and `...2219Z` were
  `owned-cleaned` with no broad cleanup. Owner-authorized exact disposable
  test DB `data/test_e2e.db` was registered before each run, classified
  test-only/current-run use, and left untouched after fixture lifecycle; no
  production/dev DB was targeted. Exact E2E server child/listener port 8765
  was run-created per receipt and exited with runner; no foreign process was
  touched. Out-of-bound temp/log paths remain preserved/non-target.
- Delivery refresh preflight was blocked safely: pre-existing listener
  `0.0.0.0:8000`, PID `229810`, PGID `229806`, parent command `uv run uvicorn
  omaha.main:app --host 0.0.0.0 --port 8000`, started
  `2026-08-22 17:57:00` (local), was not current-run-owned. Existing health
  was read-only green at `http://192.168.1.4:8000/healthz`; exact process,
  port, and dev DB `data/portfolio.db` were preserved. No kill, adoption,
  replacement, or DB reset was attempted. A fresh refresh receipt cannot be
  issued until owner provides isolated runner/ownership for port 8000.

## Surgical remediation 2/2 — execution evidence

- Pre-edit boundary was captured before editing with `git diff HEAD~1 --` and
  `git status --short --branch`. Complete pre-existing boundary: modified
  `openspec/PRD.md`; deleted T34 dossier files
  `openspec/changes/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58/`
  (`.openspec.yaml`, `design.md`, `proposal.md`, both delta specs, and
  `tasks.md`); modified `openspec/roadmap.md`; existing F65 implementation
  hunks in `src/omaha/routes/imports.py`,
  `src/omaha/templates/_patrimonio_add_asset_modal.html`,
  `src/omaha/static/app.css`, `tests/test_import_preview.py`, and
  `tests/e2e/test_import_modal.py`; untracked F63 dossier; untracked F65
  dossier; and untracked import-review dossier. No F63 file was read for
  implementation or edited. This pass owns only the five named F65 runtime/test
  files plus F65 `design.md` and `tasks.md`.
- Remediation changes: `_diff_display`/`_changed_field` now emit typed BRL
  integer and quantity prior displays; modal `diffPreviousDisplay` delegates
  visible values to canonical BRL/quantity formatters and disclosure visible
  text is prior value only; disclosure CSS is absolute non-flow overlay with
  no icon; Compra/Venda labels are transparent neutral checkbox controls; the
  class swatch element is removed while class-color cell/select and pending
  state remain driven by the wrapper `x-effect`. Changed symbols/files are
  limited to the seven owned files above.
- Targeted assertions added/adjusted: API quantity and
  `116615.5300 -> R$ 116.616` prior formatting; E2E prior-only overlay,
  absolute positioning, incoming text preservation, BRL integer formatting,
  neutral Compra/Venda computed style, class select/cell color retention, and
  absent swatch absence.
- Focused API: `uv run task test-file tests/test_import_preview.py` -> 17
  passed in 8.35s (`f65-remediation2-api-20260822T`, PID/PGID `268762`,
  natural exit, exact cleanup no-op, `owned-cleaned`).
- Focused isolated E2E final: `uv run task test-file
  tests/e2e/test_import_modal.py` with exact current-run isolation plugin and
  DB roots -> 7 passed in 29.46s (`f65-remediation2-e2e-final4-20260822T`,
  PID/PGID `273739/273739`, ports 8765/8767 absent after run, exact DB
  roots/plugin bounded-cleaned, `owned-cleaned`). Earlier diagnostic isolated
  copy attempts timed out before test execution and were bounded-cleaned;
  intermediate E2E runs exposed the removed-swatch `x-effect` dependency and
  over-specific geometry assertions. Both were corrected; no test was skipped,
  weakened, xfailed, or deleted.
- Lint: first `uv run task lint` exposed one owned-test E501 and exited 1;
  line was corrected. Final `uv run task lint` -> passed
  (`f65-remediation2-lint-final-20260822T`, PID/PGID `275821/275821`, natural exit,
  exact cleanup no-op, `owned-cleaned`). `git diff --check` -> passed.
- Refresh receipt: `f65-remediation2-refresh-20260822T`. Before replacement,
  exact pre-existing PID `256705`, PGID `256702`, listener `0.0.0.0:8000`, and
  command `uvicorn omaha.main:app --host 0.0.0.0 --port 8000` were verified;
  owner-authorized exact PGID TERM replaced only that Omaha group. Authorized
  operations executed: `uv run task db-migrate` rc 0 and `uv run task db-seed`
  rc 0 against local-dev `data/portfolio.db`; new server startup log records
  Alembic startup, idempotent seed skip, and `quote refresh OK: refreshed=1`.
  DB counts were `11 classes / 90 assets / 88 positions` before and after.
  Read-only profile breakdown after startup: `Italo 6/47/46`, `Ana 5/43/42`,
  `Família 0/0/0` (classes/assets/positions).
  New Omaha server remains active at `0.0.0.0:8000` (PID/PGID `277274/277270`);
  initial health probe raced
  startup and was retried successfully. Final health was `ok`, dashboard smoke
  counted `RF Din` 5, and F65 source visual smoke found `Revisar posições` plus
  `import-review-section`. Exact cookie/launcher paths were removed
  idempotently; server/log are intentionally preserved for delivery.
- Ownership receipts: API
  `/tmp/opencode/f65-remediation2-api-20260822T.receipt`; isolated E2E final
  `/tmp/opencode/f65-remediation2-e2e-final4-20260822T.receipt`; lint
  `/tmp/opencode/f65-remediation2-lint-final-20260822T.receipt`; refresh
  `/tmp/opencode/f65-remediation2-refresh-20260822T.receipt`. Each records
  `resource_kind`, exact `resource_id`, current F65 owner/evidence,
  `started_at`/`ended_at` where exited, status, classification, observed
  lifecycle, and bounded cleanup result. Focused E2E used only exact
  run-created DB/temp resources; pre-existing `data/test_e2e.db` remained
  untouched. No foreign process, listener, DB, or out-of-bound temp resource
  was adopted, killed, freed, or deleted.
- Canonical review isolation: full `uv run task test` was not launched because
  I10 is `maintenance-suspended`; review owns canonical verification. Relevant
  focused-run process/listener/test-DB inventory is clean except intentionally
  active current-run Omaha PID/PGID on port 8000 and its preserved log. No
  baseline or allowlist exception was used.

## Review Findings

### Review R2
Scope audit: proposal requirements pass; all three delta specs plus
owner-authorized four-group follow-up pass; scenarios pass; tasks 13/13 pass;
design decisions and remediation decisions pass; changed symbols pass;
implementation/test scope pass (only the five named runtime/test files contain
F65 implementation hunks, with F65 dossier edits separately bounded);
four mutually exclusive groups pass (`new`, `changed`, `unchanged`, `absent`);
name-normalized/profile-scoped `Ausentes` pass; absent rows are read-only and
non-committable in API and excluded from assignment/commit wire data; incoming
values and broker totals pass; canonical previous-value-only overlay, absolute
non-flow positioning, hover/focus behavior, and `116615.5300` → `R$ 116.616`
formatting pass; `Revisar posições`, neutral Compra/Venda controls, class color
select semantics, and removed swatch pass; matcher/compatibility arrays,
explicit commit, snapshot/audit, Família guard, preview non-mutation,
profile/TTL ownership, and LAN/runtime boundaries pass; no test deletion,
skip, xfail, retry, masking, or coverage reduction found; no area not
assessable.

Full suite: `uv run task test` -> `NOT RUN — maintenance-suspended` under
owner-authorized I10 state in `openspec/PRD.md` §4.13 and
`openspec/config.yaml`; review did not launch canonical suite. Applicable
focused product evidence: `uv run task test-file tests/test_import_preview.py`
-> 17 passed in 8.35s (`f65-remediation2-api-20260822T`); isolated
`uv run task test-file tests/e2e/test_import_modal.py` -> 7 passed in 29.46s
(`f65-remediation2-e2e-final4-20260822T`); `uv run task lint` -> passed
(`f65-remediation2-lint-final-20260822T`); `git diff --check` -> passed;
`openspec validate f65-triagem-de-ativos-por-estado-no-preview-de-posicao
--type change --strict` -> valid; `openspec validate --specs --strict` -> 75
passed. Focused product tests green. Canonical duration and six-lane receipt
are not applicable while suspension remains active.

Preflight: ledger receipts
`/tmp/opencode/f65-remediation2-api-20260822T.receipt`,
`/tmp/opencode/f65-remediation2-e2e-final4-20260822T.receipt`,
`/tmp/opencode/f65-remediation2-lint-final-20260822T.receipt`, and
`/tmp/opencode/f65-remediation2-refresh-20260822T.receipt` were inspected.
Each declared resource has `resource_kind`, exact `resource_id`, current F65
owner, owner evidence, start/end state, classification, evidence, and bounded
cleanup. Focused process groups, E2E ports 8765/8767, isolated test DB roots,
and helper paths classify `owned-cleaned` or `absent`. Delivery listener
`0.0.0.0:8000`, PID/PGID `277274/277270` (receipt parent PGID `277270`) and
preserved log classify `owned-current-run` with owner-authorized local startup
and intentional delivery preservation; no foreign or unknown relevant state
was adopted, killed, freed, deleted, or allowlisted. Decision: trusted
preflight; suspension forbids canonical launch.

Postflight: focused API, isolated E2E, lint, artifact validation, and bounded
temporary-resource receipts ended naturally with exact cleanup; E2E ports and
isolated DB/temp roots are absent/`owned-cleaned`; delivery server/log remain
intentionally active/preserved under owner handoff. No review-run child or
canonical-suite cleanup exists because canonical command was not launched.
Decision: postflight evidence sufficient for suspended gate.

Runner isolation: pass. Relevant process/listener/test-DB/temp inventory had no
unowned state at review handoff. Active port 8000 is exact owner-authorized F65
delivery state, not a baseline or foreign-resource exception. No broad cleanup
or pathname-based adoption occurred.

Verdict: APPROVED

No blocking findings.
