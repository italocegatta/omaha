# dashboard-sidebar Specification

## Purpose
DEPRECATED 2026-07-04 (F02). Sidebar removed in favor of top-nav
with 4 tabs (`Patrimônio | Rebalanceamento | Rentabilidade |
Proventos`). No drawer mobile, no off-canvas substitute. See
`openspec/changes/archive/2026-07-04-f02-top-level-tab-nav-and-patrimonio/specs/dashboard-sidebar/spec.md`
for the removal delta. Behaviour coverage continues under:
`patrimonio-portfolio-header`, `dashboard-inline-editing`,
`rebalance-page`, and the top-nav tab components in `base.html`.

## Requirements

### Requirement: Dashboard sidebar no longer renders in runtime UI

The authenticated runtime UI SHALL NOT render the legacy dashboard sidebar container, sidebar slots, or sidebar-only action layout. Navigation and page actions SHALL live in the top-nav and page body introduced by F02.

#### Scenario: Authenticated pages render without sidebar container
- **WHEN** an authenticated user opens `GET /patrimonio` or `GET /rebalanceamento`
- **THEN** no element matching the legacy sidebar container is rendered
- **AND** page navigation is provided by the top-nav tabs in `base.html`
