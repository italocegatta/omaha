## ADDED Requirements

### Requirement: README documents the post-F-slice navigation

The `README.md` SHALL describe the four top-level tabs
(`/patrimonio`, `/rebalanceamento`, `/rentabilidade`,
`/proventos`) introduced by F02 and SHALL NOT reference the legacy
`/dashboard` route or the removed sidebar.

#### Scenario: Quick start references the new routes

- **WHEN** an operator reads the **Testing the app** section
- **THEN** the dashboard URL is documented as
  `$(bash scripts/print_lan_url.sh)/patrimonio` and the section
  mentions the four-tab top-level nav

#### Scenario: Legacy sidebar references are absent

- **WHEN** an operator greps `README.md` for `sidebar` or
  `/dashboard`
- **THEN** no hits remain (the sidebar was removed in F02 and the
  route was renamed to `/patrimonio`)

### Requirement: README reflects the Família sentinel profile

The `README.md` SHALL document the Família aggregate profile
option in the header profile-switcher (peer of Italo / Ana,
introduced by F07) and SHALL NOT reference the removed
`Italo RF2` fixture or the `?view=household` toggle.

#### Scenario: Família profile option is documented

- **WHEN** an operator reads the **Testing the app** section
- **THEN** the profile-switcher is described as offering
  `Italo` / `Ana` / `Família` (aggregate view)

#### Scenario: Removed Italo RF2 fixture is not referenced

- **WHEN** an operator greps `README.md` for `Italo RF2`
- **THEN** no hits remain (the fixture was retired by F07)

### Requirement: README points to the OpenSpec project structure

The `README.md` SHALL direct readers to `openspec/` (PRD,
roadmap, specs, changes) as the source-of-truth for project
specifications, and SHALL NOT reference the legacy `.gsd/`
directory.

#### Scenario: Project specs section points to openspec

- **WHEN** an operator reads the **Project specs** section
- **THEN** the bullet list references `openspec/PRD.md`,
  `openspec/roadmap.md`, `openspec/specs/`, and
  `openspec/changes/` (and only these)

#### Scenario: Legacy .gsd references are absent

- **WHEN** an operator greps `README.md` for `.gsd` or
  `STATE.md` / `ROADMAP.md` (legacy paths)
- **THEN** no hits remain

### Requirement: README documents the dark mode theme

The `README.md` SHALL mention that the UI ships in a dark
warm-neutral palette (per F05) and SHALL NOT reference the
off-white register as the current theme.

#### Scenario: Visual description matches the current palette

- **WHEN** an operator reads the intro paragraph under `# Omaha`
- **THEN** the description references the dark warm-neutral
  palette (or omits any specific palette claim) and does not
  describe an off-white / light register as current

### Requirement: README defers the backup and TLS renewal sections to I01 / I02

The `README.md` SHALL NOT contain a host-cron block for backups
(superseded by the I01 scheduler) and SHALL NOT contain the
manual `certbot certonly` step in **Production deploy**
(superseded by the I02 scheduler). Both sections are owned by
the respective I-slice change.

#### Scenario: Host-cron block is absent

- **WHEN** an operator greps `README.md` for `cron.d` or
  `/etc/cron.d/omaha-backup`
- **THEN** no hits remain (I01 owns the backup cadence section)

#### Scenario: Manual certbot step is absent from Production deploy

- **WHEN** an operator reads the **Production deploy** section
- **THEN** the manual `certbot certonly --standalone` step is
  not present (I02 owns the TLS renewal section)

### Requirement: README task table includes current development tasks

The `README.md` task table SHALL list the currently active
development tasks, including `test-bdd`, `test-integration`,
and `mutation` (introduced by T03).

#### Scenario: New test tasks are documented

- **WHEN** an operator runs `uv run task --list`
- **THEN** every task documented in the README task table
  resolves to an existing taskipy entry, and the table
  explicitly mentions `test-bdd`, `test-integration`, and
  `mutation`