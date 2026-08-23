## Context

F59/F60 converge manual CSV upload and MyProfit position refresh on
`_build_preview_response`. Current response preserves two compatibility arrays:
`auto_matched` (name-normalized Asset match) and `unmatched` (no Asset match),
in broker input order. The review modal renders those arrays as two sections,
shows incoming row values, initializes editable class/trade assignments, and
calls the existing explicit commit only after operator confirmation.

F65 adds a review-only triage layer. It must classify against the database
state that existed when preview was created, not against a later request or
against name matching alone. No database schema or commit route change is
needed: `ImportPreview.raw_json` can carry a private serialized baseline beside
the existing `RawPosition` fields, while legacy previews without a baseline
fall back to current response-time state for compatibility.

The additive UI contract is fixed by the current modal inventory. Every Step 2
triage section continues to show and edit `Nome`, `Qtde`, `Preço médio`, `Total
atual`, `Classe`, `Compra`, `Venda`, and `Moeda`. `Classe` keeps its assignment
binding, suggestion, class-color swatch, and pending state; `Compra` and `Venda`
keep their checkbox setters; `Moeda` keeps its BRL/USD select. `broker_ticker`
remains the hidden assignment key and row identity; no ticker text or `Ativo /
ticker` heading is rendered. Triage state, counts, order, and prior-value
disclosure add information around this surface; they do not replace it.

The visual review decision removes the prototype's standalone manual-import
block. F65 production UI SHALL retain the existing `Importar CSV` entry,
Step-1 manual upload, and Step-2 `Cancelar`/`Confirmar` modal actions only. F65
must not add a manual-import panel/card, duplicate call-to-action, or
explanatory footer. Existing explicit confirmation, snapshot/audit, and
Família read-only protections remain non-negotiable.

## Code map

- `src/omaha/routes/imports.py`
  - `_raw_to_dict` / `_dict_to_raw`: current lossless `RawPosition` preview
    serialization. Extra baseline data must round-trip without changing the
    parser model.
  - `preview_from_blob`: manual and F59 byte-to-preview persistence boundary;
    capture Asset/Position baseline here before returning a usable preview.
  - `_existing_assets_for_profile`: profile-scoped Asset query used by the
    existing matcher; preserve active-profile and Família boundaries.
  - `_build_preview_response`: canonical serializer for manual and F59
    previews. Keep `auto_matched`, `unmatched`, and `asset_classes` compatible;
    add triage rows and field-level diff payload here.
  - `preview_import`, `get_preview`, `MyProfitSyncService.status_for_profile`,
    and `commit_import`: existing preview/commit edges. They must continue to
    call the canonical builder, preserve TTL/ownership, and never commit while
    building triage.
- `src/omaha/templates/_patrimonio_add_asset_modal.html`
  - `import-modal-overlay` Step 1 file upload and Step 2 review markup: current
    two sections expose the eight-column production inventory (`Nome`, `Qtde`,
    `Preço médio`, `Total atual`, `Classe`, `Compra`, `Venda`, `Moeda`). The
    assignment key is `row.broker_ticker` but is not a visible column. The
    existing sections and assignment controls are the visible review surface to
    preserve while adding three state sections; existing
    `import-modal-actions` `Cancelar`/`Confirmar` remains the manual commit
    boundary and must not gain a second manual-import panel or CTA.
  - `Alpine.store('importModal')`: `autoMatched`, `unmatched`, `buildAssignments`,
    `hydratePreview`, `openPreview`, `openModal`, `commit`, and formatting
    helpers. Preserve assignment initialization, dynamic-select
    `$nextTick`/`x-effect`, manual upload, sync handoff, close/reset,
    expiry/reupload, and explicit commit.
- `src/omaha/templates/_patrimonio_actions.html::dashboard-import-btn`
  - existing `Importar CSV` trigger that opens `$store.importModal.openModal()`;
    preserve as the sole manual-import entry point and do not duplicate it in
    the F65 Step-2 review surface.
- `openspec/changes/f65-triagem-de-ativos-por-estado-no-preview-de-posicao/visual-prototype.html`
  - static owner-review evidence. `.manual-note` and its explanatory copy /
    `Importar manualmente` CTA are removed; each triage table visibly repeats
    the eight current columns and controls, keeps only the hidden
    `broker_ticker` assignment input, and `.actions` keeps only the existing
    `Cancelar` and `Confirmar importação` hierarchy.
- `src/omaha/static/app.css`
  - `.modal-panel--wide`: current 1100px desktop cap and mobile shell rules.
  - `.import-review-section*`, `.import-review-table*`, and class-cell rules:
    existing section grammar, table readability, class controls, focus rings,
    and dark-surface tokens to extend for triage/diff cues.
- `tests/test_import_preview.py`
  - `TestPostImportPreview` response-shape, matching, totals, empty/profile,
    and persistence scenarios. Add deterministic baseline/classification,
    equality, ordering, compatibility, and no-mutation assertions.
- `tests/e2e/test_import_modal.py`
  - `TestS04ImportModal.test_import_modal_happy_path` and modal visual/error
    scenarios. Extend browser coverage for three sections, counts, incoming
    values, hidden empty groups, sorted names/ticker ties, and keyboard/focus
    previous-value disclosure while retaining commit journey assertions.

The ORM fields supplying comparison state are `Asset.name`,
`Asset.buy_enabled`, `Asset.sell_enabled`, `Asset.currency_code`, and the
matching `Position` fields `qty`, `avg_price`, `current_price`,
`total_invested`, and `total_current`. No model file edit is authorized.

## Current relevant flow

1. Manual upload or F59 downloaded bytes enter `preview_from_blob`.
2. UTF-8/size/parser validation produces `RawPosition[]`; the existing code
   stores those rows in profile-scoped `ImportPreview.raw_json` and does not
   mutate Asset/Position rows.
3. `_build_preview_response` rehydrates raw rows, matches normalized names to
   current-profile Assets, and emits `auto_matched`, `unmatched`, and class
   options. F59 status serialization and manual `POST /api/import/preview`
   both consume this builder.
4. Alpine `hydratePreview` stores response arrays, builds assignments, and
   opens Step 2. Existing rows use current class/trade/currency controls;
   unmatched rows use suggested class/default controls. Each row retains the
   eight visible production columns and uses `broker_ticker` only as hidden
   assignment identity. The existing `Importar CSV` trigger and Step-1 file
   input remain manual-entry controls; Step-2 `Cancelar` closes review and
   `Confirmar` calls `commit()`, the only mutation path, guarded by explicit
   confirmation, snapshot, and audit. No separate manual-import panel
   participates in this flow.

Boundary conditions: missing/expired/foreign previews remain unusable; the
Família sentinel remains read-only; malformed CSV still fails before preview;
broker-published totals remain authoritative; preview generation never calls
commit or snapshot/audit; manual reupload remains available after expiry; active
profile ownership remains enforced; mobile modal remains full width.

## Goals / Non-Goals

**Goals:**

- Capture a pre-preview comparison baseline without schema migration.
- Classify every incoming row exactly once as new, changed, or unchanged.
- Compare position values and preview-represented Asset metadata with explicit
  null/Decimal/text/boolean rules.
- Emit deterministic group ordering and field-level changed-value payloads.
- Render PT-BR state sections with counts, incoming values, and accessible
  hover/focus disclosure of prior values.
- Preserve the complete current eight-column editable review inventory in every
  state section; hide ticker text while retaining hidden `broker_ticker`
  assignment keys. On narrow viewports, horizontal scrolling is allowed only
  as an explicit readability treatment; columns and controls remain present.
- Keep manual import controls limited to the existing modal entry/upload and
  `Cancelar`/`Confirmar` actions; exclude any new manual-import panel, card,
  explanatory footer, or duplicate CTA from production.
- Preserve all existing preview, sync handoff, assignment, confirmation,
  snapshot/audit, profile, Família, and compatibility behavior.

**Non-Goals:**

- No Asset/Position mutation, automatic commit, migration, seed change, or
  snapshot/audit creation during preview.
- No change to the matcher, `auto_matched`/`unmatched` meaning, preview TTL,
  endpoint names, F59 job lifecycle, or MyProfit connector.
- No inferred class assignment, target percentage comparison, class movement,
  ticker rewrite, or client-side recomputation of broker totals.
- No standalone manual-import panel/card/footer, duplicate manual-import CTA,
  or replacement for the existing modal actions.
- No F63 edits, shared table refactor, new UI dependency, tooltip-only
  disclosure, or page-wide layout change.

## Decisions

### 1. Persist baseline at preview creation, preserve legacy fallback

At `preview_from_blob`, match parsed rows against the active profile's Assets
and serialize, per row, matched Asset identity/metadata plus matching
`Position` state into preview JSON. `_build_preview_response` uses that baseline
for F65 triage. Existing previews created before F65 lack the baseline; for
those previews, use current response-time state only to produce triage while
leaving existing compatibility arrays unchanged.

Alternative rejected: querying only when the modal polls/renders. It would
mislabel a preview after another import or edit changed the database and would
violate the pre-preview comparison contract.

### 2. Match identity separately from equality

Asset identity uses existing `match_positions` normalized-name semantics. A row
with no matched Asset is `new`. A matched Asset with no same-Asset,
same-`broker_ticker` Position is `changed`, because an Asset exists but its
position baseline does not. A matched Asset with a Position is `unchanged` only
when every compared field is equal; any difference makes it `changed`.

`broker_ticker` is row identity, not a changed field. Asset name equality is
exact after trimming (so case/accent spelling changes are visible) while the
identity matcher remains normalized. Asset metadata comparison is limited to
incoming preview-represented fields: `name`, `buy_enabled`, `sell_enabled`,
and `currency_code`; absent incoming metadata is not fabricated or treated as
a difference. Position comparison covers `qty`, `avg_price`, `current_price`,
`total_invested`, and `total_current`.

Alternative rejected: treating every `auto_matched` row as unchanged. Name
matching proves identity only; it cannot prove values match.

### 3. Use exact typed equality and explicit diff semantics

Decimal values compare as exact `Decimal` values after canonical conversion;
no tolerance and no float conversion apply. `None` equals `None` only; missing
broker totals are not silently equal to numeric zero. Strings compare trimmed
and case-sensitively for metadata values, booleans compare by boolean value,
and currency codes compare upper-cased from the validated allow-list.

Each changed row carries `changed_fields[]` entries with stable field id,
Portuguese label, unit, sign, incoming value/display value, and previous
value/display value. Numeric sign is derived from incoming minus previous
(`positive`, `negative`, or `zero`); text/boolean changes use `not-applicable`.
Missing prior Position uses `previous: null` and display text `Não havia
posição`. Incoming values remain the default cell content; previous values are
never substituted or invented.

### 4. Sort on the server and render server order

Each `triage` group is sorted by asset name using Unicode NFKD accent removal
and `casefold`, with missing names last. Equal normalized names use normalized
broker ticker as tie-breaker, then raw name/ticker for deterministic output.
Alpine must not resort these arrays using locale-dependent browser behavior.
Empty groups are not rendered; counts belong in each non-empty PT-BR header.

Alternative rejected: sorting only in CSS/Alpine. It creates browser-locale
drift and can separate count/order semantics between manual and F59 payloads.

### 5. Make prior-value disclosure keyboard reachable

Changed fields render incoming value with a persistent changed cue and a
focusable disclosure control/wrapper. Hover and keyboard focus reveal a
visible prior-value panel; `aria-describedby`/equivalent accessible naming
announces field label, incoming value, previous value, unit, and sign. The
pattern must use existing focus tokens and remain usable without pointer. Equal
fields have no diff decoration or disclosure.

Alternative rejected: native `title` only. It is not reliably keyboard
discoverable or sufficiently structured for screen readers.

### 6. Widen only existing review panel

Increase `.modal-panel--wide` desktop cap from 1100px to 1200px (roughly 9%),
retain bounded viewport height/scroll, and keep the existing mobile rule at
100% width/full-height behavior for widths at or below 768px. No page-wide
layout or F63 styling changes are allowed.

### 7. Preserve production review inventory additively

The template change wraps the existing row presentation in triage sections; it
does not redesign row controls. Each section must visibly contain, in this
order, `Nome`, `Qtde`, `Preço médio`, `Total atual`, `Classe`, `Compra`, `Venda`,
and `Moeda`. The class cell retains Alpine assignment binding, suggestion
initialization, color swatch, and pending styling. Trade cells retain their
checkbox setters and visible enabled/blocked state. Currency retains its
allow-listed select. Incoming position values remain primary, including
quantity, average price, and broker-published current total.

Ticker handling is deliberately asymmetric: `broker_ticker` remains in each
row's assignment payload/key path and may remain in hidden inputs or data
binding, but ticker text, an `Ativo / ticker` heading, and any visible ticker
replacement are forbidden. This is not a new identity rule; it preserves the
current contract while removing only visual ticker exposure.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/routes/imports.py::preview_from_blob` | Stores only parsed raw rows | Stores raw rows plus per-row pre-preview Asset/Position baseline metadata | Make triage stable against later DB changes |
| `src/omaha/routes/imports.py::_build_preview_response` | Emits compatibility arrays in matcher/input order | Emits same arrays unchanged plus `triage` groups, sorted rows, typed diffs, and counts | Add review contract without breaking F59/F60 consumers |
| `src/omaha/routes/imports.py::_raw_to_dict` / `_dict_to_raw` | Round-trips parser fields | Ignores/preserves additive baseline envelope while retaining parser round-trip | Avoid model/schema change and preserve old previews |
| `_patrimonio_add_asset_modal.html::Step 2` | Existing/new sections show eight production columns and editable controls; row identity uses hidden `broker_ticker` | Conditional Novos/Alterados/Inalterados sections with counts and shared incoming/diff rendering; every section repeats all eight columns/controls, while ticker remains hidden | Make review state legible without functional loss or visible ticker regression |
| `_patrimonio_add_asset_modal.html::importModal` | Stores `autoMatched`/`unmatched` and hydrates them | Stores additive triage groups, validates compatibility fallback, preserves assignment/commit methods | Keep manual/F59 entry paths and explicit commit identical |
| `_patrimonio_actions.html::dashboard-import-btn` | Existing `Importar CSV` opens modal | Remains unchanged as sole manual-import entry; no F65 duplicate CTA | Preserve current manual upload path and avoid a second commit affordance |
| `visual-prototype.html` review tables | Prototype shows only name, quantity, current value, and class | Every `Novos`/`Alterados`/`Inalterados` table visibly shows `Nome`, `Qtde`, `Preço médio`, `Total atual`, `Classe`, `Compra`, `Venda`, `Moeda`; hidden inputs carry `broker_ticker`; narrow view uses horizontal scrolling without hiding columns | Make owner review prove additive preservation and hidden-ticker contract |
| `visual-prototype.html::.manual-note` and review child block | Prototype renders standalone `Importação manual` copy plus `Importar manualmente` button | Block and related CSS are absent; existing `Cancelar`/`Confirmar importação` actions remain | Align static owner evidence with production decision and prevent visual approval of UI that must not ship |
| `src/omaha/static/app.css::.modal-panel--wide` | 1100px desktop cap | 1200px cap with existing mobile full-width rule | Moderately widen textual review panel |
| `src/omaha/static/app.css::.import-review-*` | Two-section styling, no diff disclosure | Three state headers/counts, changed cue, hover/focus previous-value disclosure, responsive table rules | Support visual and keyboard review |
| `tests/test_import_preview.py::TestPostImportPreview` | Proves old shape/matching/totals | Adds baseline equality, mutually exclusive groups, sorting, diff payload, and no-mutation compatibility scenarios | Server contract oracle |
| `tests/e2e/test_import_modal.py::TestS04ImportModal` | Proves two sections and commit journey | Proves three sections/counts, incoming values, empty-section omission, sorting, focus disclosure, and unchanged commit journey | Browser rendering/accessibility oracle |

## Risks / Trade-offs

- **Additive JSON grows preview rows** → keep baseline compact, omit fields not
  compared, and retain legacy arrays; test response key compatibility.
- **Legacy previews lack baseline** → use bounded response-time fallback and
  never reject or mutate them; test both new and legacy-shaped raw JSON.
- **Decimal/null drift** → compare typed values before serialization; test
  missing totals, zero, equal decimals with different textual scale, and real
  differences.
- **Duplicate names/tickers** → stable normalized-name/ticker sorting plus raw
  tie-break; test case/accent variants and missing names.
- **Dense three-section tables** → 1200px cap, existing scroll/mobile rules,
  no empty placeholders, explicit all-column/control inventory, and owner
  visual review before Apply. Horizontal scrolling may preserve readability;
  hiding production columns or controls is not an acceptable responsive result.
- **Hover-only accessibility regression** → focusable disclosure with keyboard
  and accessible description tests; no `title`-only implementation.
- **Concurrent F63 visual edits** → F65 Apply must wait for F63/shared surface
  coordination; changed-file audit forbids F63 edits.
- **Manual CTA duplication** → F65 must preserve the existing modal entry and
  commit boundary only; artifact inspection and focused UI acceptance must
  reject any standalone manual-import panel/card/footer or duplicate CTA.
- **Contract regression through triage markup** → shared row rendering must be
  checked against the current modal inventory in every group. Reject any visible
  ticker, missing `broker_ticker` assignment key, removed column, removed class
  binding/suggestion/color/pending state, missing trade toggle, missing currency
  select, or changed upload/sync/expiry/Cancelar/Confirmar boundary.

## Migration Plan

1. Before Apply, obtain owner approval of the static mock/prototype/browser
   rendering described in the visual gate below. Without recorded approval,
   F65 remains blocked.
2. Implement additive baseline/triage response data, then template/CSS
   rendering, preserving compatibility arrays and commit boundary.
3. Run focused server/e2e tests and lint; do not run browser/server/DB during
   Propose. No migration or seed operation is required.
4. After runtime Apply, invoke mandatory `refresh-for-test`, capture current
   browser-rendered evidence, and record receipt before Review. This is an
   Apply delivery obligation, not Propose work.
5. Rollback removes only F65 response/template/CSS/tests/spec artifacts;
   existing ImportPreview rows, Assets, Positions, snapshots, audits, and F59
   job state remain valid.

## Owner visual-rendering gate (mandatory before Apply)

Owner must approve one static mock, prototype, or browser rendering and record
decision in this `design.md` before Apply starts. Exact checklist:

- three labels exactly `Novos`, `Alterados`, `Inalterados`, each with count;
- each row appears in exactly one section; empty sections are absent;
- each section is sorted case/accent-insensitively by name with ticker tie-break;
- incoming position/metadata values remain primary; changed fields have a
  persistent cue and prior-value disclosure on both hover and keyboard focus;
- disclosure is readable, labelled, unit/sign aware, and does not rely on
  pointer-only tooltip behavior;
- panel is moderately wider on desktop (1200px cap target) and remains full
  width/readable on mobile; existing class controls and Confirmar/Cancelar
  hierarchy remain intact;
- preview/sync handoff, explicit confirmation, Família read-only, and no
  auto-commit remain visually unchanged; no standalone manual-import
  panel/card/footer or duplicate CTA is present, and existing modal actions are
  the only manual commit controls.

Required owner record format before Apply:
`F65 visual approval: APPROVED | artifact/mock path: <exact path or URL> |
checksum if file: <sha256> | checklist: all items above | owner: <name> |
timestamp: <UTC>`. Missing record is a hard Apply blocker. This Propose gate
does not create or run visual artifacts.

## Open Questions

None blocking. Owner visual-rendering approval remains a mandatory external
decision before Apply, not an implementation discovery task.

## Propose revision: static visual review artifact

`visual-prototype.html` is the bounded, self-contained review artifact for this
gate. It uses inline CSS and deterministic fixture copy only; it has no live
data, network request, database, MyProfit connector, application import route,
or runtime dependency. It is visual evidence, not implementation and not a
replacement for the later browser-rendered Apply evidence.

### Exact owner review checklist

Owner must review the file at
`openspec/changes/f65-triagem-de-ativos-por-estado-no-preview-de-posicao/visual-prototype.html`
and decide each item below:

- [ ] Three visible section labels are exact: `Novos`, `Alterados`,
  `Inalterados`.
- [ ] Each visible section has count (`2`, `2`, `1` in fixture); every fixture
  row belongs to one section only; no empty section or empty-state placeholder
  is shown.
- [ ] Every visible section repeats all current production columns exactly:
  `Nome`, `Qtde`, `Preço médio`, `Total atual`, `Classe`, `Compra`, `Venda`,
  `Moeda`. Each row visibly retains editable class select, class
  suggestion/color/pending state, Compra toggle, Venda toggle, and Moeda select.
- [ ] No `Ativo / ticker` heading or visible ticker value appears. Each row
  retains a hidden `broker_ticker` assignment key; hidden identity is not
  replaced by a visible identity control.
- [ ] Each group is visibly deterministic: asset names use
  case/accent-insensitive order and broker ticker is the tie-breaker.
- [ ] Incoming values remain primary: quantity and broker-published current
  value are shown in each row; changed fields retain incoming text by default.
- [ ] Changed fields have persistent cue and prior-value disclosure that is
  reachable by mouse hover and keyboard focus. Disclosure includes field
  label, incoming value, previous value, unit, and sign; equal fields have no
  disclosure decoration.
- [ ] Review panel is moderately wide on desktop (`1200px` cap shown by the
  prototype) and constrained to full-width, horizontally readable content on
  mobile (`<=768px` media rule); horizontal scrolling, if needed, preserves all
  columns and controls rather than hiding them.
- [ ] No standalone `Importação manual` panel/card, explanatory footer, or
  duplicate `Importar manualmente` action is present. Existing modal
  `Importar CSV` entry/upload and separate `Cancelar` / `Confirmar importação`
  actions remain the only manual review and commit controls; `Confirmar` does
  not imply automatic commit.
- [ ] Família context is visibly disabled/read-only, while active profile
  context remains visible; no visual path suggests mutable Família data.
- [ ] Prototype is understood as static evidence only: no live preview,
  network, DB, MyProfit, or application behavior is being approved by this
  artifact.

### Owner decision recording location

After review, owner records decision in this same `design.md`, directly below
this section, using the existing durable format:

`F65 visual approval: APPROVED | artifact/mock path: openspec/changes/f65-triagem-de-ativos-por-estado-no-preview-de-posicao/visual-prototype.html | checksum if file: <sha256> | checklist: all items above | owner: <name> | timestamp: <UTC>`

`APPROVED` is the only value that releases Apply. `REJECTED` or a partial
checklist keeps F65 blocked and must state requested visual correction here;
this Propose revision adds no runtime implementation task and does not change
F65 behavior scope. Owner approval remains pending for this revision.

### Revision record

- Revision scope: additive production-column/control preservation and exact
  hidden-ticker contract in static evidence and implementation dossier.
- Revised artifact checksum (SHA-256):
  `6a2540a74067051eaacb1988af26cfba33d8ab075a6f6d76fe2373ea8f8002e6`.

F65 visual approval: APPROVED | artifact/mock path: openspec/changes/f65-triagem-de-ativos-por-estado-no-preview-de-posicao/visual-prototype.html | checksum if file: 6a2540a74067051eaacb1988af26cfba33d8ab075a6f6d76fe2373ea8f8002e6 | checklist: all items above, including three exclusive PT-BR sections/counts, deterministic name/ticker order, incoming values, hover/focus labelled prior-value disclosure with unit/sign, 1200px desktop cap, full-width readable mobile behavior, preserved eight production columns/controls, hidden broker_ticker assignment key, existing Importar CSV/upload and Cancelar/Confirmar boundary, and read-only Família context | owner: owner (conversation approval) | timestamp: 2026-08-22T20:28:19Z

## Implementation Decisions

- Remediation 1/2 keeps `Ausentes` name-based: build active-profile absent
  membership from `normalize_name(Asset.name)` versus all normalized incoming
  asset names, not ticker or matcher row identity. This ensures an existing ETH
  asset with a different broker ticker is absent only when no normalized `ETH`
  name occurs in batch. Evidence: API regression covers `ETH-OLD` versus
  `ETH-NEW` and keeps BTC absent.
- Remediation 1/2 renders prior-value disclosure in normal table-cell flow
  instead of an absolutely positioned child inside `.import-review-table-wrap`.
  This preserves horizontal scrolling while preventing overflow clipping on
  hover and keyboard focus. Incoming remains primary; disclosure exists only
  for changed fields and uses `previous_display`.
- Remediation 1/2 applies owner-selected visual treatment B: neutral review
  surfaces, existing zebra/hover row tokens, and semantic state header/left
  border edges. Changed controls use existing accent token focus treatment;
  no page/table surface tint or unrelated layout styling is introduced.

- Remediation 2/2 keeps incoming cell text as the unchanged primary content.
  Prior-value disclosure contains only formatted prior value text, with no
  visible label, incoming-value copy, question-mark/icon treatment, or
  `Anterior`/`Recebido` prose. Disclosure is an absolutely positioned,
  hover/focus-visible overlay, so showing it does not reflow the table or
  replace incoming cell text. Monetary prior values use canonical BRL integer
  formatting (`R$` plus Brazilian thousands separator, no fractional digits;
  `116615.5300` displays as `R$ 116.616`); quantity uses canonical quantity
  formatting with asset-name precision, and text/null values retain their
  established field-specific display (`Não havia posição` for missing prior
  position). The accessible name retains field label/unit/sign without adding
  that metadata to visible overlay text.
- Remediation 2/2 keeps Compra/Venda as native checkbox-plus-label controls on
  a transparent, neutral surface: no pill, colored text background, or
  semantic/data behavior change. Classe retains its color-tinted cell/select
  formatting and assignment/pending behavior, while only the redundant class
  swatch/legend element is removed; no class assignment semantics change.

- Remediation 3/3 adds only bounded bottom clearance to
  `.import-review-table-wrap`: `padding-bottom: 2rem`. The disclosure remains
  absolutely positioned and non-flow; padding enlarges the scroll container's
  clipping boundary without changing table cell text, column layout, or
  interaction. Evidence: the focused browser assertion measures the final
  disclosure rectangle inside both table-wrap and modal-panel at the last-row
  boundary.

## Owner-authorized surgical follow-up rule

The asset-review modal SHALL say `Revisar posições`, disclose a changed
field's readable prior value on both mouse hover and keyboard focus while the
incoming value remains primary, and render exactly four mutually exclusive
groups: `Novos` for batch-only rows, `Alterados` and `Inalterados` for rows
present in both the import batch and the active profile portfolio, and
`Ausentes` for rows present only in the current active-profile portfolio.
`Ausentes` rows SHALL be deterministic alphabetic order, profile scoped,
visibly separate, read-only, and non-committable; confirmation SHALL neither
update nor delete them. Existing preview-then-confirm behavior and all other
F65 compatibility and safety boundaries remain unchanged.
