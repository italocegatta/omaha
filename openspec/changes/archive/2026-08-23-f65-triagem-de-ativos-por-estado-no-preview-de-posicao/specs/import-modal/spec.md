## MODIFIED Requirements

### Requirement: Revisão e commit de import (Step 2)

The modal SHALL render Step 2 as up to three mutually exclusive review
sections labelled `Novos`, `Alterados`, and `Inalterados`, each with a row
count. Rows SHALL retain incoming values as the primary display and preserve
editable class/trade/currency controls and existing assignment keys. Every
triage section SHALL visibly retain the current production columns, in order:
`Nome`, `Qtde`, `Preço médio`, `Total atual`, `Classe`, `Compra`, `Venda`, and
`Moeda`. `Classe` SHALL retain assignment binding, suggestion, color, and
pending-state behavior; `Compra` and `Venda` SHALL remain editable toggles;
`Moeda` SHALL remain an editable allow-listed control. `broker_ticker` SHALL
remain the hidden row-assignment key and SHALL NOT be rendered as visible text
or an `Ativo / ticker` column. A section with no rows SHALL NOT render.
Changed rows SHALL carry the additive field-diff cue; unchanged rows SHALL
carry no diff decoration.

On `Confirmar`, the modal SHALL continue to POST `/api/import/commit` with the
existing assignments and reload only after successful commit. Opening or
reviewing a preview SHALL never commit automatically. F65 SHALL NOT add a
standalone manual-import panel, card, explanatory footer, or duplicate
`Importar manualmente` call-to-action to production. The existing `Importar
CSV` modal entry/upload and existing `Cancelar`/`Confirmar` actions SHALL
remain the sole manual review and commit controls.

#### Scenario: Three-way Step 2 review

- **WHEN** preview contains new, changed, and unchanged rows
- **THEN** Step 2 renders three labelled sections with exact counts and every
  row appears in exactly one section; each section visibly contains all eight
  current columns and controls, without visible ticker text

#### Scenario: Triage preserves production review inventory

- **WHEN** any non-empty triage section renders
- **THEN** `Nome`, `Qtde`, `Preço médio`, `Total atual`, `Classe`, `Compra`,
  `Venda`, and `Moeda` are visible and editable according to their existing
  bindings; class suggestion/color/pending state remains visible; each row
  retains hidden `broker_ticker` assignment identity

#### Scenario: Responsive preservation does not hide controls

- **WHEN** Step 2 is viewed at viewport width 768px or below
- **THEN** responsive overflow may scroll horizontally, but no listed column,
  control, incoming value, or assignment key is removed or replaced

#### Scenario: Empty section is hidden

- **WHEN** preview has no changed rows
- **THEN** `Alterados` section and its heading/count are absent

#### Scenario: Confirmation remains explicit

- **WHEN** operator reviews triaged rows and has not activated `Confirmar`
- **THEN** no commit request or portfolio mutation occurs

#### Scenario: No standalone manual-import UI

- **WHEN** F65 triage review renders Step 2
- **THEN** no separate `Importação manual` panel/card/footer or duplicate
  `Importar manualmente` action is rendered, and existing modal actions remain
  the manual commit boundary

#### Scenario: Existing manual entry remains the source of control

- **WHEN** operator starts a manual import
- **THEN** existing `Importar CSV` entry opens the modal upload step and only
  existing `Confirmar` can invoke commit after review; F65 adds no alternate
  manual-import action

### Requirement: Separação visual entre ativos existentes e novos

The Step 2 state sections SHALL use distinct, token-based visual headers for
`Novos`, `Alterados`, and `Inalterados`, while preserving readable table
surfaces, class-control focus states, and no empty placeholder. The section
grammar SHALL communicate state without hiding changed rows or using a generic
unsorted bucket.

#### Scenario: State headers distinguish sections

- **WHEN** all three triage groups contain rows
- **THEN** each section has a distinct state header and count, and changed
  rows are not merged into `Inalterados`

#### Scenario: Existing class controls remain usable

- **WHEN** operator focuses class/trade controls in any state section
- **THEN** existing select/toggle assignment behavior and visible focus ring
  remain available before commit

### Requirement: Largura do modal 1100px no desktop

The import review panel SHALL use a moderate widened desktop cap of 1200px at
viewport widths above 768px to accommodate three state sections, labels, and
field disclosures. At viewport widths 768px or below, the panel SHALL retain
full-width/full-height responsive behavior with readable horizontal content
handling.

#### Scenario: Widened desktop panel

- **WHEN** operator opens review at viewport width greater than 768px
- **THEN** `.modal-panel--wide` has `max-width: 1200px` and text columns have
  the additional reading room

#### Scenario: Mobile panel remains full width

- **WHEN** operator opens review at viewport width 768px or below
- **THEN** the panel occupies the available viewport width without page-wide
  overflow or clipped disclosure content

## ADDED Requirements

### Requirement: Changed field previous value is accessible on hover and focus

For each field listed in a changed row's `changed_fields`, the modal SHALL show
the incoming value by default and expose the previous value through a
focusable, keyboard-reachable disclosure that also responds to hover. The
disclosure SHALL provide field label, unit, and sign through accessible naming
or description. A native `title` alone SHALL NOT satisfy this requirement.

#### Scenario: Hover reveals previous value

- **WHEN** pointer hovers a changed field cue
- **THEN** a visible disclosure shows the field label and previous value while
  the incoming value remains visible

#### Scenario: Keyboard focus reveals previous value

- **WHEN** keyboard focus enters the changed field cue without pointer input
- **THEN** the same previous-value disclosure becomes visible and is available
  to assistive technology

#### Scenario: Equal field has no disclosure

- **WHEN** a row is classified `Inalterados` or a field is equal
- **THEN** no changed cue or previous-value disclosure is rendered for it

### Requirement: Existing preview and sync handoffs remain compatible

The modal SHALL accept manual and successful F59 preview payloads with existing
compatibility arrays plus additive triage data. If additive triage data is
absent, the modal SHALL retain a safe compatibility rendering path using the
existing arrays; it SHALL not open a commit path, bypass Família, or discard
manual assignments.

#### Scenario: Legacy preview remains reviewable

- **WHEN** valid preview payload lacks `triage`
- **THEN** existing review data remains visible and editable without runtime
  error or automatic commit

#### Scenario: Successful sync still opens review

- **WHEN** F59 returns a valid successful preview with triage
- **THEN** existing import modal opens Step 2 without navigation, connector
  access, or commit request
