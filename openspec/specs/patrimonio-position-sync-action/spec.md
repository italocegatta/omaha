# patrimonio-position-sync-action

## Purpose

Dashboard action that starts profile synchronization and hands successful
previews to existing manual import review.

## Requirements

### Requirement: Patrimônio exposes Atualizar posição beside manual import

The real-profile Patrimônio action strip SHALL render a visible button labeled
`Atualizar posição` immediately left of the existing `Importar CSV` button,
with a stable `data-testid="dashboard-sync-btn"`. Clicking it SHALL start the
existing F59 job through `POST /api/myprofit/sync` without navigation.

#### Scenario: Real profile sees paired actions

- **WHEN** an authenticated operator views Patrimônio with a real active profile
- **THEN** both controls are visible and `Atualizar posição` is immediately left
  of `Importar CSV`
- **AND** its leading icon is the `sync` Material Symbols Outlined ligature

### Requirement: Sync action renders explicit lifecycle states

The action SHALL expose observable `idle`, `loading`, `success`, `error`, and
`disabled` states with accessible status text. Loading SHALL prevent duplicate
activation while polling F59; polling SHALL stop at terminal or error states.

#### Scenario: Loading prevents duplicate starts

- **WHEN** synchronization starts and remains queued or running
- **THEN** the action is visibly loading and disabled while status is polled
- **AND** a second activation does not create another start request

### Requirement: Successful sync opens existing manual review

Only a successful F59 payload SHALL open existing `$store.importModal` review.
Assignments remain editable, and explicit commit remains the only portfolio
mutation.

#### Scenario: Success hands off to existing review

- **WHEN** F59 returns a compatible successful preview
- **THEN** the existing import review opens without navigation or automatic
  commit

### Requirement: Família keeps synchronization visible but read-only

When active profile is Família, the action SHALL remain visible and disabled or
read-only, issuing no start, poll, or modal request.

#### Scenario: Família cannot synchronize

- **WHEN** Família is the active profile
- **THEN** the visible action is disabled/read-only and activation issues no
  synchronization or modal request

### Requirement: Sync lifecycle uses transient notification cards

Lifecycle feedback SHALL use dismissible bottom-corner notification cards with
safe PT-BR copy, required live-region semantics, and bounded 8-second dismissal.

#### Scenario: Lifecycle feedback is transient and accessible

- **WHEN** synchronization enters idle, loading, success, or error
- **THEN** one safe notification card presents state with required live-region
  semantics and dismisses after 8 seconds unless hovered or focused
