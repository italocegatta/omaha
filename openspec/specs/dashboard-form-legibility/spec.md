# Capability: dashboard-form-legibility

## Purpose

Ensure dashboard form inputs and modals are legible and accessible on dark theme with proper contrast, alignment, and absence of unnecessary chrome.

## Requirements

### Requirement: Add-asset modal SHALL use a slightly wider desktop surface and clearer input treatment

The system SHALL render the add-asset modal with a desktop max-width of 528px and a mobile max-width of 100%. The modal's input fields SHALL use a higher-contrast surface treatment than the surrounding shell so labels and values remain easy to scan on the dark theme.

#### Scenario: Desktop modal gets extra width

- **WHEN** the user opens add-asset modal on desktop viewport
- **THEN** panel max-width is 528px
- **AND** fields have enough horizontal room to read labels and enter values without crowding

#### Scenario: Mobile modal stays full-width

- **WHEN** the user opens add-asset modal on mobile viewport
- **THEN** panel uses full available width
- **AND** fields still render with the same contrast treatment

### Requirement: Numeric inputs in add-asset modal SHALL render without spinner chrome

The system SHALL render numeric inputs inside add-asset modal without browser spinner chrome. Keyboard step behavior SHALL remain available through the input's native `step` handling.

#### Scenario: Modal numeric field has no steppers

- **WHEN** the add-asset modal renders a numeric input
- **THEN** no native spinner controls are visible
- **AND** arrow-key stepping still changes value

### Requirement: Header profile switcher SHALL keep option text left-aligned and legible

The system SHALL render the header profile switcher with left-aligned option text and selected value. The `Família` option SHALL remain visually distinct only through readable text and contrast, not centering or extra ornament.

#### Scenario: Família option reads as normal selectable option

- **WHEN** the authenticated header renders profile switcher
- **THEN** option text is left-aligned
- **AND** `Família` is readable at same hierarchy as other options
- **AND** no centering or chip-style treatment is introduced
