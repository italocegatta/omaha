## Purpose

A persistent left action rail on the dashboard that consolidates the
three primary mutating operations (Importar CSV, + Ativo, + Nova classe)
into a single card-index of actions. Anchored by a serif wordmark
carrying the active profile's name. Provides a mobile off-canvas drawer
behind a hamburger button. Also owns the 3-step zero-classes onboarding
card and the modal form for creating a new class.

## ADDED Requirements

### Requirement: Sidebar renders on the dashboard

The dashboard MUST render a persistent left sidebar
(`<aside class="app-sidebar" data-testid="app-sidebar">`) immediately
to the left of the dashboard content. The sidebar MUST contain a serif
wordmark and three action block-buttons, in this order from top to
bottom: `Importar CSV`, `+ Novo ativo`, `+ Nova classe`.

#### Scenario: Sidebar visible on dashboard load

- **WHEN** the dashboard renders for a logged-in user with an active profile
- **THEN** the sidebar element (`data-testid="app-sidebar"`) is present in the DOM
- **AND** the wordmark shows the active profile's name (e.g. `Italo`)
- **AND** three buttons are rendered inside the sidebar with text labels
  `Importar CSV`, `+ Novo ativo`, `+ Nova classe`

#### Scenario: Sidebar is hidden on /login and /profiles

- **WHEN** the user is on `/login` or `/profiles` (no active profile)
- **THEN** the sidebar element is not present in the DOM

### Requirement: Sidebar wordmark uses Source Serif 4

The sidebar MUST render the active profile's name (`{{ profile.name }}`)
inside an element with class `sidebar-wordmark` and
`data-testid="sidebar-wordmark"`, styled with `font-family: 'Source
Serif 4', serif; font-weight: 600; font-size: 1.75rem;
letter-spacing: -0.02em;`.

#### Scenario: Wordmark renders serif and source-name

- **WHEN** the sidebar renders for the active profile
- **THEN** the wordmark element exists with `data-testid="sidebar-wordmark"`
- **AND** the element's computed `font-family` resolves to `Source Serif 4`
  (with system serif fallback)
- **AND** the element's text content equals `{{ profile.name }}`

### Requirement: Sidebar carries the action trigger testids

The three sidebar block-buttons MUST carry the testids that previously
lived on the inline triggers: `data-testid="dashboard-import-btn"` on
the `Importar CSV` button, `data-testid="dashboard-add-asset-open"` on
the `+ Novo ativo` button, and `data-testid="empty-state-create-class"`
on the `+ Nova classe` button (the sidebar entry absorbs the
empty-state testid's role because the empty-state button no longer
exists in its original location).

#### Scenario: Importar CSV sidebar button opens importModal

- **WHEN** the user clicks the `Importar CSV` button inside the sidebar
- **THEN** `$store.importModal.open` becomes `true`
- **AND** the import modal overlay
  (`data-testid="import-modal-overlay"`) becomes visible

#### Scenario: + Novo ativo sidebar button opens addAssetModal

- **WHEN** the user clicks the `+ Novo ativo` button inside the sidebar
- **THEN** `$store.addAssetModal.open` becomes `true`
- **AND** the add-asset modal overlay
  (`data-testid="add-asset-modal-overlay"`) becomes visible

#### Scenario: + Nova classe sidebar button opens newClassModal

- **WHEN** the user clicks the `+ Nova classe` button inside the sidebar
- **THEN** `$store.newClassModal.open` becomes `true`
- **AND** the new-class modal overlay
  (`data-testid="new-class-modal-overlay"`) becomes visible

### Requirement: Active state indicator on sidebar buttons

The sidebar block-button for an open modal MUST display a 3px vertical
bar in `--accent` flush to its left edge, implemented via a
`::before` pseudo-element and gated by `aria-current="true"` on the
button.

#### Scenario: Import button shows active bar when importModal is open

- **WHEN** `$store.importModal.open` is `true`
- **THEN** the `Importar CSV` sidebar button has `aria-current="true"`
- **AND** the button renders a 3px vertical bar in the fern accent
  color flush to its left edge

#### Scenario: Asset button shows active bar when addAssetModal is open

- **WHEN** `$store.addAssetModal.open` is `true`
- **THEN** the `+ Novo ativo` sidebar button has `aria-current="true"`

#### Scenario: Class button shows active bar when newClassModal is open

- **WHEN** `$store.newClassModal.open` is `true`
- **THEN** the `+ Nova classe` sidebar button has `aria-current="true"`

### Requirement: New class modal posts to /api/classes

The new-class modal form MUST POST JSON
`{"name": "...", "target_pct": "..."}` to `/api/classes`. On a 201
response the page MUST reload so the new class section renders with
server-side aggregate data (color, current_pct, assets). On 409
(duplicate name) or 422 (validation error) the modal MUST surface the
server's Portuguese error message in
`data-testid="new-class-modal-error"`.

#### Scenario: 201 reloads the dashboard

- **WHEN** the user submits the new-class modal form
- **AND** the server returns 201 with the new class payload
- **THEN** the page reloads
- **AND** the new class section is visible on the dashboard

#### Scenario: 409 shows duplicate-name error inline

- **WHEN** the user submits a name that already exists in the active
  profile's classes
- **AND** the server returns 409 with `{"detail": "..."}`
- **THEN** the new-class modal stays open
- **AND** `data-testid="new-class-modal-error"` shows the server's
  `detail` message in Portuguese

### Requirement: Mobile off-canvas drawer

On viewports narrower than 480px, the sidebar MUST render as an
off-canvas drawer positioned at the left edge of the viewport with
`transform: translateX(-100%)` by default. A hamburger button in
`.app-header-left` (`.app-header-hamburger`,
`data-testid="app-header-hamburger"`) MUST toggle the drawer via
`$store.sidebar.toggle()`. When `$store.sidebar.open` is `true`, the
drawer MUST slide in (`transform: translateX(0)`), a backdrop covering
the rest of the viewport MUST render with click-to-close behavior,
and focus MUST be trapped inside the drawer. ESC MUST close the drawer
and return focus to the hamburger button.

#### Scenario: Hamburger opens drawer on mobile

- **WHEN** the viewport is narrower than 480px
- **AND** the user taps the hamburger button
- **THEN** `$store.sidebar.open` becomes `true`
- **AND** the sidebar slides in from the left edge
- **AND** a backdrop covers the rest of the viewport

#### Scenario: Backdrop click closes drawer

- **WHEN** the drawer is open
- **AND** the user taps the backdrop
- **THEN** `$store.sidebar.open` becomes `false`
- **AND** the drawer slides out

#### Scenario: ESC closes drawer and returns focus

- **WHEN** the drawer is open
- **AND** the user presses the ESC key
- **THEN** `$store.sidebar.open` becomes `false`
- **AND** keyboard focus returns to the hamburger button

### Requirement: Hamburger visibility is gated by active profile

The hamburger button MUST only render when the user has an active
profile (i.e. is on the dashboard). On `/login` and `/profiles` the
hamburger MUST NOT be in the DOM.

#### Scenario: Hamburger present on dashboard

- **WHEN** the user is on the dashboard with an active profile
- **THEN** the hamburger element
  (`data-testid="app-header-hamburger"`) is in the DOM

#### Scenario: Hamburger absent on /login

- **WHEN** the user is on `/login`
- **THEN** the hamburger element is NOT in the DOM

### Requirement: 3-step zero-classes onboarding card

The dashboard MUST render an `.empty-state-onboarding` card in place
of the existing inline `.empty-state` block when `asset_classes` is
empty. The card MUST show the heading `Vamos comecar` and three rows
in numbered order: `1. Crie uma classe`, `2. Adicione ativos`,
`3. Importe o extrato da corretora`, followed by a hint pointing
the user at the sidebar: `Use os botoes na barra lateral. As classes
devem somar 100%.`. No inline `+ Nova classe` button or inline
`newClassForm` SHALL be rendered in the dashboard — the sidebar
entry is the only way to create a class.

#### Scenario: Onboarding card renders when zero classes

- **WHEN** the dashboard renders with `asset_classes` empty
- **THEN** the element
  (`data-testid="empty-state-onboarding"`) is visible
- **AND** no inline element with
  `data-testid="empty-state-create-class"` is in the DOM
- **AND** no inline `newClassForm` (`data-testid="new-class-container"`'s
  inline trigger button) is in the DOM

#### Scenario: Onboarding card absent when at least one class exists

- **WHEN** the dashboard renders with one or more classes
- **THEN** the `.empty-state-onboarding` element is NOT in the DOM
- **AND** the normal distribution view renders
