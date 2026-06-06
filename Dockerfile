# Omaha dev image (S01). S06 swaps this for a multi-stage production build.
#
# Layout: a thin python:3.12-slim layer that copies `uv` from the official
# `uv` image, then installs the locked dependency set with `uv sync
# --frozen --no-install-project`, then layers the project source on top. The
# `--no-install-project` step caches the venv until the source actually
# changes, so `docker compose build` is fast on no-op rebuilds.

FROM python:3.12-slim AS base

# Copy uv from the official image — keeps the runtime layer free of a Rust
# toolchain and means we always pull the same `uv` version regardless of
# what is on the host.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install system deps that the wheel builds for bcrypt / sqlalchemy expect.
# `build-essential` is only needed during the `uv sync` build; it stays in
# the image because the S01 dev build doesn't shrink itself — S06 introduces
# a multi-stage build that strips it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy *only* the lockfile-bearing files first so this layer is cached until
# pyproject.toml or uv.lock changes.
COPY pyproject.toml uv.lock ./

# Install dependencies into the project venv (the default for `uv sync`).
# `--no-install-project` skips installing the project itself; we copy the
# source next, then `uv sync` again (or rely on `uv run`) to install the
# project in editable mode for the dev image.
RUN uv sync --frozen --no-install-project

# Now layer the source on top. Mounting a volume over `/app/src` in
# docker-compose would still let `uv run fastapi ...` pick up the live
# edits because the source is installed in editable mode.
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Install the project itself (editable) so `uv run omaha` and
# `alembic` work without extra PATH tweaks.
RUN uv sync --frozen

# Put the project venv on PATH so the CMD below can call `alembic` and
# `fastapi` directly. Without this, only `uv run ...` would find them
# because the venv isn't auto-activated for the bash subshell that
# CMD spawns.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# The container's entrypoint runs migrations + the idempotent seed before
# booting the app, so `docker compose up --build` against a wiped volume
# recovers to a fully-initialised database. `exec` hands the PID over to
# `fastapi run` so SIGTERM from `docker stop` reaches the server.
CMD ["bash", "-c", "alembic upgrade head && exec fastapi run --host 0.0.0.0 --port 8000 src/omaha/main.py"]
