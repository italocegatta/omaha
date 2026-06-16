## Why

The project has 19 taskipy tasks covering the core dev loop (serve, test, lint, db, install), but several common operations still require ad-hoc commands. Docker dev/prod workflows, DB migration inspection, test coverage, dependency updates, and onboarding (`SECRET_KEY` generation) all lack shortcut tasks. Every uncaptured command is a context switch or a README re-read.

## What Changes

Add ~13 taskipy tasks to `pyproject.toml` grouped into 5 areas:

- **DB inspection** — `db-current`, `db-history`, `db-downgrade` to complete the migration loop
- **Docker dev** — `docker-build`, `docker-up`, `docker-down` for the dev compose stack
- **Docker prod** — `prod-up`, `prod-down`, `prod-logs`, `prod-rebuild` for the production stack
- **Code quality** — `coverage` (requires adding `pytest-cov` to dev deps), `update` for lockfile upgrades
- **Onboarding** — `secret-key` for generating a random SECRET_KEY

## Capabilities

### New Capabilities
- `dev-tasks`: Taskipy shortcut tasks for development workflow automation — covering Docker, database operations, code quality, and project onboarding.

### Modified Capabilities
<!-- No existing spec changes — this is pure dev-infrastructure -->

## Impact

- **`pyproject.toml`**: ~13 new `[tool.taskipy.tasks]` entries
- **`pyproject.toml` dev deps**: add `pytest-cov`
- **`README.md`**: update the task table with new entries
- **No breaking changes** — existing tasks keep their names and behavior
