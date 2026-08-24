## Why

F65 delivers four review states, but modal section order is currently an
implementation detail of the client list and can diverge from owner-facing
sequence. F67 fixes review readability after manual import, `Atualizar
posição`, and any local preview hydration without changing classification or
sync timing.

## What Changes

- Render non-empty review sections in fixed PT-BR order: `Novos`, `Ausentes`,
  `Alterados`, `Inalterados`.
- Apply same order to every `importModal` hydration path: manual upload,
  successful MyProfit handoff, preview re-fetch/local action, and legacy
  compatibility fallback.
- Preserve F65 four-way classification, counts, rows, deterministic
  within-group ordering, editable controls, hidden assignment keys, and
  no-empty-section behavior.
- Preserve `auto_matched`, `unmatched`, `asset_classes`, and additive `triage`
  payload compatibility; no timeout, polling, expiry, error, commit, or D06
  behavior changes.
- Add API/browser mixed-batch acceptance proving payload semantics stay intact
  while rendered section order is fixed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `import-modal`: review Step 2 gains an explicit fixed four-state section
  sequence while preserving existing review and commit behavior.

## Impact

- Inspect `src/omaha/templates/_patrimonio_add_asset_modal.html` store
  `triageSections`, hydration/reset paths, and Step 2 loop.
- Inspect `src/omaha/routes/imports.py` preview builder and GET/POST preview
  boundaries; preserve F65 classification, deterministic row ordering,
  compatibility arrays, legacy payload fallback, and all job/TTL behavior.
- Extend focused API coverage in `tests/test_import_preview.py` and browser
  coverage in `tests/e2e/test_import_modal.py`.
- No database, migration, seed, connector, timeout, D06 archive, or unrelated
  slice changes.
- Owner must approve browser rendering or an equivalent mixed-batch mock before
  Apply; missing approval blocks Apply.
