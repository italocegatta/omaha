# Logging Contract

## Purpose

Preserve named logger compatibility and startup snapshot-prune logging.

## Requirements

### Requirement: Public logger factory preserves standard logger compatibility

The system SHALL expose `omaha.logging_config.get_logger(name)` as a thin
logger factory that returns the standard-library logger identified by `name`.
The returned logger MUST retain normal `logging.Logger` methods, hierarchy,
identity, and compatibility with handlers and levels installed by
`configure_logging`.

#### Scenario: Named logger is returned

- **WHEN** a caller invokes `get_logger("omaha.some_module")`
- **THEN** the result is the same logger object returned by
  `logging.getLogger("omaha.some_module")`
- **AND** its name is `omaha.some_module`

#### Scenario: Logger participates in configured output

- **WHEN** `configure_logging(level="INFO", fmt="json")` has configured the
  Omaha logger hierarchy and a caller emits an INFO message through
  `get_logger("omaha.some_module")`
- **THEN** the message is handled by the existing configured logging surface
- **AND** no additional handler or formatter is installed by `get_logger`

### Requirement: Snapshot-prune startup can emit deletion log

The system SHALL allow `omaha.main._prune_snapshots_on_startup` to complete its
positive-deletion logging branch when snapshot pruning returns one or more
deleted files. It SHALL use the restored logger factory for the existing INFO
event and SHALL preserve zero-deletion no-op behavior and existing prune error
propagation.

#### Scenario: Startup prune logs deleted count

- **WHEN** startup snapshot pruning returns a positive deleted-file count
- **THEN** `_prune_snapshots_on_startup` emits an INFO event containing the
  deleted count and destination directory
- **AND** it does not fail because `get_logger` is unavailable

#### Scenario: Startup prune with no deletions remains quiet

- **WHEN** startup snapshot pruning returns zero deleted files
- **THEN** `_prune_snapshots_on_startup` emits no prune INFO event
- **AND** it does not attempt logger lookup for that branch
