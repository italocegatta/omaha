## ADDED Requirements

### Requirement: Família SHALL be read-only before MyProfit synchronization job access

The existing Família read-only contract SHALL include the asynchronous MyProfit
job boundary. Job start and job polling while the active profile is the Família
sentinel SHALL be rejected before credential resolution, connector/browser
access, network navigation, temporary-file creation, or access to another
profile's job. The rejection SHALL use the existing
`household_read_only` semantic and SHALL contain no secret or job detail.

#### Scenario: Família cannot create or inspect a synchronization job

- **WHEN** active profile is Família
- **AND** caller sends synchronization start or polling request
- **THEN** request is rejected with stable `household_read_only` semantics
- **AND** no worker is scheduled, no job is inspected across profiles, and no
  filesystem path is accessed
