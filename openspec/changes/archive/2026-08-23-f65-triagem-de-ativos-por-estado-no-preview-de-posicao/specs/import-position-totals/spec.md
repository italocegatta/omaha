## MODIFIED Requirements

### Requirement: Total atual exibido por linha, 0 casas decimais

The import review SHALL display incoming broker-published `qty`, `avg_price`,
`current_value` (`total_current`), and `invested` (`total_invested`) values from
the preview in the existing `Qtde`, `Preço médio`, and `Total atual` columns.
Currency values SHALL use the existing Brazilian currency formatter with zero
decimal places. F65 triage equality SHALL compare the typed broker totals
against the pre-preview Position totals; it SHALL NOT recompute totals as `qty
* current_price` and SHALL NOT replace missing broker totals with a fabricated
calculation. Existing compatibility payload keys `invested` and
`current_value` remain available to the modal, and no triage section may hide
these columns.

#### Scenario: Incoming total current remains primary

- **WHEN** preview row carries broker `current_value = "3250.00"` and
  `qty * current_price` would produce a different value
- **THEN** review displays the broker value as `R$ 3.250` and triage compares
  that broker value with prior `Position.total_current`

#### Scenario: Incoming quantity and average price remain primary

- **WHEN** preview row carries `qty = "120"` and `avg_price = "27.00"`
- **THEN** review displays those incoming values in `Qtde` and `Preço médio`
  without replacing either column with ticker or triage-only metadata

#### Scenario: Incoming invested total remains primary

- **WHEN** preview row carries broker `invested = "3100.00"`
- **THEN** review displays `R$ 3.100` using existing formatting and does not
  derive invested value from quantity or price

#### Scenario: Missing broker total is explicit

- **WHEN** source CSV omits `total_current` or `total_invested`
- **THEN** existing compatibility display remains the established zero
  placeholder, while equality preserves missing-vs-numeric distinction and
  does not recompute a replacement total
