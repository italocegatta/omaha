## Context

F63 is a surgical visual port from the existing patrimônio asset-table pattern to the one asset table rendered by `/rebalanceamento`. Current source was inspected before proposal:

- `src/omaha/templates/_rebalance_plan.html:72-127` — `rebalance-plan` renders one `table.data-table.rebalance-table[data-testid="rebalance-asset-table"]`; Alpine `columns` generates both `<thead>` and `<tbody>`, and `filteredRows` generates `tr.rebalance-asset-row` with `rowClass(row)`.
- `src/omaha/templates/_patrimonio_class_section.html:83-397` — patrimônio renders `table.data-table.asset-table`; this is source pattern only and is outside F63 write scope.
- `src/omaha/static/app.css:3574-3606` — existing canonical sticky-header and row-hover selectors cover `.table-sticky-header`, `.class-table`, and `.asset-table`; patrimônio receives `position: sticky`, `top: 0`, `z-index: 1`, transition, and `--bg-hover` on every hovered cell.
- `src/omaha/static/app.css:3284-3302` — rebalance-specific zebra and action-state backgrounds; `.rebalance-asset-row:hover td` currently uses `--table-row-hover`, while buy/sell/neutral idle state rules use `!important`.
- `tests/test_rebalance_page.py` — server-rendered rebalance contract, column model, filters, row classes, and payload assertions.
- `tests/visual/test_snapshots.py:98-132` — browser snapshot workflow that submits a contribution, waits for plan rows/charts, and captures `rebalance-plan`.

### Current relevant flow

1. User opens `/rebalanceamento` and submits contribution through existing form/PRG flow.
2. Route supplies `plan_dict`; `rebalancePage()` transforms `columns` and `filteredRows` into one table header and one row template.
3. Browser renders eight existing columns, filter controls, sort indicators, action badges, zebra backgrounds, and action-state row classes.
4. Existing `.asset-table`/`.table-sticky-header` CSS is not activated by the rebalance table because its table lacks the canonical `table-sticky-header` class. Rebalance has its own hover rule, but action-state `!important` backgrounds can mask the shared patrimoine hover cue.
5. Empty `plan.asset_plan` bypasses table rendering and keeps existing empty-state output. No API, data, sort, filter, Alpine, or route boundary is involved.

## Goals / Non-Goals

**Goals:**

- Activate existing `table-sticky-header` behavior on only `rebalance-asset-table`.
- Make hovered rebalance data rows use patrimônio’s existing `--bg-hover` cue across every cell for pointer duration, while retaining idle zebra and buy/sell/neutral state colors.
- Keep filters, sort clicks, filter-panel positioning, columns, payload, row keys, actions, empty state, and layout unchanged.
- Leave `_patrimonio_class_section.html` byte/semantically unchanged.
- Provide server markup and browser-rendered acceptance evidence for sticky position and row-wide hover.

**Non-Goals:**

- No tooltip, persistent selection, click-selected row, focus redesign, action behavior, or data/semantic change.
- No new internal scroll container, overflow/layout refactor, generic alternate table pattern, or sticky behavior on any other table.
- No API, model, migration, seed, route, Alpine data, formatter, filter, sorting, or snapshot-baseline refactor.
- No application/test implementation during proposal gate.

## Decisions

### D1. Use existing canonical class for sticky behavior

Add `table-sticky-header` to the existing rebalance `<table>` class list. This reuses current selectors instead of adding a new selector or changing `.patrimonio` markup. Existing rules provide `position: sticky; top: 0; z-index: 1`; existing `.rebalance-table-th` background and border preserve filter/header visuals. No internal scroll is introduced.

Alternative rejected: adding `overflow-y` or a new shell scroll boundary. Roadmap explicitly forbids new internal scroll and layout changes.

### D2. Port patrimônio hover token at rebalance row boundary

Keep `.rebalance-asset-row` and `rowClass(row)` unchanged. Adjust only its existing hover declaration to use `var(--bg-hover)` with hover precedence over action-state `!important` backgrounds. Precedence applies only during `tr:hover`; idle zebra and buy/sell/neutral colors remain unchanged. Existing transition is activated by the canonical class and remains 80ms.

Alternative rejected: adding JavaScript/Alpine hover state or persistent selection. CSS pseudo-state is the existing pattern and has no data/state side effect.

### D3. Preserve patrimônio as an unchanged reference

Do not edit `_patrimonio_class_section.html` or its existing `.asset-table` selectors. Diff audit must show no patrimônio template change. Browser regression keeps `/patrimonio` in the existing visual lane; its behavior is an invariant, not a new variant.

### D4. Verify behavior at two boundaries

Add minimal server markup coverage in `tests/test_rebalance_page.py` and browser coverage in `tests/visual/test_snapshots.py`. Browser oracle reads computed `position`, `top`, and hovered-cell background, and checks row/table selectors remain singular. Existing snapshot content and data assertions remain intact.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/templates/_rebalance_plan.html` — asset-plan `<table>` | `class="data-table rebalance-table"` | Add existing `table-sticky-header` class; retain `data-testid`, columns, filters, sort handlers, row templates, and keys exactly | Activate canonical sticky header only on rebalance table |
| `src/omaha/static/app.css` — `.rebalance-asset-row:hover td` | Rebalance hover uses `var(--table-row-hover)` and loses to action-state `!important` colors | Use existing patrimônio `var(--bg-hover)` with hover-only precedence so every hovered cell visibly lifts; retain idle state rules | Port row-wide patrimônio cue without changing non-hover states |
| `src/omaha/templates/_patrimonio_class_section.html` | Existing patrimoine table and behavior | No change | Preserve source behavior byte/semantically |
| `tests/test_rebalance_page.py` — rebalance markup contract | No assertion for canonical sticky hook / row visual hook | Assert exactly one rebalance table carries hook and existing eight-column/filter/row contracts remain | Independent server-rendered structure oracle |
| `tests/visual/test_snapshots.py` — `test_rebalance_plan_snapshot` or focused helper | Snapshot proves table presence but not hover/sticky behavior | Add browser assertions for sticky header computed style/scroll position and all-cell hover background; retain screenshot and existing waits | Independent browser-visible acceptance oracle |

## Risks / Trade-offs

- **[Sticky header overlays top content]** → reuse existing `top: 0`, `z-index: 1`, header background, and browser assertion after page scroll; do not add new offsets or scroll shells.
- **[Action-state `!important` masks hover]** → make only the existing rebalance hover declaration win during `:hover`; verify buy, sell, and neutral rows plus idle state in browser where fixtures permit.
- **[Filter panels become clipped or hidden]** → preserve `.rebalance-table-th`/`.rebalance-table-th--has-filter` positioning and `overflow: visible`; test existing filter-trigger markup and no new overflow rule.
- **[Patrimônio regression from shared CSS edit]** → use existing tokens/selectors only, do not alter `.asset-table` rules or patrimônio template, and run focused visual patrimoine coverage during implementation review.
- **[Scope drift into refactor]** → changed-file audit limited to F63 runtime/test files plus F63 artifacts; no baseline, route, data, or generic table cleanup unless acceptance proves necessity.

## Migration Plan

No migration or deployment step. Apply is blocked until F60 is `Applied`, F60 owner visual validation is recorded, and owner approves F63 static mock/prototype/browser rendering. Apply then makes listed surgical edits, runs focused taskipy tests, and records browser evidence. Rollback removes only the added class, hover declaration adjustment, and F63 test assertions/spec artifacts; no database or seed operation is authorized.

## Open Questions

None for proposal. Apply must stop with `BLOCKED_FOR_IMPLEMENTATION_BRIEF` if current CSS/template differs from this inspected map or if the required F60/owner approvals are absent.

## Implementation Decisions

- Preflight 2026-08-24 confirmed the implementation map remains exact: the
  rebalance table has no `table-sticky-header` class, its existing hover rule
  uses `--table-row-hover`, and buy/sell/neutral idle backgrounds use
  `!important`; canonical sticky/transition/`--bg-hover` rules remain scoped
  to existing hooks. Decision: add only the canonical table class, make the
  existing rebalance hover declaration win during `:hover`, and leave
  patrimônio selectors/template untouched. Impact: no Alpine, layout, data, or
  interaction changes. Evidence: current source inspection of
  `_rebalance_plan.html`, `_patrimonio_class_section.html`, and `app.css`.
- Browser preflight 2026-08-24 exposed a cascade interaction not visible in
  static markup: canonical `.table-sticky-header thead th` specificity
  overrode existing `.rebalance-table-th` header background/border when the
  hook was added. Decision: add one rebalance-table-scoped preservation rule
  using existing header tokens after canonical sticky rules. Impact: sticky
  positioning activates without changing filter/header appearance or
  screenshot baseline; no other table receives override. Evidence: first
  focused browser run passed sticky/hover assertions and showed a 48-row
  header-only snapshot diff before this bounded override.
- Remediation preflight 2026-08-24 confirmed the supported visual fixture still
  binds to the exact declared `data/test_visual.db` path and deletes that path
  inside `live_url_visual` before seeding (`tests/visual/conftest.py:35,90-99`).
  The exact path was already present before this remediation run, without
  current-run ownership evidence. Decision: do not launch the fixture, adopt
  the DB, or modify unrelated visual harness code; stop before resource use
  and require a trusted isolated runner. Impact: F63 remains blocked on R1-F01
  despite no implementation change. Evidence: preflight stat/hash receipt in
  `tasks.md` remediation evidence.
- Final remediation 2026-08-24 used explicit owner authorization to delete and
  recreate only the exact visual DB path, then ran the supported patrimônio
  snapshot command once. Both existing dimension contracts still failed before
  any F63-specific behavior assertion: desktop `1605x4271` expected versus
  `1605x4241` current, mobile `1669x4398` expected versus `1669x4346` current.
  Decision: classify R1-F01 as unresolved pre-existing visual dimension drift;
  do not change patrimônio code, harness, tests, or baselines. Impact: final
  remediation remains blocked, with current-run DB cleanup proven. Evidence:
  `tasks.md` remediation 2/2 ledger and focused command receipt.
