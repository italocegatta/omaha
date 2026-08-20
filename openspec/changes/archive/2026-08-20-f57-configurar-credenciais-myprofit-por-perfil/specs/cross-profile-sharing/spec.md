## ADDED Requirements

### Requirement: Família is read-only for MyProfit synchronization

The existing Família read-only contract SHALL include MyProfit
synchronization. A synchronization attempt while the active profile is the
Família sentinel SHALL be rejected before credentials are resolved or any
external MyProfit operation begins. The rejection SHALL use the existing
family-read-only semantic and SHALL not expose secrets.

#### Scenario: Family aggregate cannot synchronize MyProfit

- **WHEN** active profile is Família
- **AND** a MyProfit synchronization is requested
- **THEN** the request is rejected as family read-only
- **AND** no credential lookup, browser launch, HTTP request, or file download
  occurs
