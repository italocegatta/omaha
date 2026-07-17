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

All previous slices archived or closed. Active queue empty.

### F21 - PoC tabelas com libs na página de teste
Status: `Archived` — 2026-07-11
Goal: decidir lib de tabela por PoC com plano de rebalanceamento.
Archive: `openspec/changes/archive/2026-07-11-f21-poc-tabelas-com-libs-na-pagina-de-teste/`

### F22 - Implantar lib de tabela escolhida no rebalanceamento
Status: `Archived` — 2026-07-11
Goal: aplicar na interface real tabela validada na POC F27, seguindo handoff e mantendo filtros por coluna já validados.
Archive: `openspec/changes/archive/2026-07-11-f22-implantar-lib-de-tabela-escolhida-no-rebalanceamento/`

### F23 - Rebalanceamento e importação automáticos
Status: `Archived` — 2026-07-12
Goal: remover `Rebalancear`, recalcular plano após Enter em input, remover botão `Enviar` no import CSV, disparar upload automático e avançar próxima tela ao sucesso.
Candidate OpenSpec change id: `f23-rebalanceamento-e-importacao-automaticos`
Archive: `openspec/changes/archive/2026-07-12-f23-rebalanceamento-e-importacao-automaticos/`
Files to inspect: `src/omaha/routes/pages.py`, `src/omaha/routes/rebalance.py`, `src/omaha/templates/_patrimonio_add_asset_modal.html`, `src/omaha/templates/rebalance.html`, `src/omaha/static/app.css`
Notes: fluxo de ação imediata, sem botão manual extra.
Progress log: `2026-07-10` added from owner request.
Progress log: `2026-07-12` proposal queued.
Progress log: `2026-07-12` implementation applied; targeted integration, browser, BDD, and visual checks pass.
Progress log: `2026-07-12` review repair: Enter-only rebalance submit, persistent negative-input error, stale preview-response guard.
Progress log: `2026-07-12` archived after spec sync and roadmap closeout.

### F24 - Polimento de inputs e modal
Status: `Archived` — 2026-07-17
Goal: ampliar modal em ~10%, aumentar contraste do campo moeda, remover steppers numéricos, alinhar Família à esquerda.
Archive: `openspec/changes/archive/2026-07-17-f24-polimento-de-inputs-e-modal/`

### F25 - Sistema de cards com cores de target
Status: `Archived` — 2026-07-17
Goal: definir linguagem visual comum para cards, remover label `CLASSE`, e colorir cards por alvo: verde acima, vermelho abaixo.
Candidate OpenSpec change id: `f25-sistema-de-cards-com-cores-de-target`
Spec link: `openspec/changes/archive/2026-07-17-f25-sistema-de-cards-com-cores-de-target/`
Files to inspect: `src/omaha/templates/_rebalance_*`, `src/omaha/static/app.css`
Notes: cards precisam parecer mesma família, não mesmo molde.
Progress log: `2026-07-10` added from owner request.
Progress log: `2026-07-12` proposal queued.
Progress log: `2026-07-17` applied — removed CLASSE kicker, color by sign (--above/--below), flat surface, reduced shadow/radius, typography hierarchy. 434 tests pass.
Progress log: `2026-07-17` fix: card pct values (Atual, Alvo, Projetado) formatted to 1 decimal via formatPct1. 434 tests pass.
Progress log: `2026-07-17` archived — specs synced, change moved to archive.

### F26 - Padronização de tabelas e inspeção visual
Status: `Deprecated` — 2026-07-12 (split into F27-F29)
Goal: aplicar padrão visual único nas tabelas e adicionar inspeção visual obrigatória para pegar wrap, overflow, desalinhamento e diferença tipográfica entre células.
Candidate OpenSpec change id: `f26-padronizacao-de-tabelas-e-inspecao-visual`
Spec link: `openspec/changes/f26-padronizacao-de-tabelas-e-inspecao-visual/`
Files to inspect: `src/omaha/templates/_*.html`, `src/omaha/static/app.css`, `tests/e2e/`
Notes: inclui correção de casos como `Atual` com fonte diferente e headers apertados.
Progress log: `2026-07-10` added from owner request.
Progress log: `2026-07-12` proposal queued.
Progress log: `2026-07-12` split into F27-F29 per owner request.

### F27 - Tabela ativos espelhada do rebalanceamento
Status: `Archived` — 2026-07-12
Goal: portar para tabela de ativos em patrimônio recursos de tabela do rebalanceamento: ordenação aprimorada, filtro por coluna, e consistência visual entre header e body.
Candidate OpenSpec change id: `f27-tabela-ativos-espelhada-do-rebalanceamento`
Archive: `openspec/changes/archive/2026-07-12-f27-tabela-ativos-espelhada-do-rebalanceamento/`
Files to inspect: `src/omaha/templates/_patrimonio*.html`, `src/omaha/templates/_rebalance*.html`, `src/omaha/static/app.css`
Notes: slice de porta/consistência de tabela.
Progress log: `2026-07-12` added from owner request.
Progress log: `2026-07-12` proposal queued.
Progress log: `2026-07-12` apply complete; refresh-for-test smoke OK.
Progress log: `2026-07-12` archived after spec sync and closeout.

### F28 - Números arredondados e ganho unificado
Status: `Archived` — 2026-07-13
Goal: formatar campos numéricos com arredondamento para 0 casas decimais, exceto QTD de BTC com 3 casas, e reestruturar coluna ganho para mostrar valor absoluto + percentual juntos, ordenando por absoluto.
Candidate OpenSpec change id: `f28-numeros-arredondados-e-ganho-unificado`
Archive: `openspec/changes/archive/2026-07-13-f28-numeros-arredondados-e-ganho-unificado/`
Files to inspect: `src/omaha/templates/_patrimonio*.html`, `src/omaha/templates/_rebalance*.html`, `src/omaha/static/app.css`
Notes: foco em densidade e leitura.
Progress log: `2026-07-12` added from owner request.
Progress log: `2026-07-13` proposal queued.
Progress log: `2026-07-13` implementation started.
Progress log: `2026-07-13` apply complete; focused regressions, unit suite, lint, OpenSpec validation, and refresh-for-test smoke passed.
Progress log: `2026-07-13` review feedback: restore asset-table advanced filter parity and round pct columns.
Progress log: `2026-07-13` review repair applied; asset filters, pct rounding, focused browser tests, validation, and refresh smoke passed.
Progress log: `2026-07-13` review rejected; fix filter clipping/parity and scope pct rounding to requested cells.
Progress log: `2026-07-13` second review rejected; update stale route test, keep horizontal scroll, fix BTC range labels, zero normalization, and class desvio rounding.
Progress log: `2026-07-13` third review rejected; fix enum mapping, boundary identity, popover scroll/resize, and empty-range safety.
Progress log: `2026-07-13` fourth review rejected; update visual baselines and replace unregistered icon.
Progress log: `2026-07-13` fifth review rejected; render exact zero target values as `0%`, not dash.
Progress log: `2026-07-13` review repair applied; visible filter overlays, Qtd/Preço médio ranges, scoped pct rounding, browser coverage, lint, and OpenSpec validation pass.
Progress log: `2026-07-13` second-review repair applied; horizontal scroll + fixed filter popovers, BTC range labels, rounded class desvio, normalized `0%`, focused browser/route checks, validation, and refresh smoke passed. Awaiting final review.
Progress log: `2026-07-13` third-review repair applied; enum filters map to canonical asset fields, tied BTC range boundaries retain identity, teleported popovers reposition on scroll/resize, empty ranges use finite bounds. Integration passed; F28 browser coverage passed; OpenSpec validation and refresh smoke passed. Ready for final review.
Progress log: `2026-07-13` fourth-review repair applied; header filter uses cataloged `expand_more`, intentional Patrimônio/import and rebalance visual baselines regenerated, unit + visual gates and OpenSpec validation pass; refresh smoke passed. Ready for final review.
Progress log: `2026-07-13` fifth-review repair applied; exact numeric asset targets use `0%` in Classe / Alvo and Carteira / Alvo, while `—` remains absent/invalid-only. Focused browser regression, unit suite, lint, OpenSpec validation, and refresh smoke passed. Ready for final review.

### F29 - Compra e venda com emoji toggle
Status: `Archived` — 2026-07-15
Goal: simplificar colunas compra e venda com emoji de acerto/bloqueio e manter clique que alterna ícone e grava novo valor no banco.
Archive: `openspec/changes/archive/2026-07-15-f29-compra-e-venda-com-emoji-toggle/`

### R30 - Extrair padrão CSS compartilhado de tabelas
Status: `Archived` — 2026-07-15
Goal: extrair estilos comuns de tabelas (shell, header, rows, cells) em classes base `.data-table-*` com variáveis CSS para troca de tema; rebalance e portfolio herdam dessas bases.
Candidate OpenSpec change id: `r30-extrair-padrao-css-compartilhado-de-tabelas`
Archive: `openspec/changes/archive/2026-07-15-r30-extrair-padrao-css-compartilhado-de-tabelas/`
Files to inspect: `src/omaha/static/app.css`, `src/omaha/templates/_rebalance_plan.html`, `src/omaha/templates/_patrimonio_class_section.html`
Notes: fundação para padronização visual. Variáveis de tema (`--table-*`) devem permitir troca de paleta sem duplicar regras.
Progress log: `2026-07-14` added from owner request.
Progress log: `2026-07-14` proposal queued.
Progress log: `2026-07-15` archived after spec sync and closeout.

### R31 - Padronizar filter panel e header de tabelas
Status: `Archived` — 2026-07-15
Goal: unificar filter panel (teleport vs inline), transformar macro `asset_filter_controls` em componente reutilizável, e alinhar UX de filtros entre rebalance e portfolio.
Archive: `openspec/changes/archive/2026-07-15-r31-padronizar-filter-panel-e-header-de-tabelas/`

### F32 - Aplicar padrão de tabela rebalance em portfolio
Status: `Archived` — 2026-07-15
Goal: portar design visual (cores, font, efeitos, tema) da tabela rebalance para tabelas de ativos em portfolio, incluindo linha de resumo por classe como exceção documentada.
Archive: `openspec/changes/archive/2026-07-15-f32-aplicar-padrao-de-tabela-rebalance-em-portfolio/`

### R33 - Refatorar formatters e comportamentos de tabela para reutilização
Status: `Archived` — 2026-07-15
Goal: centralizar formatação numérica (BRL,%,Qtd), lógica de sinal (signClass/signIcon), row color-coding e cell formatting em módulo compartilhado; rebalance e portfolio consomem a mesma API.
Candidate OpenSpec change id: `r33-refatorar-formatters-e-comportamentos-de-tabela-para-reutilizacao`
Archive: `openspec/changes/archive/2026-07-15-r33-refatorar-formatters-e-comportamentos-de-tabela-para-reutilizacao/`
Files to inspect: `src/omaha/templates/rebalance.html`, `src/omaha/templates/_patrimonio_add_asset_modal.html`, `src/omaha/static/app.css`
Notes: JS/Alpine layer — separado do CSS (R30). Formatters atuais estão duplicados ou acoplados a tabela específica. Foco: API compartilhada, não behavior change.
Progress log: `2026-07-14` added from owner request.
Progress log: `2026-07-14` proposal queued.
Progress log: `2026-07-15` applied: shared module `table-formatters.js` (11 functions), rebalance static import, portfolio dynamic import with fallback. Review repair: formatQty fraction digits aligned, formatBRL null handling unified.
Progress log: `2026-07-15` archived after spec sync and closeout.

### I05 - Otimizar hooks pre-commit e pre-push
Status: `Archived` — 2026-07-15
Goal: commit < 1 min, push < 3 min. Remover `pytest-unit` duplicado do pre-push (já roda no pre-commit), trocar `task test-integration` por `task test-integration-parallel` no hook pre-push.
Archive: `openspec/changes/archive/2026-07-15-i05-otimizar-hooks-pre-commit-e-pre-push/`

### T21 - Auditar e podar testes redundantes e obvios
Status: `Archived` — 2026-07-15
Goal: todo teste precisa validar comportamento real do sistema. Sobreviventes de mutation test (killed por acaso), testes óbvios (assert trivial), testes redundantes (mesma lógica testada 2x): reescrever com cenário real ou excluir.
Candidate OpenSpec change id: `t21-auditar-e-podar-testes-redundantes-e-obvios`
Archive: `openspec/changes/archive/2026-07-15-t21-auditar-e-podar-testes-redundantes-e-obvios/`
Notes: -4 testes (5 deletados + 1 merge). Zero código de produção. Zero seed.

### I06 - Reorganizar hooks prek: modificar em pre-commit, validar em pre-push
Status: `Archived` — 2026-07-15
Goal: pre-commit corrige código (ruff format+fix, whitespace, EOF). Pre-push só valida (ruff check sem fix, testes, commitizen). Push nunca modifica código.
Candidate OpenSpec change id: `i06-reorganizar-hooks-prek-modificar-em-pre-commit-validar-em-pre-push`
Archive: `openspec/changes/archive/2026-07-15-i06-reorganizar-hooks-prek-modificar-em-pre-commit-validar-em-pre-push/`
Files to inspect: `prek.toml`, `openspec/specs/prek-hooks/spec.md`
Notes: pre-commit: ruff-format (priority 1) + ruff --fix (priority 2) + whitespace/EOF (priority 3). Pre-push: ruff check (validate only) + pytest-integration + commitizen-branch + uv-lock.
Progress log: `2026-07-15` applied: pre-commit runs ruff-format, ruff --fix, trailing-whitespace, end-of-file-fixer; pre-push runs ruff (validate-only), uv-lock, pytest-integration, commitizen-branch. Spec synced. Archived.

### T22 - Isolar audit_inventory em job CI separado
Status: `Archived` — 2026-07-15
Goal: `test_audit_inventory.py` não bloqueia push — mover para `tests/audit_integration/`, fix path depth, update PERFORMANCE.md refs.
Archive: `openspec/changes/archive/2026-07-15-t22-isolar-audit-inventory-em-job-ci-separado/`

### T23 - Otimizar setup do test_seed_from_csv
Status: `Archived` — 2026-07-15
Goal: reduzir overhead de setup dos 20 testes serial em `test_seed_from_csv.py` (~50s total, ~2.5s/setup). Compartilhar fixture de seed entre testes via session scope ou cache de estado SQLite.
Candidate OpenSpec change id: `t23-otimizar-setup-do-test-seed-from-csv`
Archive: `openspec/changes/archive/2026-07-15-t23-otimizar-setup-do-test-seed-from-csv/`
Files to inspect: `tests/test_seed_from_csv.py`, `tests/support/db.py`, `tests/conftest.py`
Notes: session-scoped snapshot fixture, 1 setup + 19 file copies. ~50s → ~13.5s (3.7x speedup).
Progress log: `2026-07-15` added from test suite performance analysis.
Progress log: `2026-07-15` archived after spec sync and closeout.

### T23.1 - Corrigir flaky test_dashboard_shows_position_counts sob xdist
Status: `Archived` — 2026-07-15
Goal: corrigir flaky test sob xdist parallel.
Archive: `openspec/changes/archive/2026-07-15-t231-corrigir-flaky-test-dashboard-shows-position-counts-sob-xdist/`
Notes: 12/12 tests pass, xdist parallel respected.

### T24 - Corrigir classificação de arquivos integration mal taggeados
Status: `Archived` — 2026-07-15
Goal: `test_admin_recovery.py` e `test_db_mutations.py` usam TestClient + DB mas estão marcados `unit`. Mover para `_INTEGRATION_PREFIXES` em `tests/conftest.py`. Ganho: limpeza + ~1.5s off unit suite.
Candidate OpenSpec change id: `t24-corrigir-classificacao-de-arquivos-integration-mal-taggeados`
Archive: `openspec/changes/archive/2026-07-15-t24-corrigir-classificacao-de-arquivos-integration-mal-taggeados/`

### T25 - Auditar suite completa: cada teste prova que o sistema funciona
Status: `Archived` — 2026-07-15
Goal: inventário final de todos os 864 testes. Cada teste deve ter justificativa de por que prova comportamento real. Testes que só verificam import, existência de função, ou formato de output sem impacto funcional: eliminar ou reescrever como teste de comportamento.
Candidate OpenSpec change id: `t25-auditar-suite-completa-cada-teste-prova-que-o-sistema-funciona`
Archive: `openspec/changes/archive/2026-07-15-t25-auditar-suite-completa-cada-teste-prova-que-o-sistema-funciona/`
Files to inspect: `tests/`, `openspec/specs/`, `openspec/PRD.md` §4
Notes: 864 testes auditados, 0 removidos. Todos atendem ao menos 1 critério de retenção (error-path, integration, spec-contract, regression-guard). `tests/AUDIT.md` com justificativas por arquivo. Nova spec `test-suite-audit` criada.

### T26 - Elevar kill rate de mutation testing em policy.py
Status: `Archived` — 2026-07-15
Goal: reduzir sobreviventes de mutation de 145 para < 30 em `policy.py`. Baseline atual: 90% killed (3468/3867), mas `policy.py` contribui com 69% dos sobreviventes (145/211). Funções críticas sem cobertura de mutation: `evaluate_progressive_sales_stage_solution` (44 survived), `build_contribution_only_rejection_reason` (16), `calculate_solution_top_gaps` (14), `build_overweight_projected_value_floor` (13).
Candidate OpenSpec change id: `t26-elevar-kill-rate-de-mutation-testing-em-policy`
Archive: `openspec/changes/archive/2026-07-15-t26-elevar-kill-rate-de-mutation-testing-em-policy/`
Notes: Add 104 mutation-targeted tests. policy.py survived: 145 → 47 (-67.6%). ~30 remaining are equivalent mutants (dtype=None).

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

### T07 - Revisar suite quebrada e corrigir regressões
Status: `Archived` — 2026-07-10
Goal: Revisar falhas atuais de `uv run task test` no grupo browser/workflow e
  fechar raiz do problema, seja corrigindo código, ajustando teste, ou
  alinhando contrato/spec quando a expectativa estiver errada. Foco: BDD,
  e2e, import modal, e fluxos visíveis de navegação/importação.
Archive: `openspec/changes/archive/2026-07-10-t07-revisar-suite-quebrada-e-corrigir-regressoes/`

### T08 - Revisar paralelismo e custo da suite de testes
Status: `Archived` — 2026-07-10
Goal: Alinhar buckets/tasks/hooks/CI da suite, limpar drift de markers, e
  registrar limites seguros de serial/paralelismo para testes pesados.
Archive: `openspec/changes/archive/2026-07-10-t08-revisar-paralelismo-e-custo-da-suite-de-testes/`

### T09 - Revisar regressões visuais e baselines
Status: `Archived` — 2026-07-10
Goal: Revisar regressões visuais e baselines para separar drift de baseline,
  seletor frágil, ou regressão real de UI. Corrigir menor lado correto.
Archive: `openspec/changes/archive/2026-07-10-t09-revisar-regressoes-visuais-e-baselines/`

### T10 - Revisar pipeline CSV real e seed_from_csv
Status: `Archived` — 2026-07-10
Goal: Revisar pipeline CSV real e seed_from_csv, corrigir drift de contrato
  entre specs, CSVs, e testes. Minoridade corrigida no lado docs/tests.
Archive: `openspec/changes/archive/2026-07-10-t10-revisar-pipeline-csv-real-e-seed-from-csv/`

### I03 - Regularizar plumbing do pre-push
Status: `Archived` — 2026-07-10
Goal: Corrigir plumbing de `pre-push` para rodar buckets canônicos de tarefa
  sem parse quebrado de `&&`, mantendo gate intacto e sem mexer em produto.
Archive: `openspec/changes/archive/2026-07-10-i03-regularizar-plumbing-do-pre-push/`

### I04 - Limpar drift lint repo-wide
Status: `Archived` — 2026-07-10
Goal: Limpar drift lint repo-wide revelado pelo hook de pre-push, sem relaxar
  regras nem alterar comportamento de produto.
Archive: `openspec/changes/archive/2026-07-10-i04-limpar-drift-lint-repo-wide/`

### T11 - Revisar contratos de rebalance schema e glue
Status: `Archived` — 2026-07-10
Goal: Alinhar engine metrics (`current_deviation_pct`/`projected_deviation_pct`)
  com spec percentual 0-100 e limpar chaves `total_buy_amount`/`total_sell_amount`.
Archive: `openspec/changes/archive/2026-07-10-t11-revisar-contratos-de-rebalance-schema-e-glue/`

### T12 - Isolar hang tardio do harness browser/live-server
Status: `Archived` — 2026-07-10
Goal: Isolar e corrigir hang tardio do harness BDD/e2e com replay 1 teste por
  vez, teardown mais seguro e diagnóstico de navegação Playwright.
Archive: `openspec/changes/archive/2026-07-10-t12-isolar-hang-tardio-do-harness-browser-live-server/`

### T13 - Cobertura fora dos browsers
Status: `Archived` — 2026-07-14
Goal: tirar cobertura/XML de e2e, bdd e visual; manter coverage em unit + integration e separar fast lane de browser lane.
Archive: `openspec/changes/archive/2026-07-14-t13-cobertura-fora-dos-browsers/`

### T14 - Helpers compartilhados de setup e wipe
Status: `Archived` — 2026-07-14
Goal: extrair bootstrap, wipe de DB e helpers de browser/fixture de `conftest` e testes para módulos de support compartilhados.
Archive: `openspec/changes/archive/2026-07-14-t14-helpers-compartilhados-de-setup-e-wipe/`

### T15 - Contratos e docs da suíte
Status: `Archived` — 2026-07-14
Goal: alinhar README, docs de BDD e performance baseline com behavior real de tasks, markers e contratos da suíte.
Archive: `openspec/changes/archive/2026-07-14-t15-contratos-e-docs-da-suite/`

### T16 - Gate pré-merge sub-2m
Status: `Archived` — 2026-07-14
Goal: definir lane pré-merge rápida abaixo de 2 min, separando fast gate de browser lanes e coverage pesada.
Archive: `openspec/changes/archive/2026-07-14-t16-gate-pre-merge-sub-2m/`

### T17 - Paralelizar integration com DB por worker
Status: `Archived` — 2026-07-14
Goal: habilitar paralelismo seguro no lane integration via isolamento de banco por worker para reduzir wall-clock sem corromper estado compartilhado.
Archive: `openspec/changes/archive/2026-07-14-t17-paralelizar-integration-com-db-por-worker/`

### T18 - Cortar setup repetido dos hotspots
Status: `Archived` — 2026-07-14
Goal: reduzir custo de bootstrap/alembic/seed nos testes mais caros de integration, focando helpers compartilhados e fixtures session-scoped.
Archive: `openspec/changes/archive/2026-07-14-t18-cortar-setup-repetido-dos-hotspots/`
Progress log: `2026-07-14` archived after spec sync and closeout.

### T19 - Expandir mutation testing para módulo rebalance completo
Status: `Archived` — 2026-07-14
Goal: estender escopo de mutmut de `solver.py` + `validation.py` para todos os arquivos críticos do módulo `rebalance/` (engine, policy, postprocessing, builders, glue), mantendo tempo total < 20min via parallelismo.
Candidate OpenSpec change id: `t19-expandir-mutation-testing-para-modulo-rebalance-completo`
Archive: `openspec/changes/archive/2026-07-14-t19-expandir-mutation-testing-para-modulo-rebalance-completo/`
Files to inspect: `pyproject.toml` (`[tool.mutmut]`), `src/omaha/rebalance/engine.py`, `src/omaha/rebalance/policy.py`, `src/omaha/rebalance/postprocessing.py`, `src/omaha/rebalance/builders.py`, `src/omaha/rebalance/glue.py`, `src/omaha/rebalance/constants.py`
Notes: baseline atual (2026-07-06): 869 mutants, 64.9% killed, escopo solver+validation. Arquivos novos somam ~2.7K LOC. Estimativa: 1500-2500 mutants adicionais. Usar `mutmut run` com cache do baseline anterior.
Progress log: `2026-07-14` added from performance analysis.
Progress log: `2026-07-14` proposal generated; 12 tasks, 4 design decisions.
Progress log: `2026-07-14` proposal queued.
Progress log: `2026-07-14` archived after spec sync and closeout.

### T20 - Baseline automático de mutation no CI
Status: `Archived` — 2026-07-14
Goal: configurar `mutmut run` + `mutation-baseline` como passo CI pós-merge no `main`, gerando baseline atualizado e commit automático para detecção de regressão de mutation score.
Candidate OpenSpec change id: `t20-baseline-automatico-de-mutation-no-ci`
Archive: `openspec/changes/archive/2026-07-14-t20-baseline-automatico-de-mutation-no-ci/`
Files to inspect: `.github/workflows/ci.yml`, `pyproject.toml` (`[tool.mutmut]`, taskipy tasks), `scripts/mutation_baseline.py`
Notes: requer T19 (scope expansion) antes para baseline refletir módulo completo. CI deve rodar em cron ou pós-merge only (não em PR — custo alto).
Progress log: `2026-07-14` added from performance analysis.
Progress log: `2026-07-14` proposal generated; 4 tasks, 5 design decisions.
Progress log: `2026-07-14` applied: added `mutation-ci` taskipy task, `mutation-baseline` CI job (post-merge only, fresh run, commit-back with [skip ci]), spec synced.
Progress log: `2026-07-14` archived after spec sync and closeout.

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
Goal: Replace warm-brown dark palette (hue 60) with Catppuccin Frappe cool blue-gray (hue ~274). Differentiate components via elevation, class-colored headers, sunk asset tables, compact rows, angular borders, and high-contrast numbers.
Archive: `openspec/changes/archive/2026-07-08-f14-catppuccin-frappe-theme/`

### F15 - Patrimônio table redesign for class and asset metrics
Status: `Archived` — 2026-07-08
Goal: Rebuild class totals row + asset table on `/patrimonio` with grouped columns, sortable fields, gain deviation icons, and remove legacy asset-row `Classe` column.
Archive: `openspec/changes/archive/2026-07-08-f15-patrimonio-table-redesign-for-class-and-asset-metrics/`

### F16 - Rebalanceamento sempre pronto com aporte persistente
Status: `Archived` — 2026-07-08
Goal: Manter um plano de rebalanceamento sempre materializado para perfil ativo usando valor atual de `aporte`, recalculando após mutações e preservando `aporte` entre páginas na mesma execução.
Archive: `openspec/changes/archive/2026-07-08-f16-rebalanceamento-sempre-pronto-com-aporte-persistente/`

### F17 - Precisao canonica de alvo e atalho de percentual global
Status: `Archived` — 2026-07-08
Goal: Tornar `% classe` e `% ativo na classe` fontes de verdade do dominio, manter edicao de `% ativo na carteira` como atalho server-side, elevar precisao interna de `Asset.target_pct`, usar `Decimal` ate fronteira numpy/CVXPY.
Archive: `openspec/changes/archive/2026-07-08-f17-precisao-canonica-de-alvo-e-atalho-de-percentual-global/`

### F18 - Rebalanceamento UI: resumo por classe, filtros, desvios
Status: `Archived` — 2026-07-09
Goal: Redesenhar a página de rebalanceamento: substituir 6 cards de métricas por resumo de desvio por classe (cards horizontais cor-coded), compactar aporte + thresholds, filtros multi-select, colunas de desvio, rows coloridas.
Archive: `openspec/changes/archive/2026-07-09-f18-rebalanceamento-ui-resumo-por-classe-filtros-desvios/`

### F19 - Gate de compra e venda por desvio minimo no otimizador
Status: `Archived` — 2026-07-09
Goal: Restringir plano de rebalanceamento para só liberar `Compra` e `Venda` quando desvio do ativo ultrapassar thresholds mínimos absoluto (R$) e percentual (%) informados na tela.
Archive: `openspec/changes/archive/2026-07-09-f19-gate-de-compra-e-venda-por-desvio-minimo-no-otimizador/`

### F20 - Calculo da qtd de compra ou venda no plano de rebalanceamento
Status: `Archived` — 2026-07-09
Goal: Expor quantidade operacional `Qtd` na tabela do plano de rebalanceamento, calculada a partir do valor de compra/venda e preço atual, com conversão BRL->USD quando ativo negocia em dólar.
Archive: `openspec/changes/archive/2026-07-09-f20-calculo-da-qtd-de-compra-ou-venda-no-plano-de-rebalanceamento/`

---

### R34 - Extrair lógica de filtros de tabela para módulo compartilhado
Status: `Archived` — 2026-07-15
Goal: extrair lógica JS de filtros e painéis HTML de filtros de rebalance e PoC para módulo compartilhado.
Archive: `openspec/changes/archive/2026-07-15-r34-extrair-logica-de-filtros-de-tabela-para-modulo-compartilhado/`

### F35 - Bug cadeado cinza na tabela ativos
Status: `Archived` — 2026-07-15
Goal: corrigir bug de regressão onde ícones compra/venda exibem terceiro estado inválido (cadeado cinza) além de Liberado/Bloqueado.
Archive: `openspec/changes/archive/2026-07-15-f35-bug-cadeado-cinza-na-tabela-ativos/`

### F36 - Consistência visual completa tabela ativos ↔ rebalance
Status: `Archived` — 2026-07-15
Goal: alinhar tabela de ativos com tabela rebalanceamento em 5 dimensões: ícones Material Symbols, teleport validado, formatação desvio 0 casas decimais, card totais com cor da classe, espaçamento cabeçalhos.
Archive: `openspec/changes/archive/2026-07-15-f36-consistencia-visual-completa-tabela-ativos-rebalance/`
Progress log: `2026-07-15` spec proposed — proposal, design, spec, tasks created. Task 4.5 blocked on owner color validation.

### F37 - Contraste de alerta por desvio
Status: `Archived` — 2026-07-16
Goal: simplificar alerta de desvio para 2-tier (ok/ danger), remover badge verde fraco de contraste ruim.
Archive: `openspec/changes/archive/2026-07-16-f37-contraste-de-alerta-por-desvio/`

### F38 - Padronização de margens das páginas
Status: `Archived` — 2026-07-16
Goal: unificar margens e padding de todas as páginas full-width com simetria horizontal (0.75rem), vertical generoso (1rem), max-width 1920px centralizado. Stubs e login mantêm padrão próprio.
Archive: `openspec/changes/archive/2026-07-16-f38-padronizacao-de-margens-das-paginas/`

### F39 - Revisão de margens: meio termo entre antigo e novo
Status: `Archived` — 2026-07-16
Goal: encontrar meio termo entre margens atuais (F38) e versão anterior para patrimônio e rebalancemaneto: restaurar respiro vertical entre seções e padding de células da tabela, mas manter margens laterais apertadas para maximizar espaço horizontal da tabela.
Archive: `openspec/changes/archive/2026-07-16-f39-revisao-de-margens-meio-termo/`

### F40 - Bug template tabelas ativos patrimonio
Status: `Archived` — 2026-07-17
Goal: corrigir 3 bugs (word wrap, colunas vazias, filtro clipado) + melhorias de filtro (race condition, formatação de números, Compra/Venda align).
Archive: `openspec/changes/archive/2026-07-17-f40-bug-template-tabelas-ativos-patrimonio/`

### R41 - Limpar CSS duplicado e código morto
Status: `Archived` — 2026-07-17
Goal: remover seletores CSS duplicados, código morto, e consolidar blocos `:root` conflitantes em `app.css`.
Archive: `openspec/changes/archive/2026-07-17-r41-limpar-css-duplicado-e-codigo-morto/`

---

## Recommended Execution Order

**Active queue:** none

Order note: F35 archived (bug cadeado cinza). F36 (consistência visual) — maior escopo, 5 melhorias agrupadas. F37 (alerta desvio) —
independente, pode rodar após F36 ou em paralelo se F36 atrasar.
F39 (margin revision) — CSS-only, quick apply.
F29 archived (emoji toggle). R30-R34 for table standardization.

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
- **D-F18.1 — 6 cards → resumo por classe.** Owner 2026-07-08.
- **D-F18.2 — Aporte barra compacta + thresholds editáveis.** Owner 2026-07-08.
- **D-F18.3 — Filtros multi-select (Classe, Ação) + busca por nome.** Owner 2026-07-08.
- **D-F18.4 — Colunas Desvio(abs) e Desvio(%) na tabela de ativos.** Owner 2026-07-08.
- **D-T26.1 — mutmut sempre silencioso.** Rodar `mutmut run` com output em arquivo (`> /tmp/mutmut.log 2>&1`), ler só `mutmut results` com grep de contadores. Evita consumo excessivo de token do modelo. Applied in T26.

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
