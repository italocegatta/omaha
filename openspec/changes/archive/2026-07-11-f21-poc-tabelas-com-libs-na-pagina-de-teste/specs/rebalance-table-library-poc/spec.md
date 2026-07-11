# Decision Record: rebalance-table-library-poc

## Disposition

Owner selected AG Grid Community for future F22 real-table work and explicitly discarded F21 comparison page. F21 adds no production capability.

The F21 runtime PoC has been removed completely: `/rebalanceamento/poc-tabelas`, template, PoC JS/CSS, sole-use vendored table libraries, selectors, and PoC tests do not ship.

## ADDED Requirements

### Requirement: F21 comparison page remains discarded

The system SHALL NOT expose the F21 `/rebalanceamento/poc-tabelas` comparison page. This requirement records F21 disposal only and SHALL NOT be synced into main specs.

#### Scenario: Requesting discarded F21 route
- **WHEN** a requester accesses `/rebalanceamento/poc-tabelas`
- **THEN** the system SHALL return HTTP 404

## F22 handoff

Official AG Grid Community guidance to preserve for F22 planning:

- Set shared `sortable`, `filter`, and `floatingFilter` behavior with `defaultColDef`.
- Use `agNumberColumnFilter` for numeric range filters.
- Use `agSetColumnFilter` for categorical values.
- Use AG Grid theming and Omaha CSS/tokens for custom styling.

## Sync status

This is a discarded discovery record, not a capability delta. Do **not** sync it into main specs.
