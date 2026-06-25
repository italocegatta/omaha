---
name: refresh-for-test
description: Restart the omaha dev server and bring the DB to a known state so the user can hit the LAN URL and test in the browser. Trigger on requests to "subir", "servir", "buildar", "atualizar o ambiente", "preparar para teste", "refresh the interface", "restart server", "ready to test", or any task ending with "test this", "show me", "does it work?". Runs the AGENTS.md "Delivery finalization" checklist using taskipy tasks (`db-migrate` / `db-reset` / `db-clear-assets` / `db-seed`) so the dev DB and uvicorn process are in the right state before reporting done.
---

# Refresh for test — omaha

Run the AGENTS.md **Delivery finalization** checklist
(`AGENTS.md:264-369`) end-to-end before reporting done. User inspects the
running app, not the test report — a green test suite ≠ ready to test.

## When to use

- User asks to bring up / serve / restart / refresh the dev app.
- Task ends with "test this", "show me", "does it work?", "pra eu testar".
- Any feature/fix delivery that touches routes, templates, models,
  migrations, seed, login, or static assets.
- **Not** for pure doc / OpenSpec / non-runtime edits — no restart needed,
  but still report what changed.

## Hard rules (from AGENTS.md)

- **Bind `--host 0.0.0.0`.** Never `127.0.0.1`, never `localhost`.
- **Report LAN URL via `bash scripts/print_lan_url.sh`.** Never hardcode
  the IP. Canonical today: `http://192.168.1.6:8000`.
- **DB state must match what the user will see.** Default = **populated**
  (6 classes + 48 assets + 47 positions for Italo via CSV path).
- **Leaving the DB asset-free is a delivery failure** — user opens empty
  dashboard, concludes feature is broken.
- **Kill prior uvicorn** so new code loads.

## Recipe

Run all steps. Skip a step only if you have a verified reason and say so
in the final report.

### 1. Restart the dev server

Kill any prior `uvicorn omaha.main` and start fresh, fully detached so
the bash tool doesn't hang:

```bash
pkill -f "uvicorn omaha.main" 2>/dev/null || true
sleep 1
setsid bash -c 'exec uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000' \
  </dev/null >/tmp/omaha-uvicorn.log 2>&1 &
disown
```

`task serve` works in a foreground terminal; `serve-prod` is the
no-reload variant. For background spawns use the pattern above.

### 2. Smoke-check `/healthz` via LAN URL

```bash
URL=$(bash scripts/print_lan_url.sh)
curl -fsS --max-time 5 "$URL/healthz"
```

Expect `{"status":"ok","db":"ok","service":"omaha",...}`. If it fails,
fix before continuing.

### 3. Bring DB to the right state

Pick **one** based on what changed (do not guess, do not default to
"leave the DB alone"):

| Change type                              | Task                            |
|------------------------------------------|---------------------------------|
| New migration / model edit               | `uv run task db-migrate`        |
| Default — populated, ready to test       | `uv run task db-reset`          |
| User explicitly asked for empty import   | `uv run task db-clear-assets`   |
| Only seed / config layer changed         | `uv run task db-seed`           |

**Default for delivery = `db-reset`** unless the user explicitly asked
for an asset-free surface.

After `db-reset`, verify the row counts:

```bash
uv run python -c "import sqlite3; c=sqlite3.connect('data/portfolio.db'); cur=c.cursor()
print('classes', cur.execute('select count(*) from asset_classes').fetchone()[0])
print('assets', cur.execute('select count(*) from assets').fetchone()[0])
print('positions', cur.execute('select count(*) from positions').fetchone()[0])"
```

Expect `classes 6  assets 48  positions 47`. After `db-clear-assets`
expect `assets 0  positions 0  classes 6`.

### 4. Visual smoke-check the dashboard

A green `/healthz` is not enough — fetch the rendered page and confirm
seeded class names appear:

```bash
URL=$(bash scripts/print_lan_url.sh)
COOKIE=$(mktemp)
curl -c "$COOKIE" -X POST "$URL/login" \
  -d "username=Italo" -d "password=distendidos" -o /dev/null
curl -L -c "$COOKIE" -b "$COOKIE" -X POST "$URL/profiles/1/select" -o /dev/null
curl -L -b "$COOKIE" "$URL/" | grep -c "RF Din"
```

Expect `>= 1`. If zero, dashboard is empty — re-check DB state, do not
report done.

### 5. Report

Final message must include:

- `URL=$(bash scripts/print_lan_url.sh)` — the actual URL, not a
  hardcoded IP.
- One-line DB state: `"Italo: 6 classes + 48 assets + 47 positions"` /
  `"asset-free (6 classes, 0 assets, 0 positions)"` / etc.
- What to test — 1-2 sentences mapped to the user's request.

## Why

`uvicorn`'s `127.0.0.1` default is silent — server starts, logs look
healthy, user opens URL on client, gets `connection refused`, wastes a
round trip. The DB defaults drift the same way — agent restarts the
server but leaves whatever was last committed, user opens an empty or
stale dashboard, concludes the feature is broken. The checklist makes
both failures loud.

## Gotchas

- `pkill` against `uvicorn omaha.main` matches both old and newly
  spawned process if you fire them in the same shell. Spawn detached
  with `setsid ... </dev/null &` and `disown`, then verify with a
  separate `curl` call.
- `task serve` blocks the foreground — don't run it inline. Use the
  detach pattern above or `task serve-prod` in a detached terminal.
- `db-reset` wipes + reseeds via the CSV path
  (`scripts/seed_from_csv.py`) — it is the only sanctioned way to
  populate assets/positions. Inline literal seeds are forbidden by
  AGENTS.md "Seed data" rule.
- `ADMIN_PASSWORD` is locked to `distendidos` (family password); never
  suggest rotating it without owner sign-off.