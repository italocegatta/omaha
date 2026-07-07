## ADDED Requirements

### Requirement: Display face is Red Hat Display (sans, not serif)

The system SHALL render the portfolio hero numerals, the active tab label, the profile name in the profile-switcher, and the section titles (`.portfolio-stat-value`, `.profile-name`, `.tab-nav__btn--active`, `.patrimonio-section-title`, `.app-header__logo`, `.profile-stat-value`) using **Red Hat Display** at weight 700 or 800. The display face SHALL be sans-serif (NOT serif) per the D02 §Gate 3 decision; Source Serif 4 SHALL NOT appear in the Google Fonts URL nor in any `font-family` declaration in `app.css`.

#### Scenario: Display selectors reference Red Hat Display

- **WHEN** `app.css` declares a `font-family` for any of the six known display selectors
- **THEN** the first family in the chain SHALL be `"Red Hat Display"`
- **AND** Source Serif 4 SHALL NOT appear anywhere in `app.css`

#### Scenario: Hero numeral renders in Red Hat Display 700

- **WHEN** a user opens `/patrimonio` for the Italo profile
- **THEN** the `.portfolio-stat-value` element SHALL render with `font-family: "Red Hat Display"`, `font-weight: 700`
- **AND** the active tab `.tab-nav__btn--active` SHALL also render in Red Hat Display 700

#### Scenario: Source Serif 4 is absent from the build

- **WHEN** a regression scan searches `app.css` and `base.html` for `Source Serif 4` or `Source+Serif+4`
- **THEN** the scan SHALL return zero matches (the family has been retired per D02 §Gate 3)

### Requirement: Body declares Inter variable with tnum, cv01, ss01, ss02

The system SHALL render body text in **Inter** (variable, weights 400–700 via the Google Fonts variable axis `wght@400..700`). The `body` selector in `app.css` SHALL declare `font-feature-settings: "tnum", "cv01", "ss01", "ss02"` so the body picks up tabular figures (`tnum`), the 1 with serif base (`cv01`), open 6 and 9 (`ss01`), and 0/O disambiguation (`ss02`) per the D02 §Typography specification.

#### Scenario: Body font-feature-settings include all four

- **WHEN** a regression scan parses the `body { ... }` rule in `app.css`
- **THEN** the rule SHALL declare `font-feature-settings` with all four values: `tnum`, `cv01`, `ss01`, `ss02`
- **AND** no other `font-feature-settings` declaration on `body` SHALL remove any of the four

#### Scenario: Body font is Inter, not a serif

- **WHEN** `body { font-family: ... }` is parsed
- **THEN** the first family in the chain SHALL be `"Inter"`
- **AND** the chain SHALL include system-sans fallbacks (`-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`)
- **AND** no serif family SHALL appear in the body chain

#### Scenario: Inter loads as a variable font

- **WHEN** the Google Fonts URL in `base.html` is parsed
- **THEN** the URL SHALL declare `family=Inter:wght@400..700` (range syntax, covering the variable axis)
- **AND** SHALL NOT use fixed-weight multi-declarations (`wght@400;500;600` is rejected as over-rigid for the four feature-settings use case)

### Requirement: Google Fonts URL is the single font source

The system SHALL load both Inter and Red Hat Display from a single Google Fonts CSS endpoint declared in `src/omaha/templates/base.html`. The URL SHALL end in `&display=swap` to avoid FOIT on slow connections. The URL SHALL preconnect to both `https://fonts.googleapis.com` (CSS) and `https://fonts.gstatic.com` (WOFF2 files); the gstatic preconnect SHALL carry `crossorigin` because the WOFF2 fetch uses CORS.

#### Scenario: Single Google Fonts link in base.html

- **WHEN** `base.html` is parsed for font-loading elements
- **THEN** there SHALL be exactly one `<link rel="stylesheet" href="https://fonts.googleapis.com/...">`
- **AND** the URL SHALL end in `&display=swap`

#### Scenario: Both preconnects are present

- **WHEN** `base.html` is parsed for preconnect links
- **THEN** `<link rel="preconnect" href="https://fonts.googleapis.com">` SHALL be present
- **AND** `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` SHALL be present
- **AND** the `crossorigin` attribute SHALL appear on the gstatic preconnect (not the googleapis one — the CSS fetch is same-origin)

#### Scenario: No local @font-face declarations for Inter or Red Hat Display

- **WHEN** `app.css` is scanned for `@font-face` blocks
- **THEN** the scan SHALL return zero `@font-face` declarations for `font-family: 'Inter'` or `font-family: 'Red Hat Display'`
- **AND** self-hosting (deferred per F09 design D-F09.1) SHALL NOT be reintroduced without an owner-driven follow-up slice

### Requirement: No serif family in the display chain

The system SHALL NOT introduce a serif fallback (`"Source Serif 4"`, `"IBM Plex Serif"`, `Georgia`, `serif`, or any named serif) into any `font-family` chain targeting the six display selectors. The display chain SHALL end in the same sans fallbacks used by the body (`-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `sans-serif`) so a Google Fonts outage degrades to a consistent sans rendering.

#### Scenario: Display selectors end in sans fallbacks

- **WHEN** `app.css` declares `font-family` for any of the six display selectors
- **THEN** the chain SHALL end in `sans-serif`
- **AND** the chain SHALL NOT contain `serif`, `Georgia`, `"Source Serif 4"`, or `"IBM Plex Serif"`

#### Scenario: Body and display share the same fallback chain

- **WHEN** the body chain and any display chain are compared
- **THEN** the fallback tail (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`) SHALL be identical across body and display selectors
- **AND** only the leading named family differs (Inter for body, Red Hat Display for display)

### Requirement: Body and display stay synchronized via base.html + app.css pair

The system SHALL keep `base.html` and `app.css` synchronized: any change to the display face in `app.css` SHALL be reflected in the Google Fonts URL in `base.html`, and any removal of a family from the URL SHALL be reflected in the `font-family` chains that reference it. A regression test SHALL pin the contract so a future edit to one file without the other fails the test suite.

#### Scenario: Test pins the synchronization contract

- **WHEN** `tests/test_typography_tokens.py` runs as part of `task test-unit`
- **THEN** the test SHALL assert that the Google Fonts URL in `base.html` declares both Inter and Red Hat Display
- **AND** SHALL assert that `app.css` references both Inter (in the body chain) and Red Hat Display (in the six display chains)
- **AND** SHALL fail if either file references a family that the other does not

#### Scenario: Single PR introduces and removes the change

- **WHEN** a future maintainer removes Red Hat Display from the Google Fonts URL
- **THEN** the regression test SHALL fail because `app.css` still references `"Red Hat Display"` in the six display chains
- **AND** the maintainer SHALL update both files in the same commit to keep the contract intact
