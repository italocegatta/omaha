## MODIFIED Requirements

### Requirement: Seções colapsáveis
The dashboard MUST render a chevron in each class section header. Clicking
the class section header MUST toggle the visibility of the class section
body (the asset table and the delete confirm dialog). The toggle state (`isOpen`) MUST be in-memory
only — reloading the page MUST reset every class section to expanded.
The default value of `isOpen` MUST be `true` (expanded) on every load.

The chevron MUST be a single rotating glyph (e.g. `▸` rotated 90° when
open) so the icon is the same width in both states. The body MUST use the
existing `max-height` + `opacity` CSS transition (200ms) so the
collapse/expand is animated, not instant.

#### Scenario: Chevron is rendered in every class header
- **WHEN** the dashboard renders the asset table
- **THEN** every class section header contains a chevron element
  (data-testid="class-chevron")
- **AND** the chevron has class `class-chevron--open` (rotated 90°,
  pointing down) on initial load
- **AND** the corresponding `<div class="class-section-body">` is visible

#### Scenario: Clicking the class header collapses the section
- **WHEN** the user clicks anywhere on a class section header
  (data-testid="class-section-header")
- **THEN** the `isOpen` state of that class section toggles to `false`
- **AND** the chevron loses the `class-chevron--open` class (rotates
  back to pointing right)
- **AND** the `<div class="class-section-body">` gains the
  `class-section-body--collapsed` class
- **AND** the asset table rows and delete confirm dialog inside
  that class become hidden (no longer in the rendered layout)

#### Scenario: Clicking the class header again expands the section
- **WHEN** the user clicks the class section header a second time
- **THEN** the `isOpen` state toggles back to `true`
- **AND** the chevron regains the `class-chevron--open` class
- **AND** the `class-section-body--collapsed` class is removed
- **AND** the asset table rows are visible again

#### Scenario: Default state is expanded on every load
- **WHEN** the dashboard loads or is reloaded
- **THEN** every class section has `isOpen: true` (no persistence
  across reloads)
- **AND** every asset table is visible
- **AND** no `class-section-body--collapsed` class is present on any
  section body

#### Scenario: Collapse state is per-class, not global
- **WHEN** class A is collapsed and class B is expanded
- **THEN** clicking class B's header expands/collapses class B only
- **AND** class A's `isOpen` state is unchanged

### Requirement: Asset table with sortable columns

The dashboard MUST render all assets as rows in a single `<table>`
inside the "Ativos" section. Each row MUST carry the same data as
the previous card layout: name, class, position count, current value,
alvo % classe, atual % classe, alvo % total, atual % total. Each
column MUST be sortable by clicking its `<th>`. The first click
sorts ascending, the second descending, the third re-asserts the
default. The default sort MUST be class asc then alvo % classe asc.
The sort state MUST NOT persist across page reloads. The asset
table MUST NOT include any per-asset horizontal progress bar — the
class section's `Atual` pill in the header is the single source of
truth for class-level deviation; per-row bars would be visual noise.
The asset table MUST NOT include any per-class group header row
inside the table — the class section header above the table is the
single source of truth for class name, Alvo, Atual, and per-class
delta.

#### Scenario: Click on a column header sorts the table

- **WHEN** the user clicks the `<th>` for column "Valor" (data-testid="asset-table-th-current-value")
- **THEN** all asset rows are sorted by current value ascending
- **AND** the sort indicator (data-testid="asset-table-sort-current-value") shows the ascending glyph

#### Scenario: Second click toggles sort direction

- **WHEN** the user clicks the same `<th>` again
- **THEN** the rows are sorted by current value descending
- **AND** the sort indicator shows the descending glyph

#### Scenario: Sort groups stay attached to their class

- **WHEN** the active sort key is anything other than class
- **THEN** each class's assets remain visually grouped under the
  class section that owns them (the class section header above the
  asset table)
- **AND** only the rows within each class's slice of the table are
  reordered
- **AND** no per-class group header row (`data-testid="asset-group-header"`)
  is rendered inside the asset table

#### Scenario: Default sort applies on every load

- **WHEN** the dashboard loads or is reloaded
- **THEN** the sort key is class asc and the secondary key is
  alvo % classe asc
- **AND** no previous user-chosen sort is restored

#### Scenario: No per-asset progress bar in the table

- **WHEN** the dashboard renders the asset table
- **THEN** no element with `data-testid="asset-progress-bar"` is in
  the DOM
- **AND** each asset row consists of exactly one `<tr>` (no
  sibling `<tr>` wrapping a progress bar)

### Requirement: Per-class group is always visible

Each per-class group of asset rows MUST be visible (expanded) on
every dashboard load, regardless of any previous user interaction.
After the user commits any inline edit on a class target or any
asset within a class, that class's group MUST remain visible
(expanded). The chevron toggle that previously collapsed a class
group is removed.

#### Scenario: Group visible on first load

- **WHEN** the dashboard loads
- **THEN** every per-class group is visible
- **AND** no chevron control is rendered to collapse the group

#### Scenario: Group stays visible after inline edit

- **WHEN** the user commits an inline edit on a class target or on
  any asset within a class
- **THEN** that class's group remains visible
- **AND** the asset row that was edited remains in the visible group

### Requirement: Class section header carries no compare bars

The class section MUST NOT render a horizontal target-vs-current
compare bar (no element with `data-testid="class-compare-bar"` in
the DOM). The class target and current percentages are surfaced via
the inline `Alvo` and `Atual` pills in the header
(see "Class card header inline pills"). The compare bar added no
information beyond what the two pills already convey.

#### Scenario: No compare bar in the class section

- **WHEN** the dashboard renders a class section that has at least
  one asset
- **THEN** no element with `data-testid="class-compare-bar"` is in
  the DOM
- **AND** no element with the CSS class `compare-bar` is in the DOM

### Requirement: Inline editing de target % da classe

The dashboard MUST allow editing the class target % by clicking the
`Alvo` pill in the class section header
(`data-testid="class-target-pct-view"`), which becomes an inline
input. O save faz PATCH /api/classes/{id} e atualiza o valor local
sem recarregar a página. The editor SHALL accept numeric input and
MUST update the displayed value on a 200 response. The editor MUST
commit on either Enter pressed inside the input or blur of the input,
and MUST cancel on Escape pressed inside the input. The editor MUST
NOT render a save or cancel button alongside the input.

#### Scenario: Clique no Alvo pill abre input inline

- **WHEN** the user clicks the `Alvo` pill
  (`data-testid="class-target-pct-view"`) in a class section header
- **THEN** the pill is replaced by a numeric input
  (`data-testid="class-inline-edit-input"`) on the same row
- **AND** the input is pre-filled with the current `classTargetPct`

#### Scenario: Enter salva e atualiza localmente

- **WHEN** the user types a new value and presses Enter inside the
  inline input
- **THEN** PATCH /api/classes/{id} is sent
- **AND** on a 200 response, the local `classTargetPct` is updated
- **AND** the input disappears and the `Alvo` pill renders the new
  value

#### Scenario: Blur do input salva e atualiza localmente

- **WHEN** the user types a new value and moves focus out of the
  input (click on another cell, Tab, or click outside the table)
- **THEN** PATCH /api/classes/{id} is sent with the same body as
  Enter
- **AND** on a 200 response, the local `classTargetPct` is updated
- **AND** the input disappears and the `Alvo` pill renders the new
  value

#### Scenario: Escape cancela a edição

- **WHEN** the user types a new value and presses Escape inside the
  input
- **THEN** no PATCH request is sent
- **AND** the input disappears and the previous value remains on
  the `Alvo` pill

#### Scenario: Editor não renderiza botão salvar nem cancelar

- **WHEN** the inline input for the class `Alvo` pill is open
- **THEN** no element with `data-testid="class-inline-edit-commit"`
  or `data-testid="class-inline-edit-cancel"` is in the DOM

### Requirement: Client does not pre-validate inline edits before PATCH

The dashboard MUST send the PATCH for every inline-edit commit
unconditionally. The three commit functions (`commitEditClassPct`,
`commitEdit`, `commitEditTotal` in the `classSection` Alpine
component at `src/omaha/templates/dashboard.html`) MUST NOT gate
the PATCH on:

- a per-row range check (0 ≤ pct ≤ 100) — the server
  (`PATCH /api/classes/{id}` and `PATCH /api/assets/{id}`) is the
  single source of truth for "valor deve ser entre 0 e 100", and
  surfaces a 422 with the user-friendly `detail` on out-of-range;
- the per-class sum (`classDeltaMessage !== ''`) — the local
  `classDelta` / `classDeltaMessage` getters remain as **advisory**
  inputs to the per-class delta pill
  (`data-testid="class-delta-badge"`) in the class section header
  so the operator sees "Sobra X%" / "Falta X%" in real time, but
  the advisory MUST NOT block the write;
- the back-solve math in the "alvo % total" editor
  (`newTargetPct < 0 || newTargetPct > 100`) — the server
  accepts the derived `target_pct` if it is in range; otherwise
  returns 422 and the client renders the server's `detail`.

The "aceitar o commit incondicionalmente" rule applies
identically to Enter and to blur. Escape continues to cancel
without sending any PATCH. The re-entrance guard on
`commitEdit` (`if (this.editingAssetId === null) return;`)
stays — it prevents the @blur handler from re-issuing a
PATCH after a successful Enter already cleared the
`editingAssetId`. The same re-entrance pattern MUST apply
to `commitEditClassPct` and `commitEditTotal`.

#### Scenario: Asset inline edit to off-100 is accepted by the client

- **WHEN** the user clicks the "alvo % classe" cell of an asset
  (data-testid="asset-target-pct-class")
- **AND** types a value that would push the per-class sum above
  100% (e.g. asset A at 40%, asset B at 40%, type 80 into A)
- **AND** presses Enter
- **THEN** PATCH /api/assets/{id} is sent with the new value
- **AND** the server returns 200
- **AND** the asset's `alvo % classe` cell updates to the new value
- **AND** the per-class delta pill (`data-testid="class-delta-badge"`)
  in the class section header shows "Sobra X%" with the danger
  colour token (the per-class sum now exceeds 100%)

#### Scenario: Asset inline edit to off-100 is accepted on blur

- **WHEN** the user types a value that would push the per-class sum
  off 100% in the "alvo % classe" input
- **AND** moves the focus outside the input (clicks another cell,
  the table header, or any non-input element)
- **THEN** PATCH /api/assets/{id} is sent (the @blur handler runs
  without the previous `classDeltaMessage !== ''` block)
- **AND** the server returns 200
- **AND** the value is persisted

#### Scenario: Class inline edit to 100% is accepted

- **WHEN** the user clicks the "Alvo NN%" pill in a class section
  header (data-testid="class-target-pct-view")
- **AND** types 100 in the inline input
- **AND** presses Enter
- **THEN** PATCH /api/classes/{id} is sent
- **AND** the server returns 200
- **AND** the class section header shows "Alvo 100.00%"
- **AND** if the portfolio total now exceeds 100%, the sticky
  allocation alert card surfaces the new portfolio-level
  deviation

#### Scenario: Per-row out-of-range input shows server message

- **WHEN** the user types a per-row out-of-range value (e.g.
  150 or -5) in any inline editor
- **AND** presses Enter or blurs
- **THEN** the client sends the PATCH with the typed value
- **AND** the server returns 422 with `detail` "A alocação
  do ativo deve estar entre 0 e 100." (or the class-level
  variant)
- **AND** the inline error span
  (data-testid="asset-inline-edit-error" or
  data-testid="class-inline-edit-error" or
  data-testid="asset-target-pct-total-edit-error") renders the
  server's `detail` message verbatim
- **AND** the editor stays open so the user can correct

#### Scenario: Re-entrance guard prevents double-PATCH

- **WHEN** the user types a valid value and presses Enter
- **THEN** the success path sets `editingAssetId = null` (or
  `editingClassPct = false`, or `editingTotalAssetId = null`)
  BEFORE the @blur handler fires
- **AND** the @blur handler's `if (this.editingXxx === null) return;`
  guard bails out without sending a second PATCH

### Requirement: classSection exposes every class_data field used by the template

The Alpine classSection factory MUST copy every field of the
class_data blob that the surrounding template references into
a corresponding camelCase property on the returned component
object. The blob is built at Jinja render time
(`src/omaha/templates/dashboard.html:80`) with keys `id`,
`name`, `target_pct`, `color`, `current_pct`, and `assets`.
The factory MUST map at least: `id → classId`,
`name → className`, `target_pct → classTargetPct`,
`color → classColor`, `current_pct → classCurrentPct`. If a
template expression references a derived name (e.g.
`classColor`) that is not initialized in the factory, Alpine
emits an "Expression Error: X is not defined" warning, the
expression renders as empty/NaN, and the visual element
(`.class-color-swatch` background, the `Atual` pill in the
header) shows broken state.

#### Scenario: Header swatch renders the server's class color

- **GIVEN** a class "RF Test" with `color: "#0a66c2"` from the
  server
- **WHEN** the dashboard renders the class section header
- **THEN** the swatch element
  (`data-testid="class-color-swatch"`) has its inline
  `style="background: #0a66c2"` (or equivalent) applied
- **AND** the browser console emits zero `classColor is not
  defined` warnings

#### Scenario: Header "Atual NN%" pill renders the server's current_pct

- **GIVEN** a class "RF Test" with `current_pct: 25.5` from
  the server
- **WHEN** the dashboard renders the class section header
- **THEN** the `Atual` pill
  (`data-testid="class-current-pct"`) shows "Atual 25.50%"
- **AND** the browser console emits zero `classCurrentPct is
  not defined` warnings

## ADDED Requirements

### Requirement: Class card header inline pills

The class section header MUST carry three inline pills between the
class name and the × delete button: an `Alvo` pill, an `Atual`
pill, and a per-class `Sobra/Falta` delta pill. The three pills
are the single source of truth for class-level metrics — no other
element in the class section or asset table duplicates these
numbers.

The `Alvo` pill MUST render the class target percentage as
`Alvo NN%` (the existing `commitEditClassPct` flow turns the pill
into an inline editor on click). The pill MUST have a dashed
border to signal "click to edit" and carry
`data-testid="class-target-pct-view"`.

The `Atual` pill MUST render the class current percentage as
`Atual NN.NN%` (two-decimal format) and carry
`data-testid="class-current-pct"`. The pill MUST use the modifier
class `pct-current-pill--ok` when `|classCurrentPct - classTargetPct| <= 0.01`
(within tolerance) and `pct-current-pill--off` otherwise. The
status colour is the single visual signal that the class is on
target; the user reads the `Sobra/Falta` pill for the magnitude.

The delta pill MUST carry `data-testid="class-delta-badge"` and
render the per-class Sobra/Falta message (`Sobra X%` /
`Falta X%`) when `|classDelta| > 0.01`. The pill MUST NOT render
when `|classDelta| <= 0.01`. The pill MUST always show when off,
regardless of whether the user is mid-edit on an asset (the
previous "only during inline edit" guard is removed).

#### Scenario: Alvo pill renders class target

- **WHEN** the dashboard renders a class section whose
  `classTargetPct` is 25
- **THEN** the `Alvo` pill
  (`data-testid="class-target-pct-view"`) shows "Alvo 25%"
- **AND** the pill has the dashed-border CSS class that signals
  inline editability

#### Scenario: Atual pill shows ok status within tolerance

- **GIVEN** a class with `classTargetPct: 25` and
  `classCurrentPct: 25.5` (delta 0.5%, within tolerance)
- **WHEN** the dashboard renders the class section header
- **THEN** the `Atual` pill
  (`data-testid="class-current-pct"`) shows "Atual 25.50%"
- **AND** the pill carries the modifier class
  `pct-current-pill--ok`

#### Scenario: Atual pill shows off status outside tolerance

- **GIVEN** a class with `classTargetPct: 25` and
  `classCurrentPct: 31` (delta 6%, outside tolerance)
- **WHEN** the dashboard renders the class section header
- **THEN** the `Atual` pill shows "Atual 31.00%"
- **AND** the pill carries the modifier class
  `pct-current-pill--off`

#### Scenario: Delta pill is hidden when on target

- **GIVEN** a class with `classTargetPct: 25` and `classSum: 100`
  (per-asset delta within tolerance)
- **WHEN** the dashboard renders the class section header in
  steady state (no inline edit in flight)
- **THEN** no element with `data-testid="class-delta-badge"` is in
  the DOM

#### Scenario: Delta pill is visible when off, in steady state

- **GIVEN** a class whose per-asset target sum is 110 (delta -10,
  "Sobra 10%")
- **WHEN** the dashboard renders the class section header with no
  inline edit in flight on any asset
- **THEN** the delta pill (`data-testid="class-delta-badge"`) is
  visible
- **AND** the pill text is "Sobra 10%"
- **AND** the pill uses the "Sobra" colour treatment (green /
  accent, matching the existing
  `.class-delta-badge--long` semantic)

#### Scenario: Pills update reactively after inline asset edit

- **WHEN** the user commits an inline edit on an asset that pushes
  the per-class sum off 100%
- **THEN** on the same Alpine tick, the `Atual` pill switches to
  the `pct-current-pill--off` modifier if the new `classCurrentPct`
  falls outside tolerance of the unchanged `classTargetPct`
- **AND** the delta pill (`data-testid="class-delta-badge"`)
  appears with the new "Sobra/Falta" message

#### Scenario: Pills share the header row with the × button

- **WHEN** the dashboard renders a class section header at a
  desktop viewport (>= 480px)
- **THEN** the chevron, colour swatch, class name, three pills,
  and × delete button are all on the same horizontal row
- **AND** the three pills sit between the class name and the ×
  button
- **AND** no element with `data-testid="class-section-stats"` is
  in the DOM (the legacy vertical stats stack is removed)

### Requirement: × delete button is always visible

The class section header's × delete button MUST be visible at all
times in steady state (no hover required), and MUST render with a
visible red border (`color: var(--negative)` plus a 1px border in
the same colour family) so the destructive action is scannable
from a glance. The hover state MUST darken both the border and the
background to confirm the action. The button carries
`data-testid="class-delete-btn"`.

#### Scenario: × button is red in steady state

- **WHEN** the dashboard renders a class section header without
  any user interaction
- **THEN** the × button is visible
- **AND** the button's computed `color` is the value of the
  `--negative` CSS custom property
- **AND** the button has a visible border (computed `border-style`
  is not `none` and `border-color` is not transparent)

#### Scenario: × button hover darkens

- **WHEN** the user hovers the × button
- **THEN** the button's background darkens (compared to the
  steady-state background)
- **AND** the button's border darkens

## REMOVED Requirements

### Requirement: Per-class group header row

**Reason**: The asset table's per-class group header row
(`<tr class="asset-group-header">`,
`data-testid="asset-group-header"`) duplicates the class section
header's class name + Alvo + Atual, and was the only home of the
per-class delta badge before the badge moved to the class card
header. With the move, the group row has no remaining purpose.
**Migration**: Consumers reading the per-class delta must read
`data-testid="class-delta-badge"` (now in the class section
header) instead of the removed
`data-testid="asset-group-header-alert"`. The BDD step files and
e2e selectors that reference `class-target-pct-view` and
`class-current-pct` keep working because the header pills reuse
those test-ids. E2E selectors that asserted
`data-testid="asset-group-header-alert"` are removed; new e2e
scenarios cover the delta pill in the header.

### Requirement: Per-class compare bar overlay

**Reason**: The horizontal target-vs-current compare bar overlay
(no longer in the DOM) was redundant with the `Alvo` and `Atual`
pills in the class section header — the same two numbers, encoded
twice. Removing the bar cuts one full visual layer from the
class section and tightens the layout.
**Migration**: No consumer reads the compare bar after this
change. The e2e selectors that asserted compare-bar target widths
(`tests/e2e/test_user_journey_rebalance.py:221-236`) are removed.
The compare-bar markup, CSS classes
(`.compare-bar`, `.compare-bar-track`, `.compare-bar-fill`,
`.compare-bar-target-fill`, `.compare-bar-current-fill`), and the
`@keyframes fill-bar` animation are removed from
`src/omaha/static/app.css`. The `:nth-of-type(N) .compare-bar-current-fill`
colour-cycling rules (`app.css:79-105`) are removed because they
target an element that no longer exists.

### Requirement: Per-asset horizontal progress bar

**Reason**: Each asset row was wrapped in a sibling `<tr>` carrying
a horizontal progress bar (`data-testid="asset-progress-bar"`).
The bar encoded the asset's `current_pct_class` as a fill width —
the same information already on the table's "Atual % classe" cell.
The bar was decorative visual noise.
**Migration**: The `<tr>` is removed from the template, the
`.asset-progress-bar` and `.asset-progress-fill` CSS classes and
the `@keyframes fill-asset` animation are removed. The `--i` CSS
custom property that drove the stagger delay is removed from the
inline style of each asset row in the template (no other style
consumes `--i`). E2E selectors that asserted
`data-testid="asset-progress-bar"` and its `--final-width` are
removed.