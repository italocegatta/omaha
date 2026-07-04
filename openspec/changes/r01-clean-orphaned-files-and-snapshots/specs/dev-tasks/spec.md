## ADDED Requirements

### Requirement: Housekeeping purge of debug artefacts
Debug artefacts (`data/probe*.db`, `data/test_*.db`, `pytestdebug.log`, `data/seed/fixtures/auto_class.csv`) SHALL be candidate for deletion during housekeeping slices. The canonical live database `data/portfolio.db` SHALL remain untouched. The `.gitignore` rules SHALL continue to cover these patterns so they do not re-enter the working tree after `git clean`.

#### Scenario: Debug artefacts are gitignored
- **WHEN** developer inspects `.gitignore`
- **THEN** `data/*`, `*.log` rules keep debug artefacts out of the working tree

#### Scenario: Live portfolio DB is preserved
- **WHEN** housekeeping slice runs purge
- **THEN** `data/portfolio.db` is preserved (gitignored but excluded from the purge path)