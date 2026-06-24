## ADDED Requirements

### Requirement: Client does not pre-validate inline edits before PATCH

The dashboard MUST send the PATCH for every inline-edit commit
unconditionally. The three commit functions (`commitEditClassPct`,
`commitEdit`, `commitEditTotal` in the `classSection` Alpine
component at `src/omaha/templates/dashboard.html`) MUST NOT gate
the PATCH on:

- a per-row range check (0 ≤ pct ≤ 100) — the server
  (`PATCH /api/classes/{id}` and `PATCH /api/assets/{id}`) is the
  single source of truth for "valor deve ser entre 0 e 100", and
  surfaces a 422 with the user-friendly `detail` on out-of-range;
- the per-class sum (`classDeltaMessage !== ''`) — the local
  `classDelta` / `classDeltaMessage` getters remain as **advisory**
  inputs to the per-class delta badge
  (`data-testid="asset-group-header-alert`) so the operator sees
  "Sobra X%" / "Falta X%" in real time, but the advisory MUST NOT
  block the write;
- the back-solve math in the "alvo % total" editor
  (`newTargetPct < 0 || newTargetPct > 100`) — the server
  accepts the derived `target_pct` if it is in range; otherwise
  returns 422 and the client renders the server's `detail`.

The "aceitar o commit incondicionalmente" rule applies
identically to Enter and to blur. Escape continues to cancel
without sending any PATCH. The re-entrance guard on
`commitEdit` (`if (this.editingAssetId === null) return;`)
stays — it prevents the @blur handler from re-issuing a
PATCH after a successful Enter already cleared the
`editingAssetId`. The same re-entrance pattern MUST apply
to `commitEditClassPct` and `commitEditTotal`.

#### Scenario: Asset inline edit to off-100 is accepted by the client

- **WHEN** the user clicks the "alvo % classe" cell of an asset
  (data-testid="asset-target-pct-class")
- **AND** types a value that would push the per-class sum above
  100% (e.g. asset A at 40%, asset B at 40%, type 80 into A)
- **AND** presses Enter
- **THEN** PATCH /api/assets/{id} is sent with the new value
- **AND** the server returns 200
- **AND** the asset's `alvo % classe` cell updates to the new value
- **AND** the per-class group header alert
  (data-testid="asset-group-header-alert") shows "Sobra X%" with
  the danger color token (the per-class sum now exceeds 100%)

#### Scenario: Asset inline edit to off-100 is accepted on blur

- **WHEN** the user types a value that would push the per-class
  sum off 100% in the "alvo % classe" input
- **AND** moves the focus outside the input (clicks another cell,
  the table header, or any non-input element)
- **THEN** PATCH /api/assets/{id} is sent (the @blur handler runs
  without the previous `classDeltaMessage !== ''` block)
- **AND** the server returns 200
- **AND** the value is persisted

#### Scenario: Class inline edit to 100% is accepted

- **WHEN** the user clicks the "Alvo NN%" pill in a class section
  header (data-testid="class-target-pct-view")
- **AND** types 100 in the inline input
- **AND** presses Enter
- **THEN** PATCH /api/classes/{id} is sent
- **AND** the server returns 200
- **AND** the class section header shows "Alvo 100.00%"
- **AND** if the portfolio total now exceeds 100%, the sticky
  allocation alert card surfaces the new portfolio-level
  deviation

#### Scenario: Per-row out-of-range input shows server message

- **WHEN** the user types a per-row out-of-range value (e.g.
  150 or -5) in any inline editor
- **AND** presses Enter or blurs
- **THEN** the client sends the PATCH with the typed value
- **AND** the server returns 422 with `detail` "A alocação
  do ativo deve estar entre 0 e 100." (or the class-level
  variant)
- **AND** the inline error span
  (data-testid="asset-inline-edit-error" or
  data-testid="class-inline-edit-error" or
  data-testid="asset-target-pct-total-edit-error") renders the
  server's `detail` message verbatim
- **AND** the editor stays open so the user can correct

#### Scenario: Re-entrance guard prevents double-PATCH

- **WHEN** the user types a valid value and presses Enter
- **THEN** the success path sets `editingAssetId = null` (or
  `editingClassPct = false`, or `editingTotalAssetId = null`)
  BEFORE the @blur handler fires
- **AND** the @blur handler's `if (this.editingXxx === null) return;`
  guard bails out without sending a second PATCH
