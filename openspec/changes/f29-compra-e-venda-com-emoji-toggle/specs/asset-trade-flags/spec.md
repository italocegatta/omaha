## MODIFIED Requirements

### Requirement: Dashboard renders inline per-asset trade-control toggles

The system SHALL render, for each asset row in the dashboard's
asset table, inline toggle controls for `buy_enabled` and
`sell_enabled`, and a visible badge (or column) for
`currency_code`. Clicking a toggle SHALL send a
`PATCH /api/assets/{id}` with the changed field and update
the row's visual state on a 200 response. The toggle SHALL be
disabled while the PATCH is in flight.

The toggle SHALL display a Material Symbols Outlined icon
(`check_circle` when enabled, `lock` when disabled) instead
of a text label. Each button SHALL carry an `aria-label`
attribute that announces the current state in Portuguese
(e.g., "Compra: Liberado"). The button wrapper, CSS classes
(`trade-toggle--on` / `trade-toggle--off`), `data-testid`
attributes, and `@click` handler are unchanged.

This is per-asset only — there is no bulk toggle at the
asset-class level. The dashboard does not provide a class-
level mechanism for setting or clearing trade-control flags
across multiple assets in one action.

#### Scenario: Toggle buy_enabled inline

- **WHEN** a user clicks the buy-enabled toggle on asset row
  for PETR4
- **THEN** the dashboard sends
  `PATCH /api/assets/{id} {"buy_enabled": <new-value>}`
  and updates the toggle's visual state to reflect the new
  value on a 200 response

#### Scenario: Toggle renders icon not text

- **WHEN** the dashboard renders the asset table
- **THEN** each buy/sell toggle cell contains a Material
  Symbols Outlined icon (`check_circle` when enabled,
  `lock` when disabled) and no visible text label

#### Scenario: Toggle has accessible label

- **WHEN** the dashboard renders a buy/sell toggle
- **THEN** the button element has an `aria-label` attribute
  in the format `<field>: <state>` (e.g.,
  "Compra: Liberado", "Venda: Bloqueado")

#### Scenario: Currency badge is visible per asset

- **WHEN** the dashboard renders the asset table
- **THEN** each asset row shows a visible currency indicator
  matching the asset's `currency_code` value

#### Scenario: Toggle buy and sell are independent

- **WHEN** a user clicks the sell-enabled toggle on asset row
  for PETR4
- **THEN** only the sell-enabled toggle disables during the
  in-flight PATCH; the buy-enabled toggle stays clickable
  and does not flicker
