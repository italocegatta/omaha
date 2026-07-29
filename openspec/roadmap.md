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

Active slices appear below. Archived and deferred slices retained as history.

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
Goal: remover `Rebalancear`, recalcular plano após Enter, upload automático no import CSV.
Archive: `openspec/changes/archive/2026-07-12-f23-rebalanceamento-e-importacao-automaticos/`

### F24 - Polimento de inputs e modal
Status: `Archived` — 2026-07-17
Goal: ampliar modal em ~10%, aumentar contraste do campo moeda, remover steppers numéricos, alinhar Família à esquerda.
Archive: `openspec/changes/archive/2026-07-17-f24-polimento-de-inputs-e-modal/`

### F25 - Sistema de cards com cores de target
Status: `Archived` — 2026-07-17
Goal: linguagem visual comum para cards, remover CLASSE, colorir por alvo (verde acima, vermelho abaixo), pct 1 casa decimal.
Archive: `openspec/changes/archive/2026-07-17-f25-sistema-de-cards-com-cores-de-target/`

### F26 - Padronização de tabelas e inspeção visual
Status: `Deprecated` (archived) — 2026-07-12 (split into F27-F29; regularized 2026-07-28)
Goal: padrão visual único em tabelas + inspeção visual obrigatória.
Archive: `openspec/changes/archive/2026-07-12-f26-padronizacao-de-tabelas-e-inspecao-visual/`

### F27 - Tabela ativos espelhada do rebalanceamento
Status: `Archived` — 2026-07-12
Goal: portar ordenação, filtro por coluna e consistência visual da tabela rebalance para tabela de ativos.
Archive: `openspec/changes/archive/2026-07-12-f27-tabela-ativos-espelhada-do-rebalanceamento/`

### F28 - Números arredondados e ganho unificado
Status: `Archived` — 2026-07-13
Goal: arredondar campos numéricos (0 casas, BTC 3 casas) e reestruturar coluna ganho (absoluto + %).
Archive: `openspec/changes/archive/2026-07-13-f28-numeros-arredondados-e-ganho-unificado/`

### F29 - Compra e venda com emoji toggle
Status: `Archived` — 2026-07-15
Goal: simplificar colunas compra e venda com emoji de acerto/bloqueio e manter clique que alterna ícone e grava novo valor no banco.
Archive: `openspec/changes/archive/2026-07-15-f29-compra-e-venda-com-emoji-toggle/`

### R30 - Extrair padrão CSS compartilhado de tabelas
Status: `Archived` — 2026-07-15
Goal: extrair estilos comuns de tabelas em classes `.data-table-*` com variáveis CSS para troca de tema.
Archive: `openspec/changes/archive/2026-07-15-r30-extrair-padrao-css-compartilhado-de-tabelas/`

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
Goal: centralizar formatação numérica, lógica de sinal e cell formatting em módulo compartilhado.
Archive: `openspec/changes/archive/2026-07-15-r33-refatorar-formatters-e-comportamentos-de-tabela-para-reutilizacao/`

### I05 - Otimizar hooks pre-commit e pre-push
Status: `Archived` — 2026-07-15
Goal: commit < 1 min, push < 3 min. Remover `pytest-unit` duplicado do pre-push (já roda no pre-commit), trocar `task test-integration` por `task test-integration-parallel` no hook pre-push.
Archive: `openspec/changes/archive/2026-07-15-i05-otimizar-hooks-pre-commit-e-pre-push/`

### T21 - Auditar e podar testes redundantes e obvios
Status: `Archived` — 2026-07-15
Goal: reescrever ou excluir testes que não provam comportamento real (-4 testes, zero código de produção).
Archive: `openspec/changes/archive/2026-07-15-t21-auditar-e-podar-testes-redundantes-e-obvios/`

### I06 - Reorganizar hooks prek: modificar em pre-commit, validar em pre-push
Status: `Archived` — 2026-07-15
Goal: pre-commit corrige código (ruff format+fix), pre-push só valida (ruff check, testes, commitizen).
Archive: `openspec/changes/archive/2026-07-15-i06-reorganizar-hooks-prek-modificar-em-pre-commit-validar-em-pre-push/`

### T22 - Isolar audit_inventory em job CI separado
Status: `Archived` — 2026-07-15
Goal: `test_audit_inventory.py` não bloqueia push — mover para `tests/audit_integration/`, fix path depth, update PERFORMANCE.md refs.
Archive: `openspec/changes/archive/2026-07-15-t22-isolar-audit-inventory-em-job-ci-separado/`

### T23 - Otimizar setup do test_seed_from_csv
Status: `Archived` — 2026-07-15
Goal: fixture session-scoped para 20 testes serial (~50s → ~13.5s, 3.7x speedup).
Archive: `openspec/changes/archive/2026-07-15-t23-otimizar-setup-do-test-seed-from-csv/`

### T23.1 - Corrigir flaky test_dashboard_shows_position_counts sob xdist
Status: `Archived` — 2026-07-15
Goal: corrigir flaky test sob xdist parallel.
Archive: `openspec/changes/archive/2026-07-15-t231-corrigir-flaky-test-dashboard-shows-position-counts-sob-xdist/`

### T24 - Corrigir classificação de arquivos integration mal taggeados
Status: `Archived` — 2026-07-15
Goal: mover `test_admin_recovery.py` e `test_db_mutations.py` para `_INTEGRATION_PREFIXES`.
Archive: `openspec/changes/archive/2026-07-15-t24-corrigir-classificacao-de-arquivos-integration-mal-taggeados/`

### T25 - Auditar suite completa: cada teste prova que o sistema funciona
Status: `Archived` — 2026-07-15
Goal: inventário de 864 testes com justificativa de retenção; 0 removidos, `tests/AUDIT.md` criado.
Archive: `openspec/changes/archive/2026-07-15-t25-auditar-suite-completa-cada-teste-prova-que-o-sistema-funciona/`

### T26 - Elevar kill rate de mutation testing em policy.py
Status: `Archived` — 2026-07-15
Goal: reduzir sobreviventes de mutation em policy.py de 145 para 47 (-67.6%).
Archive: `openspec/changes/archive/2026-07-15-t26-elevar-kill-rate-de-mutation-testing-em-policy/`

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
Notes: pasta ativa duplicada removida em 2026-07-28; `tasks.md` anotado consolidado no archive.

### F09 - Typography refresh (Red Hat Display + Inter)
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-f09-typography-refresh/`

### F10 - Component state language + table pattern
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-f10-component-state-language-and-table-pattern/`

### F12 - Material Symbols icons
Status: `Archived` — 2026-07-07
Archive: `openspec/changes/archive/2026-07-07-f12-material-symbols-icons/`

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
Goal: corrigir falhas de `uv run task test` em browser/workflow (BDD, e2e, import modal, navegação).
Archive: `openspec/changes/archive/2026-07-10-t07-revisar-suite-quebrada-e-corrigir-regressoes/`

### T08 - Revisar paralelismo e custo da suite de testes
Status: `Archived` — 2026-07-10
Goal: alinhar buckets/tasks/hooks/CI, limpar drift de markers, registrar limites seguros.
Archive: `openspec/changes/archive/2026-07-10-t08-revisar-paralelismo-e-custo-da-suite-de-testes/`

### T09 - Revisar regressões visuais e baselines
Status: `Archived` — 2026-07-10
Goal: separar drift de baseline, seletor frágil ou regressão real de UI; corrigir menor lado.
Archive: `openspec/changes/archive/2026-07-10-t09-revisar-regressoes-visuais-e-baselines/`

### T10 - Revisar pipeline CSV real e seed_from_csv
Status: `Archived` — 2026-07-10
Goal: corrigir drift de contrato entre specs, CSVs e testes no pipeline seed.
Archive: `openspec/changes/archive/2026-07-10-t10-revisar-pipeline-csv-real-e-seed-from-csv/`

### I03 - Regularizar plumbing do pre-push
Status: `Archived` — 2026-07-10
Goal: corrigir parse de `&&` no pre-push para rodar buckets canônicos sem quebrar gate.
Archive: `openspec/changes/archive/2026-07-10-i03-regularizar-plumbing-do-pre-push/`

### I04 - Limpar drift lint repo-wide
Status: `Archived` — 2026-07-10
Goal: limpar drift lint revelado pelo hook de pre-push, sem relaxar regras.
Archive: `openspec/changes/archive/2026-07-10-i04-limpar-drift-lint-repo-wide/`

### T11 - Revisar contratos de rebalance schema e glue
Status: `Archived` — 2026-07-10
Goal: alinhar engine metrics com spec percentual 0-100 e limpar chaves órfãs.
Archive: `openspec/changes/archive/2026-07-10-t11-revisar-contratos-de-rebalance-schema-e-glue/`

### T12 - Isolar hang tardio do harness browser/live-server
Status: `Archived` — 2026-07-10
Goal: corrigir hang do harness BDD/e2e com replay 1 teste e teardown mais seguro.
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
Goal: reduzir custo de bootstrap/alembic/seed nos testes mais caros via fixtures session-scoped.
Archive: `openspec/changes/archive/2026-07-14-t18-cortar-setup-repetido-dos-hotspots/`

### T19 - Expandir mutation testing para módulo rebalance completo
Status: `Archived` — 2026-07-14
Goal: estender mutmut de solver+validation para todos os arquivos críticos do módulo rebalance/.
Archive: `openspec/changes/archive/2026-07-14-t19-expandir-mutation-testing-para-modulo-rebalance-completo/`

### T20 - Baseline automático de mutation no CI
Status: `Archived` — 2026-07-14
Goal: `mutmut run` + `mutation-baseline` como passo CI pós-merge no main.
Archive: `openspec/changes/archive/2026-07-14-t20-baseline-automatico-de-mutation-no-ci/`

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
Goal: substituir paleta warm-brown por Catppuccin Frappe cool blue-gray e diferenciar componentes.
Archive: `openspec/changes/archive/2026-07-08-f14-catppuccin-frappe-theme/`

### F15 - Patrimônio table redesign for class and asset metrics
Status: `Archived` — 2026-07-08
Goal: reconstruir row de totais por classe + tabela de ativos com colunas agrupadas e ordenáveis.
Archive: `openspec/changes/archive/2026-07-08-f15-patrimonio-table-redesign-for-class-and-asset-metrics/`

### F16 - Rebalanceamento sempre pronto com aporte persistente
Status: `Archived` — 2026-07-08
Goal: manter plano materializado com `aporte` persistente, recalculando após mutações.
Archive: `openspec/changes/archive/2026-07-08-f16-rebalanceamento-sempre-pronto-com-aporte-persistente/`

### F17 - Precisao canonica de alvo e atalho de percentual global
Status: `Archived` — 2026-07-08
Goal: `% classe` e `% ativo na classe` como fontes de verdade; `% ativo na carteira` como atalho server-side.
Archive: `openspec/changes/archive/2026-07-08-f17-precisao-canonica-de-alvo-e-atalho-de-percentual-global/`

### F18 - Rebalanceamento UI: resumo por classe, filtros, desvios
Status: `Archived` — 2026-07-09
Goal: substituir 6 cards por resumo de desvio por classe, filtros multi-select, colunas de desvio.
Archive: `openspec/changes/archive/2026-07-09-f18-rebalanceamento-ui-resumo-por-classe-filtros-desvios/`

### F19 - Gate de compra e venda por desvio minimo no otimizador
Status: `Archived` — 2026-07-09
Goal: restringir Compra/Venda a desvio mínimo absoluto (%) e percentual (%) informados na tela.
Archive: `openspec/changes/archive/2026-07-09-f19-gate-de-compra-e-venda-por-desvio-minimo-no-otimizador/`

### F20 - Calculo da qtd de compra ou venda no plano de rebalanceamento
Status: `Archived` — 2026-07-09
Goal: expor `Qtd` na tabela de rebalanceamento com conversão BRL->USD quando necessário.
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
Goal: alinhar tabela ativos com rebalance em ícones, teleport, formatação, cards e espaçamento.
Archive: `openspec/changes/archive/2026-07-15-f36-consistencia-visual-completa-tabela-ativos-rebalance/`

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

### F41 - Remover Atual e Alvo da linha de totais da classe
Status: `Archived` — 2026-07-17
Goal: remover valores de Atual e Alvo (sempre 100%/100%) da linha de totais da classe, manter apenas Desvio.
Archive: `openspec/changes/archive/2026-07-17-f41-remover-atual-e-alvo-da-linha-de-totais-da-classe/`

### F42 - Desvio condicional na linha de totais
Status: `Archived` — 2026-07-17
Goal: exibir desvio na linha de totais apenas quando diferente de zero (verde positivo, vermelho negativo, "—" para zero).
Archive: `openspec/changes/archive/2026-07-17-f42-desvio-condicional-na-linha-de-totais/`

### F43 - Corrigir tamanho da fonte na linha de totais
Status: `Archived` — 2026-07-17
Goal: alinhar tamanho da fonte da linha de totais da classe com o resto da tabela de patrimônio (atualmente parece menor).
Archive: `openspec/changes/archive/2026-07-17-f43-corrigir-tamanho-da-fonte-na-linha-de-totais/`

### F44 - Ajustar largura das colunas da tabela de patrimônio
Status: `Archived` — 2026-07-17
Goal: otimizar largura das colunas — aumentar "Ativo", reduzir colunas de percentual.
Archive: `openspec/changes/archive/2026-07-17-f44-ajustar-largura-das-colunas-da-tabela-de-patrimonio/`

### F45 - Separar visualmente grupos Classe e Carteira
Status: `Archived` — 2026-07-17
Goal: quebrar linha contínua de borda entre headers "Classe" e "Carteira" para criar 2 segmentos visuais distintos.
Archive: `openspec/changes/archive/2026-07-17-f45-separar-visualmente-grupos-classe-e-carteira/`

### F46 - Formatação 1 casa decimal nas colunas Classe e Carteira
Status: `Archived` — 2026-07-19
Goal: formatar colunas Atual/Alvo/Desvio nos grupos Classe e Carteira com 1 casa decimal.
Archive: `openspec/changes/archive/2026-07-19-f46-formatacao-1-casa-decimal-classe-e-carteira/`

### F47 - Corrigir filtros teleport tabela patrimônio
Status: `Archived` — 2026-07-20
Goal: restaurar filtros na tabela patrimônio — remover teleport, alinhar com padrão rebalance, adicionar fallbacks inline.
Archive: `openspec/changes/archive/2026-07-20-f47-corrigir-filtros-teleport-tabela-patrimonio/`
Notes: Teleport removido. Overflow CSS corrigido. Fallbacks inline + static import + openFilter pré-populado.

### T27 - Corrigir 5 integration tests desatualizados
Status: `Archived` — 2026-07-25
Goal: corrigir assertions em test_pages_routes.py e test_real_csv_flow.py que ficaram defasadas após commits ab2e0aa (F46) e bcb68836 (CSV alignment). Test-only, zero production code.
Archive: `openspec/changes/archive/2026-07-25-fix-5-failing-integration-tests/`

### T28 - Corrigir 18 E2E/BDD tests (2 code bugs + 3 test drifts)
Status: `Archived` — 2026-07-25
Goal: corrigir 2 bugs de produção (stale filter bounds após PATCH, prefixo R$ duplicado no import modal) e 3 drifts de assertion (formato decimal F46, contagem de colunas F39, selector faltante). 13 testes BDD + 5 testes E2E.
Archive: `openspec/changes/archive/2026-07-25-fix-18-failing-e2e-bdd-tests/`

### T29 - Investigar e corrigir testes falhando (diagnóstico completo)
Status: `Archived` — 2026-07-26
Goal: garantir rotina completa verde em até 5 minutos com cobertura de testes/harness reconciliada e redução visual desktop exatamente autorizada.
Archive: `openspec/changes/archive/2026-07-26-t29-investigar-e-corrigir-testes-falhando/`

### F48 - PoC sincronização MyProfit via Playwright
Status: `Archived` — 2026-07-27
Goal: encerrar PoC Playwright MyProfit após bloqueio pré-login, sem caminho automatizado suportado.
Archive: `openspec/changes/archive/2026-07-27-f48-poc-sincronizacao-myprofit-playwright/`

### I07 - Profile-based model/provider/effort management for OpenCode agents
Status: `Archived` — 2026-07-25
Goal: fix profile config delivery — OpenCode ignores env vars; generate effective `opencode.json` per profile via template + atomic write.
Candidate OpenSpec change id: `i07-profile-based-model-provider-effort-management`
Spec link: `openspec/changes/i07-profile-based-model-provider-effort-management/`
Files: `scripts/oc_profile.py`, `scripts/opencode_template.json`, `.opencode-profiles/`, `.gitignore`, `AGENTS.md`
Archive: `openspec/changes/archive/2026-07-25-i07-profile-based-model-provider-effort-management/`
Notes: root cause confirmed — OpenCode doesn't read env vars for model override; `opencode.json` hardcoded prevalece. Correction: template + atomic config generation. Manual subagent ping confirmed `openai-balanced` effective.

### T30 - Investigar cards de classe, dados disponíveis e alternativas de chart lib
Status: `Archived` — 2026-07-27
Goal: entregar investigação técnica source-linked para propor F49 bridge graphic, com decisão SVG/CSS puro e gaps de dados documentados.
Archive: `openspec/changes/archive/2026-07-27-t30-investigar-cards-classes-dados-e-chart-lib/`

### F49 - Bridge graphic com linguagem visual para cards de classe
Status: `Archived` (superseded por F52; abordagem manual abandonada) — 2026-07-28
Goal: substituir resumo numérico por waterfall/bridge monetária mantível em cada card de classe, com sequência normativa `Atual → Compra/Venda líquida → Desvio residual → Alvo`; escala BRL independente por card e referenciada ao valor atual, sem comparação entre cards.
Candidate OpenSpec change id: `f49-bridge-graphic-linguagem-visual-cards-classe`
Archive: `openspec/changes/archive/2026-07-28-f49-bridge-graphic-linguagem-visual-cards-classe/`
Notes: Fidelity ledger: quatro etapas monetárias visíveis — `Atual → Compra/Venda líquida → Desvio residual → Alvo`; cada etapa exibe BRL e percentual pareados. Geometria usa valores BRL referenciados ao valor atual dentro do próprio card; não há escala compartilhada entre cards. Compra/venda líquida deve representar trades mistos compensados, sem tratar operação líquida como classe negociável/executável. Proibidos: gráfico percentual genérico, overlay atual/projetado, marcador de alvo por ponto/bolinha. Cores, ícones e efeitos distinguem contribuição e estado sem depender apenas de cor. Fallback textual, WCAG AA, mobile 320px e tokens dark mode obrigatórios. Mapeamento de campos BRL, fontes, sinais, arredondamento, zero, limites e ausente são perguntas de proposta; não inferir comportamento. Gate: owner aprova mock/protótipo visual e mapping antes de implementação runtime.
Acceptance: Ações — Atual R$100k/14.6%, compra líquida R$25k/0.2%, residual R$25k/0.2%, Alvo R$150k/15%. FII — Atual R$120k/15.2%, venda líquida R$20k/0.2%, residual R$0/0%, Alvo R$100k/15%. Sequência, BRL/% pareados e escala local devem ser preservados; tabela por ativo e contratos não relacionados não mudam.
Progress: 2026-07-28 — implementação manual abandonada e substituída por F52 (ECharts). Change folder arquivada como histórico em `openspec/changes/archive/2026-07-28-f49-bridge-graphic-linguagem-visual-cards-classe/`; mock/handoff preservados (handoff também em `openspec/.temp_assets/f49-bridge-handoff.md`). Não retomar.

<!-- Historical contract superseded by corrected F49 ledger above; retained for audit only.

#### Objetivo
Transformar os cards de classe de resumo numérico (Atual/Alvo/Desvio/Valor/Projetado) em bridge graphic horizontal que mostra visualmente a trajetória de cada classe: posição atual → posição alvo, com resultado líquido do rebalanceamento (compra/venda) evidenciado por cor, ícone e seta.

#### Não-objetivos
- Adicionar tooltip interativo, zoom, pan ou animações complexas (ECharts overkill para este caso).
- Mostrar escala absoluta entre cards (cada card tem escala interna própria, normalizada 0-100% ou 0-max(valor_absoluto)).
- Alterar a tabela de plano por ativo (seção `rebalance-asset-section`).
- Alterar métricas globais (`RebalancePlanMetrics`).
- Adicionar filtros ou ordenação nos cards (já existe sorting por `categorySortKey`).
- Alterar o solver ou engine de rebalanceamento.

#### Escopo funcional
1. **Bridge graphic por card** — barra horizontal dupla:
   - **Barra inferior** (fundo): posição atual (`current_pct`) — cor vermelha se acima do alvo, verde se abaixo.
   - **Barra superior** (projetada): posição após rebalanceamento (`projected_pct`) — cor que indica direção.
   - **Marcador de alvo**: linha vertical ou indicador no ponto `target_pct`.
   - **Seta/seta de gap**: indica distância entre atual e alvo, colorida por direção.
2. **Resultado líquido** — badge ou ícone showing:
   - `delta > 0` → compra (verde, seta para cima ou `▲`)
   - `delta < 0` → venda (vermelho, seta para baixo ou `▼`)
   - `delta ≈ 0` → hold (neutro, `—` ou sem badge)
3. **Linguagem visual** — manter sistema de cores existente:
   - `--positive` (verde): abaixo do alvo, compra, gap positivo
   - `--negative` (vermelho): acima do alvo, venda, gap negativo
   - Bordas, fundos e ícones seguindo padrão `--above`/`--below` já validado em F25/F37.
4. **Fallback textual** — se SVG não renderizar, mostrar valores numéricos (Atual/Alvo/Desvio) como fallback.

#### Cenários de compra/venda líquida
- **Cenário 1 (compra, abaixo do alvo)**:
  - `current_pct = 15%`, `target_pct = 25%`, `deviation_pct = -10pp`
  - `delta = +R$ 5.000` (compra líquida)
  - `projected_pct = 22%` (não chega ao alvo por falta de aporte)
  - Bridge: barra vermelha (atual) < barra verde (alvo), seta verde mostrando gap residual.
  - Cores: card `--below` (borda vermelha), bridge verde (compra).
- **Cenário 2 (venda, acima do alvo)**:
  - `current_pct = 35%`, `target_pct = 25%`, `deviation_pct = +10pp`
  - `delta = -R$ 8.000` (venda líquida)
  - `projected_pct = 25%` (enquadra exatamente)
  - Bridge: barra vermelha (atual) > barra verde (alvo), seta vermelha mostrando redução.
  - Cores: card `--above` (borda verde), bridge vermelho (venda).
  - Gap 0 = barra projetada encosta na barra alvo.
- **Cenário 3 (hold, no alvo)**:
  - `current_pct = 25%`, `target_pct = 25%`, `deviation_pct = 0pp`
  - `delta ≈ 0`
  - Bridge: barras alinhadas, cor neutra, sem seta.
  - Card pode mostrar badge "✓" ou texto "No alvo".

#### Regras de cálculo e estados
- **Posição atual**: `current_pct` (server-side, `postprocessing.py`). Normalizar para escala do card: `current_pct / max_pct_in_card * bar_width`.
- **Posição alvo**: `target_pct` (server-side). Normalizar idem.
- **Posição projetada**: `projected_pct` (client-side, `_computeCategories`). Normalizar idem.
- **Gap**: `target_pct - current_pct` (em pp). Se negativo, acima do alvo.
- **Resultado líquido**: `delta` (server-side, `projected_value - current_value`). Sinal determina buy/sell/hold.
- **Ação computada** (front): `net_action = delta > threshold ? 'buy' : delta < -threshold ? 'sell' : 'hold'` onde `threshold` pode ser 0 ou `min_deviation_pct` (decisão T30).
- **Estados visuais**:
  - `deviation_pct >= 0` → `--above` (borda verde, fundo verde claro)
  - `deviation_pct < 0` → `--below` (borda vermelha, fundo vermelho claro)
  - `delta > 0` → badge compra verde
  - `delta < 0` → badge venda vermelho
  - `|delta| < epsilon` → badge hold neutro

#### Requisitos de escala interna por card
- Bridge graphic NÃO compartilha escala entre cards (decisão de design: cada card normaliza internamente).
- Dentro do card: escala 0 a max(`current_pct`, `target_pct`, `projected_pct`) * 1.1 (folga 10%).
- Barra largura: 100% do card (dentro do padding).
- Altura da barra: ~8-12px (compacto, cabe em card de ~13rem).
- Marcador de alvo: linha vertical de ~16px altura, cor `--accent` ou `--ink-muted`.
- Seta de gap: SVG path ou CSS border-trick, ~12px.

#### Acessibilidade e responsividade
- Cada card com bridge graphic precisa de `aria-label` descritivo: "Classe Renda Fixa: atual 15%, alvo 25%, compra R$ 5.000, projetado 22%".
- Bridge graphic SVG precisa de `role="img"` e `aria-hidden="true"` (info textual já no aria-label).
- Contraste: texto sobre bridge graphic deve ter ratio >= 4.5:1 (WCAG AA). Testar com `--positive`/`--negative` sobre `--surface`.
- Mobile (< 13rem): bridge graphic mantém proporção, barras ficam mais finas. Testar em viewport 320px.
- Dark mode: bridge graphic usa `var(--*)` tokens, funciona automaticamente com palette swap (F14).
- Keyboard: cards não são interativos (apenas display), então não precisam de focus ring.

#### Decisão ECharts vs SVG/CSS
**Decisão: SVG/CSS puro (recomendado).**
- Bridge graphic é 2-3 barras horizontais + 1 marcador vertical + 1 seta. Não precisa de: tooltip, zoom, pan, legend, axis, animation easing, data binding.
- SVG inline + CSS variables = zero dependência, ~0KB extra, controle total de tema.
- ECharts (~250KB gzipped) seria overkill; justificável apenas se owner quiser tooltips interativos ou gráficos mais complexos no futuro.
- Se owner insistir em ECharts após ver protótipo SVG: criar fatia separada para migração.

#### Dados e campos esperados
| Campo | Tipo | Origem | Usado no bridge graphic |
|-------|------|--------|-------------------------|
| `category_name` | str | schema | sim (header do card) |
| `current_pct` | float | schema | sim (barra atual, eixo X) |
| `target_pct` | float | schema | sim (marcador de alvo, eixo X) |
| `deviation_pct` | float | schema | sim (cor da seta, badge) |
| `delta` | float | schema | sim (badge compra/venda/hold, cor) |
| `projected_pct` | float | computado front | sim (barra projetada, eixo X) |
| `current_value` | float | schema | opcional (tooltip ou fallback textual) |
| `projected_value` | float | schema | opcional (tooltip ou fallback textual) |

#### Arquivos a alterar
1. `src/omaha/templates/_rebalance_plan.html` — substituir conteúdo do card (L46-76) por bridge graphic SVG + fallback textual.
2. `src/omaha/templates/rebalance.html` — adicionar helper `computeNetAction(delta)`, possivelmente helper `bridgeScale(pct)` para normalização.
3. `src/omaha/static/app.css` — novos estilos `.rebalance-bridge-*` (bar, marker, arrow, badge). Manter estilos `.rebalance-class-card*` existentes como fallback.
4. `src/omaha/rebalance/schemas.py` — possível adição de campo `net_action` se T30 concluir que `delta` não é suficiente (decisão pendente).
5. `tests/test_rebalance_page.py` — atualizar `test_class_deviation_summary_renders` para verificar bridge graphic (SVG ou data-testid).
6. `tests/test_rebalance_schemas.py` — se schema mudar, atualizar `test_category_plan_row_carries_exactly_seven_fields`.
7. `tests/visual/test_snapshots.py` — atualizar baseline `rebalance-plan` para incluir bridge graphic.

#### Testes e aceitação
- [ ] Bridge graphic renderiza para cada classe com `current_pct`, `target_pct`, `projected_pct`.
- [ ] Cenário 1 (compra, abaixo): card verde, seta verde, badge "Compra R$ X".
- [ ] Cenário 2 (venda, acima): card vermelho, seta vermelha, badge "Venda R$ X".
- [ ] Cenário 3 (hold, no alvo): card neutro, sem seta, badge "No alvo" ou "—".
- [ ] Gap residual visível quando projected não alcança target.
- [ ] Gap 0 visível quando projected = target (barra projetada encosta na alvo).
- [ ] `aria-label` descritivo em cada card.
- [ ] Contraste >= 4.5:1 (WCAG AA) para texto sobre bridge graphic.
- [ ] Responsivo: bridge graphic legível em 320px mobile.
- [ ] Dark mode: bridge graphic usa tokens CSS, não hardcoded colors.
- [ ] Fallback textual: se SVG falhar, valores numéricos aparecem.
- [ ] Visual baseline atualizado sem diff inesperado.
- [ ] `test_category_plan_row_carries_exactly_seven_fields` passa (ou atualizado se schema mudar).
- [ ] `test_class_deviation_summary_renders` passa com bridge graphic.
- [ ] E2E `test_editing_contribution_refreshes_plan_automatically` não quebra.
- [ ] Nenhum impacto na tabela de plano por ativo.

#### Dependências
- **Hard**: T30 (investigação deve completar antes de propor F49).
- **Soft**: F48 (PoC MyProfit) pode coexistir; não há conflito de arquivos.
- T27, T28, T29 podem coexistir; não há conflito de arquivos.

#### Riscos
- **Alto**: se `delta` não representar compra/venda líquida (T30 deve confirmar), F49 precisa de campo adicional no schema → impacto cascata em postprocessing, glue, engine, stub, testes de schema.
- **Médio**: bridge graphic pode quebrar visual baseline existente → precisa atualizar snapshots.
- **Médio**: se SVG inline for muito verbose, pode impactar performance de renderização com muitas classes (>10).
- **Baixo**: contraste de cores em dark mode → mitigado por uso de tokens CSS.
- **Baixo**: responsividade mobile → mitigado por escala interna do card.

#### Ordem recomendada
1. T30 (investigação) → completar notas técnicas.
2. F49 (implementação) → propor com base em T30, implementar bridge graphic.

#### Critério de pronto
- Bridge graphic renderiza corretamente para todos os cenários (compra, venda, hold).
- Visual baseline atualizado e passando.
- Todos os testes de cards passando.
- Acessibilidade OK (aria-label, contraste, responsividade).
- Dark mode funciona sem hardcoded colors.
- Owner aprova visual no browser (refresh-for-test).

Notes: BLOQUEADA: implementação atual viola gramática visual aprovada pelo owner; não iniciar mais implementação, review ou finalização nesta fatia. Preservar change id e artifacts históricos. A correção será planejada em F50/F51; F49 não deve ser renomeada, apagada ou retomada.
Progress: 2026-07-27 — proposta criada em `openspec/changes/f49-bridge-graphic-linguagem-visual-cards-classe/`; validação anterior passou. Implementação/review interrompidos por contrato visual incorreto; substituição planejada sem alterar histórico.

-->

### F50 - Mock aprovado da ponte monetária dos cards de classe
Status: `Deprecated` — 2026-07-27 (owner directed correction to remain entirely in F49; no separate execution slice)
Goal: historical split rejected; mock/prototype approval is now a gate inside F49.
Candidate OpenSpec change id: `f50-mock-aprovado-ponte-monetaria-cards-classe`
Spec link: `openspec/changes/f50-mock-aprovado-ponte-monetaria-cards-classe/`
Files: `src/omaha/templates/_rebalance_plan.html`, `src/omaha/templates/rebalance.html`, `src/omaha/rebalance/schemas.py`, `src/omaha/rebalance/glue.py`, `src/omaha/rebalance/postprocessing.py`
Dependencies: F49 apenas como histórico bloqueado; não depende de implementação F49. F51 depende de mock e mapeamento aprovados pelo owner.
Notes: Deprecated per owner direction; mock, mapping, ledger and approval gate absorbed into F49.
Progress: pending — propor mock; pending — obter aprovação owner; pending — registrar mapping/grammar final; pending — spec verification.

### F51 - Integrar ponte monetária aprovada nos cards de classe
Status: `Deprecated` — 2026-07-27 (owner directed correction to remain entirely in F49; no separate execution slice)
Goal: historical split rejected; runtime integration is now part of F49 after its approval gate.
Candidate OpenSpec change id: `f51-integrar-ponte-monetaria-aprovada-cards-classe`
Spec link: `openspec/changes/f51-integrar-ponte-monetaria-aprovada-cards-classe/`
Files: `src/omaha/templates/_rebalance_plan.html`, `src/omaha/templates/rebalance.html`, `src/omaha/static/app.css`, `src/omaha/rebalance/schemas.py`, `tests/test_rebalance_page.py`
Dependencies: None; runtime work absorbed into F49.
Notes: Deprecated per owner direction; runtime integration absorbed into F49 after its owner-approval gate.
Progress: pending — proposta; pending — owner handoff F50 confirmado; pending — implementação; pending — review; pending — refresh-for-test; pending — finalização.

### D03 - Gate de performance de testes nos agentes apply e review
Status: `Archived` — 2026-07-26
Goal: separar validação focada do apply de uma única suíte completa temporizada no review, com teto de cinco minutos sem reduzir cobertura.
Archive: `openspec/changes/archive/2026-07-26-d03-gate-de-performance-de-testes-nos-agentes/`

### F52 - Waterfall ECharts nos cards de classe
Status: `Archived` — 2026-07-28
Goal: waterfall ECharts (renderer SVG) nos cards de classe do `/rebalanceamento` — ponte `Atual → Compra/Venda → Desvio → Alvo`, eixo Y adaptativo por card, rótulos short-scale, fonte Inter 300; fixes de PRG/cold-load/cache no caminho; mock aposentado.
Archive: `openspec/changes/archive/2026-07-28-f52-waterfall-echarts-nos-cards-de-classe/`
Notes:
- **Referência normativa:** `openspec/.temp_assets/f49-bridge-handoff.md` — contrato visual aprovado (§1), regras de negócio runtime (§2), lições aprendidas (§3), inventário verificado do que substituir/remover/preservar (§4), diretriz ECharts (§5). Ler integralmente antes de propor. Mock aprovado + spec delta de F49 são leitura complementar.
- **Context7 obrigatório:** antes/durante o propose, consultar documentação ATUAL do Apache ECharts via Context7 — receita de waterfall (barra empilhada com série base transparente), API de `stack`, theming (registro de tema ou `getComputedStyle` + re-registro no swap dark), `tooltip: { show: false }`, eixo Y (`min: 0`, `max`/`interval` do `_niceAxis`, `axisLabel.formatter` short scale, `splitLine` em todo tick), labels de série (lib cuida de colisão — lição 3, NÃO reposicionar à mão), resize responsivo (`ResizeObserver`/320px). Objetivo declarado pelo owner: gráficos de fácil manutenção.
- **Vendor/CDN:** decisão de design no propose (vendored em `static/vendor/` vs CDN) — não é fatia separada. Justificar manutenção + offline.
- **Fidelity ledger (mock aprovado é normativo, não inspiração):** requisito literal → ponte monetária por classe aprovada no mock; semântica percebida → trajetória `Atual → Compra/Venda → Desvio → Alvo` em BRL dentro do próprio card; renderização exigida → ECharts empilhado com totais ancorados em zero e deltas flutuantes entre níveis cumulativos C1/C2/C3; fonte de dados → payload existente `window.__rebalancePlan` (agregação alvo via `_targetForCategory`, denominador via `_plannedTotal`); evidência → handoff §1/§2 + mock L18-109.
- **Gramática visual (handoff §1):** sequência fixa 4 etapas; totais `Atual`/`Alvo` azuis `--class-1` ancorados em 0; deltas Compra (verde `--positive`) / Venda (vermelho `--negative`) / Desvio não-zero (âmbar `--alert-warn`), zero = linha sólida neutra SEM barra; conectores cumulativos tracejados sem pontos; escala local BRL por card, Y de R$0 com 4-5 ticks bonitos (1/2/2,5/5 × 10ⁿ, teto = próximo tick estritamente acima de `max(Atual, Projetado, Alvo)`, menor teto → menor passo); grid horizontal em todo tick; largura de barra 45% centralizada; nomes das etapas SOMENTE no eixo X centralizados; rótulos sobre barra SOMENTE valor absoluto short scale + percentual; shell `.rebalance-class-card` EXATO preservado; gráfico ocupa todo o conteúdo disponível (sem footer/status/equação); estado acima/abaixo apenas via borda + `aria-label` (vermelho/azul), gráfico não comunica estado por fundo; legível em 320px sem overflow; dark mode via tokens (proibido cor hardcoded — WCAG AA, DESIGN.md §6).
- **Mapeamentos numéricos:** short scale obrigatória em TODOS os rótulos e eixo Y — `R$ 113.746,00` → `R$ 113,7k` (1 casa, PT-BR; < 1000 integral); percentuais de etapa = `round(abs(valor_etapa) / total_final_planejado × 100, 1)` com `total_final_planejado = Σ asset_plan.target_value` finitos (NUNCA derivar de `target_pct` — denominador é total corrente, ver handoff §2); ε = `DISPLAY_TOLERANCE = 0.0001` classifica Compra/Venda/zero; cenário de aceite: Ações `R$100k/14,6% → +R$25k/0,2% → +R$25k/0,2% → R$150k/15%` (ticks `0/50,0k/100,0k/150,0k/200,0k`), FII `R$120k/15,2% → -R$20k/0,2% → R$0/0% → R$100k/15%` (ticks `0/50,0k/100,0k/150,0k`).
- **Zero/borda/ausente:** desvio dentro de ε → etapa válida `R$ 0` + `0%` sem barra; classe sem linhas `asset_plan` ou input não-finito ou `total_final_planned <= 0` → fallback `Dados indisponíveis para esta ponte`, SEM instanciar chart, SEM `R$0` inferido, SEM geometria falsa.
- **Proibições (reinterpretar o mock = falha):** gráfico percentual genérico, overlay atual/projetado, marcador/bolinha de alvo, delta ancorado em zero como total, 4 mini-barras antigas, escala compartilhada entre cards, loop SVG/Alpine, tooltip-only como informação, nomes repetidos na barra, controle de trade por classe, cores hardcoded. Textos removidos NÃO podem voltar: aviso `Sugestões abaixo dos mínimos viram Manter.` e linha visível `Compra/Venda líquida` + valor (nome da etapa líquida apenas em `aria-label`). Display-only: saldo líquido é informativo, nunca ordem executável; tabela por ativo é a única fonte de ação; solver/thresholds/métricas globais intocados.
- **Limpeza:** remover CSS morto `.rebalance-waterfall-*` (app.css L2893-3002), `.rebalance-bridge-svg/-track/-residual/-marker/-legend` (L3009-3056) e overrides 360px associados (L3066-3073); reescrever `.rebalance-class-card-bridge` como container do chart; preservar shell `.rebalance-class-card*` (L2855-2888) e grid `.rebalance-class-summary` (L2848-2854) EXATOS; substituir DOM manual em `_rebalance_plan.html` L52-83 mantendo header L49-51, `data-testid`, tabela `.rebalance-asset-section` e fallback de indisponibilidade (inventário completo no handoff §4).
- **Mock route:** `/rebalanceamento/bridge-mock` + `rebalance_bridge_mock.html` NÃO mexer durante a implementação; aposentar somente após owner aprovar a versão ECharts por side-by-side (aposentadoria pode ser follow-up mínimo no finalize/propose, registrar no propose).
- Gate visual: mock já aprovado pelo owner — NÃO há gate de mock novo; o gate é paridade visual da implementação ECharts com o mock aprovado, verificada pelo owner antes do archive.
Acceptance: side-by-side com `/rebalanceamento/bridge-mock` sem divergência perceptível em desktop + viewport 320px + dark mode (owner aprova); todas as regras de negócio do handoff §2 preservadas (short scale `R$ 113,7k` em barras e eixo Y, ε `0.0001`, estado `Dados indisponíveis para esta ponte` sem chart, denominador `total_final_planned`); shell do card e `aria-labels` intactos; textos removidos ausentes; testes comportamentais focados (renderização ECharts por card, estados compra/venda/zero/indisponível, agregações) + suíte completa verde + baseline visual atualizado sem diff não-autorizado; refresh-for-test com receipt obrigatório (PRD §4.9).
Progress: propose DONE (4 artifacts, validate --strict ✓); apply DONE (ECharts 6.1.0 vendored, focused tests green, receipt emitted); T29 pre-existing manifest fix DONE (reverted incomplete 1025→1027 rename); review round 1 CHANGES_REQUESTED (gitignore vendor blocker + aria state + nits) → fixes applied; full-suite re-review interrupted; owner testou → charts initially empty = stale browser cache (no Cache-Control on HTML), resolvido com hard refresh; 2026-07-28 owner visual feedback: remover labels do eixo Y + gráfico preencher todo espaço do card (respeitar título + padding geral) → DONE (grid containLabel:false, y axisLabel.show:false, CSS intocado); 2026-07-28 owner reportou pixelização no zoom = canvas raster (renderer padrão) → DONE trocar para renderer SVG (echarts.init com renderer:'svg'), vira elemento vetorial DOM, probe 6/6 svg 0 canvas; 2026-07-28 cards vazios DE NOVO no browser do owner — causa REAL: assets estáticos (app.css/echarts.min.js) sem Cache-Control → cache heurístico → CSS/JS velho na página fresca (HTML já era no-store; SVG funcionava, probe 6/6) → DONE: StaticCacheControlMiddleware em middleware.py+main.py seta Cache-Control:no-cache em /static/* (HTML mantido no-store, endossado); 2026-07-28 owner: gráfico some no refresh + alerta "reenviar formulário?" — diagnóstico HIGH: gráfico OK (GET/POST/re-POST 6/6 svg); raiz = violação POST-Redirect-GET pré-existente em post_rebalanceamento (pages.py:701 renderiza 200 em vez de 303) → bugfix cirúrgico separado do F52 (sucesso POST→303→GET); 2026-07-28 owner: gráfico some no HARD REFRESH mas volta em reload/navegação — diagnóstico HIGH (reproduzido EXP C throttled): race de loading, x-init do Alpine roda antes do echarts.min.js (1.1MB frio), renderBridgeChart return silencioso sem retry/RO; fix = rAF-retry até window.echarts existir + corrigir comentário errado (rebalance.html:4-6) + teste regressão e2e que atrasa echarts; 2026-07-28 owner aprovou visual (SVG/tamanho/espaço); NOVO pedido: eixo Y com piso adaptativo por card (menor valor arredondado p/ baixo, espelhando o teto) → implementar _niceAxisRange(min,max) + rebasear barras de total (Atual/Alvo) para o piso (evitar clipping; labels seguem valores reais; consequência = barras de total relativas ao piso, comunicado ao owner); 2026-07-28 owner aprovou eixo adaptativo; pedido padronização de fonte do gráfico: fontFamily Inter (RHD descartada — só carrega 700/800), x-names 15px/300, valor R$ 14px/300, pct 300 por consistência; CRÍTICO: Inter hoje carrega 400..700 (sem 300) → alargar base.html p/ Inter:wght@300..700 senão 300 vira fallback; DONE — archived 2026-07-28 (commit `054f320`, full suite 1.028 nodes green, owner aprovou todas as melhorias; mock aposentado, specs sincronizadas, change arquivado).

### F53 - Ordem dos cards de classe no rebalanceamento
Status: `Archived` — 2026-07-29
Goal: exibir os cards de classe do `/rebalanceamento` na ordem normativa `RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`, sem alterar conteúdo, estilo ou solver.
Archive: `openspec/changes/archive/2026-07-29-f53-ordem-dos-cards-de-classe-no-rebalanceamento/`
Notes:
- Ordem resolvida client-side por mapa nome→posição em `rebalance.html` (sort dead removido); classes fora do mapa renderizam ao final em ordem alfabética. `RebalanceCategoryPlanRow` (7 campos) e payload intactos. Requisito sincronizado em `openspec/specs/rebalance-page/spec.md`.

### F54 - Ordem dos blocos de classe no patrimônio
Status: `Archived` — 2026-07-29
Goal: exibir os blocos de tabelas de classe do `/patrimonio` na ordem normativa `RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto` via renumeração do `display_order` no seed CSV.
Archive: `openspec/changes/archive/2026-07-29-f54-ordem-dos-blocos-de-classe-no-patrimonio/`
Notes:
- Escopo mínimo: somente renumeração dos CSVs, zero mudança em `pages.py`. Cores rotacionam posicionalmente (owner aceitou).
- Gate: edições em `data/seed/` exigem permissão explícita do owner por ação.

### F55 - Aumentar tamanho da fonte do menu principal
Status: `Archived` — 2026-07-29
Goal: aumentar em 50% o font-size dos nomes das páginas na tab nav superior.
Archive: `openspec/changes/archive/2026-07-29-f55-aumentar-tamanho-da-fonte-do-menu-principal/`

### D04 - Corrigir spec drift do POST /rebalanceamento
Status: `Archived` — 2026-07-29
Goal: corrigir o requisito da spec `rebalance-page` que ainda descrevia `POST /rebalanceamento` retornando 200; o código (PRG fix F52) retorna 303 → GET.
Archive: `openspec/changes/archive/2026-07-29-d04-corrigir-spec-drift-post-rebalanceamento/`

---

## Recommended Execution Order

**Active queue:**
_— vazio —_

**Archived since prior queue:** F55 (fonte tab nav +50%, 2026-07-29), F54 (ordem normativa dos blocos, 2026-07-29), F53 (ordem normativa dos cards, 2026-07-29), F52 (waterfall ECharts, commit `054f320`, 2026-07-28), T27, T28, T29, I07 e D03. Não são trabalho ativo.

Order note: F49 correction absorbs mock approval and runtime integration after owner direction. F50/F51 deprecated and excluded from execution.

Order note: F41-F45 são melhorias visuais na tabela de patrimônio. Ordens sugeridas:
1. F43 (corrigir fonte) — CSS-only, correção visual rápida
2. F44 (ajustar largura) — CSS-only, melhoria de layout
3. F45 (separar grupos) — CSS + HTML, separação visual
4. F41 (remover Atual/Alvo) — HTML-only, simplificação
5. F42 (desvio condicional) — HTML + lógica, comportamento novo

**Deferred/Deprecated** (owner decides):
- F03 (Rentabilidade) — closed, reactivation path documented above.
- F04 (Proventos) — deprecated, `restore f04` to reactivate.


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
