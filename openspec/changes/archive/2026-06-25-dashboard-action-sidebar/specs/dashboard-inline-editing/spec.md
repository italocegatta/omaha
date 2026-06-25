## MODIFIED Requirements

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
