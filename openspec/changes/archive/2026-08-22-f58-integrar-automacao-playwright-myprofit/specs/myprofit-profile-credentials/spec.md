## MODIFIED Requirements

### Requirement: MyProfit configuration SHALL be isolated by real profile

The system SHALL expose profile-scoped MyProfit configuration for the two real
profiles only. It SHALL load separate email and password values from
`MYPROFIT_ITALO_EMAIL`, `MYPROFIT_ITALO_PASSWORD` and the corresponding
`MYPROFIT_ANA_*` variables. No destination, selector, modulator, or
profile-dependent URL variable SHALL be part of this configuration. The
resolver SHALL select configuration from the active real profile and SHALL not
use one profile's values as fallback for the other.

#### Scenario: Italo resolves Italo credentials

- **WHEN** active profile is real Italo
- **AND** synthetic Italo email and password environment values are configured
- **THEN** resolver returns Italo email and password
- **AND** no Ana environment value is read as fallback
- **AND** the resolved configuration has no destination property

#### Scenario: Ana resolves Ana credentials

- **WHEN** active profile is real Ana
- **AND** synthetic Ana email and password environment values are configured
- **THEN** resolver returns Ana email and password
- **AND** no Italo environment value is read as fallback
- **AND** the resolved configuration has no destination property

#### Scenario: Destination variables are ignored and not required

- **WHEN** environment contains legacy `MYPROFIT_ITALO_DESTINATION` or
  `MYPROFIT_ANA_DESTINATION` values
- **THEN** settings and resolver do not read, validate, or return those values
- **AND** complete email/password configuration resolves without destination

#### Scenario: Non-real profile has no MyProfit credentials

- **WHEN** resolver receives Família or any profile not mapped to Italo or Ana
- **THEN** it rejects the request with a stable, non-secret domain error
- **AND** it does not return credentials or any routing value

### Requirement: MyProfit secrets SHALL never be exposed

Password values SHALL use a secret-safe representation at configuration and
connector boundaries. `repr`, validation errors, application logs, and safe
operational errors SHALL omit email and password values; errors SHALL identify
only a field or sanitized reason. Tests and documentation SHALL contain
synthetic values or placeholders only, never real credentials.

#### Scenario: Credential sanitization survives diagnostics

- **WHEN** configuration or connector execution uses synthetic email and
  password values
- **THEN** rendered configuration diagnostics and connector errors contain no
  email or password value
- **AND** no raw environment payload, page content, or downloaded CSV bytes are
  included

### Requirement: Configuration tests SHALL remain offline

Configuration tests SHALL inject false values through isolated environment
overrides and SHALL not call MyProfit, Playwright, HTTP clients, or live
network endpoints. `.env.example` SHALL contain only distinct non-production
email/password placeholders and SHALL not be interpreted as proof of live
connectivity.

#### Scenario: Fake credentials exercise resolver without external access

- **WHEN** a test sets synthetic Italo or Ana email/password values
- **THEN** resolver behavior is verified entirely in process
- **AND** test doubles observe zero external calls
