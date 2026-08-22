## ADDED Requirements

### Requirement: Connector SHALL expose an offline-testable CSV boundary

The system SHALL provide a narrow `MyProfitConnector` interface whose position
download operation accepts an active profile boundary and returns a result with
sanitized filename and CSV bytes. The connector SHALL not require a FastAPI
request, database session, ORM row mutation, import preview, or UI state.

#### Scenario: Connector returns downloaded CSV in memory

- **WHEN** a real profile has valid synthetic credentials and fake browser
  objects produce a download
- **THEN** connector returns suggested filename reduced to its basename and
  downloaded bytes
- **AND** no database, parser, import route, or preview operation is called

### Requirement: Playwright connector SHALL use direct StockDetail navigation

The concrete connector SHALL use `launch_persistent_context` with a fresh
temporary profile and downloads enabled. After login it SHALL navigate directly
to `https://myprofitweb.com/App/StockDetail.aspx`; no destination environment
variable, selector, profile-dependent URL, or modulator SHALL be accepted.
The export flow SHALL open `button[aria-label="Export"]`, select exact `CSV`,
and capture the selection inside Playwright `expect_download`.

#### Scenario: Authenticated StockDetail export is captured

- **WHEN** fake page navigation and login controls succeed
- **AND** connector reaches the fixed StockDetail URL
- **AND** Export → CSV emits a Playwright download
- **THEN** connector returns download bytes
- **AND** the launcher was created only after profile credentials passed guard

### Requirement: Optional 2FA setup defer SHALL fail closed for real challenges

After submitting login, connector SHALL perform a bounded probe for a visible
optional setup control named `Mais tarde` or `Later`. If present, it SHALL click
that control once and continue. If absent, it SHALL continue only after the
authenticated page state is confirmed. Connector SHALL not automate or bypass
an actual second-factor challenge, CAPTCHA, or enrollment flow; an unconfirmed
state SHALL return a sanitized `two_factor` or `login` failure.

#### Scenario: Optional setup prompt is deferred

- **WHEN** visible `Mais tarde` or `Later` appears after successful login
- **THEN** connector clicks it once
- **AND** navigation continues to fixed StockDetail URL

#### Scenario: Optional setup prompt is absent

- **WHEN** no optional setup prompt appears within its bounded probe
- **AND** authenticated state is confirmed
- **THEN** connector continues without clicking a missing control

#### Scenario: Actual second factor is not bypassed

- **WHEN** login leaves an unconfirmed second-factor or CAPTCHA state
- **THEN** connector stops with sanitized operational error
- **AND** it does not navigate to export or download a file

### Requirement: Connector SHALL bound failures and clean resources

Connector SHALL apply explicit bounded timeouts to login/page navigation,
optional prompt probe, Export control, CSV option, and download capture. It
SHALL close browser resources and remove temporary profile/download artifacts in
success and failure paths. Operational errors SHALL identify only a sanitized
stage/code and SHALL never include email, password, raw Playwright exception,
page content, screenshot, trace, or CSV bytes.

#### Scenario: Timeout becomes sanitized stage error

- **WHEN** login, navigation, export, or download exceeds its configured
  timeout
- **THEN** connector raises a stage-labelled sanitized error
- **AND** context closes and temporary artifacts are removed

#### Scenario: Successful download leaves no temporary artifact

- **WHEN** connector returns CSV bytes successfully
- **THEN** browser context closes
- **AND** temporary profile and download directory are removed

### Requirement: Connector tests SHALL remain fake and offline

Connector tests SHALL use fake launcher, context, page, locator, and download
objects. Default unit/test task execution SHALL never launch a browser, access
`myprofitweb.com`, load `.env` credentials, or touch production/dev portfolio
databases. Família and missing/placeholder credential tests SHALL prove zero
launcher calls.

#### Scenario: Offline fake proves full connector flow

- **WHEN** unit test doubles model login, optional prompt, fixed navigation, and
  CSV download
- **THEN** flow and cleanup assertions pass entirely in process
- **AND** external request and database mutation spies remain unused
