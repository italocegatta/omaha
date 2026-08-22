## ADDED Requirements

### Requirement: Patrimônio exposes Atualizar posição beside manual import

The real-profile Patrimônio action strip SHALL render a visible button labeled
`Atualizar posição` immediately left of the existing `Importar CSV` button,
with a stable `data-testid="dashboard-sync-btn"`. The button SHALL use the
existing Material Symbols Outlined system with the exact `sync` ligature before
its label. Clicking it SHALL start the existing F59 job through
`POST /api/myprofit/sync` without changing `window.location` or navigating away
from Patrimônio.

#### Scenario: Real profile sees paired actions

- **WHEN** an authenticated operator views Patrimônio with a real active profile
- **THEN** `Importar CSV` and `Atualizar posição` are visible in the same action
  strip and adjacent in visual order
- **AND** `Atualizar posição` is immediately left of `Importar CSV`
- **AND** `Atualizar posição` has `data-testid="dashboard-sync-btn"`
- **AND** its leading icon is the `sync` Material Symbols Outlined ligature
  with `class="icon icon--md"` and `aria-hidden="true"`

#### Scenario: Starting synchronization stays on page

- **WHEN** the operator activates `Atualizar posição`
- **THEN** the browser sends `POST /api/myprofit/sync`
- **AND** a `202` response `job_id` is retained for polling
- **AND** the browser remains on the current Patrimônio URL
- **AND** no import commit request is sent

### Requirement: Sync action renders explicit lifecycle states

The action SHALL expose observable UI states `idle`, `loading`, `success`,
`error`, and `disabled` through stable state attributes/classes and accessible
status text. `loading` SHALL disable duplicate activation while the client polls
the F59 status endpoint. Polling SHALL stop on `succeeded`, `failed`, or
`expired`; it SHALL not run invisibly without a visible loading/status state.

#### Scenario: Loading state prevents duplicate starts

- **WHEN** F59 start succeeds and the job is queued or running
- **THEN** the action renders its loading state and disables activation
- **AND** the client polls `GET /api/myprofit/sync/{job_id}`
- **AND** a second click does not create another start request

#### Scenario: Successful terminal state is visible

- **WHEN** polling returns `status="succeeded"` with a preview
- **THEN** the action renders its success state before handing the preview to
  the existing review modal
- **AND** polling stops

### Requirement: Sync action matches sibling button language

The real-profile `Atualizar posição` control SHALL share the `Importar CSV`
control's typography, computed control height, padding, border, radius,
alignment, focus-visible ring, and idle/hover/focus/disabled/error state
language. It SHALL NOT retain sync-only geometry such as a distinct minimum
width. Success styling MAY be shown only while its review handoff is active and
SHALL be cleared when that handoff is cancelled.

#### Scenario: Sync control has sibling visual parity

- **WHEN** an operator compares `dashboard-sync-btn` with `dashboard-import-btn`
  in the real-profile action strip
- **THEN** font family, size, weight, line-height, height, padding, border,
  radius, baseline alignment, and focus ring match
- **AND** the sync icon inherits the control's current text color
- **AND** the action remains visually distinct only through its lifecycle
  state, not through a different control geometry

#### Scenario: Cancelling review clears success presentation

- **WHEN** a successful sync opens the existing review modal and the operator
  activates `Cancelar`
- **THEN** the existing review modal closes
- **AND** `Atualizar posição` returns to idle styling without green,
  highlighted, success-state, or `aria-busy` presentation
- **AND** no sync-origin notification remains

#### Scenario: Failed or expired terminal state is visible

- **WHEN** polling returns `status="failed"` or `status="expired"`
- **THEN** the action renders its error state with safe PT-BR feedback
- **AND** polling stops

### Requirement: Successful sync opens existing manual review

Only a successful F59 payload SHALL open the existing `$store.importModal`
classification/review window. The client SHALL reuse the payload fields
`preview_id`, `auto_matched`, `unmatched`, and `asset_classes`, preserve manual
class assignment, and leave the existing explicit commit action as the only
way to mutate portfolio rows.

#### Scenario: Success hands off to current review window

- **WHEN** F59 polling returns `status="succeeded"` and a non-null compatible
  `preview`
- **THEN** the existing import modal opens on its review step
- **AND** auto-matched and unmatched rows render from that preview
- **AND** no page navigation occurs
- **AND** no `POST /api/import/commit` is sent automatically

#### Scenario: Missing success preview is treated as error

- **WHEN** a terminal success response has no usable `preview` payload
- **THEN** the action renders an error state on Patrimônio
- **AND** the existing import modal remains closed
- **AND** no commit request is sent

### Requirement: Família keeps synchronization visible but read-only

When the active view is Família, the `Atualizar posição` action SHALL remain
visible with a disabled/read-only affordance and SHALL not issue a start or poll
request. Existing Família read-only behavior for all other mutation actions and
endpoints SHALL remain unchanged.

#### Scenario: Família cannot start sync from visible action

- **WHEN** the operator views Patrimônio with the Família sentinel active
- **THEN** `Atualizar posição` is visible and disabled with an accessible
  read-only indication
- **AND** activating it produces no network request
- **AND** no import modal opens

### Requirement: Sync lifecycle uses transient notification cards

The sync action SHALL present lifecycle copy in bottom-corner notification cards,
not a page-inline status paragraph. The exact cards SHALL contain
`Pronto para atualizar posição.`, `Atualizando posição...`, and
`Atualização concluída. Revise posições antes de confirmar` for idle, loading,
and successful review handoff respectively. Each card SHALL auto-dismiss after
exactly 8,000 milliseconds when not hovered or focused, expose a manual close
button, and preserve safe allowlisted PT-BR error feedback.

Cards SHALL be placed at logical bottom-end with a 1rem desktop inset and
0.75rem mobile inset, remain below the existing modal layer, and stack with an
8px gap with no more than three cards. F60 SHALL replace prior lifecycle copy
instead of accumulating duplicate cards. Status/loading/success cards SHALL
use `role="status"` and `aria-live="polite"`; safe error cards SHALL use
`role="alert"` and `aria-live="assertive"`; every card SHALL use
`aria-atomic="true"` and a keyboard-accessible close control named
`Fechar notificação`.

#### Scenario: Lifecycle copy is announced as a dismissible notification

- **WHEN** sync enters idle, loading, or successful review handoff
- **THEN** the exact lifecycle copy appears in a bottom-corner card
- **AND** the card has the required live-region role, accessible close button,
  and 8,000 ms auto-dismiss behavior
- **AND** hovering or focusing the card pauses dismissal

#### Scenario: Error remains safe and page-local

- **WHEN** sync start, poll, failed, expired, or malformed-success handling
  produces an error
- **THEN** safe PT-BR error copy appears in an assertive notification card
- **AND** no raw credential, path, exception, CSV, URL, or unsafe F59 detail is
  rendered
- **AND** the browser remains on Patrimônio with the review modal closed
