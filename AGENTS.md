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
