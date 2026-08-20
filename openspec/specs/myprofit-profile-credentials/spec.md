# myprofit-profile-credentials Specification

## Purpose

Define profile-isolated, secret-safe MyProfit configuration before connector work.

## Requirements

### Requirement: MyProfit configuration SHALL be isolated by real profile

The system SHALL expose profile-scoped MyProfit configuration for the two real
profiles only. It SHALL load separate email, password, and destination values
from `MYPROFIT_ITALO_EMAIL`, `MYPROFIT_ITALO_PASSWORD`,
`MYPROFIT_ITALO_DESTINATION` and the corresponding `MYPROFIT_ANA_*` variables.
The resolver SHALL select configuration from the active real profile and SHALL
not use one profile's values as fallback for the other.

#### Scenario: Italo resolves Italo configuration

- **WHEN** active profile is real Italo
- **AND** synthetic Italo environment values are configured
- **THEN** resolver returns Italo email, password, and destination
- **AND** no Ana environment value is read as fallback

#### Scenario: Ana resolves Ana configuration

- **WHEN** active profile is real Ana
- **AND** synthetic Ana environment values are configured
- **THEN** resolver returns Ana email, password, and destination
- **AND** no Italo environment value is read as fallback

#### Scenario: Non-real profile has no MyProfit destination

- **WHEN** resolver receives Família or any profile not mapped to Italo or Ana
- **THEN** it rejects the request with a stable, non-secret domain error
- **AND** it does not return credentials or destination

### Requirement: Família SHALL be blocked before synchronization

Any MyProfit synchronization boundary SHALL reject Família before resolving or
using credentials and before opening a network, browser, or external-client
connection. The rejection SHALL preserve existing Família read-only semantics
and SHALL contain no credential, environment value, or destination detail.

#### Scenario: Família synchronization is rejected

- **WHEN** active profile is the Família sentinel
- **AND** a caller asks for MyProfit synchronization configuration
- **THEN** the call fails with the stable family-read-only reason
- **AND** no MyProfit client or network operation is invoked

### Requirement: MyProfit secrets SHALL never be exposed

Password values SHALL use a secret-safe representation at configuration
boundaries. `repr`, validation errors, application logs, and safe operational
errors SHALL omit password and credential values; errors SHALL identify only a
field or sanitized reason. Tests and documentation SHALL contain synthetic
values or placeholders only, never real credentials.

#### Scenario: Secret sanitization survives diagnostics

- **WHEN** configuration is loaded with synthetic credential values
- **THEN** rendered configuration diagnostics and resolver errors contain no
  password value
- **AND** the safe error contains no complete email, destination, or raw env
  payload

### Requirement: Configuration tests SHALL remain offline

Configuration tests SHALL inject false values through isolated environment
overrides and SHALL not call MyProfit, Playwright, HTTP clients, or live
network endpoints. Placeholder values in `.env.example` SHALL be demonstrably
non-production and SHALL not be interpreted as proof of live connectivity.

#### Scenario: Fake values exercise resolver without external access

- **WHEN** a test sets synthetic Italo or Ana environment values
- **THEN** resolver behavior is verified entirely in process
- **AND** test doubles observe zero external calls
