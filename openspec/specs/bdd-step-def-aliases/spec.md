# bdd-step-def-aliases Specification

## Purpose

Capture the contract for the alias chain that the BDD step def
`clico em "{label}"` (in `tests/bdd/step_defs/common_steps.py`)
consults before its default text/testid candidates. The chain
exists so that label drift between feature Gherkin and production
UI, introduced by F-slices that re-organise affordances (F02
sidebar removal being the canonical example), does not silently
fail the BDD suite. Aliases are explicit, documented, and
version-controlled; adding a new alias is a deliberate operation
tied to a specific F-slice that justifies the drift.

## Requirements

### Requirement: Step def consults an explicit alias map before default candidates

The system SHALL consult an explicit alias map `STEP_CLICK_ALIASES`
(a `dict[str, tuple[str, ...]]`) before the default candidate
sequence in the BDD step def `clico em "{label}"`. The default
candidate sequence is `button:has-text`, then
`[data-testid="{label}"]`, then `a:has-text`. The alias map SHALL
be declared at the top of `tests/bdd/step_defs/common_steps.py`
above the `click_button` function definition.

For each label key present in the map, the step def SHALL try
the CSS selectors in the tuple order, applying the same
two-phase visibility filter used for the default candidates
(`wait_for(state="visible", timeout=5000)` followed by
`locator("visible=true")`). The first selector that resolves to
a visible, clickable element wins. The step def SHALL then fall
through to the default candidate sequence if and only if no alias
selector matches.

For labels not present in the map, the step def SHALL behave
identically to the pre-T05 implementation (default candidate
sequence only).

#### Scenario: + Nova classe resolves to empty-state-create-class testid

- **WHEN** a Gherkin step reads `clico em "+ Nova classe"`
- **AND** the patrimonio page is rendered with zero classes for
  the active profile
- **THEN** the step def consults `STEP_CLICK_ALIASES["+ Nova classe"]`
- **AND** the first selector `[data-testid="empty-state-create-class"]`
  resolves to a visible button
- **AND** the step def clicks that button (opening the
  new-class modal)
- **AND** the default candidate sequence is NOT consulted

#### Scenario: Aliases are documented inline with the originating F-slice

- **WHEN** a new entry is added to `STEP_CLICK_ALIASES`
- **THEN** the entry SHALL carry an inline comment naming the
  F-slice (or R/T-slice) that introduced the drift
- **AND** the entry SHALL map the pre-drift label to the
  post-drift testid (not text) so the chain survives future
  copy edits

#### Scenario: Unmapped labels fall through to default candidates

- **WHEN** a Gherkin step reads `clico em "Salvar"` (a label
  NOT present in `STEP_CLICK_ALIASES`)
- **THEN** the step def skips the alias map entirely
- **AND** the default candidate sequence resolves
  `button:has-text("Salvar")` against the in-modal submit
- **AND** behavior is byte-identical to the pre-T05 implementation
