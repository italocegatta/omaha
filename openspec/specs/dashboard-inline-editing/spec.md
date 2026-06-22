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
MUST update the displayed value on a 200 response.

#### Scenario: Clique no % abre input inline

- **WHEN** usuário clica no target % da classe (data-testid="class-target-pct-view")
- **THEN** o span some e um input numérico (data-testid="class-inline-edit-input") aparece
- **AND** o input contém o valor atual preenchido

#### Scenario: Enter salva e atualiza localmente

- **WHEN** usuário digita novo valor e pressiona Enter
- **THEN** PATCH /api/classes/{id} é enviado
- **AND** em caso de 200, o valor local (classTargetPct) é atualizado
- **AND** o input some e o novo valor aparece no span

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
(data-testid="dashboard-add-asset-open") SHALL open a modal
(data-testid="dashboard-add-asset-modal") carrying the class
selector, asset name, and target_pct inputs. The form MUST POST to
`/api/assets` and the page MUST reload on a 201 response.

#### Scenario: Single dashboard-level add button

- **WHEN** the dashboard renders the "Ativos" section header
- **THEN** a single `+ Ativo` button (data-testid="dashboard-add-asset-open")
  is visible
- **AND** no per-class `+ Ativo` button is rendered

#### Scenario: Modal opens with empty form

- **WHEN** the user clicks the dashboard-level `+ Ativo` button
- **THEN** the modal is visible
- **AND** the class selector, name input, and target_pct input are
  empty (or default to the first available class)
- **AND** submitting the form POSTs to /api/assets
- **AND** on 201, the page reloads and the new asset appears in the
  table

### Requirement: Seções colapsáveis

The dashboard SHALL remove the previous D016 default-closed behavior
and the chevron toggle. The dashboard MUST NOT render a chevron to
collapse a class group. Every per-class group MUST be visible on every
load. The "Default expandido e permanece expandido após edição"
requirement above is the source of truth for this behavior; the
chevron toggle scenario is no longer applicable.

#### Scenario: No chevron rendered

- **WHEN** the dashboard renders the asset table
- **THEN** no chevron control is present in any group header
- **AND** no `data-testid="class-chevron"` element exists in the DOM

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
the new value locally. The save button (data-testid="asset-inline-edit-commit"
or "asset-target-pct-total-edit-commit") MUST be enabled at all
times. The client MUST NOT block the commit when the local
preview's per-class sum differs from 100%. The PATCH /api/assets/{id}
endpoint MUST accept the write unconditionally (within per-row range
0-100) and MUST NOT return 422 for a per-class sum violation. The
resulting deviation, if any, is surfaced through the
`asset-allocation-alerts` spec, not by blocking the write.

#### Scenario: Off-100 edit is accepted

- **WHEN** the user commits a new target_pct that pushes the per-class
  sum to 110%
- **THEN** the save button is enabled
- **AND** the PATCH call returns 200
- **AND** the asset's local target_pct updates to the new value
- **AND** the per-class badge (asset-group-header-alert) shows
  "Sobra X%"

#### Scenario: Add asset with off-100 sum is accepted

- **WHEN** the user submits a new asset with `target_pct` such that
  the per-class sum exceeds 100%
- **THEN** the POST /api/assets call returns 201
- **AND** the new row is added to the table
- **AND** the per-class badge reflects the new deviation
