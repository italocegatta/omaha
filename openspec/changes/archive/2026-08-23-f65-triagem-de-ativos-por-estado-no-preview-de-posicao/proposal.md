## Why

F59/F60 now deliver MyProfit and manual position previews through one review
modal, but the current `auto_matched`/`unmatched` split does not tell operator
which existing rows will change. F65 makes incoming position review legible
before explicit commit without weakening manual assignment or mutation safety.

## What Changes

- Classify every preview row, mutually exclusively, as `Novos`, `Alterados`,
  or `Inalterados` against the active profile's pre-preview `Asset` and
  `Position` state.
- Define equality for position values and asset metadata; never equate
  name-matched rows with unchanged rows, and keep incoming values as the
  primary displayed values.
- Return a compatibility-preserving triage/diff payload alongside existing
  `auto_matched`, `unmatched`, and `asset_classes` keys until replacement
  consumers are proven.
- Sort each non-empty group case/accent-insensitively by asset name, with
  broker ticker as deterministic tie-breaker; hide empty sections.
- Render three state sections with counts. Changed fields retain incoming
  value and expose their previous value through an accessible hover/focus
  disclosure carrying field label, unit, and sign.
- Preserve every current production review column and control in every triage
  section: `Nome`, `Qtde`, `Preço médio`, `Total atual`, `Classe`, `Compra`,
  `Venda`, and `Moeda`. `Classe` remains bound to the assignment, suggestion,
  color, and pending-state behavior; `Compra`/`Venda` remain editable toggles;
  `Moeda` remains editable through its current allow-listed control.
- Keep `broker_ticker` as the hidden row-assignment key. Do not render ticker,
  `Ativo / ticker`, or any replacement identity column. Triage detail adds
  state/count/order and prior-value disclosures without removing current
  values, bindings, controls, or handoffs.
- Moderately widen the existing import review panel for textual readability;
  preserve full-width mobile behavior. Narrow viewports may use horizontal
  table scrolling, but no production column, control, or value is hidden.
- Do not add a standalone manual-import panel, card, explanatory footer, or
  duplicate call-to-action in production. Preserve the existing manual
  `Importar CSV` entry and modal `Cancelar`/`Confirmar` actions as the only
  manual review and commit controls.
- Preserve preview TTL/profile ownership, manual upload and MyProfit handoff,
  expiry/reupload behavior, explicit confirmation, snapshot/audit, Família
  guard, and no-commit preview behavior.

## Capabilities

### New Capabilities

- `import-preview-triage`: Three-way preview classification, deterministic
  ordering, field-level previous-value disclosure, and compatibility payload.

### Modified Capabilities

- `import-modal`: Step 2 renders triage sections and accessible field diffs
  while retaining existing review, assignment, and explicit commit behavior.
- `import-position-totals`: Preview totals remain broker-incoming values for
  display and comparison; no client-side recomputation is introduced.

## Impact

- Runtime preview builder: `src/omaha/routes/imports.py`.
- Review markup and Alpine state: `src/omaha/templates/_patrimonio_add_asset_modal.html`.
- Import modal sizing, section, diff, hover/focus, and responsive styles:
  `src/omaha/static/app.css`.
- Focused API/compatibility tests: `tests/test_import_preview.py`.
- Focused browser rendering and keyboard disclosure tests:
  `tests/e2e/test_import_modal.py`.
- Static owner-review evidence: `visual-prototype.html` visibly repeats all
  eight current columns and controls in all three triage sections, with the
  ticker assignment key hidden.
- No schema, seed, commit route, snapshot/audit route, MyProfit connector, or
  unrelated F63 work.
