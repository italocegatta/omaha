## Why

The dashboard today is the only active page in the app, but its three
primary action triggers (`Importar CSV`, `+ Ativo`, `+ Nova classe`) are
scattered in three different inline locations — top, mid, and bottom of
the page. After the user has scrolled down through the class sections,
the `Importar CSV` button is off-screen. There is no consistent surface
where the family finds "what can I do right now?" — every CTA is
contextual to its position in the layout.

This change consolidates the three actions into a single left rail — a
permanent, sticky card-index of the dashboard's mutating operations —
anchored by the profile's name in serif. The dashboard content becomes a
bounded card, mirroring the spreadsheet discipline that DESIGN.md already
commits to. On mobile, the rail becomes an off-canvas drawer behind a
hamburger in the header.

## What Changes

- **New**: Persistent left sidebar on `dashboard.html` (`<aside class="app-sidebar">`)
  with three block-buttons — `Importar CSV`, `+ Novo ativo`, `+ Nova classe` —
  rendered above the dashboard content. Sticky (`position: sticky; top: 1rem`)
  on desktop, off-canvas drawer on `<480px`.
- **New**: A bounded card wrapper (`.dashboard-card`, max-width 720px,
  `--surface` background, 1px border, 8px radius) around the existing
  dashboard content. The old `main { max-width: 640px; margin: 2rem auto }`
  rule is deleted; the dashboard content lives inside the card.
- **New**: A big serif wordmark at the top of the sidebar — Source Serif 4,
  1.75rem, 600, -0.02em letter-spacing — rendering the active profile's
  name (`Italo` or `Ana Livia`). The page `<h1>` keeps the existing
  `Bem-vindo, {{ profile.name }}` greeting.
- **New**: A new Alpine store `$store.newClassModal` plus a `<div class="new-class-modal-overlay">`
  that promotes the existing inline `newClassForm` to a modal. Reuses
  the same `POST /api/classes` endpoint; reloads the page on 201 to pick
  up server-rendered aggregates.
- **New**: A CSS-only modal shell abstraction — `.modal-overlay`,
  `.modal-panel`, `.modal-header`, `.modal-title`, `.modal-body`,
  `.modal-footer`, `.modal-close`. The existing `.import-modal-*` and
  `.add-asset-modal-*` rules refactor onto the shell; bodies stay bespoke.
- **Modified**: The three inline action triggers
  (`dashboard-import-btn` above the welcome heading;
  `dashboard-add-asset-open` above the class sections;
  `empty-state-create-class` + `new-class-plus-btn` in the
  empty-state / inline form) are removed from `dashboard.html`. The
  sidebar carries the same `data-testid`s.
- **Modified**: The zero-classes empty state becomes a 3-step onboarding
  card: `1. Crie uma classe / 2. Adicione ativos / 3. Importe o
  extrato da corretora`, with a hint pointing the user at the sidebar.
  The inline `newClassForm` (its form inputs + Save/Cancel buttons) is
  removed; only the modal form survives.
- **Modified**: Mobile (<480px) — header gains a hamburger button
  (`.app-header-hamburger`) before the wordmark. Tapping opens the
  drawer via `$store.sidebar.toggle()`. A backdrop covers the rest of
  the viewport. ESC closes; focus returns to the hamburger.
- **Modified**: `README.md` — line 250 ("Click **Importar** in the
  nav to test the CSV importer") and line 296 (template list) are
  updated to reflect that `/classes`, `/assets`, `/import`,
  `/import/review` are retired routes that 302 to `/`. The
  template list marks them as retained-but-dead.
- **Modified**: Spec `import-modal` — the requirement that the
  "Importar CSV" button sits inside `data-testid="dashboard-actions"`
  is updated to: sidebar entry carries `data-testid="dashboard-import-btn"`.
- **Modified**: Spec `dashboard-inline-editing` — the requirement that
  the single `+ Ativo` button sits above the asset table inside
  `dashboard-add-asset-actions` is updated to: sidebar entry carries
  `data-testid="dashboard-add-asset-open"`.

No new route. No DB migration. No new dependency. No breaking API
change. No new CSV seed path. CSS-only + Alpine store additions.

## Capabilities

### New Capabilities

- `dashboard-sidebar`: The persistent left action rail on the dashboard.
  Owns the sidebar markup, the three block-buttons, the serif wordmark,
  the sticky positioning, the mobile off-canvas drawer (with hamburger,
  backdrop, focus management), the Alpine store `$store.sidebar`, and the
  3-step zero-classes onboarding card. Also owns the new
  `$store.newClassModal` (the modal form for creating a class) and the
  testid contract for the three moved triggers.

- `modal-shell`: The shared CSS abstraction for modal overlays. Owns
  `.modal-overlay`, `.modal-panel`, `.modal-header`, `.modal-title`,
  `.modal-body`, `.modal-footer`, `.modal-close`. The three existing
  modals (`importModal`, `addAssetModal`, `newClassModal`) refactor onto
  this shell — markup rewrites only, no JS abstraction, no behavior
  change to the stores that back them.

### Modified Capabilities

- `import-modal`: Requirement `Botão "Importar CSV" no dashboard` —
  the button's parent context changes from `data-testid="dashboard-actions"`
  to the sidebar (`<aside class="app-sidebar">`). The testid
  `dashboard-import-btn` is preserved on the new sidebar button. No
  other requirement changes.

- `dashboard-inline-editing`: Requirement `Criação inline de ativo` —
  the trigger button's parent context changes from
  `dashboard-add-asset-actions` (above the class sections) to the
  sidebar. The testid `dashboard-add-asset-open` is preserved. No other
  requirement changes; the modal behavior is unchanged.

## Impact

- **Templates**: `dashboard.html` (sidebar markup, modal shell rewrite,
  removal of inline triggers and inline `newClassForm`); `base.html`
  (hamburger button + `$store.sidebar` script in `<head>`).
- **Static**: `app.css` (`.app-sidebar`, `.sidebar-action`,
  `.dashboard-card`, `.modal-overlay`, `.modal-panel`, `.modal-header`,
  `.modal-title`, `.modal-body`, `.modal-footer`, `.modal-close`,
  `.app-header-hamburger`, `.empty-state-onboarding`,
  `.empty-state-step`); existing `.import-modal-*` and
  `.add-asset-modal-*` rules refactor onto the shell.
- **Routes**: none.
- **DB / Alembic**: none.
- **Spec contracts**: `import-modal/spec.md` and
  `dashboard-inline-editing/spec.md` need delta specs to move the
  button location requirement.
- **Tests**: `tests/test_t03_pages_routes.py` and the BDD
  `tests/bdd/features/import-flow.feature` look for the moved testids
  in their current parent contexts — the test selectors need updating
  to find them in the sidebar. No new test files; existing ones update.
- **README**: lines 250 and 296 — clarify retired routes.
- **No new CSV seed**, **no new inline asset/position seed**, **no
  ADMIN_PASSWORD change**, **no Alpine binding gotcha** (the sidebar
  uses button `aria-current` and existing global stores; no
  server-driven `<select>` inside it).