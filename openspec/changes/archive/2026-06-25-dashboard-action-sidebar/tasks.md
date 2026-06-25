## 1. Layout shell

- [x] 1.1 In `src/omaha/static/app.css`, delete the rule
      `main { max-width: 640px; margin: 2rem auto; padding: 0 1.5rem; }`
      (line 201).
- [x] 1.2 Add the body grid layout:
      `body { display: grid; grid-template-columns: 280px 1fr; }` below
      480px, with the sidebar column collapsing to 0 below the
      breakpoint.
- [x] 1.3 Add `.dashboard-card` rule: `--surface` background, 1px
      `--border-strong` border, 8px radius, max-width 720px, padding
      `2rem 2.5rem`, centered in the right column.
- [x] 1.4 Audit every existing selector that depends on
      `main > h1`, `main > .class-summary`, etc. and migrate to
      `.dashboard-card > h1`, `.dashboard-card > .class-summary`. The
      easiest pass is to wrap the entire `{% block content %}` body
      in a `<div class="dashboard-card">` rather than touching every
      child rule.

## 2. Sidebar markup + CSS

- [x] 2.1 In `src/omaha/templates/dashboard.html`, add the
      `<aside class="app-sidebar" data-testid="app-sidebar">` element
      as a sibling of the dashboard card wrapper, above it in DOM
      order so it lands in the left grid column.
- [x] 2.2 Inside the sidebar, add the wordmark:
      `<h2 class="sidebar-wordmark" data-testid="sidebar-wordmark">{{ profile.name }}</h2>`.
- [x] 2.3 Add three block-buttons inside the sidebar, in order:
      `Importar CSV` (`data-testid="dashboard-import-btn"`),
      `+ Novo ativo` (`data-testid="dashboard-add-asset-open"`),
      `+ Nova classe` (`data-testid="empty-state-create-class"`).
      Each button is a `<button type="button" class="sidebar-action">`.
- [x] 2.4 In `app.css`, add `.app-sidebar` (sticky, hairline right
      border, padding `1.5rem 1rem`, `--bg` background), `.sidebar-wordmark`
      (Source Serif 4, 1.75rem, 600, -0.02em), `.sidebar-action` (block
      button per design.md D6), `.sidebar-action[aria-current="true"]::before`
      (3px left bar in `--accent`).

## 3. Move inline triggers to sidebar

- [x] 3.1 Remove the `<div class="dashboard-actions">` block containing
      the `Importar CSV` button (lines ~6-14 of `dashboard.html`).
- [x] 3.2 Remove the `<div class="dashboard-add-asset-actions">` block
      containing the `+ Ativo` button (lines ~42-51 of `dashboard.html`).
- [x] 3.3 Remove the empty-state `+ Nova classe` button at lines
      ~343-350 (`empty-state-create-class`).
- [x] 3.4 Remove the inline `new-class-plus-btn` button at lines
      ~365-372 (inside `new-class-container`). Keep the
      `new-class-container` div as a no-op for now — it will be
      removed entirely when the modal replaces it (task 5).

## 4. Promote `+ Nova classe` to a modal

- [x] 4.1 In `dashboard.html`, add a new Alpine store
      `Alpine.store('newClassModal', { open, name, targetPct, saving,
      error, openModal, closeModal, submit })` mirroring the existing
      `addAssetModal` shape. `submit()` POSTs to `/api/classes`; on
      201 it reloads the page; on 409/422 it surfaces `body.detail` in
      `error`.
- [x] 4.2 Add the modal markup at the bottom of `dashboard.html`,
      reusing the modal shell (task 6):
      `<div class="new-class-modal-overlay" data-testid="new-class-modal-overlay" x-data x-show="$store.newClassModal.open" x-cloak x-transition.opacity.duration.200ms @click.self="$store.newClassModal.closeModal()"> ... </div>`.
      Body fields: name input
      (`data-testid="new-class-modal-name-input"`), target_pct input
      (`data-testid="new-class-modal-pct-input"`), error paragraph
      (`data-testid="new-class-modal-error"`), Save and Cancel
      buttons.
- [x] 4.3 Remove the now-redundant inline `newClassForm()` Alpine
      component (lines ~1353-1406 of `dashboard.html`).
- [x] 4.4 Remove the empty `.new-class-container` div (lines ~365-426
      of `dashboard.html`) now that the modal exists.

## 5. Modal shell CSS abstraction

- [x] 5.1 In `app.css`, add the shell class set:
      `.modal-overlay` (fixed inset:0, backdrop), `.modal-panel`
      (`--surface`, 1px border, 8px radius, max-width 480px, padding
      1.5rem, max-height 90vh, overflow-y auto, shadow per DESIGN.md),
      `.modal-header` (flex space-between, 1px bottom border),
      `.modal-title` (1.1rem 600), `.modal-close` (× button), `.modal-body`,
      `.modal-footer` (flex end, gap 0.5rem).
- [x] 5.2 Refactor `.import-modal-overlay` and `.import-modal-panel`
      to use `.modal-overlay` and `.modal-panel` (delete the duplicate
      rules, point the existing markup at the shell classes). Behavior
      is unchanged — only the visual shell is unified.
- [x] 5.3 Refactor `.add-asset-modal-overlay` and `.add-asset-modal-panel`
      the same way.
- [x] 5.4 Apply the shell to the new `.new-class-modal-overlay` /
      `.new-class-modal-panel` markup from task 4.

## 6. Zero-classes onboarding card

- [x] 6.1 In `dashboard.html`, replace the existing
      `.empty-state` block (lines ~334-352) with a new
      `.empty-state-onboarding` card
      (`data-testid="empty-state-onboarding"`) when `asset_classes` is
      empty. Heading `Vamos comecar`, three rows
      (`1. Crie uma classe`, `2. Adicione ativos`,
      `3. Importe o extrato da corretora`), and a hint paragraph
      pointing at the sidebar.
- [x] 6.2 In `app.css`, add `.empty-state-onboarding` (1px dashed
      `--border-strong`, padding 1.5rem), `.empty-state-onboarding-title`
      (1rem 600, `--ink`), `.empty-state-step` (0.92rem row with the
      number in serif tabular figures and the label in Inter).

## 7. Mobile drawer

- [x] 7.1 In `src/omaha/templates/base.html`, add the hamburger button
      inside `.app-header-left`, before the wordmark. Visible only
      when `{% if profile is defined and profile %}`:
      `<button type="button" class="app-header-hamburger" data-testid="app-header-hamburger" aria-label="Abrir menu" aria-expanded="false" aria-controls="app-sidebar" @click="$store.sidebar.toggle()">☰</button>`.
- [x] 7.2 Add the `$store.sidebar` Alpine store in a `<script>` block
      in `base.html` (after the Alpine CDN script tag): `{ open: false,
      toggle(), close() }`.
- [x] 7.3 In `app.css`, add `.app-header-hamburger` (32×32 button,
      hidden above 480px, three horizontal lines via `::before` /
      `::after` or an inline `☰`). Add the drawer transform on
      `.app-sidebar` below 480px (`position: fixed; top: 0; bottom: 0;
      left: 0; width: 280px; transform: translateX(-100%); z-index: 50;
      transition: transform 0.2s`) and the open state
      (`[x-show="$store.sidebar.open"]` or a class toggle).
- [x] 7.4 Add the backdrop element: `<div class="app-sidebar-backdrop" data-testid="app-sidebar-backdrop" x-show="$store.sidebar.open" @click="$store.sidebar.close()" x-cloak></div>`.
      Style: `position: fixed; inset: 0; background: color-mix(in
      srgb, var(--ink) 35%, transparent); z-index: 40;`. Visible only
      below 480px.
- [x] 7.5 Add ESC key handler: `@keydown.escape.window="$store.sidebar.close()"`
      on `body` or on the drawer container.
- [x] 7.6 Add focus management: when the drawer opens, move focus to
      the first focusable element inside the sidebar (`x-init` on the
      drawer, or `x-effect` watching `$store.sidebar.open`). On close,
      focus returns to the hamburger (capture the hamburger reference
      via `x-ref` in `base.html` and call `.focus()` in the store's
      `close()` method).

## 8. Active-state wiring

- [x] 8.1 In the sidebar markup, wire each `.sidebar-action`'s
      `aria-current` to its modal's open flag:
      `:aria-current="$store.importModal.open ? 'true' : null"` on the
      Importar CSV button, `:aria-current="$store.addAssetModal.open ? 'true' : null"` on
      the `+ Novo ativo` button, `:aria-current="$store.newClassModal.open ? 'true' : null"` on
      the `+ Nova classe` button.

## 9. README + retired-route clarification

- [x] 9.1 In `README.md` line 250, replace "Click **Importar** in the
      nav to test the CSV importer" with "Click **Importar CSV** in
      the sidebar to test the CSV importer".
- [x] 9.2 In `README.md` line 296, append a note to the template list:
      `import, import_review, classes, assets` are kept in the tree
      as historical artifacts; their routes 302 to `/` and they are
      not reachable from the UI.

## 10. Test selector updates

- [x] 10.1 In `tests/test_t03_pages_routes.py`, find any
      `data-testid="dashboard-import-btn"` selector that walks up to
      `data-testid="dashboard-actions"` and update to walk up to
      `data-testid="app-sidebar"` (or just check visibility on the
      sidebar). Same for `dashboard-add-asset-open` →
      `dashboard-add-asset-actions` → `app-sidebar`.
- [x] 10.2 In `tests/bdd/features/import-flow.feature` (and any related
      step defs), update step text that references the button location.
      E.g. `When I click "Importar CSV" in the sidebar`.
- [x] 10.3 In `tests/e2e/`, find Playwright selectors
      (`page.locator('[data-testid="dashboard-import-btn"]')` etc.)
      and update parent-context assertions. Add new selectors for
      `app-sidebar`, `sidebar-wordmark`, `empty-state-onboarding`,
      `new-class-modal-overlay`.

## 11. Verification

- [x] 11.1 `uv run task lint` — ruff + format check pass.
- [x] 11.2 `uv run task test-unit` — pure-function unit tests pass.
- [x] 11.3 `uv run task test-integration` — DB + TestClient + audit
      tests pass.
- [x] 11.4 `uv run task test-bdd` — BDD scenarios pass with updated
      selectors.
- [x] 11.5 `uv run task test-e2e` — Playwright passes (or skip if
      Chromium not installed in this environment).
- [x] 11.6 `uv run task db-reset` — confirm `db-reset` still works
      after the layout change (no DB impact expected, but smoke-check).
- [x] 11.7 Use the `refresh-for-test` skill: restart uvicorn, smoke
      `/healthz`, visit dashboard via LAN URL, confirm sidebar renders,
      three buttons open the correct modals, mobile drawer works below
      480px (use Playwright's `setViewportSize`), zero-classes
      onboarding renders.
- [x] 11.8 Sync specs: `openspec sync-specs dashboard-action-sidebar`
      to write the deltas into `openspec/specs/import-modal/spec.md`
      and `openspec/specs/dashboard-inline-editing/spec.md`, and to
      archive the change into `openspec/changes/archive/`.
