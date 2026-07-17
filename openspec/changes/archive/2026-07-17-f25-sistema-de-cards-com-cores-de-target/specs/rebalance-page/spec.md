## ADDED Requirements

### Requirement: Rebalance class summary cards SHALL share one card family with target-state accents

The system SHALL render rebalance class summary cards as one consistent card family: same shell, same internal hierarchy, same spacing rhythm, and same typography treatment across all classes. Cards SHALL not rely on a repeated kicker label such as `CLASSE`; the class name is the primary header text.

Cards SHALL encode target relationship with color cues: classes above target SHALL use positive/green accenting, and classes below target SHALL use negative/red accenting. Visual differences between cards SHALL come from state accenting, not from changing the underlying card mold.

#### Scenario: All class cards share the same family structure

- **WHEN** the rebalance page renders class summary cards
- **THEN** each card uses the same shell, header hierarchy, and metric layout
- **AND** no card introduces a different structural mold for a different state

#### Scenario: Above-target class renders with positive accent

- **WHEN** a class is above its target allocation
- **THEN** its summary card renders with positive/green accenting
- **AND** the card remains part of the shared card family

#### Scenario: Below-target class renders with negative accent

- **WHEN** a class is below its target allocation
- **THEN** its summary card renders with negative/red accenting
- **AND** the card remains part of the shared card family

#### Scenario: Card header does not repeat kicker label

- **WHEN** a class summary card renders
- **THEN** the header shows the class name as primary text
- **AND** the label `CLASSE` does not render in the card header
