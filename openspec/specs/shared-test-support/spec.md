# shared-test-support Specification

## Purpose

Centralizar helpers de bootstrap, cleanup de DB, lifecycle de browser e setup do fluxo de import para que `tests/conftest.py`, `tests/e2e/conftest.py`, `tests/bdd/conftest.py`, `tests/visual/conftest.py` e `tests/e2e/test_import_user_journey.py` reutilizem a mesma implementação sem mudar comportamento da suíte.

## Requirements

### Requirement: Shared DB cleanup primitives are centralized

The system SHALL provide shared cleanup helpers under `tests/support/` (or equivalent support package) that implement the current DB wipe semantics used by the suite conftests and by `scripts/seed_from_csv/modes.py`.

The helpers SHALL:

- keep existing SQLite `PRAGMA busy_timeout = 3000` behavior where used
- short-circuit when DB or profile is absent
- delete positions before assets, assets before asset_classes, and import_previews in the same cleanup flow
- preserve orphan cleanup used by seed reset where relevant

#### Scenario: cleanup helper reused across suites

- **WHEN** e2e, bdd, or visual imports the shared cleanup helper for a populated profile
- **THEN** the same rows are deleted as before
- **AND** no orphan rows remain
- **AND** missing DB or profile still returns without exception

### Requirement: Shared browser/bootstrap primitives are centralized

The system SHALL provide shared helpers under `tests/support/` for browser and uvicorn bootstrap concerns used by `tests/e2e/conftest.py` and `tests/visual/conftest.py`, including chromium resolution, port readiness, setup env composition, and uvicorn shutdown.

Existing host, port, launch args, and browser-selection order SHALL remain unchanged.

#### Scenario: e2e and visual launch through same helper

- **WHEN** either suite launches browser/server via shared helper
- **THEN** chromium selection still honors the current path order
- **AND** launch still uses the same headless/no-sandbox args
- **AND** ports and env remain unchanged

### Requirement: Import journey setup helpers are reusable

The system SHALL provide shared helpers for login, class creation, asset seeding, and debug-dump support used by `tests/e2e/test_import_user_journey.py`.

The test module MAY keep only scenario orchestration and final assertions.

#### Scenario: import journey still builds canonical setup

- **WHEN** the import journey test runs
- **THEN** shared helper still logs in as Italo, creates 3 classes, seeds 43 assets, and reaches same 48-row end state
- **AND** the file-level assertions remain the source of truth
