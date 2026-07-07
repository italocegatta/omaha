## 1. Intro and quick-start refresh

- [x] 1.1 Rewrite the `# Omaha` intro paragraph to reflect the current state (rebalancing shipped, quotes live, family profiles with Família aggregate, dark warm-neutral palette)
- [x] 1.2 Update the **Quick start** command if the canonical invocation has shifted (verify `task serve` produces same result as the explicit `uvicorn` invocation)
- [x] 1.3 Mention `task db-reset` in the Quick start or Development tasks section as the canonical reset path

## 2. Development tasks table

- [x] 2.1 Add `test-bdd` (BDD-only pytest run)
- [x] 2.2 Add `test-integration` (integration-only pytest run)
- [x] 2.3 Add `mutation`, `mutation-report`, `mutation-baseline` (T03)
- [x] 2.4 Confirm every row in the table maps to an actual `[tool.taskipy.tasks]` entry (run `uv run task --list` and diff)

## 3. Production deploy section

- [x] 3.1 Remove the manual `certbot certonly --standalone` step (I02 owns the TLS renewal section once I02 lands)
- [x] 3.2 Replace with a one-line cross-reference: "TLS cert renewal is automated by the `certbot` scheduler service (see **Operação / TLS renewal** — added by I02)"
- [x] 3.3 Confirm the build step (`docker build -t omaha:prod .`) and the named-volume warning still apply unchanged

## 4. Backup & restore section

- [x] 4.1 Remove the host-cron block (`/etc/cron.d/omaha-backup`) — I01 owns the backup cadence section once I01 lands
- [x] 4.2 Replace with a one-line cross-reference: "Scheduled backups run automatically via the `backup-scheduler` service (see **Operação / Backup scheduler** — added by I01). Manual one-shot backups still work via `task backup` / `docker compose -f prod.yml run --rm backup`"
- [x] 4.3 Keep the **Restore** subsection verbatim (it covers both prod named-volume and dev bind-mount paths and is still accurate)

## 5. Testing the app section

- [x] 5.1 Update the dashboard URL from `/` to `/patrimonio`
- [x] 5.2 Remove the "Click **Importar CSV** in the sidebar" instruction; describe the buttons as living at the top of the patrimônio body (post-F02 redistribution)
- [x] 5.3 Update the profile-switcher description to mention the Família option as a peer of Italo / Ana (post-F07)
- [x] 5.4 Update the expected `db-reset` counts to the current baseline (Italo=6/48/47, Ana=6/52/52 + Família sentinel) — confirm by running `task db-reset` and capturing output
- [x] 5.5 Confirm `bash scripts/print_lan_url.sh` reference stays prominent

## 6. Project layout tree

- [x] 6.1 Replace `templates/dashboard.html` with `templates/patrimonio.html`
- [x] 6.2 Drop `_sidebar.html` from the templates list (deleted by F02)
- [x] 6.3 Add the six `_patrimonio_*.html` partials introduced by R04
- [x] 6.4 Add `src/omaha/quotes/provider/` (R03 refactor) and note `provider.py` was retired
- [x] 6.5 Add `nginx/` and `prod.yml` at the repo root (already documented indirectly via Production deploy; tree should reflect them)
- [x] 6.6 Add `openspec/` at the repo root and reference PRD + roadmap + specs + changes

## 7. Project specs section

- [x] 7.1 Replace the `.gsd/` bullet list with an `openspec/`-rooted list: `PRD.md`, `roadmap.md`, `specs/<capability>/spec.md`, `changes/<change-id>/`
- [x] 7.2 Drop `STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` / `DECISIONS.md` / `KNOWLEDGE.md` / `milestones/M001/` references
- [x] 7.3 Add a one-line pointer to `AGENTS.md` for the agent routing table

## 8. Spec gate + archive

- [x] 8.1 `openspec validate d01-refresh-readme --json` returns `valid: true`
- [ ] 8.2 `openspec validate readme-freshness --json` returns `valid: true` *(deferred — spec lives in delta until archive sync; will pass once `openspec archive` materialises it under `openspec/specs/readme-freshness/`)*
- [x] 8.3 Run `task lint` — green (no Python touched; ruff + prek hooks pass)
- [x] 8.4 Confirm `bash scripts/print_lan_url.sh` still prints the correct LAN URL (smoke check)
- [ ] 8.5 Archive via `openspec archive d01-refresh-readme`; sync spec delta into `openspec/specs/readme-freshness/spec.md` *(next manual `next` gate)*