## ADDED Requirements

### Requirement: classSection exposes every class_data field used by the template

The Alpine classSection factory MUST copy every field of the
class_data blob that the surrounding template references into
a corresponding camelCase property on the returned component
object. The blob is built at Jinja render time
(`src/omaha/templates/dashboard.html:80`) with keys `id`,
`name`, `target_pct`, `color`, `current_pct`, and `assets`.
The factory MUST map at least: `id → classId`,
`name → className`, `target_pct → classTargetPct`,
`color → classColor`, `current_pct → classCurrentPct`. If a
template expression references a derived name (e.g.
`classColor`) that is not initialized in the factory, Alpine
emits an "Expression Error: X is not defined" warning, the
expression renders as empty/NaN, and the visual element
(`.class-color-swatch` background, `.pct-current` "Atual NN%"
pill) shows broken state.

#### Scenario: Header swatch renders the server's class color

- **GIVEN** a class "RF Test" with `color: "#0a66c2"` from the
  server
- **WHEN** the dashboard renders the class section header
- **THEN** the swatch element
  (`data-testid="class-color-swatch"`) has its inline
  `style="background: #0a66c2"` (or equivalent) applied
- **AND** the browser console emits zero `classColor is not
  defined` warnings

#### Scenario: Header "Atual NN%" pill renders the server's current_pct

- **GIVEN** a class "RF Test" with `current_pct: 25.5` from
  the server
- **WHEN** the dashboard renders the class section header
- **THEN** the pill (`data-testid="class-current-pct"`) shows
  "Atual 25.50%"
- **AND** the browser console emits zero `classCurrentPct is
  not defined` warnings
