## ADDED Requirements

### Requirement: E2E fixed databases are explicitly ephemeral and recreatable

The E2E session fixtures SHALL recreate only their exact registered test DB
paths before spawning their matching uvicorn child. `data/test_e2e.db` is an
ephemeral/recreatable test target; its already-declared short-TTL companion is
governed by the same exact E2E allowlist. Recreation SHALL preserve one shared
path/inode for test process and uvicorn after launch, SHALL emit a
run/lane-linked receipt with `adopted: false`, and SHALL never target
`data/portfolio.db`.

#### Scenario: Existing E2E DB is safely recreated

- **WHEN** session fixture starts with an existing regular
  `data/test_e2e.db`
- **THEN** it removes only that exact E2E file, records the disposition, and
  starts uvicorn with the same path
- **AND** migrations/seed create the fresh schema through the existing startup
  flow

#### Scenario: E2E DB path is protected by type and identity checks

- **WHEN** the configured path is a symlink, directory, outside `data/`,
  `data/portfolio.db`, or already associated with a foreign active server
- **THEN** fixture fails before removal or URL yield with actionable evidence
- **AND** it preserves the path and foreign server

#### Scenario: Recreated DB remains shared through fixture lifetime

- **WHEN** E2E fixture yields its URL after recreation
- **THEN** test process and uvicorn use the same exact path and inode until
  teardown
- **AND** server teardown records child identity, graceful stop/escalation,
  port release, and any residue without deleting unrelated DBs
