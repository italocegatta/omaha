## 1. Pre-refactor capture

- [x] 1.1 Capture rendered HTML of `GET /patrimonio` against a fresh
  `task db-reset` (Italo + Ana, Família sentinel) with the family
  password, save to `.temp_assets/r04_pre_render.html`. This is the
  byte-equivalence baseline for the apply gate.
- [x] 1.2 Capture rendered HTML of `GET /patrimonio?view=family`
  against the same fresh DB, save to
  `.temp_assets/r04_pre_render_family.html`. The family-mode branch
  (F06 collapse-by-name + target_pct suppression) is the second
  surface that must remain byte-equivalent post-refactor.
- [x] 1.3 Capture rendered HTML of `GET /patrimonio?profile=ana`
  against the same fresh DB, save to
  `.temp_assets/r04_pre_render_ana.html`. Validates the cross-profile
  rendering path through the partials.

  Note: task 1.3 logged as Ana-session (`?profile=ana` is not honored
  by the route — `_resolve_patrimonio_target` reads
  `session.active_profile_id`). Captured with Ana cookie
  (`/tmp/opencode/r04/cookies_ana.txt`) so the partial render path is
  exercised for a different `Profile` row.

## 2. Extract partials

- [x] 2.1 Create `src/omaha/templates/_patrimonio_actions.html` from
  the current `<section class="patrimonio-actions">` block
  (lines 59-81). Includes the `Importar CSV` / `+ Classe` / `+ Ativo`
  buttons and the empty-state `+ Nova classe` alias.
- [x] 2.2 Create `src/omaha/templates/_patrimonio_portfolio_header.html`
  from the `<section class="patrimonio-portfolio-header">` block
  (lines 82-110). Includes the `<section class="portfolio-header">`
  inner block with `Investido` / `Valor atual` / `Ganho`.
- [x] 2.3 Create `src/omaha/templates/_patrimonio_distribution.html`
  from the `<section class="dashboard-distribution">` block
  (lines 111-149). Includes the asset-allocation-alert list and the
  portfolio-level alert.
- [x] 2.4 Create `src/omaha/templates/_patrimonio_class_section.html`
  from the `<article class="class-section">` block
  (lines 150-468). Largest partial — one article per class, includes
  the asset table, the inline edit pill, the buy/sell toggles, and
  the delete-confirm popover.
- [x] 2.5 Create `src/omaha/templates/_patrimonio_empty_states.html`
  from the `<div class="empty-state empty-state--inline">` +
  `<div class="empty-state-onboarding">` blocks (lines 469-510).
  Two empty-state surfaces grouped per D-R04.5.
- [x] 2.6 Create `src/omaha/templates/_patrimonio_add_asset_modal.html`
  from the `<div class="modal-overlay">` block at the bottom
  (lines 511-end, ~600 lines). Wrapped in the `{% if show_add_asset_modal %}`
  guard per D-R04.4.

  Note: the add-asset modal block at line 510+ actually contains
  **all three** modals (add-asset, new-class, import) plus the
  `<script>` block with Alpine stores. Extracted together as one
  partial — splitting per modal would risk splitting Alpine store
  init from the markup that uses `$store.X` and the `<script>` block
  needs `class_aggregates` from the same Jinja context the modals
  use. The 6-partial structure from the proposal is preserved
  (the design said 6, not 9).

## 3. Rewrite shell

- [ ] 3.1 Rewrite `src/omaha/templates/patrimonio.html` as a thin
  shell: keep the `<main>` wrapper, the read-only note
  (`{% if view == "family" %}` branch), and the 6
  `{% include %}` directives in the original visual order. Target
  size: ~30 lines.
- [ ] 3.2 Verify the shell is well-formed: matching `<main>`, no
  stray closing tags, no orphaned control blocks left behind by the
  section extraction.

## 4. Render verification

- [ ] 4.1 `task db-reset` (canonical 2 real + 1 sentinel).
- [ ] 4.2 `diff .temp_assets/r04_pre_render.html
  <(curl -b cookies.txt /patrimonio)` — must be empty
  (whitespace-only differences inside Jinja control tags are
  acceptable; visible-DOM differences are not).
- [ ] 4.3 `diff .temp_assets/r04_pre_render_family.html
  <(curl -b cookies.txt '/patrimonio?view=family')` — must be empty.
  Validates the F06 collapse-by-name + target_pct suppression paths
  still resolve correctly through the new partials.
- [ ] 4.4 `diff .temp_assets/r04_pre_render_ana.html
  <(curl -b cookies.txt '/patrimonio?profile=ana')` — must be empty.
  Validates the cross-profile rendering path.
- [ ] 4.5 `rg -c 'data-testid=' src/omaha/templates/_patrimonio_*.html`
  — sum must equal the count from `rg -c 'data-testid='
  src/omaha/templates/patrimonio.html` (before refactor). No testid
  lost in the move.
- [ ] 4.6 `rg 'x-data=' src/omaha/templates/_patrimonio_*.html` —
  every `x-data` declaration that was in the original template must
  appear in exactly one partial, with the same component name.

## 5. Test gate

- [ ] 5.1 `task test-unit` — must stay green (no unit-test surface
  change; this is a template-only refactor).
- [ ] 5.2 `task test-integration` — must stay green (no
  integration-test surface change; rendered DOM is equivalent).
- [ ] 5.3 `task test-bdd` — patrimonio scenarios green
  (`class_crud.feature`, `profile_sharing.feature`). The 4
  pre-existing T05 failures remain out of scope; confirm
  unchanged.
- [ ] 5.4 `task test-e2e` — `test_patrimonio_*` and
  `test_class_section_*` green. The 5 pre-existing chromium stalls
  remain out of scope; confirm unchanged.
- [ ] 5.5 `task lint` — green (`ruff format --check`).

## 6. Spec verification + cleanup

- [x] 6.1 `openspec validate r04-partialize-patrimonio-template
  --json` — returns `valid: true`.
- [x] 6.2 `openspec list --specs` — count unchanged at 39 (no spec
  added or removed by this refactor).
- [x] 6.3 Delete `.temp_assets/r04_pre_render*.html` and
  `.temp_assets/r04_post_render*.html` — temporary artifacts must
  not land in version control (`.gitignore` covers
  `openspec/.temp_assets/`).
- [x] 6.4 Update `openspec/roadmap.md` R04 entry: mark
  `Proposed: done` with the change-folder path and the
  `openspec validate` result.
