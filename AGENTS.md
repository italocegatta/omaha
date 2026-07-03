# AGENTS.md

Agent routing doc for the omaha repository. This file is **navigation only** —
it points at the canonical sources. **It does not redefine rules.**

> Golden rule: before touching anything, read
> **[openspec/PRD.md](openspec/PRD.md) §4 (Regras de Ouro)**. The 10 standing
> rules below are transcrito there. PRD is the single source of truth; this
> file is the table of contents.

---

## 1. How to read this repo

| If you want to…                                                       | Go to                                                  |
|------------------------------------------------------------------------|--------------------------------------------------------|
| Know what omaha is, who uses it, why it exists                         | [PRODUCT.md](PRODUCT.md)                               |
| Understand the visual system (tokens, type, elevation, motion)         | [DESIGN.md](DESIGN.md)                                 |
| Read a capability's contract (`SHALL` behavior)                        | `openspec/specs/<slug>/spec.md`                        |
| Pick up the **next unit of work**                                      | `openspec/roadmap.md` (bootstrap pending)              |
| Create / apply / archive a change                                      | `openspec-roadmap` (orchestrates the OpenSpec CLI skills) |
| Ship a browser-visible change end-to-end                               | `refresh-for-test` skill                               |
| Look at the source-of-truth seed                                      | `data/seed/` + [data/seed/README.md](data/seed/README.md) |
| See the running app                                                    | `bash scripts/print_lan_url.sh` → open the LAN URL     |
| Run a test subset                                                      | `task test-unit` / `test-integration` / `test-e2e` / `test-bdd` |

---

## 2. Canonical sources (no duplication)

These documents own their domains. **Do not rewrite their content into
AGENTS.md** — link to them.

### 2.1 Product identity
- **[PRODUCT.md](PRODUCT.md)** — users, purpose, anti-references, design
  principles. PR-shaped edits to identity go here.
- **[DESIGN.md](DESIGN.md)** — tokens, typography, spacing, radius,
  elevation, motion, anti-patterns, migration path. The polish pass edits
  this in lockstep with `src/omaha/static/app.css`.

### 2.2 Product contract
- **[openspec/PRD.md](openspec/PRD.md)** — capabilities inventory, model,
  ops, and the **10 standing rules** (operational invariants). Read §4
  before proposing any change.
- **[openspec/config.yaml](openspec/config.yaml)** — `schema: spec-driven`,
  project context, and roadmap token ceilings (`openspec_roadmap`).
- **[openspec/specs/](openspec/specs/)** — 34 stable capability contracts.
  Source of truth for "what `SHALL` happen". Each spec is owned by an
  archived or active OpenSpec change.

### 2.3 Execution layer
- **[openspec/roadmap.md](openspec/roadmap.md)** — does **not** exist yet
  (bootstrap pending). When it lands, this is where slices (`F`/`R`/`T`/`D`/`I`)
  are tracked, with lifecycle `Ready → Spec Proposed → Applying → Applied →
  Archived` + `Blocked`.
- **[openspec/changes/](openspec/changes/)** — per-slice OpenSpec change
  folders. `archive/` is historical.
- Skills that orchestrate the above: `openspec-propose`,
  `openspec-apply-change`, `openspec-archive-change`, `openspec-verify-change`,
  `openspec-sync-specs`, `openspec-roadmap`.

### 2.4 Operational scripts
- **`scripts/print_lan_url.sh`** — discover the canonical dev URL.
- **`scripts/seed_from_csv.py`** — only path that creates `AssetClass`,
  `Asset`, `Position` (PRD §4.3 forbids inline seeds).
- **`scripts/reset_both_profiles.py`** — backstop for `task db-reset`.
- **`scripts/backup.py`** — hot SQLite snapshot for `./backups/`.
- **`scripts/snapshot_to_csv.py`** — DB → CSV (lossless round-trip).
- **`scripts/generate_contrast_audit.py`** — thin wrapper over
  `omaha.audit.cli.main`.

---

## 3. Agent workflow (high level)

1. **Orient.** PRD §1 (identidade) + relevant spec(s). If the task is
   browser-visible, run **refresh-for-test** before declaring done (PRD §4.9).
2. **Pick next slice.** Resolve from `openspec/roadmap.md` (when it
   exists); otherwise pull from PRD §5.3 (horizonte) and convert to a
   slice in the roadmap first. *Do not invent slice IDs ad-hoc.*
3. **Propose.** Delegate to `openspec-propose` with the slice's
   `Candidate OpenSpec change id` exactly — no goal-derived slugs.
4. **Verify spec health** after `propose`, fix, then proceed.
5. **Apply.** Delegate to `openspec-apply-change`. Code goes under the
   change's `tasks.md`.
6. **Verify spec health** after `apply`.
7. **Archive.** Delegate to `openspec-archive-change`. Update roadmap
   status to `Archived`.
8. **Verify spec health** after `archive`. Pick next.

For **bugfixes < 30 min** or isolated tweaks, skip the OpenSpec loop —
just fix and ship. The OpenSpec gate exists for changes that touch tests
or production behavior; a one-line CSS patch does not.

---

## 4. Standing rules — READ [PRD §4](openspec/PRD.md#4-regras-de-ouro-operational-invariants)

The 10 invariants below live in PRD §4. Linking here so this doc stays
useful as a quick pointer. **Edit them only in the PRD.**

1. **Family password — locked** (`distendidos`) — PRD §4.1
2. **Network access — bind `0.0.0.0` always** — PRD §4.2
3. **Seed via CSV — single path for asset/position creation** — PRD §4.3
4. **Alpine `<select>` + dynamic `<template x-for>` — binding gotcha** — PRD §4.4
5. **Import preview response ↔ Alpine template sync** — PRD §4.5
6. **Test marker — explicit allow-list** — PRD §4.6
7. **BDD workflows — extraction by growth trend** — PRD §4.7
8. **Taskipy — `task <name>` not raw commands** — PRD §4.8
9. **Delivery finalization — `refresh-for-test` skill** — PRD §4.9
10. **Brand register — domestic, no ornament** — PRD §4.10

---

## 5. Companion files at the workspace root

- `README.md` — onboarding doc + Network access section (canonical for
  bind + URL).
- `pyproject.toml` — taskipy tasks (`[tool.taskipy.tasks]`).
- `.env.example` — never offers "rotate admin password" step (PRD §4.1).
- `.python-version` — pinned Python 3.12.
- `Dockerfile`, `prod.yml`, `nginx/` — production stack.

---

*AGENTS.md is a pointer, not a source. If you find yourself wanting to
add a rule here, put it in PRD §4 instead and link from §4 of this file.*
