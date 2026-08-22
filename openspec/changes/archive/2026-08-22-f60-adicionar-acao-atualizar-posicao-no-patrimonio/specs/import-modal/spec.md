## ADDED Requirements

### Requirement: Existing import review accepts a successful F59 preview handoff

The global `$store.importModal` SHALL expose an internal preview-hydration path
that accepts the existing preview response shape from F59 and opens the current
classification/review step without file upload or navigation. This path SHALL
share row-assignment initialization with manual upload and SHALL NOT call
`POST /api/import/commit`.

#### Scenario: F59 preview opens current review

- **WHEN** the dashboard sync action supplies a successful preview containing
  `preview_id`, `auto_matched`, `unmatched`, and `asset_classes`
- **THEN** `$store.importModal` stores those values and initializes editable
  assignments using the same rules as manual CSV upload
- **AND** the existing `import-modal-overlay` opens on review step 2
- **AND** the browser does not navigate or upload a file

#### Scenario: Handoff preserves explicit manual commit

- **WHEN** an operator reviews a preview delivered by F59
- **THEN** class assignments remain editable before confirmation
- **AND** the portfolio remains unchanged until the operator activates the
  existing confirmation action

### Requirement: Sync-origin review cancellation resets transient action state

When the existing review modal was opened from a successful Patrimônio sync,
its `Cancelar` action and existing close control SHALL clear the sync-origin
marker and reset the sync action's transient success presentation. This reset
SHALL NOT alter source-less manual upload behavior.

#### Scenario: Cancelar clears sync success styling

- **WHEN** a sync-origin preview is open in the existing review modal and the
  operator activates `Cancelar`
- **THEN** the modal closes through its existing close/reset path
- **AND** the sync action returns to idle without green/highlighted styling,
  success state, notification, or `aria-busy`
- **AND** focus returns to `dashboard-sync-btn` when it remains available

#### Scenario: Manual import cancellation remains unchanged

- **WHEN** a manually uploaded preview is open and the operator activates
  `Cancelar`
- **THEN** the existing manual reset behavior occurs
- **AND** no Patrimônio sync state or notification is changed
