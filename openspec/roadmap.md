# Roadmap

PRD: [`openspec/PRD.md`](PRD.md) (última revisão 2026-07-03).
Skill de orquestração: `openspec-roadmap`.

Roadmap é registro curto de execução. Gera `OpenSpec changes` por fatia.
Não duplicar `proposal.md` / `design.md` / `tasks.md` aqui.

## How To Use This Roadmap

1. Escolher a fatia `Ready` de maior prioridade (ver Recommended Execution Order).
2. Delegar `openspec-propose` passando o `Candidate OpenSpec change id`
   exato desta fatia (1:1 com `openspec/changes/<id>/`).
3. Mover lifecycle e atualizar o `Progress` da fatia após cada gate.
4. Manter escopo limitado à fatia. Mudanças adicionais viram novas
   fatias via `add` / `add-next`.

Comandos rápidos suportados: `status`, `next`, `next:dry`, `start <id>`,
`add "<intent>"`, `add-next "<intent>"`, `update <id> "<delta>"`,
`block <id>`, `deprecate <id>`, `restore <id>`, `reorder`.

## Status Model

`Ready` → `Spec Proposed` → `Applying` → `Applied` → `Archived`, mais `Blocked`.

## Parallelism and WIP limits

- Múltiplas fatias podem coexistir em `Spec Proposed`.
- Cap global: no máximo **2** fatias em `Applying` simultaneamente.
- Cap área crítica (auth, import, rebalance solver, backup): no máximo **1**
  fatia em `Applying`. Domínio crítico aqui = rebalance solver + cotação
  yfinance (ambos tocam o cálculo CVXPY em `src/omaha/rebalance/`).
- `next` permanece atômico: um comando move um gate de uma fatia.

## Spec verification gate (mandatory)

- Após `openspec-propose` → verificar spec antes de `openspec-apply-change`.
- Após `openspec-apply-change` → verificar spec antes de `openspec-archive-change`.
- Após `openspec-archive-change` → verificar spec antes de escolher a próxima fatia.
- Falha = parar, resolver, re-rodar, continuar.

Operacionalmente: rodar `opsx list --specs` (ver `openspec/config.yaml` se a
verificação for específica por comando) entre gates.

## Slices

All previous slices archived or closed. F15 is next active slice.

### F01 - Consolidação cross-profile (visão household agregada)
Status: `Archived` (superseded by F06) — 2026-07-04
Archive: `openspec/changes/archive/2026-07-04-f01-household-cross-profile-consolidation/`

### F02 - Top-level layout: tab nav + Patrimônio + Rebalanceamento + stubs
Status: `Archived` — 2026-07-04
Archive: `openspec/changes/archive/2026-07-04-f02-top-level-tab-nav-and-patrimonio/`

### F03 - Página Rentabilidade
Status: `Closed` — 2026-07-06 (owner deferiu; proposal archived sem apply)
Archive: `openspec/changes/archive/2026-07-06-f03-rentabilidade-page/`
Reactivation: mover folder de volta + re-validar.

### F04 - Página Proventos
Status: `Deprecated` — 2026-07-06 (owner: "F03 e F04 só no futuro")
Reactivation: `restore f04` quando owner retomar.

### F05 - Dark mode palette swap
Status: `Archived` — 2026-07-05
Archive: `openspec/changes/archive/2026-07-05-f05-dark-mode-palette-swap/`

### F06 - Agregado família inteira (cross-User, full-join por nome)
Status: `Archived` — 2026-07-05
Archive: `openspec/changes/archive/2026-07-05-f06-family-household-full-join-aggregate/`

### F07 - Família como opção no profile-switcher
Status: `Archived` — 2026-07-05
Archive: `openspec/changes/archive/2026-07-05-f07-familia-as-profile-option/`

### F08 - Palette overhaul v2 (apply D02)
Status: `Archived` (proposal-only, no implementation) — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-f08-palette-overhaul-v2/`

### F09 - Typography refresh (Red Hat Display + Inter)
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-f09-typography-refresh/`

### F10 - Component state language + table pattern
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-f10-component-state-language-and-table-pattern/`

### F11 - Sidebar reintroduce
Status: `Deprecated` — 2026-07-07 (owner: "não faz sentido")

### F12 - Material Symbols icons
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-f12-material-symbols-icons/`

### F13 - Light/dark toggle
Status: `Deprecated` — 2026-07-07 (owner: "não faz sentido")

### R01 - Limpar arquivos órfãos
Status: `Archived` — 2026-07-03
Archive: `openspec/changes/archive/2026-07-03-r01-clean-orphaned-files-and-snapshots/`

### R02 - Revisar sistema de seed (CSV package)
Status: `Archived` — 2026-07-06
Archive: `openspec/changes/archive/2026-07-06-r02-revise-csv-seed-system/`

### R03 - Extrair quote_provider adapter
Status: `Archived` — 2026-07-06
Archive: `openspec/changes/archive/2026-07-06-r03-extract-quote-provider-adapter/`

### R04 - Partialize patrimonio.html
Status: `Archived` — 2026-07-06
Archive: `openspec/changes/archive/2026-07-06-r04-partialize-patrimonio-template/`

### R05 - Hex literal audit + migration
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-r05-hex-literal-audit-and-migration/`

### R06 - DB mutation guards + confirmation snapshot
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-r06-db-mutation-guards-confirmation-snapshot-audit/`

### T01 - BDD + e2e suite 100% green
Status: `Archived` — 2026-07-04
Archive: `openspec/changes/archive/2026-07-04-t01-bdd-e2e-suite-100-green/`

### T02 - Coverage report no CI
Status: `Archived` (GH Actions deferred per owner) — 2026-07-06
Archive: `openspec/changes/archive/2026-07-06-t02-coverage-report-in-ci/`
Reactivation: workflow dormente em `.github/workflows/ci.yml`.

### T03 - Mutation testing rebalance engine
Status: `Archived` — 2026-07-06
Archive: `openspec/changes/archive/2026-07-06-t03-mutation-testing-rebalance-engine/`

### T04 - E2E class section alignment baselines
Status: `Archived` — 2026-07-04
Archive: `openspec/changes/archive/2026-07-04-t04-e2e-class-section-alignment-baselines/`

### T05 - BDD step-def drift after F02
Status: `Archived` — 2026-07-06
Archive: `openspec/changes/archive/2026-07-06-t05-bdd-step-def-drift-after-f02/`

### T06 - Visual regression baseline
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-t06-visual-regression-baseline/`

### I01 - Agendamento automático de backup
Status: `Archived` — 2026-07-06
Archive: `openspec/changes/archive/2026-07-06-i01-automatic-backup-scheduling/`
Caveat: `Dockerfile` não copia `scripts/` — gap pré-existente.

### I02 - TLS cert renewal automation
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-i02-tls-cert-renewal-automation/`

### D01 - Refresh do README
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-d01-refresh-readme/`

### D02 - Decisão de register do design system
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-d02-design-register-decision/`

### F14 - Catppuccin Frappe theme + component differentiation
Status: `Archived` — 2026-07-08
Archive: `openspec/changes/archive/2026-07-08-f14-catppuccin-frappe-theme/`
Goal: Replace warm-brown dark palette (hue 60) with Catppuccin Frappe
  cool blue-gray (hue ~274). Differentiate components via surface
  elevation, class-colored headers, sunk asset tables, compact rows,
  angular borders, and high-contrast numbers.
Candidate OpenSpec change id: `f14-catppuccin-frappe-theme`
Spec link: `openspec/changes/f14-catppuccin-frappe-theme/`
Spec: `openspec/specs/color-tokens/spec.md` (update),
  `openspec/specs/component-state-language/spec.md` (update)
Files: `src/omaha/static/app.css`, `DESIGN.md`,
  `_patrimonio_class_section.html`, `_patrimonio_portfolio_header.html`
Scope:
  1. Token swap: --bg, --surface, --surface-sunk, --border, --ink,
     --ink-muted, --accent, --positive, --negative, --error-bg/fg,
     --class-1..6 → Catppuccin Frappe OKLCH values.
  2. New token: --surface-elevated (portfolio header).
  3. Class header: tinted bg (color-mix 30% class-color) + 2px solid
     border-bottom. No swatch square — name carries the color.
  4. Asset table: --surface-sunk background (inset feel).
  5. Row padding: 0.55rem → 0.28rem (−50% vertical).
  6. Border-radius: pills/toggles 999px → 4px (angular).
  7. Trade toggle: Liberado = success green, Bloqueado = danger red.
  8. Number contrast: all numeric cells use --ink at weight 600+.
  9. Update DESIGN.md tokens table + color strategy section.
  10. Update visual baselines (task test-visual).
Notes: Mockup validated at /mockup (v4). Theme source:
  Catppuccin Frappe (https://catppuccin.com/palette).
  Hue 274 (periwinkle blue) replaces hue 60 (warm brown).
  PRD §4.10 brand register: "domestic, no ornament" — theme
  swap is palette-only, no gradient/glow/glassmorphism.
Progress:
  - 2026-07-08: Propose complete. All artifacts created (proposal, design,
    specs, tasks). Change validated. Status → Spec Proposed.
  - 2026-07-08: Apply complete. All 27 tasks implemented:
    token swap (1.1-1.7), component differentiation (2.1-2.6),
    class header differentiation (3.1-3.4), portfolio header elevation
    (4.1), Python class-color sync (5.1-5.2), DESIGN.md update (6.1-6.3),
    test updates (7.1, 7.3), mockup route removal (8.1).
    Visual baselines (7.2) need regeneration by owner.
    Status → Applied.
  - 2026-07-08: Refresh-for-test complete. Server restarted at
    http://192.168.1.6:8000. DB: 12 classes, 100 assets, 99 positions.
    Dashboard renders correctly. Delivery receipt emitted.

### F15 - Patrimônio table redesign for class and asset metrics
Status: `Archived` — 2026-07-08
Goal: Rebuild class totals row + asset table on `/patrimonio` to match
  new operator layout: ordered columns as mockup, nested `Classe`
  (`Atual` / `Alvo` / `Desvio`) and `Carteira` (`Atual` / `Alvo` /
  `Desvio`) groups, class totals row aligned to asset columns, split
  internal `Ganho` subcolumns (absolute + percentual) with single-column
  visual appearance, sortable columns across text and numeric fields,
  per-column formatting rules, positive/negative icon+color signaling for
  `Desvio` and `Ganho`, keep `Compra` / `Venda` / `Moeda` unchanged, and
  remove legacy asset-row `Classe` column.
Candidate OpenSpec change id: `f15-patrimonio-table-redesign-for-class-and-asset-metrics`
Archive: `openspec/changes/archive/2026-07-08-f15-patrimonio-table-redesign-for-class-and-asset-metrics/`
Spec: `openspec/specs/class-section-totals/spec.md` (update),
  `openspec/specs/patrimonio-portfolio-header/spec.md` (update),
  `openspec/specs/dashboard-inline-editing/spec.md` (update),
  `openspec/specs/asset-trade-flags/spec.md` (confirm unchanged `Compra` /
  `Venda` / `Moeda` behavior)
Files: `src/omaha/templates/_patrimonio_class_section.html`,
  `src/omaha/templates/_patrimonio_portfolio_header.html`,
  `src/omaha/templates/_patrimonio_add_asset_modal.html`,
  `src/omaha/routes/pages.py`, `src/omaha/static/app.css`,
  `tests/e2e/`, `tests/integration/`, `tests/bdd/`
Scope:
  1. Reorder asset-table columns to match approved mockup.
  2. Replace flat class metrics/header alignment contract with grouped
     `Classe` and `Carteira` subheaders and aligned class totals row.
  3. Add asset columns for aggregated quantity, average price, gain value,
     gain %, position/current value, class current/target/deviation, and
     portfolio current/target/deviation while preserving `Compra`,
     `Venda`, and `Moeda`.
  4. Make every visible column sortable (alphabetical for `Ativo`, numeric
     asc/desc for metrics).
  5. Define per-column formatting contract: currency prefix (`R$` / `US$`),
     percent suffix, thousands separator, absolute-value rounding, and one
     decimal for percentual/decimal cells.
  6. Render signed visual state for `Desvio` and `Ganho` with directional
     iconography and positive/negative color semantics.
  7. Keep `Ganho` as two internal cells for alignment/formatting while
     preserving one-column visual presentation for operator.
  8. Remove legacy asset-row `Classe` column and migrate existing tests,
     selectors, and alignment assertions to new contract.
Notes: Schema check 2026-07-08: no DB slice needed right now. Current
  models/import path already persist required source data via
  `Position.qty`, `Position.avg_price`, `Position.total_invested`,
  `Position.total_current`, `Asset.target_pct`, `Asset.buy_enabled`,
  `Asset.sell_enabled`, `Asset.currency_code`, and `AssetClass.target_pct`.
  New layout is primarily aggregation/rendering/spec work. If exact asset-level
  broker cost basis semantics prove impossible from existing rows during
  propose/apply, open follow-up slice instead of mutating F15 scope.
Progress:
  - 2026-07-08: Added from owner mockup + requirements. Positioned as next
    feature slice after F14 archive. DB/schema review complete; no missing
    persisted field identified for requested columns.
  - 2026-07-08: Propose complete. Created proposal, design, tasks, and delta
    specs under `openspec/changes/f15-patrimonio-table-redesign-for-class-and-asset-metrics/`.
    Spec health gate passed via `openspec list --specs` (`opsx` alias not
    present in this shell). Status -> Spec Proposed.
  - 2026-07-08: Apply complete. Rebuilt `/patrimonio` class table into
    16-column grouped layout (`Classe` / `Carteira`), split `Ganho`
    into aligned absolute/% subcells, moved class totals into always-visible
    totals row, added sign-state icons/colors for gain/deviation, removed
    legacy asset-row `Classe` column, preserved inline target edits +
    trade flags, and shaped new aggregate payload/placeholder behavior in
    `src/omaha/routes/pages.py`.
  - 2026-07-08: Verification complete. Commands: `uv run task lint`,
    `uv run pytest tests/test_pages_routes.py tests/test_audit_inventory.py tests/e2e/test_class_section_alignment.py -q`,
    `openspec list --specs`. Full `uv run task test-integration` still has
    unrelated pre-existing failures in `tests/test_real_csv_flow.py`
    because fixture file `tests/posicao_italo.csv` is absent in this
    workspace.
  - 2026-07-08: Refresh-for-test complete. Server restarted on LAN URL,
    `/healthz` OK, DB unchanged (`12` classes / `100` assets / `99`
    positions), authenticated dashboard smoke returned populated
    patrimônio markup. Status -> Applied.
  - 2026-07-08: Archive complete. Main specs synced, change moved to
    `openspec/changes/archive/2026-07-08-f15-patrimonio-table-redesign-for-class-and-asset-metrics/`.
    Status -> Archived.

---

## Recommended Execution Order

**Active queue:**
- none

Order note: F15 archived; pick next `Ready` slice when one appears.

**Deferred/Deprecated** (owner decides):
- F03 (Rentabilidade) — closed, reactivation path documented above.
- F04 (Proventos) — deprecated, `restore f04` to reactivate.
- F11 (Sidebar) — deprecated, owner: "não faz sentido".
- F13 (Light/dark toggle) — deprecated, owner: "não faz sentido".

---

## Decisions

Key decisions from the 2026-07-03 grill and subsequent sessions.
Each resolved and applied in the referenced slice.

- **D1 — Slugs PT-BR.** `/patrimonio`, `/rebalanceamento`, `/rentabilidade`,
  `/proventos`. Applied in F02.
- **D2 — Tab active color.** Reuse `--accent`. Applied in F02.
- **D3 — Spec `patrimonio-portfolio-header`.** Created in F02.
- **D4 — Delete ✕ already exists.** `dashboard-inline-editing` spec covers it.
- **D5 — Drop `BUILD_WARNING` chip.** Applied in F02.
- **D6 — F02 creates stubs.** `/rentabilidade` + `/proventos` "Em construção".
- **D7 — Deprecate `dashboard-sidebar`.** Applied in F02.
- **D8 — PRD §5.3 rewrite.** 4 tabs top-level. Applied in F02.
- **D9 — `rebalance-page` spec rewrite.** Form in body, no sidebar. Applied in F02.
- **D-F06.1 — Cross-User aggregate always.** Applied in F06.
- **D-F06.2 — Full-join by name.** Applied in F06.
- **D-F06.3 — `target_pct` omitted in aggregate.** Applied in F06.
- **D-F06.4 — Toggle `Casa` → `Família`.** Applied in F06.
- **D-F06.5 — Read-only gate reused.** Applied in F06.
- **D-F03-defer — F03+F04 deferred.** Owner 2026-07-05.
- **D02 — Register = Status Invest maximal.** Owner 2026-07-07. Gate for F08-F12.

---

## Checklist

- [x] PRD link no topo (`openspec/PRD.md`).
- [x] Como usar + status model + WIP + spec verification gate.
- [x] Fatias em formato lite (Status, Goal, Candidate change id, Spec link, Files, Notes, Progress).
- [x] Candidate change ids no formato `<slice-id-lower>-<slice-title-kebab>`.
- [x] Mapa de dependências preenchido para todas as fatias ativas.
- [x] Recommended execution order com notas.
- [x] Compacted history (≥8 últimas arquivadas).
- [x] Post-implementation reality check (stub inicial).
- [x] `openspec/config.yaml` tem bloco `openspec_roadmap` (token budget, context loading, pruning, quality_gate).
- [x] `.gitignore` cobre `openspec/.temp_assets/`.
- [x] Grill 2026-07-03 resolvido (D1-D9 em §Decisions).
- [x] PRD §5.3 marcado para reescrita no mesmo PR do `propose` de F02 (D8).
- [x] F14 — Catppuccin Frappe theme + component differentiation (Archived).
