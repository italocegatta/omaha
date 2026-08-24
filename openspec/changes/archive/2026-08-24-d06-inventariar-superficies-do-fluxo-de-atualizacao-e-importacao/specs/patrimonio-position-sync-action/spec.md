## MODIFIED Requirements

### Requirement: Sync action renders explicit lifecycle states

The action SHALL expose observable `idle`, `loading`, `success`, `error`, and
`disabled` states with accessible state semantics. Loading SHALL prevent
duplicate activation while polling F59; polling SHALL stop at terminal or error
states. Idle, loading, and successful handoff SHALL use the existing action or
review surfaces without creating the three D06 lifecycle notification cards.
Error states SHALL retain their existing safe notification surface.

#### Scenario: Loading prevents duplicate starts

- **WHEN** synchronization starts and remains queued or running
- **THEN** the action is visibly loading and disabled while status is polled
- **AND** a second activation does not create another start request

#### Scenario: Successful sync keeps review as success surface

- **WHEN** F59 returns a compatible successful preview
- **THEN** the action reaches `success` and opens the existing import review
- **AND** no `patrimonio-notification` card with
  `Atualização concluída. Revise posições antes de confirmar` is rendered
- **AND** no POST de commit occurs before explicit confirmation

#### Scenario: Errors retain safe feedback

- **WHEN** start, polling, job, or preview handling reaches an error state
- **THEN** the action reaches `error` and renders its existing sanitized error
  notification
- **AND** no raw credentials, paths, exceptions, CSV bytes, or URLs are shown

### Requirement: Família keeps synchronization visible but read-only

When active profile is Família, the synchronization action SHALL NOT be
rendered. The existing profile selector and read-only/mutation guards SHALL
remain available, and selecting Família SHALL issue no synchronization, poll,
or modal request.

#### Scenario: Família does not show synchronization action

- **WHEN** Família is the active profile
- **THEN** `dashboard-sync-btn` is absent from the Patrimônio action strip
- **AND** the literal `Atualizar posição` is absent from that strip
- **AND** activation issues no synchronization, polling, or modal request

### Requirement: Sync lifecycle uses transient notification cards

Lifecycle feedback SHALL use dismissible bottom-corner notification cards with
safe PT-BR copy, required live-region semantics, and bounded 8-second
dismissal for error states. Idle, loading, and successful review handoff SHALL
NOT render notification cards for `Pronto para atualizar posição.`,
`Atualizando posição...`, or `Atualização concluída. Revise posições antes de
confirmar`. Preserved error notifications SHALL continue to pause on hover or
focus and support explicit dismissal.

#### Scenario: Error feedback remains transient and accessible

- **WHEN** synchronization enters an error state
- **THEN** one safe error notification card presents the state with
  `role="alert"`, `aria-live="assertive"`, and `aria-atomic="true"`
- **AND** it dismisses after 8 seconds unless hovered or focused

#### Scenario: Non-error lifecycle cards are absent

- **WHEN** synchronization is idle, loading, or hands a valid preview to review
- **THEN** no notification card is rendered for the three D06 literals
- **AND** loading state, polling, review modal, assignments, and explicit
  confirmation remain available through their existing surfaces
