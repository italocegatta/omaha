## Context

The project uses `taskipy` to wrap common dev commands in `pyproject.toml` under `[tool.taskipy.tasks]`. Currently 19 tasks exist covering server, tests, lint, database, install, backup, and cleanup. Several daily ops still lack shortcuts — Docker dev/prod workflows, migration inspection, test coverage, dependency updates, and secret generation.

All new tasks follow the existing conventions:
- Run via `uv run task <name>`
- Defined in `pyproject.toml` under `[tool.taskipy.tasks]`
- Documented in `README.md` task table

## Goals / Non-Goals

**Goals:**
- Complete the DB migration workflow loop (current, history, downgrade)
- Add Docker dev shortcuts (build, up, down)
- Add Docker prod shortcuts (up, down, logs, rebuild)
- Add code quality tasks (coverage, update)
- Add onboarding task (secret-key)
- Document all new tasks in README.md

**Non-Goals:**
- Change existing task names or behavior
- Add CI/CD pipeline tasks (that's GitHub Actions territory)
- Add task categories that require new dependencies beyond `pytest-cov`

## Decisions

1. **DB tasks use raw `alembic` CLI** — matches existing `db-migrate`/`db-revision` style. No wrapper script needed.
2. **Docker prod tasks use `docker compose -f prod.yml`** — consistent with existing `backup` task pattern.
3. **`coverage` adds `pytest-cov` to dev deps** — lightweight plugin, minimal surface. Reports to stdout only (term-missing).
4. **`update` uses `uv sync --upgrade`** — upgrades all deps within constraints. Manual review still needed before commit.
5. **`secret-key` uses `python -c "import secrets; print(secrets.token_urlsafe(50))"`** — matches the exact command in README quick-start instructions.
6. **Group naming** — `db-*` prefix for DB tasks, `docker-*` for dev Docker, `prod-*` for production Docker, no prefix for standalone tasks like `coverage`, `update`, `secret-key`.

## Risks / Trade-offs

- **`coverage` with `pytest-cov`** adds one more dev dependency. Minimal — it's a pytest plugin with no runtime impact.
- **`prod-rebuild` chains two commands** (`docker build` + `docker compose up`). If build fails, the stack is not touched. Trade-off accepted: simpler than a script.
- **`update` may break things** — `uv sync --upgrade` can pull breaking changes. User must read diff before committing. No mitigation beyond the existing lockfile + manual review pattern.
