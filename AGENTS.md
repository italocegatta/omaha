# AGENTS.md

Agent routing doc for the omaha repository. This file is **navigation only** —
it points at the canonical sources. **It does not redefine rules.**

> Golden rule: before touching anything, read
> **[openspec/PRD.md](openspec/PRD.md) §4 (Regras de Ouro)**. The 12 standing
> rules below are transcrito there. PRD is the single source of truth; this
> file is the table of contents.

---

## 1. How to read this repo

| If you want to…                                                       | Go to                                                  |
|------------------------------------------------------------------------|--------------------------------------------------------|
| Know what omaha is, who uses it, why it exists                         | [PRODUCT.md](PRODUCT.md)                               |
| Understand the visual system (tokens, type, elevation, motion)         | [DESIGN.md](DESIGN.md)                                 |
| Read a capability's contract (`SHALL` behavior)                        | `openspec/specs/<slug>/spec.md`                        |
| Pick up the **next unit of work**                                      | `openspec/roadmap.md`                                  |
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
- **[openspec/roadmap.md](openspec/roadmap.md)** — single planning file.
  Tracks slices (`F`/`R`/`T`/`D`/`I`) with lifecycle
  `Ready → Spec Proposed → Applying → Applied → Archived` + `Blocked`.
  1:1 slice → OpenSpec change folder via the slice's
  `Candidate OpenSpec change id`.
- **[openspec/changes/](openspec/changes/)** — per-slice OpenSpec change
  folders. `archive/` is historical.
- Skills that orchestrate the above: `openspec-propose`,
  `openspec-apply-change`, `openspec-archive-change`, `openspec-verify-change`,
  `openspec-sync-specs`, `openspec-roadmap`.

### 2.3.1 Orchestrator invocation model

- **Entry alias** — `@roadmap` maps to `.opencode/agents/roadmap.md` and
  `opencode.json` key `roadmap`. Primary orchestrator. Use this for all
  day-to-day orchestration.
- **Command entrypoint** — `/roadmap <demanda>` maps to
  `.opencode/command/roadmap.md`. Use this when command invocation is more
  reliable than `@` mention in the current UI/session.
- **API/tool subagent** — `task(..., subagent_type: roadmap)` is same
  orchestrator, but only for this API surface.
- **Skill** — `openspec-roadmap` is planner logic loaded *inside* that agent;
  it is not `@` mention itself.
- Stage subagents: `explore-oai/oc`, `propose-oai/oc`, `apply-oc/oai`, `review-oai/oc`, `finalize-oc/oai`.

Recommended usage:

1. `@roadmap <demanda>`
2. `/roadmap <demanda>`

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

The 12 invariants below live in PRD §4. Linking here so this doc stays
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
11. **DB mutation contract — destructive routes formalized** (R06 platform safety) — PRD §4.11
12. **Agent — prod DB is untouchable without explicit authorization** (2026-07-07, after incident) — PRD §4.12

---

## 5. OpenSpec Roadmap layer

Work that would otherwise bloat into one giant OpenSpec change gets
decomposed first via this layer.

| Step | What                                                            | Where                                                                       |
|------|-----------------------------------------------------------------|-----------------------------------------------------------------------------|
| 1    | PRD or issue                                                    | `openspec/PRD.md` (this repo) or issue tracker                              |
| 2    | Decompose into prioritized slices                               | `openspec/roadmap.md`                                                       |
| 3    | Slice status `Ready` → create OpenSpec change                   | `openspec-propose` → `openspec/changes/<Candidate OpenSpec change id>/`      |
| 4    | Implement                                                       | `openspec-apply-change` (slice → `Applying` → `Applied`)                    |
| 5    | Complete                                                        | `openspec-archive-change` (slice → `Archived`)                              |

**Rules (must follow):**

- `openspec/roadmap.md` is a planning register only — do **not** copy
  `proposal.md` / `design.md` / `tasks.md` into it.
- Implementable slices are 1:1 with OpenSpec changes. The slice's
  `Candidate OpenSpec change id` (format `<slice-id-lower>-<slice-title-kebab>`)
  is the change folder name — pass it verbatim to `openspec-propose`.
  Never invent a folder name from goal/PRD text.
- Slice lifecycle: `Ready` → `Spec Proposed` → `Applying` → `Applied`
  → `Archived` (`Blocked` when decisions are pending).
- Keep `next` atomic (one gate per command) and respect `Applying` WIP
  limits from the roadmap (max 2 globally, max 1 in critical domains).
- Run repo OpenSpec spec verification (`openspec/config.yaml` →
  `openspec_roadmap.quality_gate`) after each lifecycle gate and resolve
  issues before the next gate.
- Update the roadmap after every `propose`, `apply`, and `archive`.
- **After every `apply` that touches runtime code (routes, templates,
  models, seed, migrations, static assets), the agent MUST invoke the
  `refresh-for-test` skill and emit the mandatory delivery receipt
  (PRD §4.9) before reporting done. Skipping the receipt is a
  delivery failure — the user opens the URL and sees a stale or empty
  DB and concludes the feature is broken. No exceptions for "trivial"
  follow-up patches.
- Token/context limits come from `openspec_roadmap` in
  `openspec/config.yaml`. Do not load the full PRD unless the slice is
  ambiguous.

Anti-overengineering gate: do **not** route through this skill for
bugfixes under 30 min, isolated copy/UI tweaks, one-file refactors, or
exploratory spikes. Fix and ship.

**Skill location**

| Task                                              | Skill file                                                       |
|---------------------------------------------------|------------------------------------------------------------------|
| Bootstrap / lifecycle / decompose PRD into slices | `.agents/skills/openspec-roadmap/SKILL.md`                       |
| Templates, checklists, agent-docs snippet          | `.agents/skills/openspec-roadmap/REFERENCE.md`                   |

---

## 6. Companion files at the workspace root

- `README.md` — onboarding doc + Network access section (canonical for
  bind + URL).
- `pyproject.toml` — taskipy tasks (`[tool.taskipy.tasks]`).
- `.env.example` — never offers "rotate admin password" step (PRD §4.1).
- `.python-version` — pinned Python 3.12.
- `Dockerfile`, `prod.yml`, `nginx/` — production stack.

---

*AGENTS.md is a pointer, not a source. If you find yourself wanting to
add a rule here, put it in PRD §4 instead and link from §4 of this file.*
