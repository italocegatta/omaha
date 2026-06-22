# AGENTS.md

Project-level rules for the coding agent. Overrides defaults.

## Network access — non-negotiable

The dev app is **always** accessed from another machine on the LAN. The
local dev host is a server, not a client. The default `uvicorn` bind
(`127.0.0.1`) is **wrong** — it makes the app unreachable from the
client.

### Rules

1. **Bind `--host 0.0.0.0` always.** Never `127.0.0.1`, never
   `--host localhost`. The dev uvicorn command is:
   `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`.
2. **Report the LAN IP, never `localhost`.** The canonical address is
   `http://192.168.1.7:8000`. If the host IP changes, re-detect with
   `ip -4 addr | grep inet` and use the LAN/Tailscale address. Never
   write `http://localhost:8000` or `http://127.0.0.1:8000` in
   chat output, in documentation, or in test instructions meant for a
   human.

> **Verifique o IP da máquina antes de usar:** rode
> `ip -4 addr | grep "inet " | grep -v 127.0.0.1` para descobrir o IP real.
> Se este host é `192.168.1.6`, use `http://192.168.1.6:8000`. O
> `192.168.1.7` aqui é referência histórica; o IP pode variar entre máquinas.

3. **README "Network access" section is the source of truth** for
   bind + address. Read it before any "start the app" instruction.

### When this applies

- Starting the dev server for a manual UI test.
- Telling the user how to reach the app.
- Writing or updating any doc / runbook / README that says how to
  open the app.
- Running smoke checks (`curl http://...`) — use the LAN IP, not
  `localhost`.

### Why

`uvicorn`'s `127.0.0.1` default is silent: the server starts, the
process logs look healthy, the user opens the URL on their client
machine, gets `connection refused`, and wastes a round trip. The
README's "Network access" section (lines 143-161) already documents
this; this file is the agent's standing reminder.

## Seed data — classes only, never assets

**Rule:** automated / agent-driven data creation is limited to
**classes** (AssetClass rows). The agent MUST NOT create **assets**
(Asset rows) — neither via `seed.py`, fixtures, ad-hoc scripts, demo
wiring, nor any change under `openspec/changes/`.

The canonical seed (`src/omaha/seed.py`) creates users + profiles only.
It is correct as-is. Do not extend it to seed assets, and do not
introduce parallel seeding paths that create assets.

### Why

Real assets reflect real portfolio positions. Auto-populating fictional
assets pollutes the user's view and breaks the dashboard's signal. The
user supplies assets explicitly through the import flow (CSV upload
via the modal that this project is fixing).

### When this applies

- Editing `src/omaha/seed.py` — leave it user+profile only.
- Writing demo / smoke / pre-population scripts — assets are off-limits.
- Drafting OpenSpec changes that promise "fresh state" — describe the
  empty-asset baseline; do not propose seeding assets.
- Reviewing a PR that introduces asset creation outside the import
  flow — flag it.
- Loading fixtures in tests is fine (tests have their own scope), but
  the dev DB the user inspects at `http://192.168.1.7:8000` must stay
  asset-free until the user runs an import.

## Alpine `<select>` + dynamic `<template x-for>` options — binding gotcha

**Rule:** for a `<select>` whose options are rendered by an inner
`<template x-for>`, the two-way bind MUST be:

```html
<select x-init="$nextTick(() => { const a = <bound-expr>; if (a) $el.value = a.<id-field> ?? ''; })"
        x-effect="(() => { const a = <bound-expr>; if (a) $el.value = a.<id-field> ?? ''; })()"
        @change="<bound-expr>.<id-field> = $event.target.value">
  <option value="">Selecione...</option>
  <template x-for="ac in <options-array>" :key="ac.id">
    <option :value="ac.id" x-text="ac.name"></option>
  </template>
</select>
```

### Why

- `x-model` on `<select>` does NOT re-sync `select.value` when the
  options change. It only re-syncs when the bound expression changes.
  When the inner `<template x-for>` adds the matching `<option>` after
  the `x-model` directive has already run, the select stays on the
  placeholder (`value=""`) because no option matched at the time of
  the bind.
- `x-effect` alone is insufficient for the *initial* render: there is
  no reactive state change between the `<select>` mount and the inner
  template's option render — both happen in the same tick. The effect
  fires once, before the options exist, and never fires again because
  the bound value did not change.
- `$nextTick` in `x-init` defers the `select.value = X` assignment to
  the next microtask, which runs *after* Alpine has finished
  processing the inner `<template x-for>`. By then the matching
  `<option>` exists, and the assignment sticks.
- The `x-effect` covers the case where the bound value changes later
  (e.g. user override via `@change` triggers a re-render).
- The `@change` keeps the source-of-truth property in sync after
  manual user picks.

### Anti-pattern (DO NOT use)

```html
<!-- BROKEN: select.value set before options exist; never re-syncs -->
<select x-model="assignments[ticker].class_id" ...>
  <option value="">Selecione...</option>
  <template x-for="ac in assetClasses" :key="ac.id">
    <option :value="ac.id" x-text="ac.name"></option>
  </template>
</select>
```

```html
<!-- ALSO BROKEN: x-effect reads only the bound value, not the
     options array; the initial render races the inner template. -->
<select x-effect="$el.value = assignments[ticker].class_id" ...>
```

### When this applies

- Any modal/table/form in `src/omaha/templates/*.html` with a
  `<select>` whose options come from a server-driven list
  (classes, profiles, broker tickers, etc.).
- Adding a new asset-class picker, target-percentage selector, or
  profile switcher.
- Code review on Alpine templates: if a `<select>` uses `:value` or
  `x-model` with a `<template x-for>` child, flag it.

### Reference implementation

- `src/omaha/templates/dashboard.html:510` (auto-matched) and `:553`
  (unmatched) — the import modal's class picker.
- Change: `openspec/changes/fix-import-modal-select-binding/`. Tasks
  list and design.md are stale (still describe the failed `x-model`
  attempt); the live code uses the `x-init $nextTick` + `x-effect`
  pattern. Do not "fix" the code to match the change artifacts — fix
  the change artifacts.

## Test marker rule — explicit allow-list, not pattern matching

**Rule:** `tests/conftest.py::pytest_collection_modifyitems` partitions
the suite via two lists:

- `_INTEGRATION_PREFIXES` — full path prefixes for files that hit DB,
  TestClient, or the audit pipeline. Currently S02/S03/S04 + T01 model
  tests + T02 routes/seed + T03 routes/auth/e2e + T04 e2e + T06
  backup/healthz + T99.
- `_UNIT_FILES` — full file basenames for the small set of pure-function
  tests (audit, parsers, validators, dockerfile smoke, logging). These
  predate the integration list and would otherwise trip
  `UnknownTestPath`.
- `tests/e2e/*.py` — no marker, run by `task test-e2e`.
- `tests/audit_integration/*.py` — `@pytest.mark.integration`.
- A module-level `pytestmark` wins over the path rule (already
  supported; `test_audit_inventory.py` uses this).

Any `tests/test_*.py` file that hits DB/TestClient but is NOT in
`_INTEGRATION_PREFIXES` emits a `UnknownTestPath` warning. The warning
is the loud-future-drift signal: if you add `tests/test_t07_*.py` that
hits DB, you MUST also add its prefix to `_INTEGRATION_PREFIXES`,
otherwise the file silently becomes `unit` and pollutes the unit subset.

### Why

The previous rule used a coarse "default everything to `unit`" branch
with carve-outs for `tests/e2e/` and `tests/audit_integration/`. Net
effect: ~25 files that hit DB + TestClient (S02/S03/S04 + T0* families)
were silently tagged `unit`, defeating the purpose of
`task test-integration`. `task test-unit` ran 277 tests in 44s; with
the explicit allow-list it runs 121 tests in 1.3s.

### When this applies

- Adding a new `tests/test_*.py` file that hits DB / TestClient — add
  the prefix to `_INTEGRATION_PREFIXES` in `tests/conftest.py`.
- Adding a new pure-function test under `tests/` — add the file basename
  to `_UNIT_FILES` to silence the `UnknownTestPath` warning.
- Reviewing a PR that introduces a new test file in `tests/` — verify
  the marker assignment matches what the test does.

## Taskipy — use `task <name>`, not raw commands

**Rule:** prefer `uv run task <name>` (or `task <name>` with venv
active) over typing the underlying command. Tasks live in
`pyproject.toml` under `[tool.taskipy.tasks]`. `use_vars = true` means
`{app_target}` and friends get expanded — literal braces in commands
must be written as `{{}}`.

Canonical tasks (full list: `uv run task --list`):

| Task              | Purpose                                                  |
|-------------------|----------------------------------------------------------|
| `serve`           | uvicorn `--host 0.0.0.0 --port 8000 --reload`            |
| `serve-prod`      | uvicorn `--host 0.0.0.0 --port 8000` (no reload)         |
| `test`            | full suite (unit + integration + e2e)                    |
| `test-unit`       | `pytest -m unit` — pure-function, no DB / no HTTP         |
| `test-integration`| `pytest -m integration` — DB + TestClient + audit        |
| `test-e2e`        | `pytest tests/e2e -v` — Playwright                       |
| `test-file`       | `task test-file tests/test_X.py`                         |
| `test-pattern`    | `task test-pattern "smoke"` — `-k` substring match        |
| `test-one`        | `task test-one tests/test_X.py::test_y` — single node    |
| `lint`            | `prek run --all-files` (ruff format check + ruff --fix)  |
| `format`          | `ruff format .`                                          |
| `check`           | `lint && test-unit` — CI gate                            |
| `db-migrate`      | `alembic upgrade head`                                   |
| `db-revision`     | `alembic revision --autogenerate` (pass `-m "msg"`)       |
| `db-seed`         | idempotent family + profiles seed                        |
| `db-reset`        | wipe + reseed Italo for manual import-flow testing       |
| `db-clear-assets` | delete ALL asset rows (keeps classes)                    |
| `db-current`      | show Alembic head                                        |
| `db-history`      | show full migration timeline                             |
| `db-downgrade`    | revert last migration                                    |
| `install`         | `uv sync`                                                |
| `install-e2e`     | Playwright Chromium download (one-time)                  |
| `prek-install`    | install prek git hooks                                   |
| `docker-up`       | `docker compose up -d` (dev stack)                       |
| `docker-down`     | `docker compose down`                                    |
| `prod-up`         | `docker compose -f prod.yml up -d`                       |
| `prod-down`       | `docker compose -f prod.yml down` — `down -v` wipes DB   |
| `prod-logs`       | stream prod logs                                         |
| `prod-rebuild`    | rebuild prod image + restart stack                       |
| `backup`          | one-off snapshot to `./backups/` (`prod.yml` profile)    |
| `clean`           | wipe `__pycache__`, `.pytest_cache`, `.ruff_cache`        |
| `coverage`        | pytest + coverage report                                 |
| `secret-key`      | generate cryptographically random `SECRET_KEY`           |

### Why

Typing `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`
inline burns cycles re-deriving the bind flags every session, and
risks dropping `--host 0.0.0.0` (see "Network access" above).
`task serve` is the canonical entrypoint; it always binds correctly
and picks up new tasks automatically as they're added.

### When this applies

- Starting/stopping the dev server for any manual test.
- Running tests, lint, format, or coverage during dev.
- Any DB operation (migrate, seed, reset, clear, downgrade).
- Docker / prod stack control.
- First-time setup (`install`, `install-e2e`, `prek-install`).

### Gotchas

- `task serve` blocks the foreground — for parallel work, background it
  with `nohup ... &` or run `serve-prod` in a detached terminal.
- `docker compose -f prod.yml down` preserves the `omaha-data` named
  volume; only `down -v` wipes the DB.
- `db-clear-assets` is the asset wipe, NOT `db-reset` (which reseeds
  the full family + profile).
