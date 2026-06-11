# Omaha production image (S06/T03).
#
# Multi-stage build: a `builder` stage compiles dependencies (with
# build-essential so the bcrypt / cffi / sqlalchemy wheel builds
# succeed) and a `runtime` stage ships only the venv + source on
# top of python:3.12-slim. The runtime user is `omaha` (uid 1000)
# so a container escape lands in an unprivileged shell.
#
# This Dockerfile is shared by docker-compose.yml (dev, with bind
# mount on /app/src) and prod.yml (prod, named volume for /app/data).
# The 127.0.0.1 bind in CMD is correct for prod (nginx fronts the
# public port); docker-compose.yml dev users must run with
# `-p 8000:8000` to reach it from the host.

FROM python:3.12-slim AS builder

# Copy uv from the official image so the runtime layer never sees
# a Rust toolchain. Pin to `latest` for now; the lockfile is what
# keeps the resolved dependency set reproducible, not the uv
# version.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# System deps for wheel builds (libffi for cffi, gcc for any source
# distribution that doesn't ship a wheel for slim). These stay in
# the builder stage only \u2014 the runtime image below does not
# inherit them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy *only* the lockfile-bearing files first so the venv layer
# is cached until pyproject.toml or uv.lock actually changes.
COPY pyproject.toml uv.lock ./

# Pre-install deps without the project. This populates
# /app/.venv/ with the locked dependency set; the second `uv sync`
# below adds the project itself.
RUN uv sync --frozen --no-install-project

# Now copy the project source. Anything not under src/ + alembic/
# + alembic.ini is intentionally omitted (e.g. tests/, .github/,
# .gsd/) -- the prod image never runs them.
# README.md is included because the hatchling build backend
# validates ``readme = "README.md"`` from pyproject.toml at build
# time (it needs the file to exist, not just to be referenced).
COPY README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

# Final sync: installs the project into the venv (non-editable
# because /app/src will not be bind-mounted in prod).
RUN uv sync --frozen

# --- runtime stage ----------------------------------------------------------
FROM python:3.12-slim AS runtime

# Copy the venv, source, and alembic assets from the builder. We
# intentionally do NOT copy pyproject.toml or uv.lock into the
# runtime image \u2014 the operator does not need them to run the app,
# and keeping them out shrinks the build context that gets sent
# through `docker save` / a registry push.
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/alembic.ini /app/alembic.ini

# The SQLite database file lives in /app/data. Create it as root
# and chown to the unprivileged user so the runtime process can
# read and write the file. The named volume in prod.yml is
# mounted over this directory.
RUN mkdir -p /app/data \
    && groupadd -g 1000 omaha \
    && useradd -u 1000 -g omaha -m -s /bin/bash omaha \
    && chown -R omaha:omaha /app

# Put the venv on PATH so CMD can call alembic + fastapi directly.
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
USER omaha

EXPOSE 8000

# Self-test HEALTHCHECK. Hits the in-container /healthz every 30s
# and marks the container unhealthy after 3 consecutive failures.
# `urllib.request` keeps the healthcheck self-contained (no curl
# in the slim image). The orchestrator (portainer, k8s) reads this
# status to decide whether to restart the container.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=3).status==200 else 1)"

# Run migrations before booting the app so a wiped volume
# (`docker compose down -v` + up) recovers to a fully-migrated
# database. `exec` hands the PID to fastapi so SIGTERM from
# `docker stop` reaches the server, not the bash subshell.
#
# 127.0.0.1 (not 0.0.0.0) is correct for prod: the container is on
# an internal docker network, nginx fronts the public bind on the
# host, and the in-container port is never exposed to the LAN.
CMD ["bash", "-c", "alembic upgrade head && exec fastapi run --host 127.0.0.1 --port 8000 src/omaha/main.py"]
