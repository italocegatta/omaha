# cross-profile-sharing Specification

## Purpose
TBD - created by archiving change direct-landing-with-header-profile-switcher. Update Purpose after archive.
## Requirements
### Requirement: Any logged-in user can view any profile's dashboard data

The system SHALL render the dashboard at `GET /` for whichever
profile `active_profile_id` points to, regardless of which
`User` owns that profile. Cross-profile viewing is the explicit
contract; the prior implicit isolation guarantee is removed.

#### Scenario: Ana views Italo's classes
- **WHEN** Ana is logged in, `active_profile_id` points to
  Italo's profile, and Italo's profile has at least one
  `AssetClass` row
- **THEN** `GET /` returns 200 with those `AssetClass` rows
  rendered in the dashboard's `class-summary` section

#### Scenario: Ana views Italo's positions
- **WHEN** Ana is logged in, `active_profile_id` points to
  Italo's profile, and Italo's `AssetClass` rows own `Asset` +
  `Position` rows
- **THEN** `GET /` returns 200 with the portfolio aggregates
  computed from Italo's rows (invested, current value, gain)
- **AND** the rendered asset table includes Italo's `Asset`
  rows with their position counts

#### Scenario: Ana can mutate Italo's portfolio
- **WHEN** Ana is logged in with `active_profile_id` pointing
  to Italo's profile
- **THEN** `POST /classes`, `POST /api/assets`, `DELETE
  /api/assets/{id}`, `PATCH /api/assets/{id}`, and
  `POST /import` succeed against Italo's profile (the
  per-profile ownership gates in `routes/classes.py`,
  `routes/assets.py`, `routes/imports.py` are loosened to
  "must belong to the active profile" only)

### Requirement: Cross-profile previews and assets no longer 404 by ownership

The system SHALL NOT raise 404 on the basis of viewer-vs-owner
mismatch. API endpoints that previously raised 404 when the
active session pointed at a profile different from the
resource's owner MUST accept the operation when the resource
belongs to the active profile (regardless of viewer).

#### Scenario: PATCH /api/assets/{id} for active-profile asset
- **WHEN** Ana is logged in, `active_profile_id` points to
  Italo's profile, and the asset id belongs to a class under
  Italo's profile
- **THEN** the PATCH returns 200 with `{"id", "target_pct"}`
  (no 404)

#### Scenario: POST /import commits against the active profile
- **WHEN** Ana is logged in with `active_profile_id` pointing
  to Italo's profile and posts a CSV preview commit
- **THEN** the committed `Position` rows land under Italo's
  profile (not Ana's), regardless of the viewer

### Requirement: BDD profile_sharing feature asserts cross-profile visibility

The BDD suite SHALL ship a `profile_sharing.feature` (renamed
from `profile_isolation.feature`) whose scenarios assert the
new contract: any logged-in user can switch to another
profile's dashboard and see that profile's classes and
positions.

#### Scenario: Ana sees Italo's seeded classes after switching
- **WHEN** Ana logs in, switches to Italo's profile via the
  header chip, and Italo's profile has at least one seeded
  class
- **THEN** the dashboard renders Italo's class summary (not
  Ana's empty state)

#### Scenario: Italo sees Ana's seeded classes after switching
- **WHEN** Italo logs in, switches to Ana's profile via the
  header chip, and Ana's profile has at least one seeded
  class
- **THEN** the dashboard renders Ana's class summary (not
  Italo's empty state)
