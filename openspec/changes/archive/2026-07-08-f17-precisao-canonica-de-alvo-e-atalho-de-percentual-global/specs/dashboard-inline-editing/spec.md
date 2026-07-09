## MODIFIED Requirements

### Requirement: Inline edit of alvo % total

The dashboard MUST allow the user to edit the `alvo % total` cell of
an asset row inline. Editing this cell MUST send the operator's typed
global target percentage to `PATCH /api/assets/{id}` using a dedicated
shortcut field for `% ativo na carteira`; the server, not the browser,
MUST convert that value into the canonical persisted `target_pct`
(`% ativo na classe`) using the owning class's current `target_pct`.
The cell MUST show an inline confirm hint while in edit mode
describing the effect of the edit (recalculation of the asset's
`alvo % classe` within the class, other assets in the class
unaffected). Only one cell per row may be in edit mode at a time.

On success, the UI MUST update both the canonical `alvo % classe` cell
and the derived `alvo % total` cell from the server-confirmed state,
without re-applying browser-side back-solve rounding.

#### Scenario: Edit alvo % total commits a server-derived alvo % classe

- **WHEN** the user commits a new `alvo % total` value of 20 for
  an asset whose class has `classTargetPct = 30`
- **THEN** the client sends `PATCH /api/assets/{id}` with the typed
  global-target shortcut field carrying `20`
- **AND** the server derives the canonical in-class target from
  `20 * 100 / 30`
- **AND** on 200, the asset's `alvo % classe` cell updates from the
  server-confirmed canonical value
- **AND** the asset's `alvo % total` cell updates to `20.00`

#### Scenario: Confirm hint visible while editing alvo % total

- **WHEN** the user clicks the `alvo % total` cell to edit
- **THEN** the cell enters edit mode
- **AND** a confirm hint is visible next to the input (e.g.
  "recalcula apenas a posição deste ativo dentro da classe")
- **AND** the `alvo % classe` cell on the same row is in read-only
  view mode (not editable) while the edit is in flight

#### Scenario: Browser does not decide persisted rounding for alvo % total edit

- **WHEN** the user commits a `alvo % total` value whose back-solved
  in-class target has more than two decimal places
- **THEN** the browser still sends the typed global value unchanged
- **AND** persisted `target_pct` precision is decided by the server's
  canonical conversion rule, not by client-side `toFixed(2)`

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
  inputs to the per-class delta pill
  (`data-testid="class-delta-badge"`) in the class section header
  so the operator sees "Sobra X%" / "Falta X%" in real time, but
  the advisory MUST NOT block the write;
- browser-side back-solve math in the `alvo % total` editor — the
  browser sends the typed global value, and the server decides whether
  the resulting canonical `target_pct` is valid and persistable.

The "aceitar o commit incondicionalmente" rule applies
identically to Enter and to blur. Escape continues to cancel
without sending any PATCH. The re-entrance guard on
`commitEdit` (`if (this.editingAssetId === null) return;`)
stays — it prevents the @blur handler from re-issuing a
PATCH after a successful Enter already cleared the
`editingAssetId`. The same re-entrance pattern MUST apply
to `commitEditClassPct` and `commitEditTotal`.

#### Scenario: Off-100 edit is still accepted

- **WHEN** the user commits a new target percentage that pushes the
  per-class sum to 110% by pressing Enter (or by blurring the input)
- **THEN** the PATCH call returns 200
- **AND** the asset's local target state updates to the new value
- **AND** the per-class delta pill (`data-testid="class-delta-badge"`)
  in the class section header shows "Sobra X%"

#### Scenario: Server rejects invalid global shortcut math

- **WHEN** the user commits an `alvo % total` value that cannot be
  converted into a valid canonical `target_pct` for the current class
- **THEN** the browser still sends the PATCH
- **AND** the server returns 422 with `detail`
- **AND** the inline editor renders that server message without
  inventing a client-side validation rule
