# Omaha

Self-hosted family investment portfolio tracker for the household — two
real profiles (Italo and Ana Livia) plus a third read-only **Família**
aggregate that joins both across every class. FastAPI + SQLAlchemy 2 +
SQLite + Jinja2 + Alpine.js. Ships in a dark warm-neutral palette.

Profile-aware asset tree with strict target validation, broker CSV
import, distribution visualization, CVXPY-based rebalancing, and live
quotes via yfinance (BRL/USD conversion on the foreign side). The UI is
a four-tab top-level nav: `/patrimonio`, `/rebalanceamento`,
`/rentabilidade`, `/proventos`.

---

## Quick start

```bash
# 1. Install dependencies (creates .venv with Python 3.12 + locked deps)
uv sync

# 2. Configure
cp .env.example .env
# Edit .env and set a real SECRET_KEY (50+ random chars):
#   python -c "import secrets; print(secrets.token_urlsafe(50))"
# ADMIN_PASSWORD is the shared family password.
# Canonical default is `distendidos` — see AGENTS.md "Family password".

# 3. Run the dev server. Bind to 0.0.0.0 — see "Network access" below.
#    Canonical invocation:
uv run task serve
#    Equivalent raw form (the task wraps this — see pyproject.toml):
uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000 --reload
```

Migrations and the family user/profiles seed run automatically on startup
via the FastAPI lifespan hook. To run them by hand:

```bash
uv run task db-migrate
uv run task db-seed
```

The canonical **destructive** reset for a manual import-flow test
(re-seeds both profiles from the CSV triplet in one shot) is:

```bash
uv run task db-reset
# expected:
#   profile=italo mode=reset classes=6 assets=47 positions=47
#   profile=ana   mode=reset classes=6 assets=52 positions=52
```

---

## Development tasks

Routine dev work is wrapped in [taskipy](https://github.com/taskipy/taskipy)
shortcuts, declared in `pyproject.toml` under `[tool.taskipy.tasks]`.
The canonical invocation is `uv run task <name>` (which activates the
venv and runs the `task` console script); the same works as plain
`task <name>` once the venv is on `$PATH`.

Discover them any time with `uv run task --list`.

| Task               | What it does                                                                    |
|--------------------|---------------------------------------------------------------------------------|
| `serve`            | Start the dev server on `0.0.0.0:8000` with auto-reload.                        |
| `serve-prod`       | Start the server without auto-reload (production-shaped).                      |
| `test`             | Run the full test suite (unit + integration + audit + e2e + visual + BDD).      |
| `test-unit`        | Pure-function tests — no DB, no HTTP, no Playwright.                            |
| `test-integration` | Tests requiring DB, TestClient, or external services (excludes `tests/audit_integration/`). |
| `test-audit-integration` | Heavy audit integration tests under `tests/audit_integration/`.            |
| `test-e2e`         | End-to-end Playwright tests under `tests/e2e/`.                                 |
| `test-visual`      | Playwright visual regression tests under `tests/visual/`.                       |
| `test-bdd`         | BDD scenarios under `tests/bdd/` (pytest-bdd, real Chromium, serial).           |
| `test-file`        | Run a specific test file: `task test-file tests/test_X.py`.                     |
| `test-pattern`     | Run tests matching a name substring: `task test-pattern "smoke"`.               |
| `test-one`         | Run a single test by node id: `task test-one tests/test_X.py::test_y`.          |
| `lint`             | Run prek hooks: ruff format check, ruff --fix, hygiene.                         |
| `format`           | Auto-format the codebase with ruff.                                             |
| `check`            | CI-style gate: `lint` + unit tests.                                              |
| `coverage`         | Run unit + integration tests with coverage report (term-missing + XML).         |
| `mutation`         | Run mutation testing on the rebalance solver + validation (scoped via `[tool.mutmut]` `only_mutate`; first run populates `mutants/`). |
| `mutation-report`  | Render mutation results to stdout: per-status counts + killed share.            |
| `mutation-baseline`| Capture the current mutation score to `.mutmut-baseline`.                       |
| `db-current`       | Show the current Alembic revision head.                                         |
| `db-downgrade`     | Revert the last Alembic migration.                                              |
| `db-history`       | Show the full Alembic migration timeline.                                       |
| `db-migrate`       | Apply pending Alembic migrations.                                               |
| `db-revision`      | Create a new Alembic revision: `task db-revision -m "add foo column"`.          |
| `db-seed`          | Run the idempotent family + profiles seed.                                      |
| `db-seed-from-csv` | Wipe + reseed Italo from `data/seed/*.csv` (override with `-- --profile ana --mode diff`). |
| `db-seed-diff`     | Print the CSV-vs-DB diff for Italo without writing (override with `-- --profile ana`). |
| `db-seed-upsert`   | Reconcile Italo's DB with `data/seed/*.csv` (create-or-update, no delete). Override with `-- --profile ana`. |
| `db-clear-assets`  | Delete ALL asset rows (keep classes intact).                                    |
| `db-reset`         | Wipe + reseed BOTH profiles (Italo + Ana) from `data/seed/*.csv` in one invocation. |
| `db-snapshot`      | Export live DB state (classes + assets + positions) to `data/seed/*.csv` for ALL canonical profiles (italo + ana). Internal dev tool. |
| `docker-build`     | Build the dev Docker image from docker-compose.yml.                             |
| `docker-down`      | Stop and remove the dev Docker Compose stack.                                   |
| `docker-up`        | Start the dev Docker Compose stack in detached mode.                            |
| `install`          | `uv sync` — install / sync locked dependencies into `.venv`.                    |
| `install-e2e`      | Download the Playwright Chromium browser (one-time).                            |
| `prek-install`     | Install prek git hooks (pre-commit, pre-push, commit-msg) into `.git/hooks/`.   |
| `prod-down`        | Stop and remove the production Docker Compose stack.                            |
| `prod-logs`        | Stream logs from all production services.                                       |
| `prod-rebuild`     | Rebuild the prod image and restart the stack.                                   |
| `prod-up`          | Start the production Docker Compose stack.                                      |
| `backup`           | Snapshot the prod DB to `./backups/` (one-off container from `prod.yml`).       |
| `clean`            | Remove Python bytecode and tool caches (keeps `.venv` and `node_modules`).      |
| `secret-key`       | Generate a cryptographically random SECRET_KEY.                                 |
| `update`           | Upgrade all dependencies within version constraints.                            |

A few things worth knowing:

- `test-file`, `test-pattern`, and `test-one` accept the target as a
  positional arg appended to the command — taskipy just appends
  whatever follows the task name.
- `serve` binds `0.0.0.0` so the app is reachable from other machines
  on the LAN. See **Network access** below for the LAN IP to use.
- `clean` only touches `__pycache__`, `.pytest_cache`, and
  `.ruff_cache`. It is safe to run any time; the SQLite DB and your
  `.env` are untouched.
- `db-reset` is the canonical reset for a manual import-flow test
  (see **Testing the app** below).

---

## Production deploy

The production stack is `docker compose -f prod.yml`: a FastAPI
container behind an nginx TLS terminator, with a SQLite database
that lives in a **named volume** so a `docker compose down` does not
wipe it. A one-shot `backup` service (on a profile, not started by
`up`) is the manual snapshot path; a `backup-scheduler` service
runs `scripts/backup_scheduler.py` periodically (default 24h,
overridable via `BACKUP_INTERVAL`) and is the default-in-prod
automatic path.

```bash
# 1. Build the prod image once. The T03 Dockerfile is multi-stage
#    (slim runtime, non-root, baked-in HEALTHCHECK against /healthz).
docker build -t omaha:prod .

# 2. Bootstrap TLS. TLS cert renewal is automated by the `certbot`
#    scheduler service in `prod.yml` (see **Operação / TLS renewal**
#    below — added by I02). Run the **First-time setup** block once to
#    obtain the initial cert + populate `./certs/`; the scheduler
#    handles all subsequent renewals.

# 3. Bring the stack up. nginx publishes 80 + 443; web listens on
#    127.0.0.1 inside its container and is reachable only via the
#    internal docker network.
docker compose -f prod.yml up -d
```

**Verify the deploy is live:**

```bash
# TLS-terminated healthz: should be 200 OK with the JSON probe.
curl -kI https://localhost/healthz
# Body should be: {"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}

# Plain HTTP should 301 to https.
curl -I http://localhost/
# Headers: HTTP/1.1 301 Moved Permanently
#          Location: https://localhost/
```

**Named-volume warning:** the SQLite database lives in the named
volume `omaha-data`, not in a bind mount. `docker compose -f prod.yml down`
**preserves** the volume; only `docker compose -f prod.yml down -v` wipes
it. If you want to nuke the DB, be explicit: `down -v`.

A certbot sidecar is the recommended renewal path (not an in-container
certbot that would need write access to `./certs/`). The nginx config
serves `/.well-known/acme-challenge/` from `/var/www/certbot` so a
sidecar can answer the http-01 challenge without touching the running
nginx. The `certbot` service in `prod.yml` provides that sidecar out of
the box — see [TLS renewal](#tls-renewal) below for the automated
scheduler.

---

## Backup & restore

The `backup` service in `prod.yml` is on `profiles: [backup]`, so it
does **not** start with `up`. Invoke it manually:

```bash
# One-off backup. The container exits with the script's exit code
# and `run --rm` removes it. The snapshot lands in ./backups/ on
# the host (bind mount from prod.yml).
docker compose -f prod.yml run --rm backup
# expected:
#   backup OK: /app/data/portfolio.db -> /backups/portfolio-YYYYMMDDTHHMMSSZ.db (complete)
```

### Scheduled backups (default in prod)

The `backup-scheduler` service in `prod.yml` has no profile, so it
starts with `docker compose -f prod.yml up -d` alongside `web` and
`nginx`. It runs `scripts/backup_scheduler.py`, an in-container loop
that shells out to `scripts.backup` every `BACKUP_INTERVAL` seconds
(default `86400` = 24h) and logs each run with an ISO-8601 UTC
timestamp. The loop is failure-tolerant: a non-zero exit from a single
run is logged and the loop continues — the container stays in
`running` state across transient errors (DB locked by migration, disk
full).

```bash
# Tail the scheduler log to see each run (start, outcome, next sleep).
docker compose -f prod.yml logs -f backup-scheduler
# expected:
#   2026-07-06T03:14:15Z INFO backup_scheduler started interval=86400s
#   2026-07-06T03:14:15Z INFO backup started dest=/backups/portfolio-20260706T031415Z.db
#   2026-07-06T03:14:15Z INFO backup OK: backup OK: /app/data/portfolio.db -> /backups/portfolio-20260706T031415Z.db (complete)

# Disable scheduling without touching web or nginx. The container
# exits and `restart: unless-stopped` does NOT bring it back up after
# a subsequent reboot — the operator has to re-enable it explicitly.
docker compose -f prod.yml stop backup-scheduler

# Re-enable (the same `up` pattern, scoped to the scheduler service).
docker compose -f prod.yml up -d backup-scheduler

# Override the cadence (e.g. 1h) before bringing the stack up.
BACKUP_INTERVAL=3600 docker compose -f prod.yml up -d
```

**Operator responsibility — retention and rotation.** The slice writes
each snapshot to `./backups/portfolio-YYYYMMDDTHHMMSSZ.db` and never
deletes anything. Move the directory off-host (rsync, restic, b2,
whatever you trust) and prune old files on your own schedule. The
slice is intentionally small: "generate snapshot" is the boundary;
"keep the snapshot disk under control" is yours.

**Restore (prod, named volume):**

```bash
# 1. Stop the stack so the web container is not writing to the DB.
docker compose -f prod.yml down

# 2. Copy the snapshot INTO the named volume. The cleanest path is
#    `docker compose cp` (docker compose v2) — it puts the file
#    straight into the web container's filesystem; restart then
#    moves the volume mount over it.
docker compose -f prod.yml cp ./backups/portfolio-20260101T030000Z.db web:/app/data/portfolio.db.new
docker compose -f prod.yml run --rm --entrypoint sh web -c 'mv /app/data/portfolio.db.new /app/data/portfolio.db'

# 3. Bring the stack back up. /healthz reports 200 with the
#    restored data; the dashboard renders the restored positions.
docker compose -f prod.yml up -d
```

**Restore (dev, bind mount):** `cp` straight into `./data/` because
`docker-compose.yml` bind-mounts the host directory into the web
container. Stop the dev server first, then `cp ./backups/<file>.db
./data/portfolio.db`, then `uv run uvicorn ...` again.

---

## TLS renewal

Let's Encrypt certificates expire every 90 days. The `certbot` service
in `prod.yml` automates the renewal loop so the operator does not run
`certbot renew` by hand: it loops `certbot renew` every
`CERTBOT_RENEW_INTERVAL` seconds (default 43200 = 12h), which is
idempotent — `certbot renew` only acts when a cert is within 30 days
of expiry. On successful renewal, a `--deploy-hook` copies the renewed
`fullchain.pem` and `privkey.pem` into nginx's expected path
(`/etc/nginx/certs/`) and reloads nginx in-place so the new cert takes
effect on the next request.

The certbot service uses the official `certbot/certbot` image, runs as
a long-lived bash loop (`scripts/certbot_loop.sh`), and shares the host
network with nginx + web. It also bind-mounts the Docker socket
`/var/run/docker.sock` (read-only) so the deploy hook can `docker
compose exec` into nginx. This is a soft privilege escalation but is
acceptable for a single-tenant portfolio deploy; the deploy-hook only
runs on actual renewal.

### First-time setup

Before the scheduler can run, the operator must obtain the **initial**
certificate once (`certbot renew` does not bootstrap the first cert).
Then the scheduler takes over indefinitely.

```bash
# 1. Create the webroot directory that nginx and certbot share for
#    ACME http-01 challenges. Skipping this step makes nginx fail to
#    start because the bind mount cannot resolve.
mkdir -p ./certs/webroot

# 2. Set the operator-supplied env vars for the certbot service.
#    These are picked up by prod.yml's ${CERTBOT_DOMAIN:-...} /
#    ${CERTBOT_EMAIL:-...} substitutions; they have no default.
export CERTBOT_DOMAIN=omaha.example.com
export CERTBOT_EMAIL=ops@example.com

# 3. One-shot certbot run to obtain the initial cert. The web
#    service does not need to be up for this command; nginx does
#    (it serves the challenge over port 80).
docker compose -f prod.yml run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$CERTBOT_DOMAIN" \
    --email "$CERTBOT_EMAIL" \
    --agree-tos --no-eff-email

# 4. Bring the stack up. The certbot service starts alongside
#    web + nginx + backup-scheduler.
docker compose -f prod.yml up -d

# 5. Verify the initial cert was copied into nginx's expected
#    path (the deploy-hook runs only on subsequent renewals, so
#    step 3 writes to /etc/letsencrypt/live/<domain>/ but nginx
#    reads /etc/nginx/certs/ — operator must copy manually the
#    first time).
sudo cp ./certs/live/$CERTBOT_DOMAIN/fullchain.pem ./certs/fullchain.pem
sudo cp ./certs/live/$CERTBOT_DOMAIN/privkey.pem   ./certs/privkey.pem
sudo chown $USER:$USER ./certs/*.pem
chmod 600 ./certs/privkey.pem

# 6. Reload nginx to pick up the certs.
docker compose -f prod.yml exec nginx nginx -s reload
```

After step 4, renewals are automatic. Step 5–6 are one-time bootstrap
glue; the deploy-hook handles the same `cp + reload` from then on.

### Scheduler behaviour

```bash
# Tail the renewal log to see each renewal attempt (start, outcome,
# next sleep). Renewals only act when the cert is within 30 days of
# expiry, so most invocations are no-ops logged as "INFO certbot
# renew OK".
docker compose -f prod.yml logs -f certbot
# expected:
#   2026-07-06T15:00:00Z INFO certbot_loop started interval=43200s domain=omaha.example.com
#   2026-07-06T15:00:00Z INFO certbot renew started
#   2026-07-06T15:00:02Z INFO certbot renew OK
```

```bash
# Override the renewal cadence (e.g. 1h for testing) before bringing
# the stack up. Read once at start-up; mid-run changes require a
# container restart.
CERTBOT_RENEW_INTERVAL=3600 docker compose -f prod.yml up -d certbot
```

```bash
# Stop the scheduler without touching web or nginx. The container
# exits; `restart: unless-stopped` does NOT bring it back up after
# a subsequent reboot — the operator has to re-enable it explicitly.
docker compose -f prod.yml stop certbot
docker compose -f prod.yml up -d certbot    # re-enable
```

The scheduler is **failure-tolerant**: a non-zero exit from
`certbot renew` (CA unreachable, rate-limit) is logged at ERROR and the
loop continues — the container stays in `running` state across
transient errors and tries again `CERTBOT_RENEW_INTERVAL` seconds later.

### Filesystem layout

```text
./certs/                            # bind mount → certbot:rw, nginx:ro
├── .gitkeep                        # keeps the dir tracked
├── fullchain.pem                   # nginx reads these (existing)
├── privkey.pem                     #   ^ (existing; initial bootstrap copy)
├── live/<domain>/                  # certbot writes here at renewal time
│   ├── fullchain.pem               #   ↑
│   └── privkey.pem                 #   ↑
├── archive/<domain>/               # certbot's per-archive history
└── webroot/                        # ACME challenge webroot (both share)
    └── .gitkeep                    # keeps the dir tracked

./prod.yml                          # bind-mounted into certbot container
                                    #   at /app/prod.yml:ro so the
                                    #   deploy-hook can `docker compose
                                    #   -f /app/prod.yml exec nginx …`

./scripts/certbot_loop.sh           # bind-mounted into certbot container
                                    #   at /scripts/certbot_loop.sh:ro
```

nginx's `nginx.conf` is unchanged — it keeps reading
`/etc/nginx/certs/fullchain.pem` and `/etc/nginx/certs/privkey.pem`,
which is exactly the path the deploy-hook populates.

---

## Network access

> **Always start the server with `--host 0.0.0.0`.** The default
> `uvicorn` bind is `127.0.0.1` (loopback only), which is unreachable
> from any other machine on the network. The dev host has three
> LAN-eligible IPs (LAN IP via `bash scripts/print_lan_url.sh`,
> Tailscale `10.255.255.254`, Docker bridge `172.17.0.1`); the app is
> accessed from a separate client machine, so `localhost` will not work
> there.

The dev host's LAN IP is detected via `bash scripts/print_lan_url.sh`.
Open the app at the URL it prints:

```bash
bash scripts/print_lan_url.sh  # → http://192.168.1.6:8000 (or IP atual)
```

If you move to a different network, re-detect the IP with
`ip -4 addr | grep inet` and use whatever LAN / Tailscale address is
listed. `localhost` and `127.0.0.1` are never correct for a manual UI
test session.

---

## Testing the app

The canonical dev DB reset task now wipes + reseeds BOTH profiles
(Italo + Ana) from their CSV triplets in one invocation
(`scripts.reset_both_profiles.py`). Run it before any manual
import-flow test:

```bash
uv run task db-reset
# expected:
#   profile=italo mode=reset classes=6 assets=47 positions=47
#   profile=ana   mode=reset classes=6 assets=52 positions=52
```

### Snapshot the wallet state

`db-reset` is destructive — it wipes the DB before reseeding. If you
want to preserve your current wallet state across a destructive
change (a migration test, a UI rework, or just a checkpoint), `task
db-snapshot` exports the live DB to the CSV triplet under
`data/seed/`:

```bash
uv run task db-snapshot
# expected:
#   italo: 6 classes, 47 assets, 47 positions -> 3 files written
#   ana:   6 classes, 52 assets, 52 positions -> 3 files written
#   snapshot OK: 210 rows across 6 files written
```

Inspect the change with `git diff data/seed/` and commit it if the
new state is the new baseline. The next `db-reset` reproduces the
snapshotted state from scratch.

`total_invested` / `total_current` flow through the round-trip
verbatim — they are the broker-published per-row totals, never
recomputed from `qty * price` (see
`broker-csv-import-totals`). Non-tradeable rows now use `qty = 0`
with explicit `total_invested / total_current`; tradeable positions
keep unit values and pick up totals the next time the broker CSV is
imported.

Then in the browser:

1. Run `URL=$(bash scripts/print_lan_url.sh)/login` and open `$URL` in
   the browser. Sign in as `Italo` or `Ana` with the `ADMIN_PASSWORD`
   from your `.env`. Login lands directly on the named user's own
   patrimonio — no intermediate picker page.
2. The patrimonio renders the polished distribution view: portfolio
   header (invested / current / gain, BRL + %, color-coded), per-class
   sections with color swatches and a target-vs-current compare bar,
   and per-asset rows with progress bars (qty, current value, % of
   class). Switch profiles via the header profile-switcher — the
   three options are `Italo`, `Ana`, and `Família` (the read-only
   cross-User aggregate introduced by F07). Any logged-in user can
   view any profile; the Família option is read-only by design.
3. The four-tab top-level nav (`Patrimônio`, `Rebalanceamento`,
   `Rentabilidade`, `Proventos`) lives under the header. The
   **Importar CSV** button is in the patrimônio body (top of the
   page, post-F02 redistribution — the side panel was removed). To
   test the CSV importer:
    - The canonical audit fixture is `data/seed/italo_positions.csv`;
      `tests/test_real_csv_flow.py` uploads it as `posicao_italo.csv`
      and documents current importer behavior against seeded data.
    - The importer still ignores fixture `total_invested` /
      `total_current` columns. Raw broker exports belong to the
      separate import-preview journey tests.
4. Confirm the import. Positions appear under each asset on the
   patrimonio; the distribution view re-renders with the new totals.

For **Ana Livia** the patrimonio is empty until you import a CSV —
all CRUD is per-profile and isolated. Sign out from the top-right
menu; `/` then redirects to `/login`.

Health check: `curl "$(bash scripts/print_lan_url.sh)/healthz"` returns
`{"status": "ok"}`.

---

## Tests

The shortcut manager (see **Development tasks** above) wraps the
canonical test commands:

```bash
uv run task test           # full suite (unit + integration + e2e)
uv run task test-unit      # unit + integration only (faster, no browser)
uv run task test-e2e       # Playwright browser tests
uv run task test-file tests/test_X.py   # single file
uv run task test-pattern "smoke"          # name-substring match
uv run task lint           # ruff + format check + hygiene
```

The e2e suite needs Playwright + a one-time `uv run task install-e2e`
(or `playwright install chromium` directly — see `pyproject.toml` dev
deps).

---

## Project layout

```
omaha/
├── src/omaha/                  # FastAPI app
│   ├── routes/                 # auth, classes, assets, imports, pages,
│   │                           #   health, quotes, rebalance
│   ├── templates/              # base, login, patrimonio (+ six partials),
│   │                           #   rebalance, rentabilidade, proventos,
│   │                           #   import, import_review, classes, assets,
│   │                           #   profiles, audit_report
│   │                           #   `templates/_patrimonio_*.html` partials
│   │                           #   (actions, add_asset_modal, class_section,
│   │                           #    distribution, empty_states, portfolio_header)
│   │                           #   introduced by R04. import_review + the
│   │                           #   legacy classes/assets/profiles pages are
│   │                           #   retained as historical artifacts; their
│   │                           #   routes 302 → /patrimonio.
│   ├── static/app.css          # tokens + components (OKLCH palette)
│   ├── audit/                  # contrast-audit CLI (omaha.audit.cli)
│   ├── quotes/                 # quote provider package (R03 refactor)
│   │   ├── __init__.py
│   │   ├── cache.py            # in-memory + disk LRU cache
│   │   ├── service.py          # yfinance adapter + fallback
│   │   └── provider.py         # retired — `quotes/provider.py` was split
│   │                           #   into the `quotes/` package by R03
│   ├── rebalance/              # CVXPY solver + validation pipeline
│   ├── auth.py                 # password hashing + session helpers
│   ├── config.py               # pydantic-settings (reads .env)
│   ├── csv_import.py           # parser + matcher
│   ├── db.py                   # SQLAlchemy 2.0 Base + Session
│   ├── logging_config.py       # ISO-8601 UTC structured logging
│   ├── main.py                 # create_app + lifespan
│   ├── middleware.py           # request-id + access log
│   ├── models.py               # User, Profile, AssetClass, Asset,
│   │                           #   Position, ImportPreview
│   ├── seed.py                 # idempotent family + profiles seed
│   └── validators.py           # target-validation helpers
├── alembic/                    # migrations
├── nginx/                      # nginx.conf (TLS terminator)
├── openspec/                   # source-of-truth for product contract
│   ├── PRD.md                  # capabilities + 10 standing rules (§4)
│   ├── roadmap.md              # F/R/T/D/I slice register
│   ├── config.yaml             # OpenSpec + roadmap token budgets
│   ├── specs/<capability>/     # 44 stable capability contracts
│   └── changes/<change-id>/    # active OpenSpec changes
├── scripts/
│   ├── seed_from_csv/          # CSV-driven seed package (R02 refactor)
│   ├── reset_both_profiles.py  # canonical dev DB reset (`task db-reset`)
│   ├── snapshot_to_csv.py      # DB → CSV (`task db-snapshot`)
│   ├── backup.py + backup_scheduler.py  # prod hot snapshot + loop
│   ├── certbot_loop.sh         # TLS renewal scheduler (I02)
│   ├── print_lan_url.sh        # LAN URL discovery
│   ├── mutation_baseline.py + mutation_report.py  # T03 mutation
│   └── generate_contrast_audit.py  # thin wrapper over omaha.audit.cli
├── prod.yml                    # production Docker Compose stack
├── docker-compose.yml          # dev Docker Compose stack
├── tests/                      # pytest suite (unit + integration + e2e/ + bdd/)
├── data/portfolio.db           # SQLite (gitignored, created at startup)
├── data/seed/                  # CSV triplets per profile (italo + ana)
├── .env.example                # template for .env (gitignored real .env)
├── pyproject.toml              # uv-managed Python project + taskipy tasks
├── uv.lock                     # locked dep set
└── prek.toml                   # ruff hooks (format + check)
```

---

## Project specs

Source-of-truth for product contract and execution plan lives in
[`openspec/`](openspec/):

- [`openspec/PRD.md`](openspec/PRD.md) — capabilities inventory + 10
  standing rules (§4 — operational invariants).
- [`openspec/roadmap.md`](openspec/roadmap.md) — F / R / T / D / I slice
  register with lifecycle `Ready → Spec Proposed → Applying → Applied
  → Archived` (+ `Blocked`).
- [`openspec/specs/<capability>/spec.md`](openspec/specs/) — stable
  capability contracts (one folder per `SHALL` capability).
- [`openspec/changes/<change-id>/`](openspec/changes/) — active OpenSpec
  changes (each slice in the roadmap maps 1:1 to a folder here).

The agent routing table — how AI sessions decide what to read, what
to write, and which skill to delegate — lives in
[`AGENTS.md`](AGENTS.md).
