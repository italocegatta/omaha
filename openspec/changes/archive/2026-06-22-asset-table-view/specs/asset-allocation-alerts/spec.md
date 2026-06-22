## Purpose

Persistent, sticky alert surface that reports deviation of per-class
target allocations from 100% and deviation of the portfolio-level
target allocation from 100%, with severity coloring. The user reads
this surface while editing assets to converge on a closed 100%
allocation.

## ADDED Requirements

### Requirement: Sticky alert card at top of Ativos section

The dashboard MUST render a sticky alert card at the top of the "Ativos"
section whenever any class's per-asset target sum differs from 100% by
more than 0.01, or when the sum of all class target percentages differs
from 100% by more than 0.01. The card MUST position-stick to the top
of the section so it remains visible while the user scrolls the asset
table. The card MUST display the portfolio-level deviation (total
percent and signed "Falta" or "Sobra" message) and a list of every
class whose per-asset sum is in deviation, each entry showing the
class name and its signed "Falta" or "Sobra" message. The card MUST
be absent from the DOM when every class and the portfolio sum to
100% within 0.01.

#### Scenario: Card appears with portfolio deviation on load

- **WHEN** the dashboard loads with at least one class whose per-asset
  sum differs from 100% by more than 0.01
- **THEN** the card (data-testid="asset-allocation-alert") is visible
- **AND** the card shows the portfolio total (data-testid="asset-allocation-alert-portfolio")
  formatted as "NN.NN%"
- **AND** the card lists the deviating class (data-testid="asset-allocation-alert-class")
  with the class name and "Falta X%" or "Sobra X%" message

#### Scenario: Card disappears after user converges allocation

- **WHEN** the user edits an asset's target_pct and the resulting
  per-class sums and portfolio total all equal 100% within 0.01
- **THEN** the card is removed from the DOM on the next reactive tick
- **AND** no placeholder or empty-state is shown in its place

#### Scenario: Card stays visible while user scrolls

- **WHEN** the user scrolls the asset table so that rows above the
  card's natural position are off-screen
- **THEN** the card remains pinned to the top of the "Ativos" section
- **AND** the card does not overlap the portfolio header above the
  section

### Requirement: Per-class alert badge on group header

Each per-class group header row in the asset table MUST display an
inline alert badge that reports the class's per-asset target sum
deviation. The badge MUST show "OK" when the per-asset sum is within
0.01 of 100, "Falta X%" or "Sobra X%" otherwise. The badge MUST
disappear (no DOM presence) when the per-asset sum equals 100% within
0.01. The badge MUST update reactively without a page reload when
the user edits any asset in that class.

#### Scenario: Badge shows deviation after edit

- **WHEN** the user edits an asset in class A and the resulting
  per-asset sum for class A differs from 100% by more than 0.01
- **THEN** the badge (data-testid="asset-group-header-alert") on
  class A's group header is visible
- **AND** the badge text is either "Falta X%" or "Sobra X%" with
  X being the integer-rounded absolute deviation (rounding half up)

#### Scenario: Badge hides on convergence

- **WHEN** the user edits an asset and the resulting per-asset sum
  for that class equals 100% within 0.01
- **THEN** the badge is removed from the DOM on the next reactive
  tick

### Requirement: Severity coloring

The sticky alert card and the per-class badge MUST use three severity
colors. A deviation of absolute value less than or equal to 0.01 MUST
use the OK color. A deviation of absolute value greater than 0.01 and
less than or equal to 5 MUST use the WARN color. A deviation of
absolute value greater than 5 MUST use the DANGER color. The OK color
applies to the per-class badge when the per-asset sum is within 0.01
of 100; the same severity tier applies to the portfolio total in the
sticky card.

#### Scenario: Small deviation uses warn color

- **WHEN** the portfolio total is 96% (deviation = 4)
- **THEN** the sticky card's portfolio entry uses the warn color
  token (--alert-warn)
- **AND** each per-class entry in the card uses the warn color token
  if its deviation is between 0.01 and 5 inclusive

#### Scenario: Large deviation uses danger color

- **WHEN** a class's per-asset sum is 130% (deviation = 30)
- **THEN** the per-class badge on that class's group header uses the
  danger color token (--alert-danger)
- **AND** the same class's entry in the sticky card uses the danger
  color token

#### Scenario: Zero deviation uses ok color

- **WHEN** the per-asset sum for a class equals 100% within 0.01
- **THEN** the per-class badge shows "OK" with the ok color token
  (--alert-ok)
- **AND** the sticky card does not list that class

### Requirement: Alert updates reactively from edits

Both the sticky alert card and the per-class badges MUST update on
the same tick as the user's edit without a page reload, using the
same Alpine reactivity that updates the asset row. The card MUST
reflect the post-edit per-class sums and portfolio total. The
edit MUST NOT block on a server-side sum gate (the server always
returns 200 on a valid per-row range).

#### Scenario: Edit in one class updates that class's badge and the card

- **WHEN** the user commits a new target_pct for an asset in class A
  via inline edit
- **THEN** class A's per-class badge updates on the same tick
- **AND** the sticky card's portfolio total updates on the same tick
- **AND** class A's entry in the sticky card updates or disappears
  based on the new per-class sum
- **AND** no network round-trip is required to recompute the alert
  state (the local model carries the new value)

#### Scenario: Off-100 edit is accepted and reported

- **WHEN** the user commits a new target_pct that pushes the class
  sum to 110%
- **THEN** the PATCH /api/assets/{id} call returns 200
- **AND** the asset's target_pct is updated on disk
- **AND** the per-class badge shows "Sobra X%"
- **AND** the sticky card shows the new portfolio deviation

### Requirement: Tolerance matches validator

The 0.01 tolerance used to decide whether a deviation is "zero" MUST
match `SUM_TOLERANCE` in `omaha.validators`. The 5% threshold for
the warn → danger transition is fixed and MUST NOT be user-tunable
in this version.

#### Scenario: Tolerance is consistent with validator constant

- **WHEN** the alert logic computes whether a class per-asset sum
  equals 100%
- **THEN** the tolerance used is the same value as `SUM_TOLERANCE`
  in `omaha.validators`
- **AND** a deviation of 0.009 is treated as zero
- **AND** a deviation of 0.02 is treated as non-zero
