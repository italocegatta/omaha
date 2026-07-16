## MODIFIED Requirements

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
