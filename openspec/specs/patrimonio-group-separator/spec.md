# patrimonio-group-separator

## Purpose

Visual separator between Classe and Carteira group headers in the patrimônio table.

## Requirements

### Requirement: Visual separator between Classe and Carteira group headers
The patrimônio table group headers "Classe" (colspan=3) and "Carteira" (colspan=3) SHALL have a visible vertical separator between them, breaking the continuous `border-bottom` line into two distinct segments.

#### Scenario: Classe group header has right border
- **WHEN** the patrimônio page renders the group header row
- **THEN** the `<th>` for "Classe" SHALL have a `border-right` that visually separates it from "Carteira"

#### Scenario: Carteira group header has left border
- **WHEN** the patrimônio page renders the group header row
- **THEN** the `<th>` for "Carteira" SHALL have a `border-left` that visually separates it from "Classe"

#### Scenario: No structural change to table
- **WHEN** the separator is applied
- **THEN** the table column count, colspan values, and row structure SHALL remain unchanged
