## ADDED Requirements

### Requirement: Inline edit auto-focuses the input on the same click

The dashboard's three inline editors (class header `Alvo`, per-asset
`alvo % classe`, per-asset `alvo % total`) MUST auto-focus their
`<input>` and pre-select its content as part of the same click that
opens the editor. The user MUST NOT need a second click or touch
interaction to focus the input before typing. The auto-focus MUST be
scoped to the active instance of the editor — concurrent class sections
or asset rows on the page MUST NOT have their focus stolen.

#### Scenario: Single click on the class target pill focuses the input

- **WHEN** the user clicks the `Alvo NN%` pill
  (`data-testid="class-target-pct-view"`) in any class section header
- **THEN** the inline input (`data-testid="class-inline-edit-input"`)
  becomes visible
- **AND** that same input receives focus on the same click
- **AND** the input's current value is pre-selected
- **AND** the user's first keystroke replaces the pre-selected value
- **AND** no input in a different class section receives focus

#### Scenario: Single click on the per-asset alvo % classe cell focuses the input

- **WHEN** the user clicks the `alvo % classe` cell button
  (`data-testid="asset-target-pct-class"`) on any asset row
- **THEN** the inline input
  (`data-testid="asset-inline-edit-input"`) becomes visible and
  focused on the same click
- **AND** the input's current value is pre-selected
- **AND** concurrent editors on other rows stay closed

#### Scenario: Single click on the per-asset alvo % total cell focuses the input

- **WHEN** the user clicks the `alvo % total` cell button
  (`data-testid="asset-target-pct-total"`) on any asset row
- **THEN** the inline input
  (`data-testid="asset-target-pct-total-edit-input"`) becomes visible
  and focused on the same click
- **AND** the input's current value is pre-selected

### Requirement: Empty inline edit commits as zero

When the inline editor for any of the three target-% fields is
visible and the user clears the value (string is empty or
whitespace-only) and then presses Enter, blurs the input, or moves
focus outside the editor, the dashboard MUST commit the value `0` to
the server. The dashboard MUST treat this client-side coercion as a
silent normal write — no 422 round trip, no inline error span, no
visible "saved 0" toast. Existing in-range validation (0 ≤ pct ≤ 100)
remains authoritative on the server; the empty-equality-zero rule is
a client-side coercion, not a server-side exception. After a
successful `0` commit, the field's display value returns as `0%` (or
`0.00%` per existing rounding rules) and the dashboard's per-class
delta / portfolio sticky alert surfaces the resulting deviation.

#### Scenario: Clearing the class target and pressing Enter saves zero

- **GIVEN** a class with `classTargetPct: 25`
- **WHEN** the user clicks the `Alvo` pill (editor opens and focuses)
- **AND** clears the input (string becomes empty)
- **AND** presses Enter
- **THEN** PATCH /api/classes/{id} is sent with `{"target_pct": "0"}`
- **AND** on 200, the header pill shows "Alvo 0%"
- **AND** no inline error span is rendered
- **AND** no 422 response is received

#### Scenario: Clearing the per-asset alvo % classe and pressing Enter saves zero

- **GIVEN** an asset with `target_pct: 12.5`
- **WHEN** the user clicks the cell, clears the input, presses Enter
- **THEN** PATCH /api/assets/{id} is sent with `{"target_pct": "0"}`
- **AND** on 200, the row's `alvo % classe` cell shows 0.00%
- **AND** no inline error span is rendered

#### Scenario: Clearing the per-asset alvo % total and pressing Enter saves zero

- **GIVEN** an asset with `target_pct_total: 7.5` and class with
  `classTargetPct: 25`
- **WHEN** the user clicks the cell, clears the input, presses Enter
- **THEN** the client computes `new_target_pct = 0 * 100 / 25 = 0`
- **AND** PATCH /api/assets/{id} is sent with `{"target_pct": "0"}`
- **AND** on 200, both `alvo % classe` and `alvo % total` cells show
  0.00%

#### Scenario: Blurring an empty class input saves zero

- **WHEN** the user opens the class `Alvo` editor and clears the
  input then clicks outside the input (no Enter pressed)
- **THEN** the @blur handler commits `{"target_pct": "0"}` to the
  server
- **AND** the editor closes on 200

### Requirement: Inline edit inputs render without the native number spinner

The dashboard's three inline editor inputs (class header input and
both per-asset inputs) MUST NOT render the browser's native
`<input type="number">` spinner (`▲` / `▼` glyphs on the right edge).
The input visual MUST be a flat field consistent with the
surrounding pill — same border treatment, same height, no
stepper chrome. Keyboard `↑` / `↓` MUST continue to step the value
per the existing `step="0.01"` attribute. This rule applies only to
the dashboard's three inline editors; modal forms (asset create,
class create, import) MAY keep the native spinner because they are
modal forms, not inline pill editors.

#### Scenario: Class edit input has no spinner glyph

- **WHEN** the class `Alvo` editor is open
- **THEN** no `▲` / `▼` stepper element is rendered on the right side
  of `data-testid="class-inline-edit-input"`
- **AND** the input border on the right matches the border on the
  left (same color, same radius)

#### Scenario: Per-asset edit inputs have no spinner glyph

- **WHEN** either per-asset editor (`alvo % classe` or
  `alvo % total`) is open
- **THEN** no `▲` / `▼` stepper is rendered on either
  `data-testid="asset-inline-edit-input"` or
  `data-testid="asset-target-pct-total-edit-input"`
