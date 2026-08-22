## Why

`src/omaha/main.py::_prune_snapshots_on_startup` imports
`omaha.logging_config.get_logger` when startup pruning deletes snapshots, but
`logging_config.py` currently exports no such symbol. This breaks app/E2E
startup on the deletion path and blocks F60 browser validation; R42 restores
the smallest compatible logging boundary without broadening logging scope.

## What Changes

- Restore `omaha.logging_config.get_logger(name)` as a minimal compatible
  logger-factory contract for existing callers.
- Preserve `JsonFormatter`, `configure_logging`, logger configuration,
  propagation, and snapshot-prune behavior.
- Add focused regression evidence for logger lookup and startup prune logging;
  use existing snapshot tests where they prove the boundary.
- Change `src/omaha/main.py` only if required to preserve compatibility after
  restoring the logging contract.

## Capabilities

### New Capabilities

- `logging-contract`: expose minimal `get_logger(name)` compatibility and keep
  snapshot-prune startup logging callable.

### Modified Capabilities

- None.

## Impact

- Runtime: `src/omaha/logging_config.py`; optionally
  `src/omaha/main.py` only for indispensable compatibility.
- Tests: `tests/test_logging.py` and `tests/test_db_snapshot.py` only as
  needed for focused unit/startup regression evidence.
- No API, database schema, seed, F60 UI, F59 job, connector, or test-runner
  behavior changes.
