## ADDED Requirements

### Requirement: Current product acceptance delimits mobile scope without masking coverage

The current product acceptance contract SHALL state that Omaha has no current
mobile use case and that mobile browser tests are not a current acceptance
requirement. Desktop/browser behavior and existing browser acceptance SHALL
remain mandatory. This boundary SHALL NOT remove, disable, skip, xfail, retry,
or make non-runnable any versioned mobile test, lane, command, or coverage, and
SHALL NOT turn a mobile failure into a false pass or hide a desktop/browser
regression.

#### Scenario: Current acceptance uses desktop/browser boundary

- **WHEN** an operator evaluates current product acceptance
- **THEN** desktop/browser behavior remains required
- **AND** mobile browser tests are identified as outside the current product
  acceptance requirement
- **AND** the contract does not claim mobile CSS, layout, or interaction works

#### Scenario: Versioned mobile coverage remains executable

- **WHEN** a versioned mobile browser or visual test exists
- **THEN** it remains discoverable and runnable through its existing command or
  lane
- **AND** no `skip`, `skipif`, `xfail`, retry, deletion, lane removal, or
  coverage reduction is introduced to represent the product boundary

#### Scenario: Desktop/browser regression remains visible

- **WHEN** a desktop/browser acceptance test fails
- **THEN** current delivery acceptance remains blocked by that failure
- **AND** the mobile scope statement does not mask, reclassify, or suppress it
