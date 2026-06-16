## 1. DB Inspection Tasks

- [x] 1.1 Add `db-current` task: `uv run alembic current`
- [x] 1.2 Add `db-history` task: `uv run alembic history`
- [x] 1.3 Add `db-downgrade` task: `uv run alembic downgrade -1`

## 2. Docker Dev Tasks

- [x] 2.1 Add `docker-build` task: `docker compose build`
- [x] 2.2 Add `docker-up` task: `docker compose up -d`
- [x] 2.3 Add `docker-down` task: `docker compose down`

## 3. Docker Prod Tasks

- [x] 3.1 Add `prod-up` task: `docker compose -f prod.yml up -d`
- [x] 3.2 Add `prod-down` task: `docker compose -f prod.yml down`
- [x] 3.3 Add `prod-logs` task: `docker compose -f prod.yml logs -f`
- [x] 3.4 Add `prod-rebuild` task: `docker build -t omaha:prod . && docker compose -f prod.yml up -d`

## 4. Code Quality Tasks

- [x] 4.1 Add `pytest-cov` to `[dependency-groups] dev` in pyproject.toml
- [x] 4.2 Add `coverage` task: `uv run pytest --cov=src/omaha --cov-report=term-missing`
- [x] 4.3 Add `update` task: `uv sync --upgrade`

## 5. Onboarding Task

- [x] 5.1 Add `secret-key` task: `python -c "import secrets; print(secrets.token_urlsafe(50))"`

## 6. Documentation

- [x] 6.1 Update README.md task table with all new tasks
- [x] 6.2 Update README.md development tasks section with any new category headings
