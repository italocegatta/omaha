## Purpose

Inline asset class and asset management on the dashboard — edit target
percentages, add/remove assets, remove classes, and collapse sections
without leaving the dashboard view. Replaces the standalone editor
pages.
## Requirements
### Requirement: Inline editing de target % da classe

The dashboard MUST allow editing the class target % by clicking the percentage
value, which becomes an inline input. O save faz PATCH /api/classes/{id} e atualiza o
valor local sem recarregar a página. The editor SHALL accept numeric input and
MUST update the displayed value on a 200 response. The editor MUST commit on
either Enter pressed inside the input or blur of the input, and MUST cancel on
Escape pressed inside the input. The editor MUST NOT render a save or cancel
button alongside the input.

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
body (the asset table, the compare bars, the inline progress bars, and
the delete confirm dialog). The toggle state (`isOpen`) MUST be in-memory
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
- **AND** the asset table rows, compare bars, and progress bars inside
  that class become hidden (no longer in the rendered layout)

#### Scenario: Clicking the class header again expands the section
- **WHEN** the user clicks the class section header a second time
- **THEN** the `isOpen` state toggles back to `true`
- **AND** the chevron regains the `class-chevron--open` class
- **AND** the `class-section-body--collapsed` class is removed
- **AND** the asset table rows, compare bars, and progress bars are
  visible again

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
The sort state MUST NOT persist across page reloads.

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
- **THEN** each class's assets remain grouped under their class
  header (data-testid="asset-group-header")
- **AND** only the rows within each group are reordered

#### Scenario: Default sort applies on every load

- **WHEN** the dashboard loads or is reloaded
- **THEN** the sort key is class asc and the secondary key is
  alvo % classe asc
- **AND** no previous user-chosen sort is restored

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

### Requirement: Per-class group header row

The asset table MUST include a `<tr class="asset-group-header">`
(data-testid="asset-group-header") per class, sitting above that
class's asset rows. The group header MUST carry the class color
swatch, class name, class target %, class current %, and the
per-class alert badge (data-testid="asset-group-header-alert") per
the `asset-allocation-alerts` spec.

#### Scenario: Group header renders for every class

- **WHEN** the dashboard loads with N classes that own at least one
  asset each
- **THEN** N group headers are rendered, one per class, in the same
  order as the active profile's classes
- **AND** each group header sits directly above its class's asset
  rows

#### Scenario: Group header hides when class has no assets

- **WHEN** a class has zero assets
- **THEN** no group header is rendered for that class
- **AND** the asset table shows the existing empty-state markup
  for that class

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
- **AND** the per-class badge (asset-group-header-alert) shows
  "Sobra X%"

#### Scenario: Add asset with off-100 sum is accepted

- **WHEN** the user submits a new asset with `target_pct` such that
  the per-class sum exceeds 100%
- **THEN** the POST /api/assets call returns 201
- **AND** the new row is added to the table
- **AND** the per-class badge reflects the new deviation

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
  inputs to the per-class delta badge
  (`data-testid="asset-group-header-alert`) so the operator sees
  "Sobra X%" / "Falta X%" in real time, but the advisory MUST NOT
  block the write;
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
- **AND** the per-class group header alert
  (data-testid="asset-group-header-alert") shows "Sobra X%" with
  the danger color token (the per-class sum now exceeds 100%)

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

### Requirement: Column widths
The asset table MUST declare explicit widths for each of the 8 columns
so text columns ("Ativo", "Classe") get enough room for typical
Brazilian-portuguese asset names and class names, and numeric columns
("Qtd", "Alvo % classe", etc.) stay readable without wasting space.

The widths MUST sum to 100% of the table width and MUST be applied via
CSS (`.asset-table th:nth-child(N) { width: X%; }`) so the layout is
centralised and survives Jinja template regeneration. The widths MUST
be:

| Column | Width |
|---|---|
| Ativo | 24% |
| Classe | 18% |
| Qtd | 6% |
| Valor | 14% |
| Alvo % classe | 11% |
| Atual % classe | 11% |
| Alvo % total | 9% |
| Atual % total | 7% |

The `<th>` elements MUST have `transition: width 200ms` so any width
change (initial paint, future responsive adjustments) animates
smoothly.

#### Scenario: Column widths match the spec
- **WHEN** the dashboard renders the asset table at a standard desktop
  viewport (1280-1920px wide)
- **THEN** the `getBoundingClientRect().width` of each `<th>` matches
  the spec ratio within ±1px tolerance
- **AND** the sum of all 8 column widths equals the table width (no
  overflow, no underflow)

#### Scenario: Text columns are wide enough for typical names
- **WHEN** an asset has a name like "Tesouro Selic 2029" or a class
  has a name like "Renda Fixa Pós-Fixada"
- **THEN** the "Ativo" and "Classe" columns render the full name
  without ellipsis
- **AND** the numeric columns ("Qtd", "Valor", "Alvo % classe", etc.)
  render their values with the existing number/percentage formatting
