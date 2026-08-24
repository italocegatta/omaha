## Test strategy

Focused acceptance uses existing TestClient/API and Playwright browser tests;
no connector, credential, network, production DB, destructive seed, or live
commit smoke is allowed. API tests prove F65 payload/classification/count/row
compatibility and deterministic ordering within groups. Browser tests prove
actual rendered section sequence for mixed triage, manual/sync-shaped/local
hydration, legacy fallback, hidden empty groups, controls, and no commit before
confirmation.

Test files:

- `tests/test_import_preview.py`
- `tests/e2e/test_import_modal.py`

Focused commands:

- `uv run task test-file tests/test_import_preview.py`
- `uv run task test-file tests/e2e/test_import_modal.py`
- `uv run task lint`

Canonical `uv run task test` remains `NOT RUN — maintenance-suspended` per
`openspec/config.yaml`; no lane substitution, skip, xfail, retry, or test
deletion is permitted. Runtime Apply must also invoke `refresh-for-test` and
record its delivery receipt, but Propose does not run that browser delivery
workflow.

## 1. Preconditions and change boundary

- [x] 1.1 **Record owner browser-rendering/mock approval before Apply.** Target:
  F67 owner gate and `openspec/roadmap.md` F67 dependency. Exact change: obtain
  approval for a mixed payload rendering `Novos`, `Ausentes`, `Alterados`,
  `Inalterados` in order, with empty-group suppression, counts, rows, and
  controls; record approver, timestamp, artifact/mock path, payload shape, and
  rendered sequence in the Apply evidence. Preserve: D06 archived handoff and
  F65 approval; no Apply without attributable approval. Acceptance: approval
  receipt exists before any runtime edit; absent receipt returns
  `BLOCKED_FOR_IMPLEMENTATION_BRIEF`/blocked Apply rather than guessing. Test
  file/scenario: owner gate evidence, no product test. Focused taskipy command:
  N/A (approval gate). Independent oracle: owner approval record plus exact
  mixed-batch rendering artifact.

- [x] 1.2 **Capture pre-edit boundary and enforce slice allow-list.** Target:
  F67 change folder and repository status. Exact change: inspect only
  `src/omaha/templates/_patrimonio_add_asset_modal.html`,
  `src/omaha/routes/imports.py`, `tests/test_import_preview.py`, and
  `tests/e2e/test_import_modal.py` symbols named in `design.md`; record from/to
  state before editing. Preserve: all pre-existing worktree changes and every
  F60/F65/D06/T36/F68/F63/T31 artifact. Acceptance: implementation diff can
  contain only listed F67 runtime/test files plus F67 dossier/delta; no D06
  archive edit, no timeout/sync file, no DB/seed/migration. Test
  file/scenario: changed-file audit. Focused taskipy command: `uv run task
  lint`. Independent oracle: `git status --short --untracked-files=all`,
  `git diff --check`, and exact changed-file allow-list.

## 2. Apply fixed section sequence

- [x] 2.1 **Reorder shared triage section metadata.** Target:
  `src/omaha/templates/_patrimonio_add_asset_modal.html`,
  `Alpine.store('importModal').triageSections`, plus Step 2
  `template x-for="section in ...triageSections"`. Exact change: change only
  metadata order from `new`, `changed`, `unchanged`, `absent` to `new`,
  `absent`, `changed`, `unchanged`; keep labels exact and reuse existing
  `x-if` empty filtering. Preserve: `hydratePreview`, `openPreview`,
  `uploadFile`, `resetState`, `clearPreview`, `goBackToStep1`, all eight table
  columns, row testids, `broker_ticker` hidden identity, assignments,
  controls, diff disclosure, formatting, and explicit `commit()`. Acceptance:
  every entry path renders non-empty sections only in fixed order and no client
  row sort/reclassification is introduced. Test file/scenario:
  `tests/e2e/test_import_modal.py` mixed-batch, local `openPreview`, and legacy
  hydration scenarios. Focused taskipy command: `uv run task test-file
  tests/e2e/test_import_modal.py`. Independent oracle: rendered `h3` text list,
  section/row testid counts, hidden ticker keys, and zero commit requests before
  confirmation.

- [x] 2.2 **Preserve API preview contract without server presentation sort.**
  Target: `src/omaha/routes/imports.py`, `_build_preview_response`,
  `_triage_sort_key`, `_build_absent_rows`, `preview_import`, `get_preview`,
  and `MyProfitSyncService.status_for_profile`. Exact change: no behavior
  change unless focused test exposes F65 regression; if touched, preserve four
  group membership and existing within-group sort exactly, never use JSON key
  order as UI order. Preserve: `auto_matched`, `unmatched`, `asset_classes`,
  additive `triage`, baseline/raw-list legacy handling, counts/values/zero and
  missing data, profile/Family guards, TTL, job polling, sanitized errors,
  timeout (`pollDelay × maxPolls`), no preview mutation, and commit boundary.
  Acceptance: API response remains semantically identical except any explicitly
  approved additive assertion; mixed batch contains each expected row once in
  its F65 group and each group retains deterministic name/ticker order. Test
  file/scenario: `tests/test_import_preview.py` triage classification,
  deterministic ordering, absent, and legacy raw-list scenarios. Focused
  taskipy command: `uv run task test-file tests/test_import_preview.py`.
  Independent oracle: JSON group membership/counts, legacy keys, exact ordered
  row names/tickers within each group, and unchanged DB/audit counts.

## 3. Add focused acceptance evidence

- [x] 3.1 **Add API mixed-batch compatibility regression.** Target:
  `tests/test_import_preview.py`, `TestPostImportPreview` triage scenarios.
  Exact change: add or extend one deterministic fixture/assertion proving
  `new`, `changed`, `unchanged`, and `absent` counts/rows, legacy arrays, and
  within-group name/ticker order survive payload construction; do not assert
  JSON object key order as UI behavior. Preserve: existing F65 baseline,
  absent name matching, totals, profile scoping, legacy fallback, and no-
  mutation assertions. Acceptance: focused API test passes with all four groups
  populated or a mixed fixture plus existing absent case, no duplicate/missing
  row, and compatibility arrays unchanged. Test file/scenario: named API
  mixed-batch/legacy scenarios. Focused taskipy command: `uv run task test-file
  tests/test_import_preview.py`. Independent oracle: pytest exit 0, explicit
  row/count assertions, and DB counts before/after preview equal.

- [x] 3.2 **Add browser order and pathway regression.** Target:
  `tests/e2e/test_import_modal.py`, existing `test_import_modal_happy_path` and
  local `openPreview` scenarios. Exact change: prove exact rendered sequence for
  a mixed payload, hidden empty sections, manual upload, sync-shaped handoff,
  local/mock hydration, and legacy fallback; retain controls, count, row,
  assignment, diff, cancellation, explicit commit, and no-pre-confirm commit
  assertions. Preserve: F60/D06 sync tests untouched; no live connector or
  timeout test added. Acceptance: browser sees section header order exactly
  `Novos`, `Ausentes`, `Alterados`, `Inalterados` when all non-empty and the
  same relative order after empty groups disappear; all existing controls/rows
  remain available. Test file/scenario: `tests/e2e/test_import_modal.py`.
  Focused taskipy command: `uv run task test-file tests/e2e/test_import_modal.py`.
  Independent oracle: Playwright locator order/counts, row testids, assignment
  keys, and intercepted fetch log with zero `/api/import/commit` before click.

- [x] 3.3 **Run focused quality and scope checks.** Target: all F67 changed
  files and artifacts. Exact change: run API/browser focused commands and lint;
  inspect diff for no unrelated edits, no test masking, and no D06/timeout
  drift. Preserve: current test population, taskipy entrypoints, no skip/xfail/
  retry, and maintenance-suspended full-suite policy. Acceptance: all applicable
  focused commands pass; lint and whitespace checks pass; no runtime diff exists
  outside design change map. Test file/scenario: changed-file and artifact
  audit. Focused taskipy command: `uv run task lint` plus the two focused test
  commands above. Independent oracle: pytest exit 0, `git diff --check`,
  `git status --short --untracked-files=all`, and exact allow-list review.

## 4. Browser delivery and handoff

- [x] 4.1 **Refresh browser-visible runtime after Apply.** Target: F67 runtime
  delivery boundary. Exact change: invoke `refresh-for-test` after template
  implementation, using only owner-authorized DB tasks; record URL, `/healthz`,
  DB counts, seeded dashboard marker, server PID, and current F67 rendering.
  Preserve: production DB untouched without explicit authorization, bind
  `0.0.0.0`, no broad process kill, D06 removals, sync timeout/error behavior,
  and no stale server bytes. Acceptance: mandatory delivery receipt exists and
  browser opens current F67 source with populated/known state; missing owner DB
  authorization is recorded as a blocker, not bypassed. Test file/scenario:
  browser delivery smoke. Focused taskipy command: skill-owned
  `task db-migrate`/`task db-reset`/`task db-clear-assets`/`task db-seed` only
  if explicitly authorized by owner; otherwise no DB write command. Independent
  oracle: refresh receipt fields and authenticated rendered section sequence.

- [x] 4.2 **Stop at owner validation before Review/Applied.** Target: F67
  browser rendering/mock evidence and roadmap lifecycle. Exact change: present
  mixed-batch rendering for owner approval; do not archive, commit, push, or
  alter other slices. Preserve: exact change id and all exclusions. Acceptance:
  owner confirms fixed order, no empty sections, counts/rows/controls, legacy
  compatibility, and unchanged D06/timeout surfaces; absent approval keeps F67
  blocked. Test file/scenario: owner browser acceptance checklist. Focused
  taskipy command: N/A after receipt. Independent oracle: attributable owner
  approval record linked to current runtime/mock artifact and `openspec status`
  still reports the exact change artifacts complete, with no archive/finalize.

## 5. Proposal-gate validation

- [x] 5.1 **Validate exact F67 artifacts and stable specs.** Target:
  `openspec/changes/f67-ordenar-grupos-da-revisao-de-posicoes/` and all
  `openspec/specs/`. Exact change: run strict change validation and strict
  stable-spec validation; do not implement, archive, sync stable specs, commit,
  or update unrelated roadmap slices. Preserve: exact change id and only F67
  dossier files. Acceptance: proposal, design, tasks, and
  `specs/import-modal/spec.md` validate; stable spec health remains green; no
  product code/test changed in this Propose gate. Test file/scenario: artifact
  validation. Focused taskipy command: N/A (OpenSpec CLI validation; no raw
  product command). Independent oracle: `openspec validate --changes
  "f67-ordenar-grupos-da-revisao-de-posicoes" --strict --json`, `openspec
  validate --specs --strict --json`, `git diff --check`, and changed-file audit.
## Execution Evidence

### Preconditions — Initial Apply — 2026-08-24

- **Owner approval:** owner approved intended browser rendering/order on 2026-08-24 before runtime edits. Approval covers mixed F65 payload rendering `Novos → Ausentes → Alterados → Inalterados`, empty-section suppression, counts, row membership, editable controls, hidden assignment keys, and explicit confirmation boundary. Artifact/mock: F67 design fidelity ledger plus deterministic mixed-batch browser mock added to `tests/e2e/test_import_modal.py::test_review_sections_keep_fixed_order_for_sync_local_and_legacy_hydration`.
- **Approval payload shape:** additive `triage` with all four groups in arbitrary object-key order, compatibility `auto_matched`/`unmatched` arrays, `asset_classes`, row values, `changed_fields`, and absent read-only metadata.
- **Pre-edit boundary:** pre-existing worktree changes are `openspec/roadmap.md` plus four F60 visual artifacts; they are not owned by F67 and remain untouched. F67 dossier was pre-existing untracked planning input. No runtime/test file had F67 edits before this Apply.
- **Allow-list:** F67 runtime/test edits are limited to `src/omaha/templates/_patrimonio_add_asset_modal.html`, `tests/test_import_preview.py`, and `tests/e2e/test_import_modal.py`, plus this F67 dossier. `src/omaha/routes/imports.py` remains verification-only; D06 archive, timeout/sync files, DB, seed, migration, connector, CSS, and unrelated slices are excluded.
- **Implementation result:** reordered only shared `triageSections` metadata to `new`, `absent`, `changed`, `unchanged`; hydration, fallback, x-if filtering, controls, hidden ticker identity, and API serializer remain unchanged.

### Focused validation — Initial Apply — 2026-08-24

- **API:** run `F67-API-20260824T-INITIAL`, shell PID `85108`, registered at
  `2026-08-24T11:48:20Z`; `T29_RUN_ID=F67-API-20260824T-INITIAL
  T29_DB_RECEIPT_LANE=integration uv run task test-file
  tests/test_import_preview.py` → **17 passed in 5.90s**. Child process exited;
  classification `owned-cleaned`, cleanup result `task_process_exit_0`.
  Test-only session DB was runner-created and bounded; production DB untouched.
- **Lint:** first run `F67-LINT-20260824T-INITIAL` exposed 11 E501 findings in
  new browser fixture and exited 1; no test was masked. Lines were wrapped.
  Retry exposed 2 remaining E501 findings and exited 1; both were wrapped.
  Final run `F67-LINT-20260824T-FINAL`, shell PID `87744`, registered at
  `2026-08-24T11:51:41Z`; `T29_RUN_ID=F67-LINT-20260824T-FINAL uv run task lint`
  → **all hooks passed**. Classification `owned-cleaned`, cleanup result
  `task_process_exit_0`.
- **OpenSpec/spec health:** run `F67-SPEC-20260824T-INITIAL`, shell PID
  `88924`, registered at `2026-08-24T11:52:12Z`; strict active-change
  validation → **3/3 changes valid**, including F67; strict stable-spec
  validation → **77/77 specs valid**. Classification `owned-cleaned`, cleanup
  result `command_exit_0`.
- **Diff hygiene:** `git diff --check` passed before this evidence update.

### Blocked focused browser/delivery validation — Initial Apply — 2026-08-24

- **Blocker:** exact declared test-only path `data/test_e2e.db` was
  pre-existing before F67 run, inode `518344`, size `159744`, mtime
  `2026-08-24 02:48:54 -0300`; `data/test_e2e_short_ttl.db` was absent. The
  E2E fixture unconditionally deletes `data/test_e2e.db` before launching its
  server and wipes it during tests. Current F67 run has no ownership receipt or
  explicit owner authorization to delete/adopt this pre-existing test DB.
- **Preserved resources:** no E2E command launched; no test DB deletion,
  adoption, mutation, or cleanup occurred. Port `8765` and `8767` had no
  listener. Production `data/portfolio.db` was not touched.
- **Refresh blocker:** port `8000` is active as pre-existing prior D06 delivery
  listener PID `67046`, PGID `67038`, command
  `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`, with prior receipt
  `/tmp/opencode/d06-refresh-ownership-ledger-20260824T-continuation.md`.
  F67 has no current-run ownership or explicit current-run restart
  authorization; no kill, adoption, or refresh was attempted.
- **Ownership ledger:** preflight run `F67-E2E-20260824T-INITIAL` registered at
  `2026-08-24T11:49:00Z`; `data/test_e2e.db` classified `pre-existing` and
  preserved. Refresh preflight run `F67-REFRESH-20260824T-INITIAL` registered at
  `2026-08-24T11:49:21Z`; port `8000` classified `pre-existing` and preserved.
  No current-run child, listener, DB, temporary path, or log residue was
  created by blocked runs; cleanup result is bounded idempotent no-op.
- **Open tasks:** 3.2 browser regression, 3.3 final focused checks, 4.1
  refresh-for-test receipt, and 4.2 owner validation remain open. Do not claim
  READY_FOR_REVIEW until exact test DB cleanup authorization/isolated runner
  and exact port-8000 restart authorization are supplied.

### Continuation authorization and ownership preflight — 2026-08-24

- **Owner authorization:** owner authorized this Apply continuation on
  2026-08-24 to delete exactly `data/test_e2e.db` and restart only identified
  Omaha PID `67046` / PGID `67038`; owner validated intended F67 order.
  Authorized DB impact: delete test-only E2E SQLite file so fixture can create
  its own runner DB. `data/test_e2e_short_ttl.db` and
  `data/portfolio.db` are explicit non-targets. Authorized process impact:
  restart identified Omaha listener only through supported refresh workflow.
- **Preflight at 2026-08-24T12:30:48Z:** PID `67046` had PPID/PGID
  `67038` and command `/home/juca/github/omaha/.venv/bin/python .../uvicorn
  omaha.main:app --host 0.0.0.0 --port 8000`; PGID `67038` was its uvicorn
  launcher group. Listener inspection matched PID `67046` on `0.0.0.0:8000`.
  `data/test_e2e.db` existed with inode `518344`; short-TTL DB was absent;
  `data/portfolio.db` existed with inode `241846`. No identity mismatch.
- **Pre-operation ownership ledger:** run `F67-CONTINUATION-20260824T123048Z`.
  Registered before authorized resource use: `data/test_e2e.db` exact path,
  owner `F67 apply / gpt-5.6-luna`, owner evidence = this continuation's
  explicit owner authorization and preflight inode `518344`; process group
  `67038` / child PID `67046`, owner evidence = exact preflight command,
  PPID/PGID, listener, and worktree identity. Entries classified
  `owned-current-run` by explicit authorization; no other PID, PGID, port,
  DB, or path is targetable.
- **Refresh result:** old authorized PGID `67038`/PID `67046` exited after
  exact-group `SIGTERM`; no unrelated process was signaled. Supported refresh
  launch command was `setsid bash -c 'exec uv run uvicorn omaha.main:app
  --host 0.0.0.0 --port 8000'`; new launcher PID/PGID `89995`, uvicorn child
  PID `89998`, listener `0.0.0.0:8000`. `http://192.168.1.8:8000/healthz`
  returned `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
  `data/test_e2e.db` is absent after authorized deletion; short-TTL DB remains
  absent; `data/portfolio.db` remains inode `241846` and was not targeted.
- **Focused E2E ownership preflight — run
  `F67-E2E-20260824T123231Z`:** exact test DB target `data/test_e2e.db` was
  absent and owner-authorized for runner creation; `data/test_e2e_short_ttl.db`
  was absent and non-target; ports `8765` and `8767` had no listeners. The
  task runner owns its child process/group, exact lane log paths under
  `tmp/uvicorn-logs/`, and any exact runner-declared temporary DB paths emitted
   by `T29_DB_TARGET`/`T29_TEMP_ROOT`; no pre-existing relevant resource was
   adopted. Registration precedes launch; process IDs, PGIDs, log paths, temp
   root, and lifecycle timestamps are captured from T29 receipts before use.
- **E2E result at 2026-08-24T12:33:54Z:** exact command exited 0:
  `T29_RUN_ID=F67-E2E-20260824T123231Z T29_DB_RECEIPT_LANE=e2e uv run task
  test-file tests/e2e/test_import_modal.py` → **8 passed in 33.20s**.
  Runner-owned server/process groups exited and ports `8765`/`8767` are free;
  no lane log or temporary declared-boundary residue remained. Exact
  `data/test_e2e.db` was recreated by this run (inode `518289`) and is
  classified `owned-current-run`; `data/test_e2e_short_ttl.db` remains absent.
  Before cleanup, no other DB/path was adopted. Authorized bounded cleanup is
   limited to exact `data/test_e2e.db`; cleanup receipt records
   `owned-cleaned`/idempotent absent. Focused browser acceptance covered manual
  upload, sync-shaped/local hydration, legacy fallback, mixed order
  `Novos → Ausentes → Alterados → Inalterados`, empty-section suppression,
  counts/rows/controls, hidden assignment keys, and no pre-confirm commit.
- **E2E cleanup receipt at 2026-08-24T12:34:10Z:** exact current-run inode
  `518289` matched ledger and was bounded-cleaned with `rm --
  data/test_e2e.db`; final classification `owned-cleaned`, result exact
  deletion success. `data/test_e2e.db` is absent. `data/test_e2e_short_ttl.db`
  remains absent/non-target. `data/portfolio.db` remains inode `241846`,
  size `282624`, and was preserved. No foreign or unknown residue was
  touched.
- **API focused-run preflight:** run `F67-API-20260824T123410Z` owned only
  runner-created temporary DB/process/log/temp resources; persistent DBs,
  `data/test_e2e.db`, `data/test_e2e_short_ttl.db`, ports `8000`, `8765`, and
   `8767` as non-targets. Exact T29 identities were registered before launch;
   only exact current-run resources were bounded-cleaned.
- **API result at 2026-08-24T12:35:00Z:** exact command
  `T29_RUN_ID=F67-API-20260824T123410Z T29_DB_RECEIPT_LANE=integration uv run
  task test-file tests/test_import_preview.py` → **17 passed in 5.05s**.
  Test-only temporary DB/process resources exited and were bounded-cleaned by
  task runner; production and persistent E2E DB targets were untouched.
- **Lint-run preflight:** run `F67-LINT-20260824T123600Z` owns only child
  process/group and hook temporary/log resources created by exact command
  `T29_RUN_ID=F67-LINT-20260824T123600Z uv run task lint`; no DB, listener, or
  persistent path is targetable. Register child identity before use and record
  exit/cleanup receipt.
- **Refresh smoke preflight:** run `F67-REFRESH-SMOKE-20260824T123543Z` owns
  exact temporary cookie path `/tmp/f67-refresh-cookie-20260824T123543Z` only;
  path was verified absent before registration. Read-only `GET /healthz`,
  SQLite `SELECT COUNT(*)`, authenticated dashboard GET, and LAN URL discovery
  use no DB write. Cookie path is bounded-cleanup target; port `8000` and new
  server PID/PGID remain owned by continuation refresh ledger, not reaped by
  this smoke run.
- **Refresh smoke first attempt:** health and read-only counts succeeded, but
  `curl -L -X POST` preserved POST across the login 303 and produced expected
  `/` 405; dashboard marker was not claimed. Cookie was owned-cleaned. This is
   command-shape diagnosis only; no product or DB behavior changed. Retry used
   form POST without forced method on redirect and streamed dashboard HTML to a
   parser, avoiding oversized environment arguments; retry completed.
- **Refresh smoke retry diagnosis:** login succeeded and dashboard marker
  counted `RF Din` 5, but profile-select probe omitted form data and issued GET
  to POST-only `/profiles/1/select`, yielding expected 405. Cookie was again
   owned-cleaned; no DB write or foreign cleanup occurred. Final retry used
   explicit empty form POST for profile selection and completed.
- **Refresh delivery receipt — run `F67-REFRESH-SMOKE-20260824T123543Z`,
  completed 2026-08-24T12:38:05Z:**
  `bash scripts/print_lan_url.sh` → `http://192.168.1.8:8000`;
  `/healthz` → `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
  Read-only `data/portfolio.db` counts: **11 classes / 90 assets / 88
  positions**; Italo **6 / 47 / 46**; Ana **5 / 43 / 42**. Authenticated
  dashboard GET with locked family password rendered seeded marker `RF Din`
  **5** times. Current server remains PID `89998`, launcher PID/PGID
  `89995`, bound to `0.0.0.0:8000`. Cookie path
  `/tmp/f67-refresh-cookie-20260824T123543Z` was exact-run
  `owned-cleaned`. No `db-reset` ran: owner authorized only test DB deletion,
  and production `data/portfolio.db` was preserved inode `241846`; counts are
  reported as observed, not normalized.
- **Focused quality result — 2026-08-24:**
  `T29_RUN_ID=F67-LINT-20260824T123600Z uv run task lint` → **all hooks
  passed**; `git diff --check` → pass. Active F67 strict validation → valid;
  stable-spec strict validation → **77/77 valid** (informational long-text
  notices only). Final changed-file audit keeps F67 edits to the listed
  template, API/browser tests, and F67 dossier; `openspec/roadmap.md`, four
  F60 visual artifacts, and T36 dossier remain pre-existing/unowned. No
  `imports.py`, D06 archive, timeout, DB schema/seed, CSS, or unrelated runtime
  file changed. Canonical `uv run task test` remains **NOT RUN —
  maintenance-suspended** per config; focused gate is green.
- **Acceptance/owner validation:** owner authorization and intended order were
  confirmed 2026-08-24. Browser run proved manual upload plus sync-shaped/local
  and legacy hydration render `Novos → Ausentes → Alterados → Inalterados`,
  suppress empty groups, preserve counts/rows/controls/hidden assignment keys,
  and make no commit before explicit confirmation. API run proved F65 groups,
  compatibility arrays, deterministic within-group rows, and no preview DB
  mutation. D06 and F65 scope stayed unchanged. Apply stops before Review,
  Applied, archive, commit, or push.
- **Receipt-completion browser preflight:** run
  `F67-E2E-RECEIPT-20260824T123900Z` executed only the already-covered F67
  mixed-order browser scenario with `-s` so T29 server PID/PGID/log receipts
  are observable. Exact `data/test_e2e.db` is currently absent and is the only
  persistent test target; `data/test_e2e_short_ttl.db`, `data/portfolio.db`,
  ports `8000`, `8765`, and `8767` are non-targets. Register lane child/group,
  exact log, DB, and temp-root identities before launch; bounded-clean only
  exact current-run resources.
- **Receipt-completion browser result — run
  `F67-E2E-RECEIPT-20260824T123900Z`:** exact command exited 0: 1 passed in
  7.71s. T29 owner evidence: parent PID `93128`, parent PGID `93120`, lane
  child PID `93203`, lane PGID `93120`, exact port `8765`, log
  `/home/juca/github/omaha/tmp/uvicorn-logs/e2e-live-url-pyby0dh1.log`, temp
  root `/tmp/pytest-of-juca/pytest-41`; launch/ready/teardown timestamps were
  emitted before resource use and teardown reported child return `-15`,
  `port_free=true`. Exact temp root and log were absent after runner teardown
  (owned-cleaned/idempotent absent). Exact `data/test_e2e.db` inode `518454`
  was current-run-owned; short-TTL DB stayed absent. Bounded cleanup remains
  limited to exact `data/test_e2e.db`.

### Ownership ledger receipts — continuation

| resource_kind | resource_id | owner / owner_evidence | started_at / ended_at | status / classification | evidence / cleanup_result |
|---|---|---|---|---|---|
| process group + listener | old PGID `67038`, Omaha PID `67046`, `0.0.0.0:8000` | `F67 apply / gpt-5.6-luna`; owner authorization in continuation plus exact preflight command/PPID/PGID/listener | `2026-08-24T12:30:48Z` / `2026-08-24T12:32:05Z` (absent observed) | exited / `owned-cleaned` | Exact Omaha identity matched; exact-group `SIGTERM` only; no unrelated process signaled; bounded cleanup success. |
| process group + listener | new launcher PGID `89995`, uvicorn PID `89998`, `0.0.0.0:8000` | `F67 apply / gpt-5.6-luna`; run-created `setsid ... uvicorn --host 0.0.0.0 --port 8000`, health/listener match | `2026-08-24T12:31:34Z` / — | active / `owned-current-run` | Current source server; `/healthz` green; leave active for owner browser validation; no cleanup attempted. |
| test DB | `data/test_e2e.db`, initial inode `518344`, E2E inode `518289`, receipt-run inode `518454` | `F67-E2E` runs; owner authorization and exact current-run creation/deletion receipts | initial `2026-08-24T12:30:48Z`; receipt run `2026-08-24T12:39:29Z` / cleanup observed by `2026-08-24T12:39:50Z` | absent / `owned-cleaned` | Only exact authorized test DB deleted. `data/test_e2e_short_ttl.db` absent/non-target; `data/portfolio.db` inode `241846` preserved. |
| child process group + port | receipt E2E parent PID `93128`, parent PGID `93120`, lane child PID `93203`, PGID `93120`, port `8765` | `F67-E2E-RECEIPT-20260824T123900Z`; T29 launch event emitted before use with exact log/temp identities | `2026-08-24T12:39:29.792Z` / `2026-08-24T12:39:36.661Z` | exited / `owned-cleaned` | T29 teardown return `-15`, `port_free=true`; no lane process/listener residue. |
| log | `/home/juca/github/omaha/tmp/uvicorn-logs/e2e-live-url-pyby0dh1.log` | same T29 launch event, exact run/lane path | `2026-08-24T12:39:29.792Z` / `2026-08-24T12:39:36.661Z` | absent / `owned-cleaned` | Runner removed exact current-run log; no foreign log touched. |
| temporary path | `/tmp/pytest-of-juca/pytest-41` | same T29 `T29_TEMP_ROOT` receipt | `2026-08-24T12:39:29.792Z` / `2026-08-24T12:39:36.661Z` | absent / `owned-cleaned` | Exact declared temp root absent after runner teardown; no pathname discovery/adoption. |
| temporary path | `/tmp/f67-refresh-cookie-20260824T123543Z` | `F67-REFRESH-SMOKE-20260824T123543Z`; verified absent before create | `2026-08-24T12:35:43Z` / `2026-08-24T12:38:05Z` | absent / `owned-cleaned` | Exact cookie removed after read-only health/count/dashboard checks. |

Test-only API/lint child processes and temporary resources exited 0 under run
IDs `F67-API-20260824T123410Z` and `F67-LINT-20260824T123600Z`; no persistent
listener/DB target was used. Their task-runner cleanup was idempotent and left
no declared residue. Canonical full suite remains `NOT RUN —
maintenance-suspended`.

## Review Findings

### Review R1
Scope audit: requirements/scenarios pass; proposal/design/tasks/delta-spec
coherence pass; implementation symbols pass; F65 classification/counts/rows,
controls, hidden assignment keys, empty-section omission, deterministic
within-group ordering, and explicit commit boundary pass; manual upload,
sync-shaped/local hydration, and legacy fallback pass; API route/serializer and
timeout surfaces pass (unchanged); D06 archive handoff/removals pass
(unchanged); refresh delivery receipt pass; focused test and lint evidence pass;
stable-spec health pass; changed-file allow-list pass; no test deletion,
skip/xfail/retry/masking, coverage reduction, or unrelated runtime edit found.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended** per
`openspec/config.yaml` and PRD §4.13. Focused product evidence: API 17 passed
(`tests/test_import_preview.py`, 5.22s review run; Apply receipt 17 passed),
E2E 8 passed (`tests/e2e/test_import_modal.py`, 39.20s review run; Apply
receipt 8 passed), browser receipt scenario 1 passed (7.71s), lint all hooks
passed, `git diff --check` passed. Six canonical lanes were not launched under
suspension; no skips or substitutions used. Coverage/test population was not
reduced; no test file or lane was deleted.

Preflight: inspected Apply ledger entries with required resource fields
(`resource_kind`, `resource_id`, `owner`, `owner_evidence`, `started_at`,
`ended_at`, `status`, `classification`, `evidence`, `cleanup_result`). Review
resource check at `2026-08-24T12:45:41Z`: Omaha launcher/uvicorn PID/PGID
`89995/89998`, listener `0.0.0.0:8000` classified `owned-current-run` from
exact Apply launch receipt; ports `8765` and `8767` absent; short-TTL DB absent;
production `data/portfolio.db` preserved (inode `241846`); review E2E DB was
exact current-run resource, not foreign/unknown. No unowned relevant residue
observed. No canonical runner launched because gate suspended.

Postflight: focused API/lint children exited 0 with runner cleanup. Review E2E
ports and lane resources absent. Exact review-created `data/test_e2e.db` was
bounded-cleaned and verified absent; `data/test_e2e_short_ttl.db` remained
absent; production DB remained preserved. Omaha PID/PGID `89995/89998` and
port `8000` remain active source-server resources owned by Apply refresh and
were not touched. Cleanup classifications: focused children/log/temp
resources `owned-cleaned`; exact test DB `owned-cleaned`; server
`owned-current-run` intentionally active for owner validation.

Runner isolation: applicable focused runs had exact runner-owned DB/process/
temp boundaries and no foreign or unknown residue. Canonical isolated-runner
precondition was not invoked because owner-authorized `maintenance-suspended`
policy forbids launching `uv run task test`; no baseline or allowlist
exception used.

Verdict: **APPROVED**

No blocking findings. Scope complete; F67 may move Applying -> Applied. Owner
validation remains required before archive/finalize/commit/push.
