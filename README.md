# Omaha

Self-hosted family investment portfolio tracker for two profiles (Italo and
Ana Livia). FastAPI + SQLAlchemy 2 + SQLite + Jinja2 + Alpine.js.

The application is a profile-aware asset tree with strict target
validation, broker CSV import, and distribution visualization. Live
quotes, BRL/USD conversion, and rebalancing are deferred to milestone
M002.

---

## Project rules (decision register, append-only)

These rules were set by the project owner and are recorded in
`.gsd/DECISIONS.md` (decisions D003 and D004, dated 2026-06-07).

### Communication style

**Caveman full mode** is the active communication style for chat and
review sessions. Articles drop, fragments are fine, no filler, terse
like a smart caveman. Code, commits, pull requests, and this README
itself are normal prose. The rule auto-clarifies (drops caveman) for
security warnings, irreversible actions, and multi-step sequences where
the order of operations matters. Say "stop caveman" or "normal mode"
to revert.

### Delivery and validation protocol

For each task in a slice, the executor follows this loop:

1. **Implement** the task (smallest unblocker first).
2. **Run pytest** — the relevant test file, then the full suite.
3. **Commit to `main`** with a clear message:
   `feat(S##/T0X): <one-line summary>`.
4. **Validation gate**:
   - Foundation tasks (data layer, routes, no visible UI change) are
     validated by `pytest` only. No pause.
   - UI tasks (anything that changes the rendered dashboard) **pause**
     and wait for the project owner to confirm the change in the
     running `uvicorn` app before the next task starts.
5. After all slice tasks are approved, the executor reassesses the
   roadmap and starts the next slice with the same protocol.

The goal is incremental, human-in-the-loop validation. Smaller slices
reduce the diff the owner reviews per checkpoint. UI validation in the
running app catches problems that `pytest` cannot (visual regression,
copy issues, interactive edge cases). Committing to `main` keeps the
user-facing repo in sync — no extra merge step from a GSD worktree.

---

## Current state

Tracked in `.gsd/PROJECT.md` and `.gsd/REQUIREMENTS.md` (auto-refreshed
on slice completion).

**Done:**

- **S01 — Foundation and auth.** Login with the shared family
  password, profile selector (Italo / Ana Livia), empty dashboard,
  `/healthz` returns 200.
- **S02 — Macro-class CRUD with reactive pct validation.** Create up
  to N classes per profile with `target_pct`, save is blocked unless
  the sum equals 100 (the dashboard shows a live "Falta / Sobra"
  indicator via Alpine.js).

**In progress (slice S03, 5 tasks with validation gates):**

- T01 — Data layer: Asset model + 0003 migration + cascade tests
- T02 — Routes: POST /assets + POST /assets/{id}/delete + server
  validation
- T03 — UI T1: read-only asset tree on dashboard (first user
  validation gate)
- T04 — UI T2: per-class "Adicionar ativo" form (second user
  validation gate)
- T05 — UI T3: per-row delete + full e2e demo (final S03 acceptance
  gate)

After S03: S04 (CSV importer, high risk), S05 (distribution
visualization polish, low risk), S06 (production readiness, medium
risk). Each future slice will be re-broken into smaller tasks before
execution, with UI validation gates per visible change.

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — manages Python 3.12 and the locked
  dependency set declared in `uv.lock`. Install with
  `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- (Optional, for the production image) [Docker](https://docs.docker.com/get-docker/)
  and Docker Compose v2. Used in S06.

---

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url> omaha
cd omaha

# 2. Install dependencies (creates .venv with Python 3.12 + locked deps)
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env and set a real SECRET_KEY (50+ random chars):
#   python -c "import secrets; print(secrets.token_urlsafe(50))"
# ADMIN_PASSWORD is the shared family password. Change it.
# DATABASE_URL defaults to sqlite:///./data/portfolio.db.

# 4. Run database migrations and seed the family user + profiles
uv run alembic upgrade head
uv run python -m omaha.seed
# (or just start the app — its startup hook runs both automatically)

# 5. Start the dev server
uv run uvicorn omaha.main:app --reload
```

The app listens on <http://localhost:8000>.

---

## Login and what to test (S01 + S02)

The seed creates the user `family` with the password from
`ADMIN_PASSWORD` in your `.env`, plus two profiles:

- **Italo** (display order 0)
- **Ana Livia** (display order 1)

To exercise S01 + S02 in the browser:

1. Open <http://localhost:8000>. You land on `/login`.
2. Sign in as `family` with `ADMIN_PASSWORD`.
3. Pick **Italo** on the profile selector.
4. On the dashboard, the S02 class editor is rendered. Type three
   class rows:
   - `Renda Fixa` — 60
   - `Acoes` — 30
   - `Reserva` — 10

   The "Falta" / "Sobra" indicator below the table updates live as
   you type. When the total reaches 100, the Save button enables.
5. Click **Salvar classes**. The page reloads with the three classes
   saved (the classes are now in the database, queryable via
   `sqlite3 data/portfolio.db "SELECT * FROM asset_classes;"`).
6. Try the validation: change `Reserva` from 10 to 5. The indicator
   flips to "Falta 5.00", the Save button disables, and saving is
   blocked on the server side even if you bypass the UI.
7. Switch to **Ana Livia** on the profile selector. Her dashboard is
   empty — class CRUD is per-profile and isolated.
8. Logout from the top-right menu. `/` redirects to `/login`.

For the liveness check: `curl http://localhost:8000/healthz` returns
`{"status": "ok"}`.

---

## Tests

```bash
uv run pytest                    # full suite (34 tests passing on main)
uv run pytest tests/test_X.py -v # a single file
uv run prek run --all-files      # ruff-format + ruff-check
```

---

## Production image

A multi-stage production Dockerfile and `docker compose -f prod.yml`
configuration are added in S06. The development Dockerfile and
`docker-compose.yml` in this repo are placeholders until then.

---

## Project layout

```
omaha/
├── src/omaha/            # FastAPI app
│   ├── auth.py           # password hashing + require_active_profile
│   ├── config.py         # pydantic-settings (reads .env)
│   ├── db.py             # SQLAlchemy 2.0 Base + engine + Session
│   ├── main.py           # create_app + lifespan
│   ├── models.py         # User, Profile, AssetClass, Asset, Position
│   ├── seed.py           # idempotent family + profiles seed
│   ├── routes/           # auth, classes, health, pages
│   ├── static/app.css    # design tokens + component styles
│   └── templates/        # base, login, profiles, dashboard
├── alembic/              # migrations
│   ├── env.py
│   └── versions/0001_initial.py
│                       └── versions/0002_macro_classes.py
├── tests/                # pytest suite
│   ├── conftest.py
│   └── test_t0*.py
├── data/portfolio.db     # SQLite file (gitignored, created at startup)
├── .env.example          # template for .env (gitignored real .env)
├── pyproject.toml        # uv-managed Python project
├── uv.lock               # locked dep set
├── Dockerfile            # placeholder until S06
├── docker-compose.yml    # placeholder until S06
└── prek.toml             # ruff hooks (format + check)
```
