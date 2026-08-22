## ADDED Requirements

### Requirement: Família is read-only before MyProfit connector access

The existing Família read-only contract SHALL include the MyProfit connector.
Any connector request while the active profile is the Família sentinel SHALL
be rejected before credential resolution, browser/context construction, network
navigation, or file download. The rejection SHALL use the existing
`household_read_only` semantic and SHALL contain no credential, environment,
page, or download detail.

#### Scenario: Family aggregate cannot invoke connector

- **WHEN** active profile is Família
- **AND** a caller requests a MyProfit position CSV
- **THEN** the request fails with the stable family-read-only reason
- **AND** credential lookup, browser launch, HTTP navigation, and download
  spies observe zero calls
