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
