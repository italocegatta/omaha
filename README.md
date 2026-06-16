# Omaha

Self-hosted family investment portfolio tracker for two profiles (Italo and
Ana Livia). FastAPI + SQLAlchemy 2 + SQLite + Jinja2 + Alpine.js.

Profile-aware asset tree with strict target validation, broker CSV import,
and distribution visualization. Live quotes, BRL/USD conversion, and
rebalancing are deferred to milestone M002.

---

## Quick start

```bash
# 1. Install dependencies (creates .venv with Python 3.12 + locked deps)
uv sync

# 2. Configure
cp .env.example .env
# Edit .env and set a real SECRET_KEY (50+ random chars):
#   python -c "import secrets; print(secrets.token_urlsafe(50))"
# ADMIN_PASSWORD is the shared family password. Change it.

# 3. Run the dev server. Bind to 0.0.0.0 — see "Network access" below.
uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000
```

Migrations and the family user/profiles seed run automatically on startup
via the FastAPI lifespan hook. To run them by hand:

```bash
uv run alembic upgrade head
uv run python -m omaha.seed
```

---

## Production deploy

The production stack is `docker compose -f prod.yml`: a FastAPI
container behind an nginx TLS terminator, with a SQLite database
that lives in a **named volume** so a `docker compose down` does not
wipe it. A one-shot `backup` service (on a profile, not started by
`up`) is the documented snapshot path.

```bash
# 1. Build the prod image once. The T03 Dockerfile is multi-stage
#    (slim runtime, non-root, baked-in HEALTHCHECK against /healthz).
docker build -t omaha:prod .

# 2. Get a TLS cert. The recommended path is the certbot standalone
#    challenge against the public DNS name you point at the host.
#    (Replace omaha.example.com with your real hostname.)
sudo certbot certonly --standalone -d omaha.example.com

# 3. Copy the cert chain into the ./certs bind mount that prod.yml
#    wires into the nginx container. nginx reads fullchain.pem +
#    privkey.pem from /etc/nginx/certs.
sudo cp /etc/letsencrypt/live/omaha.example.com/fullchain.pem ./certs/
sudo cp /etc/letsencrypt/live/omaha.example.com/privkey.pem   ./certs/
sudo chown $USER:$USER ./certs/*.pem
chmod 600 ./certs/privkey.pem

# 4. Bring the stack up. nginx publishes 80 + 443; web listens on
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
nginx.

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

**Schedule it with host cron** (the container does not run cron
itself; the prod image is a one-process model):

```cron
# /etc/cron.d/omaha-backup — nightly at 03:00 host time.
0 3 * * * www-data cd /srv/omaha && /usr/bin/docker compose -f prod.yml run --rm backup >> /var/log/omaha-backup.log 2>&1
```

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

## Network access

> **Always start the server with `--host 0.0.0.0`.** The default
> `uvicorn` bind is `127.0.0.1` (loopback only), which is unreachable
> from any other machine on the network. The dev host has three
> LAN-eligible IPs (LAN `192.168.1.7`, Tailscale `10.255.255.254`,
> Docker bridge `172.17.0.1`); the app is accessed from a separate
> client machine, so `localhost` will not work there.

The dev host's LAN IP is `192.168.1.7` on this network. Open the app at:

```
http://192.168.1.7:8000
```

If you move to a different network, re-detect the IP with
`ip -4 addr | grep inet` and use whatever LAN / Tailscale address is
listed. `localhost` and `127.0.0.1` are never correct for a manual UI
test session.

### Windows / WSL: forwarding the host port

If the dev host is WSL on Windows, the Linux LAN IP above is not
reachable from the Windows side directly — the WSL instance is on a
virtual NIC. Forward a Windows host port to the WSL IP with
`netsh interface portproxy` and open the firewall, then point the
client at `http://localhost:<port>` (or the host's LAN IP) instead.

Run this in **PowerShell as Administrator** on the Windows host. Edit
`$port` to match the port uvicorn is bound to inside WSL (e.g. `8000`
if that is what you launched).

```powershell
$port=4096; $wslIp=(wsl -d juca hostname -I).Trim(); netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIp; netsh advfirewall firewall add rule name="WSL $port" dir=in action=allow protocol=TCP localport=$port; Write-Host "OK — porta $port aberta para $wslIp"
```

Verify the forward is in place with `netsh interface portproxy show
all`. To remove it later: `netsh interface portproxy delete v4tov4
listenport=$port listenaddress=0.0.0.0` and
`netsh advfirewall firewall delete rule name="WSL $port"`.

---

## Testing the app

The canonical dev DB reset script (`scripts/dev_reset.py`) wipes Italo's
profile and re-seeds the same state the e2e suite uses. Run it before
any manual import-flow test:

```bash
uv run python -m scripts.dev_reset
# expected:
#   reset OK — Italo now has 3 classes (Renda Fixa@60%, Acoes@30%, FIIs@10%)
#   and 43 assets. 5 unmatched on import: MXRF11, BPAC11, HGLG11, XPLG11, VINO11
```

Then in the browser:

1. Open `http://192.168.1.7:8000/login` and sign in as `family` with the
   `ADMIN_PASSWORD` from your `.env`.
2. Pick the **Italo** profile. The dashboard renders the polished
   distribution view: portfolio header (invested / current / gain, BRL
   + %, color-coded), per-class sections with color swatches and a
   target-vs-current compare bar, and per-asset rows with progress bars
   (qty, current value, % of class).
3. Click **Importar** in the nav to test the CSV importer:
   - The fixture at `tests/fixtures/sample_broker.csv` is the same
     file the e2e tests use: 48 rows, 43 auto-match against the
     seeded assets, 5 require manual category selection in the
     review screen.
   - `posicao_italo.csv` (real broker export) lives in `tests/` and
     works end-to-end too. Note: 7 CDB/RDB rows with qty=`-` are
     dropped (parser limitation, not a bug).
4. Confirm the import. Positions appear under each asset on the
   dashboard; the distribution view re-renders with the new totals.

For **Ana Livia** the dashboard is empty — all CRUD is per-profile and
isolated. Sign out from the top-right menu; `/` then redirects to
`/login`.

Health check: `curl http://192.168.1.7:8000/healthz` returns
`{"status": "ok"}`.

---

## Tests

```bash
uv run pytest                       # full suite (unit + integration + e2e)
uv run pytest tests/test_X.py -v    # single file
uv run pytest tests/e2e/ -v         # Playwright browser tests (S03–S05)
uv run prek run --all-files         # ruff-format + ruff-check
```

The e2e suite needs Playwright + a one-time `playwright install chromium`
(see `pyproject.toml` dev deps).

---

## Project layout

```
omaha/
├── src/omaha/            # FastAPI app
│   ├── routes/           # auth, classes, assets, imports, pages, health
│   ├── templates/        # base, login, profiles, dashboard, import, import_review, classes, assets
│   ├── static/app.css
│   ├── auth.py           # password hashing + session helpers
│   ├── config.py         # pydantic-settings (reads .env)
│   ├── csv_import.py     # parser + matcher
│   ├── db.py             # SQLAlchemy 2.0 Base + Session
│   ├── main.py           # create_app + lifespan
│   ├── models.py         # User, Profile, AssetClass, Asset, Position, ImportPreview
│   └── seed.py           # idempotent family + profiles seed
├── alembic/              # migrations (0001–0005)
├── scripts/dev_reset.py  # canonical dev DB reset for manual import tests
├── tests/                # pytest suite (unit + integration + e2e/)
├── data/portfolio.db     # SQLite (gitignored, created at startup)
├── .env.example          # template for .env (gitignored real .env)
├── pyproject.toml        # uv-managed Python project
├── uv.lock               # locked dep set
└── prek.toml             # ruff hooks (format + check)
```

---

## Project specs

Current state, decisions, slice plans, and lessons live in `.gsd/`:

- `STATE.md` — active milestone / slice, recent decisions, blockers
- `ROADMAP.md` — milestone + slice plan
- `REQUIREMENTS.md` — capability contract
- `DECISIONS.md` — append-only decision register (caveman mode,
  delivery protocol, etc.)
- `KNOWLEDGE.md` — rules + lessons learned
- `milestones/M001/slices/S##/` — per-slice plan, summary, UAT
