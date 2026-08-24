## 1. Handoff gates and source lock

- [x] 1.1 Confirm Apply prerequisites before touching runtime: `f60-adicionar-acao-atualizar-posicao-no-patrimonio` is `Applied`, F60 owner visual validation is recorded, and owner approval exists for F63 static mock/prototype/browser rendering. Target: `openspec/roadmap.md` F60/F63 blocks and F60 dossier. Exact change: record approval evidence in apply dossier before implementation; if any item is absent, stop `BLOCKED` without edits. Preserve: proposal scope and roadmap lifecycle. Acceptance: all three approvals are attributable and dated before Apply. Test file/scenario: none; gate evidence only. Focused taskipy command: N/A (handoff gate). Independent oracle: `openspec status --change f60-adicionar-acao-atualizar-posicao-no-patrimonio --json` plus owner approval record.
- [x] 1.2 Capture current user work before implementation and lock F63 changed-file boundary. Target: repository state and exact files named in `design.md`. Exact change: run the PRD §4.14 pre-fix diff check and record from/to boundaries; do not rewrite functional code. Preserve: all pre-existing user changes, `_patrimonio_class_section.html` byte/semantic behavior, and no unrelated files. Acceptance: implementation diff contains only `_rebalance_plan.html`, `app.css`, the two named test files, and F63 artifacts/specs. Test file/scenario: changed-file audit. Focused taskipy command: `uv run task lint`. Independent oracle: `git diff HEAD~1`, `git status --short --untracked-files=all`, and `git diff --check` show no unowned edits or whitespace errors.

## 2. Surgical runtime port

- [x] 2.1 Add canonical sticky hook to `src/omaha/templates/_rebalance_plan.html` asset-plan `<table>` only. Target symbol: line 79 `table.data-table.rebalance-table[data-testid="rebalance-asset-table"]`. Exact change: change class list to include existing `table-sticky-header`; do not alter Alpine `columns`, `<thead>`/`<tbody>` templates, filter controls, sort handler, row key, cell formatter, or action markup. Preserve: one table, eight columns, filters, sorting, data, actions, empty-plan branch, and layout. Acceptance: populated plan renders exactly one table with `data-table rebalance-table table-sticky-header`; empty plan still renders empty state and no table. Test file/scenario: `tests/test_rebalance_page.py::test_rebalance_table_visual_hooks` plus existing empty/populated plan scenarios. Focused taskipy command: `uv run task test-one tests/test_rebalance_page.py::test_rebalance_table_visual_hooks`. Independent oracle: response HTML contains one hook-bearing rebalance table, existing column/filter markers, and unchanged `data-asset-key`/action markers.
- [x] 2.2 Port patrimônio row-hover token at existing rebalance selector in `src/omaha/static/app.css`. Target symbol: `.rebalance-asset-row:hover td` near lines 3291-3293. Exact change: use existing `var(--bg-hover)` with hover-only precedence sufficient to beat buy/sell/neutral `!important` idle backgrounds; activate existing 80ms transition through canonical hook. Preserve: odd/even zebra and buy/sell/neutral colors when idle, action content, filters, sorting, and no persistent state. Acceptance: all hovered row cells visibly use patrimônio hover background; pointer exit restores pre-hover state; no new tooltip, selection, scroll container, or alternate selector pattern. Test file/scenario: `tests/visual/test_snapshots.py::test_rebalance_plan_snapshot` hover assertion. Focused taskipy command: `uv run task test-one tests/visual/test_snapshots.py::test_rebalance_plan_snapshot`. Independent oracle: Playwright computed `backgroundColor` for every hovered-row `<td>` equals resolved `--bg-hover`; after pointer exit computed state returns to row’s idle background.
- [x] 2.3 Leave `src/omaha/templates/_patrimonio_class_section.html` unchanged while reusing its existing behavior as reference. Target symbols: `table.data-table.asset-table`, existing `.asset-table` sticky/hover selectors in `app.css`. Exact change: none to patrimônio template or selectors; inspect only during implementation and diff review. Preserve: patrimônio markup, byte/semantic behavior, inline editing, delete actions, two-level headers, totals, filters, zebra rows, and existing hover/sticky visuals. Acceptance: no diff hunk touches patrimônio template; existing patrimoine visual test remains green. Test file/scenario: `tests/visual/test_snapshots.py::test_patrimonio_snapshot`. Focused taskipy command: `uv run task test-one tests/visual/test_snapshots.py::test_patrimonio_snapshot`. Independent oracle: `git diff -- src/omaha/templates/_patrimonio_class_section.html` is empty and screenshot/DOM contract remains unchanged.

## 3. Focused product verification

- [x] 3.1 Extend `tests/test_rebalance_page.py` with minimal server-rendered hook coverage. Target: populated plan table contract near `test_post_rebalanceamento_valid_contribution_renders_plan` and existing column-model assertions. Exact change: assert one `table-sticky-header` rebalance table and retain existing eight-column, filter, sort, row-key, action, and empty-state assertions; do not add production fixtures, seed paths, or new integration prefixes. Preserve: all current route/engine assertions. Acceptance: server response proves visual hook is on only rebalance table and no content/interaction markup drift exists. Test file/scenario: `test_rebalance_table_visual_hooks`, populated and empty plan scenarios. Focused taskipy command: `uv run task test-file tests/test_rebalance_page.py`. Independent oracle: pytest passes with existing integration marker and no DB/seed artifacts outside test fixture scope.
- [x] 3.2 Extend `tests/visual/test_snapshots.py` only for browser-visible acceptance. Target: `test_rebalance_plan_snapshot` and, if needed, a focused helper local to this file. Exact change: after existing plan readiness, verify one asset table; scroll page and assert header cell computed `position: sticky`, `top: 0`, visible bounds, and existing header/filter styling; hover a representative row and assert every cell receives resolved `--bg-hover`; move away and assert no persistent highlight; retain existing screenshot comparison and chart waits. Preserve: existing screenshot names, structural assertions, data submission, chart synchronization, and patrimônio tests. Acceptance: browser proves hover and sticky behavior while filters, columns, data, actions, zebra/idle states, and layout remain unchanged. Test file/scenario: `test_rebalance_plan_snapshot`. Focused taskipy command: `uv run task test-one tests/visual/test_snapshots.py::test_rebalance_plan_snapshot`. Independent oracle: Playwright DOM/computed-style/scroll assertions plus committed snapshot comparison; no screenshot update without owner visual approval.
- [x] 3.3 Run focused regression set after runtime/test edits. Target: F63 files only. Exact change: execute integration rebalance tests, the focused visual plan/patrimônio tests, and lint; do not run destructive DB reset or external connector/browser-network flows. Preserve: explicit test population, no skip/xfail/retry, canonical six-lane command availability. Acceptance: all applicable focused commands pass; canonical full suite is recorded `NOT RUN — maintenance-suspended` per config rather than masked. Test file/scenario: `tests/test_rebalance_page.py`, `tests/visual/test_snapshots.py`. Focused taskipy command: `uv run task test-file tests/test_rebalance_page.py` and `uv run task test-one tests/visual/test_snapshots.py::test_rebalance_plan_snapshot` (plus `uv run task test-one tests/visual/test_snapshots.py::test_patrimonio_snapshot`). Independent oracle: pytest exit 0, no new skips/xfails, and test receipts identify current run without production DB mutation.

## 4. Change and delivery acceptance

- [x] 4.1 Validate F63 artifacts and stable specs before handoff. Target: `openspec/changes/f63-hover-e-cabecalho-sticky-na-tabela-de-rebalanceamento/` and affected stable contracts. Exact change: run strict change validation, stable-spec validation, and diff check; do not archive, sync stable specs, commit, or push during Apply. Preserve: exact change id and unrelated slices. Acceptance: proposal/design/tasks plus both delta specs validate; no unrelated files changed. Test file/scenario: artifact/spec validation. Focused taskipy command: `uv run task lint`. Independent oracle: `openspec validate f63-hover-e-cabecalho-sticky-na-tabela-de-rebalanceamento --type change --strict --json`, `openspec validate --specs --strict --json`, `git diff --check`, and changed-file audit all pass.
- [x] 4.2 Complete browser-visible delivery receipt after runtime Apply, before reporting `READY_FOR_REVIEW`. Target: F63 runtime delivery boundary. Exact change: invoke `refresh-for-test` exactly as PRD §4.9 requires, including seeded DB, server restart, `/healthz`, LAN URL, row counts, dashboard seed check, and server PID; record receipt in apply dossier. Preserve: production DB untouched and no broad process/port cleanup. Acceptance: receipt is complete and browser opens current F63 source with seeded data; no stale server or empty DB. Test file/scenario: visual delivery smoke. Focused taskipy command: skill-owned `task db-reset` / `task db-migrate` / `task db-seed` commands as selected by `refresh-for-test`; do not substitute raw commands. Independent oracle: mandatory receipt fields URL, health, DB counts, seeded dashboard marker, and PID are present and attributable to current run.

## Execution Evidence

### Initial Apply preflight — 2026-08-24

- Task 1.1: F60 is archived after reaching `Applied`; archived dossier
  `openspec/changes/archive/2026-08-22-f60-adicionar-acao-atualizar-posicao-no-patrimonio/tasks.md`
  records owner statement **“F60 approved”** after live browser validation on
  2026-08-22, with receipt checksum
  `7426654bf758eeb446fe8425c8a131e3f86af2e90b4cd8ee8f7460a52f461949`.
  Owner authorized F63 Apply in current conversation on 2026-08-24:
  **“Aprovo F63 usando comportamento visual existente de /patrimonio como
  referência. Pode iniciar Apply.”** Roadmap records F63 `Applying` and this
  approval date.
- Task 1.2 pre-fix boundary: `git diff HEAD~1` showed pre-existing history
  changes, while worktree status before implementation contained only the
  owner-edited `openspec/roadmap.md`; target runtime/test files and patrimônio
  template were clean. `git diff --check` passed. F63-owned implementation
  boundary: `_rebalance_plan.html`, `app.css`, `tests/test_rebalance_page.py`,
  `tests/visual/test_snapshots.py`, and this change dossier; pre-existing
  `openspec/roadmap.md` remains outside F63 ownership.
- Ownership ledger run `f63-apply-preflight-20260824-142438Z` registered before
  focused lint launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 113496 | F63 initial Apply / apply agent | wrapper emitted exact PID before `uv run task lint`; run ID registered in this dossier before launch | 2026-08-24T14:27:10Z | 2026-08-24T14:27:11Z | exited | owned-cleaned | lint hooks passed checks but `ruff format` modified only the new test assertions; no child remained after exit | bounded taskipy child exited; no residue |

- Follow-up lint run `f63-apply-lint-20260824-142711Z` registered before
  launch to verify hook formatting and produce green evidence:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 114753 | F63 initial Apply / apply agent | wrapper emitted exact PID before `uv run task lint`; run ID registered in this dossier before launch | 2026-08-24T14:27:56Z | 2026-08-24T14:27:57Z | exited | owned-cleaned | all lint hooks passed; no child remained after exit | bounded taskipy child exited; no residue |

- Task 1.2 is complete. Pre-fix boundary and lint evidence above preserve
  owner-edited `openspec/roadmap.md` and leave patrimônio template unchanged.
- Focused integration run `f63-apply-hooks-20260824-142758Z` registered before
  launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 115958 | F63 initial Apply / apply agent | wrapper emitted exact PID before task use; pytest reported child PID 115967 with PGID 115958 | 2026-08-24T14:28:44Z | 2026-08-24T14:28:46Z | exited | owned-cleaned | focused test exited 1 on assertion drift; exact PID/PGID absent after exit | bounded taskipy child exited; no signal or broad cleanup |
  | process group | PGID 115958 | F63 initial Apply / apply agent | pytest failure receipt identified PGID 115958 for current run | 2026-08-24T14:28:44Z | 2026-08-24T14:28:46Z | exited | owned-cleaned | exact PGID absent after test exit | idempotent no-op; no group operation |
  | test DB resource | `/tmp/omaha-conftest-safe-7kvqubb7/portfolio.db` | F63 initial Apply / apply agent | pytest failure receipt exposed exact fixture DB path under current run | 2026-08-24T14:28:44Z | 2026-08-24T14:28:47Z | absent | owned-cleaned | test-only SQLite path was removed by exact bounded cleanup; production DB excluded | exact-file removal succeeded; post-check absent |

- Focused integration result: `uv run task test-one
  tests/test_rebalance_page.py::test_rebalance_table_visual_hooks` failed
  because test asserted a runtime Alpine `data-testid` value as literal server
  HTML; production markup correctly emits the existing dynamic `:data-testid`
  expression. Test-only assertion corrected; no product behavior changed.
- Failed-run cleanup: exact test DB path above was bounded-cleaned after
  matching current-run ownership; cleanup output confirmed removal and exact
  post-check absence. No parent-directory or foreign resource action.
- Focused integration retry `f63-apply-hooks-retry-20260824-143000Z`
  registered before launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 116131 / pytest child 116140 | F63 initial Apply / apply agent | wrapper emitted PID before task use; failure receipt emitted child and PGID | 2026-08-24T14:29:45Z | 2026-08-24T14:29:47Z | exited | owned-cleaned | focused test failed on second dynamic Alpine assertion; no child remained | bounded runner teardown; no signal |

- Retry result: `uv run task test-one
  tests/test_rebalance_page.py::test_rebalance_table_visual_hooks` failed on
  same server-rendered-versus-Alpine distinction for the action test id; test
  assertion corrected to retain existing dynamic expression. Exact retry
  resources were PID 116131 / pytest child 116140 / PGID 116131 and test DB
  `/tmp/omaha-conftest-safe-igfs9a6b/portfolio.db`; all were current-run and
  test-only; exact DB cleanup completed.
- Retry cleanup: exact current-run test DB path was bounded-cleaned and exact
  post-check confirmed absent; PIDs/PGID were already absent. No process
  signal, group operation, parent-directory deletion, or foreign action.
- Focused integration final retry `f63-apply-hooks-final-20260824-143200Z`
  registered before launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 116312 | F63 initial Apply / apply agent | wrapper emitted exact PID before task use | 2026-08-24T14:34:28Z | 2026-08-24T14:34:31Z | exited | owned-cleaned | focused hook test passed; no child remained | bounded runner teardown; no residue |

- Focused browser run `f63-apply-visual-20260824-143500Z` preflight
  registered before launch. Canonical runner declared `data/test_visual.db`
  was absent; canonical lane port 8768 had no listener. No foreign resource
  was adopted or cleaned.

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 116448 / pytest child 116457 | F63 initial Apply / apply agent | wrapper emitted PID before task use; failure receipt emitted child and PGID | 2026-08-24T14:35:50Z | 2026-08-24T14:36:33Z | exited | owned-cleaned | browser assertions passed; screenshot failed before final comparison; no child remained | bounded runner teardown; no foreign action |
  | port | TCP 8768 | F63 initial Apply / apply agent | exact canonical visual lane port preflight showed no listener before launch | 2026-08-24T14:35:00Z | 2026-08-24T14:36:33Z | absent | owned-cleaned | runner teardown left declared port absent | exact current-run teardown; no foreign action |
  | test DB resource | `data/test_visual.db` | F63 initial Apply / apply agent | exact canonical visual fixture path preflight was absent before launch | 2026-08-24T14:35:00Z | 2026-08-24T14:36:33Z | absent | owned-cleaned | current-run visual DB removed by exact bounded cleanup | exact-file removal succeeded; post-check absent |

- Visual run result: browser DOM/computed-style acceptance passed through
  sticky position/top/z-index, filter visibility, all-cell hover token, idle
  restoration, and viewport bounds. Snapshot comparison then failed because
  the new scroll assertion left page at bottom before existing screenshot;
  mobile also exposed the same existing baseline-size mismatch. Fix restores
  scroll position to top before unchanged screenshot comparison. No baseline
  update authorized.
- Visual run cleanup: PID 116448 / pytest child 116457 / PGID 116448 and port
  8768 were absent after teardown. Exact current-run `data/test_visual.db`
  was bounded-cleaned with exact post-check absence; screenshot result files
  remain preserved as existing visual artifacts, not cleanup targets.
- Visual retry `f63-apply-visual-retry-20260824-143900Z` preflight registered
  before launch. Port 8768 and exact `data/test_visual.db` were absent; no
  foreign process/listener/test DB was adopted.

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 116769 / pytest child 116778 | F63 initial Apply / apply agent | wrapper emitted PID before task use; failure receipt emitted child and PGID | 2026-08-24T14:37:33Z | 2026-08-24T14:38:15Z | exited | owned-cleaned | behavior assertions passed; mobile snapshot baseline failed; no child remained | bounded runner teardown; no foreign action |
  | port | TCP 8768 | F63 initial Apply / apply agent | exact canonical visual lane port preflight absent before launch | 2026-08-24T14:37:00Z | 2026-08-24T14:38:15Z | absent | owned-cleaned | runner teardown left declared port absent | exact current-run teardown; no foreign action |
  | test DB resource | `data/test_visual.db` | F63 initial Apply / apply agent | exact canonical visual fixture path preflight absent before launch | 2026-08-24T14:37:00Z | 2026-08-24T14:38:15Z | absent | owned-cleaned | current-run visual DB removed by exact bounded cleanup | exact-file removal succeeded; post-check absent |

- Visual retry result: behavior assertions passed; unchanged screenshot
  comparison still reported pre-existing baseline drift (desktop header
  diff reduced to 1.7707%; mobile baseline dimensions 1364x4069 versus current
  1356x4069). No baseline update authorized. Exact retry PID 116769 / pytest
  child 116778 / PGID 116769 and port 8768 were absent after teardown. Exact
  `data/test_visual.db` was bounded-cleaned and post-check confirmed absent.
- The scoped header-token cascade override is now applied. Visual final retry
  `f63-apply-visual-final-20260824-144500Z` registered before launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 117293 / pytest child 117302 | F63 initial Apply / apply agent | wrapper emitted PID before task use; failure receipt emitted pytest child and PGID | 2026-08-24T14:41:00Z | 2026-08-24T14:41:42Z | exited | owned-cleaned | desktop passed; mobile baseline dimension mismatch; no child remained | bounded runner teardown; no foreign action |
  | port | TCP 8768 | F63 initial Apply / apply agent | exact canonical visual lane port preflight absent before launch | 2026-08-24T14:40:00Z | 2026-08-24T14:41:42Z | absent | owned-cleaned | runner teardown left declared port absent | exact current-run teardown; no foreign action |
  | test DB resource | `data/test_visual.db` | F63 initial Apply / apply agent | exact canonical visual fixture path preflight absent before launch | 2026-08-24T14:40:00Z | 2026-08-24T14:41:42Z | absent | owned-cleaned | current-run visual DB removed by exact bounded cleanup | exact-file removal succeeded; post-check absent |

- Final visual retry result: desktop passed all F63 browser assertions and
  unchanged screenshot comparison. Mobile passed F63 browser assertions but
  failed pre-existing snapshot dimension contract: tracked baseline
  `rebalance-plan-mobile.png` is 1364x4069 while current runner output is
  1356x4069. F63 changes affect only sticky position/background and hover
  background; none can change document width. No baseline update or test skip
  is authorized. Focused desktop node is green; mobile snapshot remains an
  unrelated pre-existing visual-lane blocker for Review isolation.
- Final visual resources: wrapper PID 117293 / pytest child 117302 / PGID
  117293 exited; port 8768 absent; exact current-run `data/test_visual.db`
  was bounded-cleaned and exact post-check confirmed absent. Existing result
  images preserved; no baseline files changed.
- Focused F63 desktop-only evidence run
  `f63-apply-visual-desktop-20260824-144700Z` registered before launch after
  exact preflight confirmed port 8768 and `data/test_visual.db` absent:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 117660 | F63 initial Apply / apply agent | wrapper emitted exact PID before task use | 2026-08-24T14:42:53Z | 2026-08-24T14:43:16Z | exited | owned-cleaned | 1 passed, 1 deselected desktop-only diagnostic | bounded runner teardown; no residue |
  | port | TCP 8768 | F63 initial Apply / apply agent | exact canonical visual lane port preflight absent before launch | 2026-08-24T14:42:00Z | 2026-08-24T14:43:16Z | absent | owned-cleaned | runner teardown left declared port absent | exact current-run teardown; no foreign action |
  | test DB resource | `data/test_visual.db` | F63 initial Apply / apply agent | exact canonical visual fixture path preflight absent before launch | 2026-08-24T14:42:00Z | 2026-08-24T14:43:16Z | absent | owned-cleaned | current-run visual DB removed by exact bounded cleanup | exact-file removal succeeded; post-check absent |

- Desktop-only result: `uv run task test-one
  tests/visual/test_snapshots.py::test_rebalance_plan_snapshot -k desktop` →
  **1 passed, 1 deselected** in 22.07s. PID 117660 exited; port 8768 was
  absent; exact `data/test_visual.db` was bounded-cleaned and post-check
  confirmed absent. Deselect is diagnostic isolation of pre-existing mobile
  baseline drift, not test weakening in source.
- Patrimônio regression run `f63-apply-patrimonio-20260824-145000Z` registered
  before launch after exact preflight confirmed port 8768 and
  `data/test_visual.db` absent:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 117950 / pytest child 117959 | F63 initial Apply / apply agent | wrapper emitted PID before task use; failure receipt emitted pytest child and PGID | 2026-08-24T14:44:07Z | 2026-08-24T14:44:53Z | exited | owned-cleaned | patrimônio baseline dimensions mismatched before F63-specific behavior; no child remained | bounded runner teardown; no foreign action |
  | port | TCP 8768 | F63 initial Apply / apply agent | exact canonical visual lane port preflight absent before launch | 2026-08-24T14:44:00Z | 2026-08-24T14:44:53Z | absent | owned-cleaned | runner teardown left declared port absent | exact current-run teardown; no foreign action |
  | test DB resource | `data/test_visual.db` | F63 initial Apply / apply agent | exact canonical visual fixture path preflight absent before launch | 2026-08-24T14:44:00Z | 2026-08-24T14:44:53Z | absent | owned-cleaned | current-run visual DB removed by exact bounded cleanup | exact-file removal succeeded; post-check absent |

- Patrimônio regression result: `uv run task test-one
  tests/visual/test_snapshots.py::test_patrimonio_snapshot` failed before any
  F63-specific assertion on existing baseline dimensions: desktop expected
  1605x4271/current 1605x4241; mobile expected 1669x4398/current 1669x4346.
  `_patrimonio_class_section.html` has no diff and F63 CSS override is scoped
  to `.table-sticky-header.rebalance-table`; no patrimônio behavior was
  changed. No baseline update or skip authorized. PID 117950 / pytest child
  117959 / PGID 117950 exited; port 8768 absent; exact current-run
  `data/test_visual.db` bounded-cleaned and post-check confirmed absent.
- Integration full-file run `f63-apply-integration-20260824-145500Z`
  registered before launch. Test runner will use its declared test-only
  temporary DB; production DB is not a target.

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 118236 | F63 initial Apply / apply agent | wrapper emitted exact PID before task use | 2026-08-24T14:45:45Z | 2026-08-24T14:45:56Z | exited | owned-cleaned | 26 integration tests passed; no child remained | bounded runner teardown; no residue |

- Integration result: `uv run task test-file tests/test_rebalance_page.py` →
  **26 passed, 12 warnings** in 10.53s. PID 118236 exited; no process or
  process-group residue observed; test-only fixture resources were managed by
  runner and production DB was untouched.
- Final lint run `f63-apply-lint-final-20260824-145700Z` registered before
  launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 118368 | F63 initial Apply / apply agent | wrapper emitted exact PID before task use | 2026-08-24T14:46:15Z | 2026-08-24T14:46:16Z | exited | owned-cleaned | hooks passed checks; ruff formatting changed new test lines only | bounded runner teardown; no residue |

- Final lint first attempt: hooks passed checks but reformatted only the new
  test assertion lines; no product files changed. PID 118368 exited. Follow-up
  lint `f63-apply-lint-green-20260824-145800Z` registered before launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 119614 | F63 initial Apply / apply agent | wrapper emitted exact PID before task use | 2026-08-24T14:47:02Z | 2026-08-24T14:47:03Z | exited | owned-cleaned | all lint hooks passed | bounded runner teardown; no residue |

- Final lint result: `uv run task lint` → all hooks passed. PID 119614
  exited; no child residue.
- Change/spec validation result: strict F63 change validation **1 passed**;
  strict stable-spec validation **78 passed** with existing informational
  long-requirement notices; `git diff --check` passed. No archive, sync,
  commit, or push performed.

### Refresh-for-test delivery gate — blocked 2026-08-24

- Refresh preflight read-only DB state: `data/portfolio.db` contains 11
  classes / 90 assets / 88 positions. LAN URL discovery returned
  `http://192.168.1.8:8000`.
- Required exact port-8000 refresh resource inventory:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 89998 / parent PID 89995 | F63 initial Apply / apply agent | no current-run registration exists; observed only during preflight | 2026-08-24T14:48:00Z | — | active | pre-existing / unknown ownership | exact command is `/home/juca/github/omaha/.venv/bin/python ... uvicorn omaha.main:app --host 0.0.0.0 --port 8000`; cwd `/home/juca/github/omaha`; start `Mon Aug 24 09:31:34 2026`; identity matches app but not current-run ownership | untouched; no signal/adoption |
  | process group | PGID/SID 89995 | F63 initial Apply / apply agent | no current-run registration exists; observed as parent group during preflight | 2026-08-24T14:48:00Z | — | active | pre-existing / unknown ownership | exact uvicorn launcher lineage for PID 89998 | untouched; no group operation |
  | port | TCP 8000 `0.0.0.0:8000` | F63 initial Apply / apply agent | no current-run registration exists; listener preflight mapped exact port to PID 89998 | 2026-08-24T14:48:00Z | — | active | pre-existing / unknown ownership | `ss` mapped listener to pre-existing PID 89998; port identity alone does not prove ownership | untouched; no port cleanup |
- `refresh-for-test` cannot safely restart or adopt this pre-existing
  port-8000 process under current apply ownership protocol. Therefore no
  server restart, `/healthz` smoke, or delivery receipt was claimed; no DB
  mutation command was run. This blocks task 4.2 and READY_FOR_REVIEW.

### Refresh-for-test continuation — owner-authorized 2026-08-24

- Owner decision received before action: exact Omaha processes belonging to
  this application on port 8000 may be terminated/restarted; dev/test reset
  required by refresh is authorized; production DB and foreign resources
  remain excluded. Mobile/patrimônio snapshot dimension mismatches remain
  pre-existing and baselines must not change.
- Refresh run `f63-refresh-20260824-145642Z` registered before any process or
  DB action:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 89998; parent/PGID 89995 | F63 continuation / apply agent | exact command/cwd/port match plus owner authorization in current conversation | 2026-08-24T14:56:42Z | 2026-08-24T14:56:43Z | exited | pre-existing | exact TERM targeted only PID 89998; no foreign process action | bounded exact process termination; child exited; no group signal |
  | process group | PGID/SID 89995 | F63 continuation / apply agent | exact parent lineage plus owner authorization in current conversation | 2026-08-24T14:56:42Z | 2026-08-24T14:56:43Z | exited | pre-existing | launcher group ended after exact child termination | no group operation; no residue |
  | port | TCP 8000 `0.0.0.0:8000` | F63 continuation / apply agent | `ss` mapped listener to PID 89998 plus owner authorization | 2026-08-24T14:56:42Z | 2026-08-24T14:56:43Z | absent | pre-existing | exact old listener released before new launcher bind | exact port release verified; no port-wide cleanup |
  | temporary path | `/tmp/f63-refresh-20260824-145642Z-launch.sh` | F63 continuation / apply agent | exact run path registered before launcher creation | 2026-08-24T14:56:42Z | 2026-08-24T15:02:13Z | absent | owned-cleaned | launcher created, executed, then exact path removed | bounded exact removal; post-check absent |
  | log | `/tmp/f63-refresh-20260824-145642Z-uvicorn.log` | F63 continuation / apply agent | exact run log path registered before server launch | 2026-08-24T14:56:42Z | — | active | owned-current-run | startup/health/login/dashboard evidence preserved at exact path | intentionally preserved as delivery evidence |
  | test DB resource | `data/portfolio.db` | F63 continuation / apply agent | owner authorized dev/test reset; exact task declared before use | 2026-08-24T14:56:42Z | — | pre-existing | pre-existing | local SQLite dev delivery DB; production Postgres/foreign DB excluded | mutate only through authorized `uv run task db-reset`; no production cleanup |
  | child process | PID 121695; parent/PGID 121691 | F63 continuation / apply agent | exact launcher run created PID; command/cwd/port match current Omaha source | 2026-08-24T14:57:47Z | — | active | owned-current-run | `/home/juca/github/omaha/.venv/bin/python ... uvicorn omaha.main:app --host 0.0.0.0 --port 8000`; cwd `/home/juca/github/omaha`; listener `0.0.0.0:8000` | preserve for owner delivery; bounded exact stop only after receipt |
  | process group | PGID/SID 121691 | F63 continuation / apply agent | exact launcher-created parent group for PID 121695 | 2026-08-24T14:57:47Z | — | active | owned-current-run | `uv run uvicorn` launcher command/cwd match | preserve for owner delivery; no group action |
  | port | TCP 8000 `0.0.0.0:8000` | F63 continuation / apply agent | launcher created listener and `ss` mapped it to PID 121695 | 2026-08-24T14:57:47Z | — | active | owned-current-run | current-source server listener on required delivery port | preserve for owner delivery; no port cleanup |
  | temporary path | `/tmp/f63-refresh-20260824-145642Z-cookie` | F63 continuation / apply agent | exact cookie path registered before read-only dashboard smoke | 2026-08-24T14:58:30Z | 2026-08-24T15:02:13Z | absent | owned-cleaned | cookie used for read-only smoke then exact path removed | bounded exact removal; post-check absent |

#### Mandatory delivery receipt — F63 continuation

```text
URL:              http://192.168.1.8:8000
Healthz:          {"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}
DB action:        authorized `uv run task db-reset` against local dev SQLite only
DB state:         11 classes / 89 assets / 88 positions
                  Italo 6/46/46 + Ana 5/43/42 + Família 0/0/0
Dashboard seeded: "RF Din" marker count 5
Server PID:       121695 (PGID/SID 121691)
Bind:             0.0.0.0:8000
Source cwd:       /home/juca/github/omaha
Log:              /tmp/f63-refresh-20260824-145642Z-uvicorn.log
```

- `refresh-for-test` steps completed: exact authorized old Omaha PID 89998
  stopped; old PGID/SID 89995 exited; port 8000 released; current source
  restarted with exact LAN bind; `/healthz` passed; authorized local dev DB
  reset via Taskipy; counts verified; read-only login/profile/dashboard smoke
  passed. A diagnostic curl used `-L -X POST` and produced one self-caused
  `POST /` 405; corrected smoke used explicit POST then GET and passed. No
  application failure remains.
- Cleanup: exact launcher and cookie paths are absent after bounded cleanup;
  exact server PID/PGID/port remain active intentionally for owner delivery;
  exact log preserved as receipt evidence. Unregistered diagnostic response
  paths remain preserved and untouched. Production Postgres and foreign
  processes/resources were not touched.
- Baseline classification: mobile rebalance and desktop/mobile patrimônio
  dimension mismatches remain pre-existing per owner authorization; no visual
  baseline files changed. Prior F63 browser behavior assertions and 26-test
  integration evidence remain valid.

## Review Findings

### Review R1
Scope audit: requirements pass; scenarios pass for rebalance populated-table
sticky/hover behavior, idle restoration, empty-plan preservation, and
patrimônio source immutability by static diff; tasks pass (10/10); design and
delta-spec alignment pass; changed-symbol audit pass for the two runtime files
and two test files; tests pass for focused rebalance coverage; patrimonio
focused regression finding; ownership/isolation not assessable for final
patrimônio run because declared `data/test_visual.db` was already present at
preflight. No API, model, route, DB-seed, baseline, or patrimônio-template
change found. `openspec/roadmap.md` remains recorded pre-existing owner work,
outside F63 implementation ownership.

Full suite: `uv run task test` -> NOT RUN — maintenance-suspended, per
`openspec/config.yaml:85-99`; no six-lane or duration classification claimed.
Focused evidence: `uv run task test-file tests/test_rebalance_page.py` -> 26
passed, 12 warnings, real 13.64s; `uv run task test-one
tests/visual/test_snapshots.py::test_rebalance_plan_snapshot -k desktop` -> 1
passed, 1 deselected, real 24.38s; `uv run task lint` -> passed, real 22.70s;
strict F63 change validation -> 1 passed; strict stable-spec validation -> 78
passed. `uv run task test-one
tests/visual/test_snapshots.py::test_patrimonio_snapshot` -> 2 failed:
desktop expected 1605x4271/current 1605x4241 and mobile expected
1669x4398/current 1669x4346 at `tests/visual/conftest.py:202`, before any F63
patrimônio-specific assertion. Classified pre-existing baseline/dimension
drift, not F63 code bug; focused red remains blocking under maintenance policy.

Preflight: ledger `f63-review-r1-20260824` inspected child/process-group,
TCP 8768, TCP 8000, declared visual DB, and runner-declared temporary boundary
before standards/spec review. Initial visual preflight classified TCP 8768
absent and `data/test_visual.db` absent; delivery server `PID 121695` on
`0.0.0.0:8000` was preserved as current owner delivery resource. Before
patrimônio command, exact declared `data/test_visual.db` was present with no
current-review ownership receipt; classification pre-existing/ownership
unknown. Runner isolation therefore failed for that command; no adoption,
cleanup, kill, DB reset, or foreign-resource action performed.

Postflight: review visual child/process group and TCP 8768 exited/absent after
test teardown; delivery PID 121695 and TCP 8000 remained owned-current-run by
apply receipt and were preserved; `data/test_visual.db` remained present and
untouched because it lacked exact current-review ownership. No broad cleanup
performed. Existing apply delivery log and server were preserved.

Runner isolation: desktop focused run precondition passed (TCP 8768 and exact
`data/test_visual.db` absent). Patrimônio focused run precondition failed due
present declared test DB; canonical isolated-runner precondition is not
trusted for that run. This blocks verdict independently of implementation
correctness.

Verdict: BLOCKED

#### R1-F01 — Focused patrimônio regression and untrusted visual-run isolation
Status: blocked
Requirement/task: component-state-language patrimônio stability scenario;
rebalance-page patrimônio-preservation scenario; Task 2.3 and Task 3.3.
Evidence: `uv run task test-one
tests/visual/test_snapshots.py::test_patrimonio_snapshot` produced two red
tests at `tests/visual/conftest.py:202`: expected/current dimensions were
1605x4271 vs 1605x4241 (desktop) and 1669x4398 vs 1669x4346 (mobile).
Preflight immediately before that command found declared
`data/test_visual.db` present without current-run ownership evidence.
Implementation audit found no diff in
`src/omaha/templates/_patrimonio_class_section.html`; F63 CSS additions are
scoped to `.table-sticky-header.rebalance-table`.
Required change: owner must provide isolated runner with exact declared visual
DB absent or current-run-owned before launch, then resolve/classify existing
patrimônio snapshot dimension drift and obtain green applicable patrimônio
focused evidence. Do not update visual baselines as part of F63, do not skip,
xfail, retry-mask, remove tests, or alter patrimônio behavior.
Excluded scope: no F63 production-code rewrite, no patrimônio template/CSS
refactor, no baseline edit, no process or DB cleanup by review.
Acceptance: clean ownership preflight receipt, patrimônio focused command green
for applicable cases with unchanged authorized baselines, and refreshed
postflight ledger showing exact current-run cleanup.
Late finding reason: none; initial review round.

### Remediation 1/2 — blocked at trusted preflight — 2026-08-24

- Scope remained exactly R1-F01. No runtime, test, baseline, production DB, or
  unrelated harness file was changed. The supported visual boundary was
  re-confirmed before launch: `tests/visual/conftest.py` declares the fixed
  `data/test_visual.db` target and `live_url_visual` deletes it before setup;
  `tests/support/server.py::run_test_server` requires caller-owned DB deletion.
- Ownership ledger `f63-r1-remediation-1-20260824T121048-0300` was registered
  before any test launch. No test process or visual server was launched.

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | test DB resource | `/home/juca/github/omaha/data/test_visual.db` | F63 R1 remediation 1 / apply agent | exact current-run ledger registration plus preflight stat/hash captured before any fixture use | 2026-08-24T12:10:48-03:00 | 2026-08-24T12:10:49-03:00 | absent-from-use | pre-existing | exact path existed before run; inode `518164`; size `159744`; sha256 `44fe353e773e424242e6b26bc4df164256c43e31ae7e341bff4b6313c3cedd6`; no current-run receipt | untouched; no cleanup attempted; foreign/pre-existing resource preserved |
  | port | TCP `8768` | F63 R1 remediation 1 / apply agent | exact current-run ledger registration plus socket preflight before any server launch | 2026-08-24T12:10:48-03:00 | 2026-08-24T12:10:49-03:00 | absent | absent | `127.0.0.1:8768` refused connection; `ss` showed no listener | idempotent no-op; no launch and no cleanup |
  | temporary path | canonical visual runner boundary | F63 R1 remediation 1 / apply agent | no runner boundary created because DB preflight blocked launch | 2026-08-24T12:10:48-03:00 | 2026-08-24T12:10:49-03:00 | absent | absent | no child, log, pytest temp root, or server was created | idempotent no-op; no cleanup |

- Delivery server `0.0.0.0:8000` from prior F63 refresh receipt remained outside
  this visual lane boundary and was preserved; no action or ownership adoption
  occurred. Out-of-bound delivery resource cannot establish visual-run DB
  ownership and cannot unblock this finding.
- Focused validation: **not launched**. Trusted preflight failed before
  `uv run task test-one
  tests/visual/test_snapshots.py::test_patrimonio_snapshot`; therefore no
  focused result is claimed. Canonical `uv run task test` remains
  **NOT RUN — maintenance-suspended**.
- Disposition: **BLOCKED**. Required isolated runner was unavailable because
  exact declared visual DB was pre-existing/unowned. No adoption, deletion,
  masking, baseline update, skip, xfail, retry, process kill, or port cleanup.

### Remediation 2/2 — owner-authorized final pass — 2026-08-24

- Scope is limited to R1-F01. Owner authorization received before action:
  delete/recreate only `data/test_visual.db` as ephemeral visual test DB;
  protect `data/portfolio.db`, production Postgres, foreign resources, and
  visual baselines. No runtime, patrimônio behavior, test, baseline, or harness
  change is authorized.
- Preflight ledger `f63-r1-remediation-2-20260824T121343-0300` registered before
  DB action. Exact prior DB identity: `/home/juca/github/omaha/data/test_visual.db`,
  inode `518164`, size `159744`, SHA256
  `44fe353e773e424242e6b26bc4df164256c43e31ae7e341bff4b6313c3cedd6`.
  Port `8768` was absent. Delivery port `8000` mapped to prior F63-owned PID
  `121695` and remained preserved outside visual-lane scope.

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | test DB resource | `/home/juca/github/omaha/data/test_visual.db` | F63 R1 remediation 2 / apply agent | exact current-run ledger registration, prior inode/size/SHA256, and owner authorization recorded before deletion | 2026-08-24T12:13:43-03:00 | — | active | owned-current-run | exact declared visual DB only; owner authorized ephemeral delete/recreate | pending bounded exact cleanup after focused run |
  | port | TCP `8768` | F63 R1 remediation 2 / apply agent | exact socket preflight before server launch | 2026-08-24T12:13:43-03:00 | — | registered | absent | no listener on `127.0.0.1:8768` before launch | pending postflight |
  | port | TCP `8000` | F63 R1 remediation 2 / apply agent | exact `ss` mapping plus prior F63 delivery receipt; outside visual lane | 2026-08-24T12:13:43-03:00 | — | active | pre-existing | PID `121695`, prior apply-owned delivery server; not touched | preserved; no cleanup |
  | log | `/tmp/f63-r1-remediation-2-visual.log` | F63 R1 remediation 2 / apply agent | exact run log path registered before focused command launch | 2026-08-24T12:14:30-03:00 | — | registered | owned-current-run | output capture for one exact focused command | preserve as test evidence |

- Exact DB action: owner-authorized deletion at `2026-08-24T12:14:20-03:00`
  removed only `/home/juca/github/omaha/data/test_visual.db`; post-delete exact
  check was absent. Supported fixture recreated/seeds same exact path for this
  run. No product DB or Postgres target was touched.
- Focused command (run exactly once, no retry):
  `uv run task test-one
  tests/visual/test_snapshots.py::test_patrimonio_snapshot` -> **2 failed**
  in 45.49s; collected desktop and mobile cases. Structural/login/setup
  behavior completed. Both failures occurred at existing snapshot dimension
  comparison in `tests/visual/conftest.py:202`, before any F63-specific
  assertion or patrimônio behavior mutation:
  - desktop: expected `1605x4271`, current `1605x4241`;
  - mobile: expected `1669x4398`, current `1669x4346`.
- Final ownership ledger update:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID `125761` / pytest PID `125773` | F63 R1 remediation 2 / apply agent | exact run log registered before launch; wrapper log records child PID/PGID and pytest failure receipt | 2026-08-24T12:14:53-03:00 | 2026-08-24T12:15:41-03:00 | exited | owned-cleaned | exact focused command exited `1`; no listed PID remained postflight | bounded fixture teardown; no signal or broad process cleanup |
  | process group | PGID `125759` | F63 R1 remediation 2 / apply agent | wrapper recorded exact PGID before command use; pytest failure receipt matched PGID | 2026-08-24T12:14:53-03:00 | 2026-08-24T12:16:02-03:00 | exited | owned-cleaned | exact PGID absent postflight | idempotent no-op; no group operation |
  | port | TCP `8768` | F63 R1 remediation 2 / apply agent | exact port absent before launch; visual fixture owned server lifecycle for this run | 2026-08-24T12:13:43-03:00 | 2026-08-24T12:16:02-03:00 | absent | owned-cleaned | port absent after fixture teardown | exact current-run server teardown; no port-wide cleanup |
  | test DB resource | `/home/juca/github/omaha/data/test_visual.db` | F63 R1 remediation 2 / apply agent | prior identity plus owner authorization; fixture recreated exact path during run | 2026-08-24T12:14:20-03:00 | 2026-08-24T12:16:15-03:00 | absent | owned-cleaned | recreated DB inode `517864`, size `159744`, SHA256 `97bd1a03bb1ffb42ccbb1a112d3645c81a0261248ebac7aaf6c331846b5e0ad4`; exact postflight unlink succeeded | exact-file removal; post-check absent |
  | log | `/tmp/f63-r1-remediation-2-visual.log` | F63 R1 remediation 2 / apply agent | exact path registered before command launch | 2026-08-24T12:14:53-03:00 | — | exited | owned-current-run | preserves complete focused command output and failure evidence | intentionally preserved as receipt evidence |
  | port | TCP `8000` | F63 R1 remediation 2 / apply agent | prior F63 delivery receipt plus exact preflight mapping; outside visual lane | 2026-08-24T12:13:43-03:00 | — | active | pre-existing | PID `121695` remained delivery server | untouched; no cleanup |
- Read-only postflight validation registration: exact log path
  `/tmp/f63-r1-remediation-2-postvalidation.log` was registered before
  `git diff --check` / baseline / patrimônio-template checks. This validation
  does not launch application, test server, DB, or browser resources.
- Read-only postflight validation receipt: PID `126274`, PGID `126272`, started
  `2026-08-24T12:18:01-03:00`, ended `2026-08-24T12:18:02-03:00`, exit `0`;
  exact log path preserved as current-run evidence. No runtime resource was
  created; baseline diff and patrimônio-template diff remained empty.
- Baselines: `git diff --quiet -- tests/visual/baselines` passed; no baseline
  file changed. No `UPDATE_VISUAL_BASELINES`, skip, xfail, retry, or masking was
  used. `data/portfolio.db` and production Postgres remained protected.
- Canonical full suite remains **NOT RUN — maintenance-suspended**.
- Final R1-F01 disposition: **BLOCKED_FINAL_REMEDIATION**. Exact ownership
  isolation is now trusted and cleanup is complete, but focused patrimônio
  evidence remains red from pre-existing dimension drift. No third remediation
  pass is permitted.

### Owner-authorized test-artifact scope amendment — 2026-08-24

- Owner authorized this existing-F63-only amendment in the current handoff:
  regenerate exactly the approved Patrimônio desktop visual baseline so the
  snapshot records current owner-validated rendering (`1605x4241` instead of
  stale `1605x4271`). This authorization covers one test baseline image only;
  no production/runtime code, test logic/harness, patrimônio template/CSS, DB
  product data, mobile baseline, rebalance baseline, or unrelated file may
  change. No new slice, commit, archive, or push is authorized.
- Exact supported regeneration path: `UPDATE_VISUAL_BASELINES=1 uv run task
  test-one tests/visual/test_snapshots.py::test_patrimonio_snapshot -k
  desktop`. The parameterized `-k desktop` selection is diagnostic lane
  isolation, not test weakening; mobile case remains versioned and untouched.
- Baseline preflight before run `f63-baseline-desktop-20260824T153317Z`:
  `tests/visual/baselines/patrimonio-desktop.png` existed as the sole target,
  old dimensions `1605x4271`, SHA256
  `3560cbd1dbaf0ab7c3a9dd62433c49cce127560b65a20b1b8c5aeb56aaf1489a`;
  mobile baseline `patrimonio-mobile.png` was explicitly excluded. Exact
  `data/test_visual.db` was absent, TCP 8768 had no listener, and no visual
  pytest/server process existed before launch. Pre-existing delivery server
  PID 121695 / TCP 8000 was outside this visual lane and preserved.
- Ownership ledger registration before launch:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | wrapper PID assigned before task exec; exact PID to be recorded post-launch | F63 baseline amendment / apply agent | run id registered here before supported task launch | 2026-08-24T15:33:17Z | pending | registered | owned-current-run | wrapper will emit exact PID/PGID before task use | pending bounded teardown |
  | process group | wrapper PGID assigned before task exec; exact PGID to be recorded post-launch | F63 baseline amendment / apply agent | run id registered here before supported task launch | 2026-08-24T15:33:17Z | pending | registered | owned-current-run | wrapper will emit exact PGID before task use | pending bounded teardown |
  | port | TCP 8768 | F63 baseline amendment / apply agent | exact socket preflight showed no listener before launch | 2026-08-24T15:33:17Z | pending | absent | absent | canonical visual server port free before use | pending postflight |
  | test DB resource | `data/test_visual.db` | F63 baseline amendment / apply agent | exact path preflight showed absent before fixture use | 2026-08-24T15:33:17Z | pending | absent | absent | fixture may create only exact test DB path; production DB excluded | pending exact-file cleanup |
  | temporary path | canonical runner-declared visual temp paths | F63 baseline amendment / apply agent | no declared temp residue observed before launch | 2026-08-24T15:33:17Z | pending | absent | absent | no prior visual lane temp resource observed | pending postflight |

### Baseline amendment execution evidence — 2026-08-24

- Supported regeneration result: `UPDATE_VISUAL_BASELINES=1 uv run task
  test-one tests/visual/test_snapshots.py::test_patrimonio_snapshot -k
  desktop` → **1 passed, 1 deselected** in 9.75s. Only desktop parameter ran;
  no mobile baseline update path was selected.
- Exact baseline transition:
  `tests/visual/baselines/patrimonio-desktop.png`, old `1605x4271`, SHA256
  `3560cbd1dbaf0ab7c3a9dd62433c49cce127560b65a20b1b8c5aeb56aaf1489a` → new
  `1605x4241`, SHA256
  `a748ffc079ff272383d4955b0a4c3bd05ceede722e788554c76c4cc8edc22089`.
  Mobile baseline stayed unchanged: `patrimonio-mobile.png`, `1669x4398`,
  SHA256 `08363913cdfe877522b474d1245c8620ec9536cd7239822cd339d027b7be006a`.
- Focused desktop recheck: `uv run task test-one
  tests/visual/test_snapshots.py::test_patrimonio_snapshot -k desktop` →
  **1 passed, 1 deselected** in 10.61s.
- F63 focused checks: `uv run task test-file tests/test_rebalance_page.py` →
  **26 passed, 12 warnings** in 10.51s; `uv run task test-one
  tests/visual/test_snapshots.py::test_rebalance_plan_snapshot -k desktop` →
  **1 passed, 1 deselected** in 22.48s; `uv run task lint` → all hooks passed.
  No test was deleted, skipped, xfailed, retried, or masked.
- Ownership ledger completion for amendment run
  `f63-baseline-desktop-20260824T153317Z`:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 127609 | F63 baseline amendment / apply agent | wrapper emitted exact PID before `uv run task` exec; run id registered before launch | 2026-08-24T15:33:54Z | 2026-08-24T15:34:04Z | exited | owned-cleaned | supported regeneration exited 0; no child remained | bounded task child exit; no signal |
  | process group | PGID 127609 | F63 baseline amendment / apply agent | wrapper emitted exact PGID before task use | 2026-08-24T15:33:54Z | 2026-08-24T15:34:04Z | exited | owned-cleaned | exact PGID absent postflight | idempotent no-op; no group operation |
  | test DB resource | `data/test_visual.db` (inode 518195, SHA256 `87a23a3d233794474355b0c6794d43513f3332324a9b102e4b15e02b006163d9`) | F63 baseline amendment / apply agent | exact path absent before launch; fixture-created path observed after current run | 2026-08-24T15:33:54Z | 2026-08-24T15:34:39Z | absent | owned-cleaned | test-only visual DB; production `data/portfolio.db` excluded | exact-file removal succeeded; post-check absent |
  | port | TCP 8768 | F63 baseline amendment / apply agent | exact listener preflight absent before launch | 2026-08-24T15:33:17Z | 2026-08-24T15:34:39Z | absent | absent | no visual listener after fixture teardown | idempotent no-op; no port cleanup |
  | temporary path | canonical visual result paths | F63 baseline amendment / apply agent | runner-declared result boundary; exact result image preserved as evidence | 2026-08-24T15:33:17Z | — | active | owned-current-run | `tests/visual/results/patrimonio-desktop.png` is generated visual evidence, not baseline target | intentionally preserved; no cleanup |

- Focused visual recheck ledger `f63-patrimonio-desktop-focused-20260824T153448Z`:

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | PID 127927 | F63 baseline amendment / apply agent | wrapper emitted exact PID before task use | 2026-08-24T15:34:53Z | 2026-08-24T15:35:04Z | exited | owned-cleaned | focused desktop snapshot exited 0 | bounded task child exit; no signal |
  | process group | PGID 127927 | F63 baseline amendment / apply agent | wrapper emitted exact PGID before task use | 2026-08-24T15:34:53Z | 2026-08-24T15:35:04Z | exited | owned-cleaned | exact PGID absent postflight | idempotent no-op; no group operation |
  | test DB resource | `data/test_visual.db` (inode 518195, SHA256 `5596e4043cda8c728619d8048665d02c3581c528d9eb104b1cd1cc14f75975f4`) | F63 baseline amendment / apply agent | exact path absent before launch; fixture-created path observed after current run | 2026-08-24T15:34:48Z | 2026-08-24T15:35:10Z | absent | owned-cleaned | test-only visual DB; production DB excluded | exact-file removal succeeded; post-check absent |
  | port | TCP 8768 | F63 baseline amendment / apply agent | exact listener preflight absent before launch | 2026-08-24T15:34:48Z | 2026-08-24T15:35:10Z | absent | absent | no visual listener after fixture teardown | idempotent no-op; no port cleanup |

- F63 integration ledger `f63-rebalance-focused-20260824T153550Z`: child PID
  128133 / PGID 128133, started 2026-08-24T15:35:20Z and exited after the
  **26 passed, 12 warnings** result at approximately 2026-08-24T15:35:31Z;
  classified `owned-cleaned`, bounded task teardown, no process residue. Its
  fixture-scoped test DB was test-only and runner-cleaned; no production DB
  resource was used or targeted.
- F63 browser ledger `f63-rebalance-desktop-focused-20260824T153600Z`: exact
  preflight found `data/test_visual.db` and TCP 8768 absent; child PID 128262 /
  PGID 128262 started 2026-08-24T15:35:44Z and exited after **1 passed, 1
  deselected** in 22.48s; exact visual DB inode 518162, SHA256
  `e6f73fdbac9e87984e22f635d992c8019b2d58d02bc96e27832e2a22b129e829` was
  bounded-removed and post-check absent; TCP 8768 absent. All current-run
  resources classified `owned-cleaned` or `absent`; no foreign action.
- Lint ledger `f63-lint-focused-20260824T153700Z`: child PID 128478 / PGID
  128478, started 2026-08-24T15:36:23Z, exited 0 after all hooks passed;
  `owned-cleaned`, no resource residue.
- Scope audit after all runs: `git diff --name-status --
  tests/visual/baselines` reports exactly one changed file,
  `tests/visual/baselines/patrimonio-desktop.png`; mobile baseline, result
  image outside tracked diff, runtime files, test logic/harness, patrimônio
  template/CSS, product DB, rebalance baseline, and unrelated files are
  unchanged by amendment. `git diff --check` passes.
- Canonical review isolation: relevant visual process/listener/test DB
  preflight clean before each visual launch; exact current-run DB resources
  bounded-cleaned; no declared-boundary foreign or unknown residue. Existing
  delivery PID 121695 / PGID 121691 on TCP 8000 remained pre-existing,
  out-of-bound, and untouched. Canonical full suite remains `NOT RUN —
  maintenance-suspended`.
- Amendment acceptance: owner approval, old/new dimensions and hashes, exact
  desktop baseline path, focused green checks, unchanged-file audit, and
  ownership receipts recorded. No open finding introduced.

### Final review R2 preflight — 2026-08-24

- Review ledger `f63-review-r2-20260824` registered before focused verification.
  Canonical gate status is `maintenance-suspended`; full suite will not launch.
  Declared visual lane resources were inspected without discovering host-wide
  temporary paths.

  | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
  |---|---|---|---|---|---|---|---|---|---|
  | child process | visual pytest/playwright process inventory | F63 review R2 | ledger registered before focused launch; no matching process observed | 2026-08-24T16:00:00Z | 2026-08-24T16:00:01Z | absent | absent | process inventory contained no pytest/playwright/test_visual process | idempotent no-op |
  | port | TCP 8768 | F63 review R2 | exact visual-lane socket check before launch | 2026-08-24T16:00:00Z | 2026-08-24T16:00:01Z | absent | absent | no listener on declared visual port | idempotent no-op |
  | test DB resource | `data/test_visual.db` | F63 review R2 | exact declared path check before launch | 2026-08-24T16:00:00Z | 2026-08-24T16:00:01Z | absent | absent | exact path absent | no cleanup required |
  | temporary path | canonical visual runner-declared boundary | F63 review R2 | no runner launch; no boundary residue observed | 2026-08-24T16:00:00Z | 2026-08-24T16:00:01Z | absent | absent | no declared boundary created by review | no cleanup required |
  | process/listener | PID 121695 / TCP 8000 | prior F63 delivery receipt | prior owner receipt in this dossier; outside visual lane | 2026-08-24T16:00:00Z | 2026-08-24T16:00:01Z | active | pre-existing | current delivery server preserved; not review-owned | preserved; no action |

- Focused review results are complete; postflight observed exact
  `data/test_visual.db` recreated by current visual run (inode 518393, size
  159744), with no visual pytest/playwright process and no TCP 8768 listener.
  This exact current-run path is bounded-cleanup eligible; no parent directory,
  product DB, delivery server, or foreign resource is in cleanup scope.

## Review Findings

### Review R2
Scope audit: requirements pass; scenarios pass for populated rebalance
sticky header, row-wide hover, idle restoration, empty-plan preservation, and
patrimônio immutability; tasks pass (10/10); design decisions and both delta
specs pass; changed-symbol audit pass; focused product tests pass; owner
amendment scope pass; mobile context pass (tests/baseline remain versioned and
runnable, no skip/xfail/retry/mask/deletion); product DB protection pass; no
not-assessable area.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**;
`openspec/config.yaml:85-100` is explicit owner-authorized policy receipt.
Six canonical lane results and 300-second duration classification are not
claimed during suspension. Applicable focused product evidence is green.

Preflight: ledger `f63-review-r2-20260824` registered before focused launch.
Visual pytest/playwright process absent; TCP 8768 absent; exact declared
`data/test_visual.db` absent; canonical visual temporary boundary absent. Prior
delivery PID 121695 / TCP 8000 classified pre-existing and outside visual lane,
preserved. No foreign, unknown, contradictory, or incomplete relevant residue.

Postflight: focused integration process exited and left no residue. Visual
process exited; TCP 8768 absent. Current-run exact `data/test_visual.db`
(inode 518393, 159744 bytes) was bounded-cleaned by exact-file deletion and
post-check confirmed absent. PID 121695 / TCP 8000 remains pre-existing
delivery resource and was preserved. No broad cleanup performed.

Runner isolation: trusted for focused review commands. Full-suite runner was
not launched because canonical gate is suspended. No baseline or product DB
resource was adopted.

Focused commands/results: `uv run task test-file tests/test_rebalance_page.py`
-> **26 passed, 12 warnings**, external elapsed **13.08s**;
`uv run task test-one
tests/visual/test_snapshots.py::test_rebalance_plan_snapshot -k desktop` ->
**1 passed, 1 deselected**, external elapsed **24.79s**;
`uv run task lint` -> **passed**, external elapsed **21.64s**;
strict F63 change validation -> **1 passed**; strict stable-spec validation ->
**78 passed**; `git diff --check` -> **passed**.

Baseline/diff/spec evidence: owner-authorized amendment changed exactly
`tests/visual/baselines/patrimonio-desktop.png`, old `1605x4271`, SHA256
`3560cbd1dbaf0ab7c3a9dd62433c49cce127560b65a20b1b8c5aeb56aaf1489a` to new
`1605x4241`, SHA256
`a748ffc079ff272383d4955b0a4c3bd05ceede722e788554c76c4cc8edc22089`.
`patrimonio-mobile.png` remains `1669x4398`, SHA256
`08363913cdfe877522b474d1245c8620ec9536cd7239822cd339d027b7be006a`; both
rebalance baselines unchanged. `git diff --name-status -- tests/visual/baselines`
reports one file. Patrimônio template diff empty; no patrimônio CSS diff;
runtime diff limited to `_rebalance_plan.html` and scoped `app.css`; no test
logic/harness, route, model, seed, or product DB change. Owner visual approval,
old/new dimensions/hashes, supported regeneration command, and receipts are
recorded above.

Verdict: **APPROVED**

#### R2-F01 — No blocking finding
Status: resolved
Requirement/task: all F63 requirements; Tasks 2.1–4.2 and owner-authorized
desktop baseline amendment.
Evidence: focused desktop/rebalance checks green; exact one-file baseline
diff; complete dossier and owner authorization in tasks.md; no open R1 finding
remains after authorized amendment.
Required change: none. Excluded scope: mobile baseline/test policy,
patrimônio template/CSS, rebalance baseline, product DB, PRD/spec edits, and
archive/commit/push.
Acceptance: applicable focused tests green, exact amendment scope verified,
all mobile tests remain runnable and unmodified, and maintenance-suspended
canonical receipt retained.
