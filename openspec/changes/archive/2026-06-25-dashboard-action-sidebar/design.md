## Context

The dashboard (`src/omaha/templates/dashboard.html`) is the only live page
in the app. `/login`, `/profiles` are entry points; `/classes`, `/assets`,
`/import`, `/import/review` are 302 redirects to `/` (see
`src/omaha/routes/{classes,assets,imports}.py` for the redirect docstrings).
The dashboard's three primary mutating operations
(`Importar CSV`, `+ Ativo`, `+ Nova classe`) each open a different modal:

| Trigger location | Testid | Store | Modal id |
|---|---|---|---|
| `dashboard-actions` div (top of page) | `dashboard-import-btn` | `$store.importModal` | `#import-modal-overlay` |
| `dashboard-add-asset-actions` div (above classes) | `dashboard-add-asset-open` | `$store.addAssetModal` | `#add-asset-modal-overlay` |
| Empty-state button + inline form trigger | `empty-state-create-class`, `new-class-plus-btn` | `newClassForm()` Alpine component | n/a (inline) |

The `$store.importModal` and `$store.addAssetModal` are global Alpine
stores defined at the bottom of `dashboard.html` (~line 1534 and ~1710);
any trigger in any `x-data` scope can call `openModal()`. The
`newClassForm()` is a component function bound to a sibling
`new-class-container` div that listens for a window-level
`open-new-class` event.

The three modals (and the inline form) share an overlay/panel shape but
have duplicated CSS rules. Refactoring to a shared shell is the second
goal of this change.

The dashboard layout is centered at `max-width: 640px` per
`main { max-width: 640px; margin: 2rem auto; padding: 0 1.5rem; }`. The
spreadsheet discipline (1px borders, no shadows, fern accent, Source
Serif 4 used surgically) is committed to in `DESIGN.md` (line 114 —
"the dashboard naturally stays under 60ch at 760px max-width").

## Goals / Non-Goals

**Goals:**

- Consolidate the three action triggers into a single persistent
  left rail, accessible at every scroll position on the dashboard.
- Bounded card layout: the dashboard content lives inside a
  `--surface` card with a 1px border, mirroring the spreadsheet
  aesthetic committed to in DESIGN.md.
- Single source of visual identity: the serif wordmark at the top of
  the sidebar carries the profile's name, distinct from but echoing
  the page h1 greeting.
- Promote the inline `newClassForm` to a modal for visual consistency
  with the other two actions.
- Refactor the three modal overlays onto a CSS shell so the next
  modal (rename class, edit profile, …) doesn't copy-paste boilerplate.
- Mobile drawer with hamburger toggle, focus trap, ESC close.
- 3-step onboarding card when zero classes exist.
- Update README to reflect that `/classes /assets /import /import/review`
  are retired routes.

**Non-Goals:**

- New routes or DB migrations.
- New navigation surface. `/profiles` and `/login` are unchanged.
- Changes to the dashboard's data computation, classes, assets,
  positions, alerts, or compare-bars.
- Vertical mini-compare-bar or numeric sidebar labels. The sidebar
  is action-only — no metrics.
- Number prefixes (01/02/03) on sidebar items — the actions are not a
  sequence.
- Sidebar-driven theme color (the blue `#0a66c2` rectangle in the
  user-provided screenshot is a placeholder; the new sidebar is
  off-white with hairline border).
- A4: Per-class empty state for "no assets in class" (already speced
  in `dashboard-inline-editing/spec.md:247` — unchanged).
- E2E test rewrites beyond testid context updates (the modal
  behavior, CSV parsing, and step transitions are unchanged).

## Decisions

### D1. Sidebar lives in `dashboard.html`, not `base.html`.

**Why**: `/login` and `/profiles` should not show a sidebar. Putting it
in `base.html` would either show it where it doesn't belong or require
a `{% if profile is defined and profile %}` carve-out. Putting it in
`dashboard.html` keeps the sidebar scoped to the only page where the
actions apply. The hamburger + `$store.sidebar` store go in
`base.html` because the hamburger is always rendered in the header
(even when no sidebar is shown — the hamburger on `/profiles` opens an
empty drawer, which is fine: a small "no actions available" message,
or the hamburger is hidden via `{% if profile %}`).

**Alternative considered**: global sidebar with `{% block sidebar %}`
override. Rejected — adds Jinja block surface and template complexity
without benefit on a single live page.

### D2. Layout is "bounded card" (Option C).

`body { display: grid; grid-template-columns: 280px 1fr; }` below 480px,
sidebar collapses. The right column has `display: flex; justify-content:
center;` to center the card. The `.dashboard-card` is
`max-width: 720px; width: 100%; background: var(--surface);
border: 1px solid var(--border-strong); border-radius: 8px;
padding: 2rem 2.5rem;`. The old
`main { max-width: 640px; margin: 2rem auto; padding: 0 1.5rem; }`
rule is deleted.

**Why**: The card honors DESIGN.md's "cards are flat with 1px solid
var(--border), no shadow" rule (line 152). It gives the sidebar a
reason to exist as a separate visual layer — chrome vs. content. The
80px widening (640 → 720) is the smallest delta that lets the class
tables breathe without breaking the 60ch reading-width commitment.

**Alternatives considered**:
- "Sacred column" (keep main at 640px) — leaves ~600px of dead
  whitespace on a 1920px monitor. Rejected.
- "Let it breathe" (main expands to ~880px) — breaks the 60ch commitment
  in DESIGN.md. Rejected.

### D3. Boldness lives in the serif wordmark.

`.sidebar-wordmark { font-family: 'Source Serif 4', serif; font-size:
1.75rem; font-weight: 600; letter-spacing: -0.02em; color: var(--ink);
margin: 0; }`. Renders `{{ profile.name }}` (e.g. "Italo"). The page
`<h1>` keeps `Bem-vindo, {{ profile.name }}` — wordmark is identity,
h1 is greeting. Roles do not overlap.

**Why**: The profile name is already a recurring identity marker
(header text "Perfil: {{ profile.name }}", page h1 "Bem-vindo, ...",
and the dashboard wordmark is the third appearance of the same name).
Making it the sidebar's wordmark gives the sidebar a reason to be
on-brand without adding a logo or app wordmark (Omaha already lives
in the app header).

**Alternatives considered**:
- Vertical mini-compare-bar — redundant with the portfolio header
  on the page.
- Tabular-figure nav labels (01/02/03) — frontend-design skill warns
  against generic numbering when the content isn't a sequence. The
  three actions are not a sequence.

### D4. The fern accent appears only on the sidebar's active-state indicator.

Each sidebar block-button carries a 3px left bar in `--accent` when
its modal is open (`aria-current="true"` driven by
`$store.importModal.open || $store.addAssetModal.open || $store.newClassModal.open`).
This is the **only** place the fern accent appears in the sidebar.

**Why**: One signature bold element (the wordmark). One restrained
accent role (active state). Everything else in the sidebar is
neutral --ink / --surface. The skill rule "spend your boldness in
one place" is honored.

### D5. Modal shell is CSS-only; the three stores stay bespoke.

`.modal-overlay`, `.modal-panel`, `.modal-header`, `.modal-title`,
`.modal-body`, `.modal-footer`, `.modal-close` are the shared class
set. The `$store.importModal`, `$store.addAssetModal`,
`$store.newClassModal` stores stay bespoke — each has different
field state, validation, and submit logic.

**Why**: CSS-only abstraction removes ~150 lines of duplicated modal
CSS without locking in a JS contract that we don't yet have enough
evidence to design (only 3 modals exist; the 4th case is unknown).
The seam is "shared visual shell + bespoke body + bespoke store."

**Alternative considered**: full shell + JS abstraction. Rejected —
premature lock-in.

### D6. Sidebar block-buttons, not link-rows.

`.sidebar-action` is a `<button type="button">` with full-width,
1px border, padding `0.6rem 0.75rem`, font-size `0.85rem`. Hover is
`--bg-hover` + border `--ink-muted`. No icons (typography carries).
No chevrons. Active state is the 3px left bar.

**Why**: The sidebar is an action surface, not a navigation surface.
The frontend-design skill's "block-buttons vs link-rows" distinction
matters: the former signals "do something" (open a modal), the
latter signals "go somewhere" (navigate to a page). Since all three
items open modals, block-buttons are correct.

**Alternative considered**: link-row with chevrons. Rejected — would
imply navigation when there is no navigation.

### D7. Empty state becomes a 3-step onboarding card.

When `asset_classes` is empty, render an `.empty-state-onboarding`
card (1px dashed `--border-strong`, padding `1.5rem`) with the
heading `Vamos comecar` and three rows:
`1. Crie uma classe / 2. Adicione ativos / 3. Importe o extrato da
corretora`. A small hint below: `Use os botoes na barra lateral. As
classes devem somar 100%.`. The inline `newClassForm` is removed;
the sidebar `+ Nova classe` button is the only entry point.

**Why**: The empty moment is rare and precious. The current single-CTA
empty state is wasted screen real estate. Three steps is the
dashboard's only onboarding opportunity, and it now points at the
sidebar explicitly so the user learns the action surface.

**Alternative considered**: keep single-line instruction. Rejected —
too thin for a moment the user only sees once. Delete the empty
state entirely. Rejected — gives no direction.

### D8. Mobile drawer: hamburger in `.app-header-left`, before wordmark.

`.app-header-hamburger` is a 32×32 button with three horizontal
lines, `aria-label="Abrir menu"`, `aria-expanded`,
`aria-controls="app-sidebar"`. Tapping calls
`$store.sidebar.toggle()`. The drawer slides in from the left
(`transform: translateX(0)`) with a `--ink` 35%-opacity backdrop
covering the rest of the viewport. ESC closes; focus returns to
the hamburger. Focus trap inside the drawer when open
(`@keydown.tab.prevent="$el.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex=\"-1\"])').forEach(…cyclically…)"`).

**Why**: Standard pattern; lowest a11y risk; matches the existing
`.app-header` DOM structure.

### D9. Alpine store `$store.sidebar` lives in `base.html`.

```js
document.addEventListener('alpine:init', function () {
  Alpine.store('sidebar', {
    open: false,
    toggle() { this.open = !this.open; },
    close() { this.open = false; }
  });
});
```

The hamburger in `base.html` calls `toggle()`; the drawer in
`dashboard.html` reads `$store.sidebar.open`.

**Why**: Lives next to the `<script defer src="...alpinejs...">`
tag. No new file. Mirrors how `$store.importModal` etc. are defined
inline at the bottom of `dashboard.html`.

## Risks / Trade-offs

- **Risk**: The bounded card layout means all rules that depended on
  `main { max-width: 640px; margin: 2rem auto; padding: 0 1.5rem; }`
  need adjustment. Children selectors that targeted `main > h1` etc.
  migrate to `.dashboard-card > h1`.
  **Mitigation**: tasks.md item "Migrate main rules to dashboard-card"
  is an explicit checkpoint before any visual work begins.

- **Risk**: Testid re-parenting breaks existing BDD / e2e tests.
  `tests/bdd/features/import-flow.feature` and Playwright selectors
  look for `dashboard-import-btn` inside `dashboard-actions`. After
  the move, they look for it inside the sidebar.
  **Mitigation**: tasks.md item "Update test selectors" runs in the
  same commit as the move. No orphaned testids.

- **Risk**: The 3-step onboarding is heavier than the previous single
  CTA. First-time users may find it prescriptive.
  **Mitigation**: numbers are visual only — the steps don't lock the
  user into a sequence. They can ignore the rows and click
  `+ Nova classe` first.

- **Risk**: Modal shell abstraction before the 4th modal case means
  the shell contract might be wrong (e.g., missing
  `.modal-footer--split` for left/right alignment).
  **Mitigation**: shell is CSS-only; each modal's body is bespoke. If
  a new footer alignment is needed, add a modifier. No JS lock-in.

- **Risk**: Hamburger button on `/login` and `/profiles` (where no
  sidebar is rendered) creates an empty drawer.
  **Mitigation**: hamburger visibility is gated by
  `{% if profile is defined and profile %}` (only on the dashboard).

- **Risk**: The serif wordmark at 1.75rem competes with the page h1
  (also serif). Two serif elements at the same size on one screen
  is typographic noise.
  **Mitigation**: wordmark is 1.75rem, page h1 is `clamp(1.75rem,
  3vw, 2.5rem)` per DESIGN.md (line 118) — at minimum viewport width,
  the h1 is the same size as the wordmark; at wider viewports the
  h1 grows. The wordmark stays at 1.75rem always. The relationship
  is "constant identity / growing greeting," not "two competing
  displays."

- **Risk**: Source Serif 4 loads from Google Fonts; if the font
  request is slow, the wordmark shows a fallback (system serif)
  first. May look briefly inconsistent.
  **Mitigation**: `font-display: swap` is already set on the Google
  Fonts link (`base.html:16`). Acceptable.

## Migration Plan

This is a UI-only change with no DB or schema impact. The migration
is the deploy:

1. Land the change behind no feature flag (visible UI delta).
2. Existing dev DB is unchanged. `db-reset` not required.
3. Visual smoke test: `task serve` → log in as Italo → confirm
   sidebar renders with three buttons, wordmark "Italo" in serif,
   card-centered layout, modal opens for each button.
4. Mobile smoke test: viewport `<480px` → hamburger visible,
   drawer slides in, ESC closes.
5. Empty-state smoke test: `db-clear-assets` (or fresh DB) → 3-step
   onboarding card visible, no inline `+ Nova classe` button.
6. Test suite: `task test` (unit + integration + BDD). e2e with
   Playwright: `task test-e2e`.
7. README delta lands in the same commit.
8. Spec deltas land in the same commit.
9. Rollback: revert the commit. No DB migration to revert.

No data migration. No users are mid-action (modal state is
session-less; reload discards any open modal).
