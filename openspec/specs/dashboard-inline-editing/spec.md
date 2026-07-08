## Purpose

Inline asset class and asset management on the dashboard — edit target
percentages, add/remove assets, remove classes, and collapse sections
without leaving the dashboard view. Replaces the standalone editor
pages.
## Requirements
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

#### Scenario: Clique no % abre input inline

- **WHEN** usuário clica no target % da classe (data-testid="class-target-pct-view")
- **THEN** o span some e um input numérico (data-testid="class-inline-edit-input") aparece
- **AND** o input contém o valor atual preenchido

#### Scenario: Enter salva e atualiza localmente

- **WHEN** usuário digita novo valor e pressiona Enter
- **THEN** PATCH /api/classes/{id} é enviado
- **AND** em caso de 200, o valor local (classTargetPct) é atualizado
- **AND** o input some e o novo valor aparece no span

#### Scenario: Blur do input salva e atualiza localmente

- **WHEN** usuário digita novo valor e move o foco para fora do input (clique
  em outra célula, Tab, ou clique fora da tabela)
- **THEN** PATCH /api/classes/{id} é enviado com o mesmo corpo do Enter
- **AND** em caso de 200, o valor local (classTargetPct) é atualizado
- **AND** o input some e o novo valor aparece no span

#### Scenario: Escape cancela a edição

- **WHEN** usuário digita novo valor e pressiona Escape
- **THEN** nenhuma requisição PATCH é enviada
- **AND** o input some e o valor anterior permanece no span

#### Scenario: Editor não renderiza botão salvar nem cancelar

- **WHEN** o input inline do target % da classe está aberto
- **THEN** nenhum elemento com data-testid="class-inline-edit-commit" ou
  data-testid="class-inline-edit-cancel" está presente no DOM

### Requirement: Remoção de classe com confirmação

The dashboard MUST display a × button in the class header that, when clicked,
shows a "Remover classe {nome}?" confirmation. Confirmar faz DELETE /api/classes/{id}
e recarrega a página. The confirmation prompt SHALL display the class name and the
delete action MUST reload the page on a 204 response.

#### Scenario: Confirmar exclusão recarrega

- **WHEN** usuário clica × (data-testid="class-delete-btn")
- **THEN** div de confirmação (data-testid="class-delete-confirm") aparece
- **AND** ao clicar "Sim, remover", DELETE /api/classes/{id} é enviado
- **AND** em 204, página recarrega

### Requirement: Remoção de ativo com confirmação

The dashboard MUST display a × button per asset that, when clicked, shows a
"Remover ativo {nome}?" confirmation. Confirmar faz DELETE /api/assets/{id} e
recarrega a página. The confirmation prompt SHALL display the asset name and the
delete action MUST reload the page on a 204 response.

#### Scenario: Confirmar exclusão de ativo recarrega

- **WHEN** usuário clica × no ativo (data-testid="dashboard-asset-delete-btn")
- **THEN** div de confirmação (data-testid="dashboard-asset-delete-confirm") aparece
- **AND** ao clicar "Sim, remover", DELETE /api/assets/{id} é enviado
- **AND** em 204, página recarrega
- **AND** em 409, exibe erro (classe tem posições)

### Requirement: Criação inline de ativo

The previous per-class `+ Ativo` button and inline form MUST be
removed. A single dashboard-level button
(`data-testid="dashboard-add-asset-open"`) MUST render inside the
sidebar (`<aside class="app-sidebar" data-testid="app-sidebar">`)
introduced by the `dashboard-sidebar` capability, NOT in the previous
`dashboard-add-asset-actions` div above the class sections. Clicking
the button SHALL open the add-asset modal
(`data-testid="add-asset-modal-overlay"`) carrying the class selector,
asset name, and target_pct inputs. The form MUST POST to `/api/assets`
and the page MUST reload on a 201 response.

#### Scenario: Sidebar add-asset button opens modal

- **WHEN** the dashboard renders the distribution section
- **THEN** a single `+ Novo ativo` button
  (`data-testid="dashboard-add-asset-open"`) is visible inside
  `data-testid="app-sidebar"`
- **AND** no element with `data-testid="dashboard-add-asset-actions"`
  is in the DOM
- **AND** no per-class `+ Ativo` button is rendered

#### Scenario: Modal opens with empty form

- **WHEN** the user clicks the sidebar `+ Novo ativo` button
- **THEN** the modal is visible
- **AND** the class selector, name input, and target_pct input are
  empty (or default to the first available class)
- **AND** submitting the form POSTs to /api/assets
- **AND** on 201, the page reloads and the new asset appears in the
  table

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

The dashboard MUST render each class section's assets in a single
redesigned `<table>` inside the `Ativos` section. Each row MUST carry
the financial fields needed by the approved mockup: asset name,
quantity, average price, gain value, gain percentage, current
position value, position deviation, class current/target/deviation,
portfolio current/target/deviation, and the unchanged `Compra`,
`Venda`, and `Moeda` controls.

The legacy asset-row `Classe` column is removed. `Ganho` MUST behave as
one operator-facing column even if the implementation uses separate
internal absolute and percentual subcells.

Every visible data column MUST be sortable by clicking its `<th>`:

- text columns (`Ativo`, `Moeda`) sort alphabetically
- numeric/percentage/currency columns sort numerically
- first click sorts ascending, second click descending
- sort state MUST NOT persist across page reloads

Sorting remains local to each class section: rows MUST stay attached to
their owning class section and only reorder within that section.

#### Scenario: Click on asset name sorts alphabetically

- **WHEN** the user clicks the `Ativo` header (`data-testid="asset-table-th-name"`)
- **THEN** asset rows in that class section are sorted alphabetically ascending
- **AND** a second click sorts them descending

#### Scenario: Click on numeric metric sorts numerically

- **WHEN** the user clicks the `Posição` header (`data-testid="asset-table-th-position"`)
- **THEN** asset rows in that class section are sorted by current position value ascending
- **AND** a second click sorts them descending

#### Scenario: Gain remains one visible column while sorting by its numeric components

- **WHEN** the dashboard renders the redesigned table
- **THEN** the operator sees one visible `Ganho` column label
- **AND** the row cells still align absolute and percentual gain values independently
- **AND** sorting by `Ganho` uses the declared numeric key for that column

#### Scenario: Legacy class column is not rendered

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** no asset-row column labeled `Classe` is present
- **AND** each row still remains visually scoped to the class section that owns it

### Requirement: Asset table column proportions live in CSS variables

The redesigned asset table column widths SHALL be defined as CSS custom
properties at `:root`, one variable per rendered column/subcolumn,
including the two internal `Ganho` subcolumns. The table MUST consume
these variables via a `<colgroup>` and MUST use `table-layout: fixed`
and `width: 100%`.

The `.class-section-header` / class totals surface MUST consume the same
variables so grouped labels, totals, and rows re-align automatically
when any `--col-*` value changes.

Long asset names MUST wrap inside their `<td>` via `overflow-wrap:
break-word` rather than overflow horizontally or force the column to grow.

#### Scenario: Column widths are CSS-variable-driven for redesigned table

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the `<table class="asset-table">` contains a `<colgroup>` whose `<col>` widths
  resolve from the corresponding `--col-*` custom properties
- **AND** the table's computed `table-layout` is `fixed`

#### Scenario: Grouped headers and rows share the same column template

- **WHEN** both the grouped header surface and the asset rows are rendered
- **THEN** their computed column widths match the same `--col-*` template
- **AND** mutating any `--col-*` value re-aligns them on the next layout

#### Scenario: Stable header testids exist for redesigned columns

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the sortable headers expose stable `data-testid` values for the new column set,
  including at least `asset-table-th-name`, `asset-table-th-qty`,
  `asset-table-th-avg-price`, `asset-table-th-gain`, `asset-table-th-position`,
  `asset-table-th-position-deviation`, `asset-table-th-class-current`,
  `asset-table-th-class-target`, `asset-table-th-class-deviation`,
  `asset-table-th-portfolio-current`, `asset-table-th-portfolio-target`,
  and `asset-table-th-portfolio-deviation`

### Requirement: Inline edit of alvo % total

The dashboard MUST allow the user to edit the `alvo % total` cell of
an asset row inline. Editing this cell MUST compute
`new_target_pct = target_pct_total * 100 / classTargetPct` and PATCH
the resulting `target_pct` value to `/api/assets/{id}`. The cell MUST
show an inline confirm hint while in edit mode describing the effect
of the edit (recalculation of the asset's `alvo % classe` within the
class, other assets in the class unaffected). Only one cell per row
may be in edit mode at a time.

#### Scenario: Edit alvo % total commits a derived alvo % classe

- **WHEN** the user commits a new `alvo % total` value of 20 for
  an asset whose class has `classTargetPct = 30`
- **THEN** the client computes `new_target_pct = 20 * 100 / 30 = 66.67`
- **AND** PATCH /api/assets/{id} is sent with `{"target_pct": "66.67"}`
- **AND** on 200, the asset's `alvo % classe` cell updates to 66.67
- **AND** the asset's `alvo % total` cell updates to 20.00

#### Scenario: Confirm hint visible while editing alvo % total

- **WHEN** the user clicks the `alvo % total` cell to edit
- **THEN** the cell enters edit mode
- **AND** a confirm hint is visible next to the input (e.g.
  "recalcula apenas a posição deste ativo dentro da classe")
- **AND** the `alvo % classe` cell on the same row is in read-only
  view mode (not editable) while the edit is in flight

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

### Requirement: Edit acceptance is unconditional

The dashboard's inline editor MUST accept every commit and reflect
the new value locally. The inline input MUST commit on Enter or blur
without requiring any save button. The client MUST NOT block the commit when the local
preview's per-class sum differs from 100%. The PATCH /api/assets/{id}
endpoint MUST accept the write unconditionally (within per-row range
0-100) and MUST NOT return 422 for a per-class sum violation. The
resulting deviation, if any, is surfaced through the
`asset-allocation-alerts` spec, not by blocking the write.

#### Scenario: Off-100 edit is accepted

- **WHEN** the user commits a new target_pct that pushes the per-class
  sum to 110% by pressing Enter (or by blurring the input)
- **THEN** the PATCH call returns 200
- **AND** the asset's local target_pct updates to the new value
- **AND** the per-class delta pill (`data-testid="class-delta-badge"`)
  in the class section header shows "Sobra X%"

#### Scenario: Add asset with off-100 sum is accepted

- **WHEN** the user submits a new asset with `target_pct` such that
  the per-class sum exceeds 100%
- **THEN** the POST /api/assets call returns 201
- **AND** the new row is added to the table
- **AND** the per-class delta pill reflects the new deviation

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

- **WHEN** the user types a value that would push the per-class
  sum off 100% in the "alvo % classe" input
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

### Requirement: Editor inline do alvo % do ativo segue o mesmo padrão Enter-or-blur

The dashboard's per-asset inline editors (`alvo % classe` and `alvo % total` cells) MUST follow the same commit pattern as the class header editor: Enter OR blur of the input commits, Escape cancels, and no save / cancel button is rendered. The live confirm hint on the `alvo % total` editor and the inline error span on either editor MUST continue to render in edit mode.

#### Scenario: Enter no alvo % classe salva

- **WHEN** usuário clica na célula "Alvo % classe" do ativo (data-testid="asset-target-pct-class")
- **AND** digita novo valor e pressiona Enter
- **THEN** PATCH /api/assets/{id} é enviado com o novo target_pct
- **AND** o input some e o novo valor aparece no span

#### Scenario: Blur do alvo % classe salva

- **WHEN** usuário digita novo valor no input de "Alvo % classe" e move
  o foco para fora do input
- **THEN** PATCH /api/assets/{id} é enviado com o novo target_pct

#### Scenario: Enter no alvo % total salva e recalcula

- **WHEN** usuário digita novo valor no input de "Alvo % total" e
  pressiona Enter
- **THEN** o cliente calcula `new_target_pct = target_pct_total * 100 / classTargetPct`
- **AND** PATCH /api/assets/{id} é enviado com o target_pct derivado
- **AND** em 200, ambas as células (alvo % classe e alvo % total) refletem os novos valores

#### Scenario: Nenhum botão salvar/cancelar nos inputs de ativo

- **WHEN** qualquer input inline do ativo (alvo % classe ou alvo % total)
  está aberto
- **THEN** nenhum elemento com data-testid="asset-inline-edit-commit",
  data-testid="asset-inline-edit-cancel",
  data-testid="asset-target-pct-total-edit-commit", ou
  data-testid="asset-target-pct-total-edit-cancel" está presente no DOM

### Requirement: Class card header inline pills

The class section header MUST carry three inline pills
(`Alvo`, `Atual`, and per-class `Sobra/Falta` delta) and one
plain-text consolidated `Valor` stat. The four items MUST be
laid out across the columns of an 8-column CSS grid that
mirrors the asset table column structure (see
`class-section-totals` capability for the alignment
contract). The `×` delete button MUST be placed immediately
after the class name in the leading grid slot, NOT at the
trailing edge of the header row.

The `Alvo` pill MUST render the class target percentage as
`Alvo NN%` (the existing `commitEditClassPct` flow turns the
pill into an inline editor on click). The pill MUST have a
dashed border to signal "click to edit" and carry
`data-testid="class-target-pct-view"`.

The `Atual` pill MUST render the class current percentage as
`Atual NN.NN%` (two-decimal format) and carry
`data-testid="class-current-pct"`. The pill MUST use the
modifier class `pct-current-pill--ok` when
`|classCurrentPct - classTargetPct| <= 0.01` (within
tolerance) and `pct-current-pill--off` otherwise.

The delta pill MUST carry `data-testid="class-delta-badge"`
and render the per-class Sobra/Falta message
(`Sobra X%` / `Falta X%`) when `|classDelta| > 0.01`. The
pill MUST NOT render when `|classDelta| <= 0.01`.

The consolidated `Valor` stat MUST render the class's
`current_value` (sum of `current_value` across the class's
assets) as plain text (NOT a pill) in BRL with no decimal
fraction digits, and MUST carry
`data-testid="class-total-value"`. Empty state (class with
no assets, `current_value == 0`): the element renders `—`
instead of `R$ 0`.

#### Scenario: Header has consolidated Valor + three pills + × in the leading slot

- **WHEN** the dashboard renders a class section header at a
  desktop viewport (>= 480px)
- **THEN** the header (data-testid="class-section-header")
  contains, in DOM order: chevron, colour swatch, class name,
  × button (data-testid="class-delete-btn"), consolidated
  Valor (data-testid="class-total-value"), `Sobra/Falta` pill
  (data-testid="class-delta-badge", when rendered), `Alvo`
  pill (data-testid="class-target-pct-view"), and `Atual`
  pill (data-testid="class-current-pct")
- **AND** the × delete button is a sibling of the class name
  inside the leading flex group, NOT a trailing child of the
  header row

#### Scenario: × button stays visible after move (discreet gray, red on hover)

- **WHEN** the dashboard renders a class section header
- **THEN** the × button (data-testid="class-delete-btn") is
  visible (the existing visibility contract from
  `dashboard-inline-editing` is unchanged)
- **AND** the × button's computed `color` in steady state is
  the value of the `--muted` CSS custom property (a low-luminance
  gray — the destructive action is intentionally discreet and
  mirrors the per-asset × button styling)
- **AND** the × button's computed `color` flips to the value of
  the `--negative` CSS custom property on `:hover` (red, with a
  light-red `var(--error-bg)` background) so the operator sees
  what the click does before committing
- **AND** the click handler still opens the
  `.class-delete-confirm` dialog and DELETEs
  `/api/classes/{id}` on confirm (no behaviour change)

#### Scenario: Clicking × from the new position still opens the confirm dialog

- **WHEN** the user clicks the × button (now positioned right
  after the class name)
- **THEN** the confirm dialog
  (data-testid="class-delete-confirm") appears
- **AND** the rest of the contract from
  `dashboard-inline-editing` "Remoção de classe com
  confirmação" is unchanged

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

### Requirement: × delete button is always visible (discreet by default, red on hover)

The class section header's × delete button MUST be visible at all
times in steady state (no hover required). In steady state the
button MUST render discreetly with `color: var(--muted)` and a
transparent border / background (no shouty red default — the
destructive action is intentionally muted and mirrors the per-asset
× button styling). On `:hover` the button MUST flip to a destructive
red treatment — `color: var(--negative)` and a `var(--error-bg)`
background — so the operator sees what the click does before
committing. The button carries `data-testid="class-delete-btn"`.

#### Scenario: × button is discreet gray in steady state

- **WHEN** the dashboard renders a class section header without
  any user interaction
- **THEN** the × button is visible
- **AND** the button's computed `color` is the value of the
  `--muted` CSS custom property (a low-luminance gray)
- **AND** the button has a transparent border (computed
  `border-color` is transparent and `background-color` is
  transparent in steady state)

#### Scenario: × button hover turns red

- **WHEN** the user hovers the × button
- **THEN** the button's computed `color` becomes the value of
  the `--negative` CSS custom property
- **AND** the button's background becomes a light-red fill
  (`var(--error-bg)`)
- **AND** the button's border becomes a red-tinted 1px line

### Requirement: Layout do dashboard usa largura máxima de 1400px

The dashboard's `<main>` element MUST render with `max-width: 1400px`
so content occupies roughly 70% of a 1920px-class monitor with the
existing 2rem auto margin. The asset table and class sections MUST
stretch to fill the wider container. The pre-existing
`@media (max-width: 480px)` collapse rules MUST continue to apply on
small screens unchanged.

#### Scenario: Dashboard em monitor 1920px ocupa ~73% da largura

- **WHEN** o dashboard renderiza em viewport de 1920px
- **THEN** o `<main>` centraliza com `max-width: 1400px`
- **AND** a tabela de ativos ocupa toda a largura disponível do container

### Requirement: Inline edit preserves the edited row's visual position

The asset-table view MUST keep the just-edited row in the same
ordinal position it occupied before the edit, even when the new
`target_pct` would naturally re-sort the row elsewhere under the
current sort. The freeze is released on the next user-driven
`sortBy` click (clicking a column header) or on a new edit on a
different asset. The freeze is **not** released on successful
PATCH — releasing on PATCH would cause the row to jump the
instant the response lands, which is the user-perceived bug the
freeze exists to prevent.

#### Scenario: Editing the top row keeps it on top

- **GIVEN** a class "RF Test" with 3 assets in this order under
  the default sort (`target_pct` asc): "Alpha" 10%, "Bravo" 20%,
  "Charlie" 30%
- **WHEN** the user clicks the "alvo % classe" cell of the row
  holding "Alpha" (the top row), types 80, presses Enter
- **THEN** the row holding "Alpha" is still the top row in the
  class table
- **AND** the cell now shows "80.00%"

#### Scenario: Freezing is released on the next sort click

- **GIVEN** the previous scenario's state (Alpha 80% pinned to
  the top)
- **WHEN** the user clicks the "Alvo % classe" column header
  to re-sort
- **THEN** the row holding "Alpha" is no longer pinned — it sits
  in the natural position for `target_pct=80` (i.e. among the
  other high-target assets, not necessarily at the top)

### Requirement: classSection exposes every class_data field used by the template

The Alpine classSection factory SHALL copy every field of the
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
(`.class-color-swatch` background, `.pct-current` "Atual NN%"
pill) shows broken state.

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
- **THEN** the pill (`data-testid="class-current-pct"`) shows
  "Atual 25.50%"
- **AND** the browser console emits zero `classCurrentPct is
  not defined` warnings

### Requirement: Asset table column proportions live in CSS variables

The redesigned asset table column widths SHALL be defined as CSS custom
properties at `:root`, one variable per rendered column/subcolumn,
including the two internal `Ganho` subcolumns. The table MUST consume
these variables via a `<colgroup>` and MUST use `table-layout: fixed`
and `width: 100%`.

The `.class-section-header` / class totals surface MUST consume the same
variables so grouped labels, totals, and rows re-align automatically
when any `--col-*` value changes.

Long asset names MUST wrap inside their `<td>` via `overflow-wrap:
break-word` rather than overflow horizontally or force the column to grow.

#### Scenario: Column widths are CSS-variable-driven for redesigned table

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the `<table class="asset-table">` contains a `<colgroup>` whose `<col>` widths
  resolve from the corresponding `--col-*` custom properties
- **AND** the table's computed `table-layout` is `fixed`

#### Scenario: Grouped headers and rows share the same column template

- **WHEN** both the grouped header surface and the asset rows are rendered
- **THEN** their computed column widths match the same `--col-*` template
- **AND** mutating any `--col-*` value re-aligns them on the next layout

#### Scenario: Stable header testids exist for redesigned columns

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the sortable headers expose stable `data-testid` values for the new column set,
  including at least `asset-table-th-name`, `asset-table-th-qty`,
  `asset-table-th-avg-price`, `asset-table-th-gain`, `asset-table-th-position`,
  `asset-table-th-position-deviation`, `asset-table-th-class-current`,
  `asset-table-th-class-target`, `asset-table-th-class-deviation`,
  `asset-table-th-portfolio-current`, `asset-table-th-portfolio-target`,
  and `asset-table-th-portfolio-deviation`

### Requirement: Inline edit auto-focuses the input on the same click

The system SHALL auto-focus the dashboard's three inline editors (class header `Alvo`, per-asset
`alvo % classe`, per-asset `alvo % total`) so their
`<input>` and pre-select its content as part of the same click that
opens the editor. The user MUST NOT need a second click or touch
interaction to focus the input before typing. The auto-focus MUST be
scoped to the active instance of the editor — concurrent class sections
or asset rows on the page MUST NOT have their focus stolen.

#### Scenario: Single click on the class target pill focuses the input

- **WHEN** the user clicks the `Alvo NN%` pill
  (`data-testid="class-target-pct-view"`) in any class section header
- **THEN** the inline input (`data-testid="class-inline-edit-input"`)
  becomes visible
- **AND** that same input receives focus on the same click
- **AND** the input's current value is pre-selected
- **AND** the user's first keystroke replaces the pre-selected value
- **AND** no input in a different class section receives focus

#### Scenario: Single click on the per-asset alvo % classe cell focuses the input

- **WHEN** the user clicks the `alvo % classe` cell button
  (`data-testid="asset-target-pct-class"`) on any asset row
- **THEN** the inline input
  (`data-testid="asset-inline-edit-input"`) becomes visible and
  focused on the same click
- **AND** the input's current value is pre-selected
- **AND** concurrent editors on other rows stay closed

#### Scenario: Single click on the per-asset alvo % total cell focuses the input

- **WHEN** the user clicks the `alvo % total` cell button
  (`data-testid="asset-target-pct-total"`) on any asset row
- **THEN** the inline input
  (`data-testid="asset-target-pct-total-edit-input"`) becomes visible
  and focused on the same click
- **AND** the input's current value is pre-selected

### Requirement: Empty inline edit commits as zero

The system SHALL commit the value `0` when the inline editor for any of the three target-% fields is
visible and the user clears the value (string is empty or
whitespace-only) and then presses Enter, blurs the input, or moves
focus outside the editor. The dashboard MUST commit the value `0` to
the server. The dashboard MUST treat this client-side coercion as a
silent normal write — no 422 round trip, no inline error span, no
visible "saved 0" toast. Existing in-range validation (0 ≤ pct ≤ 100)
remains authoritative on the server; the empty-equality-zero rule is
a client-side coercion, not a server-side exception. After a
successful `0` commit, the field's display value returns as `0%` (or
`0.00%` per existing rounding rules) and the dashboard's per-class
delta / portfolio sticky alert surfaces the resulting deviation.

#### Scenario: Clearing the class target and pressing Enter saves zero

- **GIVEN** a class with `classTargetPct: 25`
- **WHEN** the user clicks the `Alvo` pill (editor opens and focuses)
- **AND** clears the input (string becomes empty)
- **AND** presses Enter
- **THEN** PATCH /api/classes/{id} is sent with `{"target_pct": "0"}`
- **AND** on 200, the header pill shows "Alvo 0%"
- **AND** no inline error span is rendered
- **AND** no 422 response is received

#### Scenario: Clearing the per-asset alvo % classe and pressing Enter saves zero

- **GIVEN** an asset with `target_pct: 12.5`
- **WHEN** the user clicks the cell, clears the input, presses Enter
- **THEN** PATCH /api/assets/{id} is sent with `{"target_pct": "0"}`
- **AND** on 200, the row's `alvo % classe` cell shows 0.00%
- **AND** no inline error span is rendered

#### Scenario: Clearing the per-asset alvo % total and pressing Enter saves zero

- **GIVEN** an asset with `target_pct_total: 7.5` and class with
  `classTargetPct: 25`
- **WHEN** the user clicks the cell, clears the input, presses Enter
- **THEN** the client computes `new_target_pct = 0 * 100 / 25 = 0`
- **AND** PATCH /api/assets/{id} is sent with `{"target_pct": "0"}`
- **AND** on 200, both `alvo % classe` and `alvo % total` cells show
  0.00%

#### Scenario: Blurring an empty class input saves zero

- **WHEN** the user opens the class `Alvo` editor and clears the
  input then clicks outside the input (no Enter pressed)
- **THEN** the @blur handler commits `{"target_pct": "0"}` to the
  server
- **AND** the editor closes on 200

### Requirement: Inline edit inputs render without the native number spinner

The system SHALL render the dashboard's three inline editor inputs (class header input and
both per-asset inputs) without the browser's native
`<input type="number">` spinner (`▲` / `▼` glyphs on the right edge).
The input visual MUST be a flat field consistent with the
surrounding pill — same border treatment, same height, no
stepper chrome. Keyboard `↑` / `↓` MUST continue to step the value
per the existing `step="0.01"` attribute. This rule applies only to
the dashboard's three inline editors; modal forms (asset create,
class create, import) MAY keep the native spinner because they are
modal forms, not inline pill editors.

#### Scenario: Class edit input has no spinner glyph

- **WHEN** the class `Alvo` editor is open
- **THEN** no `▲` / `▼` stepper element is rendered on the right side
  of `data-testid="class-inline-edit-input"`
- **AND** the input border on the right matches the border on the
  left (same color, same radius)

#### Scenario: Per-asset edit inputs have no spinner glyph

- **WHEN** either per-asset editor (`alvo % classe` or
  `alvo % total`) is open
- **THEN** no `▲` / `▼` stepper is rendered on either
  `data-testid="asset-inline-edit-input"` or
  `data-testid="asset-target-pct-total-edit-input"`
