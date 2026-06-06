# Omaha

Family investment portfolio tracker for two profiles (Italo and Ana Livia).
FastAPI + SQLAlchemy 2 + SQLite + Jinja2 + Alpine.js.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
  (used for the dev/prod container).
- (Optional, for local dev without Docker) [uv](https://docs.astral.sh/uv/)
  to manage Python 3.12 + the locked dependency set.

## Quick Start (Docker)

```bash
cp .env.example .env
# edit .env and set a real SECRET_KEY (50+ random chars)
docker compose up --build
```

The app listens on <http://localhost:8000>. Default dev login password is the
value of `ADMIN_PASSWORD` in your `.env` (the example uses
`family-dev-password-change-me`).

After login you pick a profile (Italo or Ana Livia) and land on the empty
dashboard. `/healthz` returns `200 OK` for liveness checks.

## Local Dev (uv)

```bash
uv sync
cp .env.example .env
uv run omaha          # or: uv run uvicorn omaha.main:app --reload
```

## Tests

```bash
uv run pytest
```

## Production image

A multi-stage production Dockerfile is added in S06.
