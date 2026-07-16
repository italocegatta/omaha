## Purpose

Persistent, sticky alert surface that reports deviation of per-class
target allocations from 100% and deviation of the portfolio-level
target allocation from 100%, with severity coloring. The user reads
this surface while editing assets to converge on a closed 100%
allocation.

## Requirements

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

### Requirement: Per-class delta pill in class section header

The per-class delta MUST be relocated to a dedicated pill in the class
section header (`data-testid="class-delta-badge"`). The pill MUST show
"Falta X%" / "Sobra X%" based on the per-class asset-target sum
deviation. The pill MUST disappear (no DOM presence) when the
per-asset sum equals 100% within 0.01. The pill MUST update reactively
without a page reload when the user edits any asset in that class.
The pill MUST always show when off, regardless of whether the user is
mid-edit on an asset.

The "OK" wording is dropped: the pill is only rendered when the class
is off, so there is no need to render an explicit "OK" state. Visual
confirmation that the class is on target comes from the `Atual` pill
in the class section header using the `pct-current-pill--ok` modifier
(green colour).

#### Scenario: Pill shows deviation after edit

- **WHEN** the user edits an asset in class A and the resulting
  per-asset sum for class A differs from 100% by more than 0.01
- **THEN** the delta pill (`data-testid="class-delta-badge"`) in
  class A's section header is visible
- **AND** the pill text is either "Falta X%" or "Sobra X%" with
  X being the integer-rounded absolute deviation (rounding half up)
- **AND** the pill is in steady state (no inline edit in flight on
  any asset)

#### Scenario: Pill hides on convergence

- **WHEN** the user edits an asset and the resulting per-asset sum
  for that class equals 100% within 0.01
- **THEN** the delta pill is removed from the DOM on the next
  reactive tick

#### Scenario: Pill appears in steady state without inline edit

- **WHEN** the dashboard loads with a class whose per-asset sum
  differs from 100% by more than 0.01
- **AND** no asset in that class is currently being inline-edited
- **THEN** the delta pill is visible in the class section header
- **AND** the pill text matches the class's current Sobra/Falta
  deviation

### Requirement: Severity coloring

The sticky alert card and the per-class delta pill MUST use two
severity colors based on the absolute deviation. Deviations less
than or equal to 0.01 MUST use the OK color (the `Atual` pill
picks up the OK modifier and the delta pill is not rendered).
Deviations greater than 0.01 MUST use the DANGER color. The OK
color applies to the `Atual` pill when the per-asset sum is within
0.01 of 100; the DANGER color applies to the portfolio total in
the sticky card and to the delta pill when it is rendered for any
non-zero deviation. The intermediate WARN tier is removed — all
deviations above the tolerance threshold use a single red highlight.

#### Scenario: Deviation uses danger color

- **WHEN** the portfolio total is 96% (deviation = 4)
- **THEN** the sticky card's portfolio entry uses the danger color
  token (--alert-danger / --negative)
- **AND** each per-class delta pill in the class section header
  uses the danger colour token if its deviation is greater than 0.01

#### Scenario: Large deviation uses danger color

- **WHEN** a class's per-asset sum is 130% (deviation = 30)
- **THEN** the per-class delta pill in that class's section header
  uses the danger colour token (--alert-danger)
- **AND** the same class's entry in the sticky card uses the
  danger colour token

#### Scenario: Zero deviation uses ok color

- **WHEN** the per-asset sum for a class equals 100% within 0.01
- **THEN** the `Atual` pill in that class's section header uses
  the OK colour token (--alert-ok) via the
  `pct-current-pill--ok` modifier
- **AND** the per-class delta pill is not rendered
- **AND** the sticky card does not list that class

### Requirement: Alert updates reactively from edits

The sticky alert card and the per-class delta pills MUST update on
the same tick as the user's edit, without a page reload. They
MUST use the same Alpine reactivity that updates the asset row.
The card MUST reflect the post-edit per-class sums and portfolio
total. The edit MUST NOT block on a server-side sum gate (the
server always returns 200 on a valid per-row range).

#### Scenario: Edit in one class updates that class's pill and the card

- **WHEN** the user commits a new target_pct for an asset in class A
  via inline edit
- **THEN** class A's per-class delta pill in the section header
  updates on the same tick (or appears if it was hidden, or
  disappears if the sum converged)
- **AND** class A's `Atual` pill switches between
  `pct-current-pill--ok` and `pct-current-pill--off` based on the
  new deviation
- **AND** the sticky card's portfolio total updates on the same
  tick
- **AND** class A's entry in the sticky card updates or disappears
  based on the new per-class sum
- **AND** no network round-trip is required to recompute the alert
  state (the local model carries the new value)

#### Scenario: Off-100 edit is accepted and reported

- **WHEN** the user commits a new target_pct that pushes the class
  sum to 110%
- **THEN** the PATCH /api/assets/{id} call returns 200
- **AND** the asset's target_pct is updated on disk
- **AND** the per-class delta pill in the section header shows
  "Sobra X%"
- **AND** the sticky card shows the new portfolio deviation

### Requirement: Tolerance matches validator

The 0.01 tolerance used to decide whether a deviation is "zero" MUST
match `SUM_TOLERANCE` in `omaha.validators`. The single danger
threshold (any deviation above 0.01) is fixed and MUST NOT be
user-tunable in this version.

#### Scenario: Tolerance is consistent with validator constant

- **WHEN** the alert logic computes whether a class per-asset sum
  equals 100%
- **THEN** the tolerance used is the same value as `SUM_TOLERANCE`
  in `omaha.validators`
- **AND** a deviation of 0.009 is treated as zero
- **AND** a deviation of 0.02 is treated as non-zero
