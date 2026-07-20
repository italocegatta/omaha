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
Status: `Deprecated` — 2026-07-12 (split into F27-F29)
Goal: padrão visual único em tabelas + inspeção visual obrigatória.

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
Status: `Applied` — validação visual OK (2026-07-19)
Goal: formatar colunas "Atual", "Alvo", "Desvio" nos grupos "Classe" e "Carteira" da tabela de patrimônio com 1 casa decimal (incluindo linha de totais), mantendo formatação centralizada e fácil de alterar.
Candidate OpenSpec change id: `f46-formatacao-1-casa-decimal-classe-e-carteira`
Spec link: `openspec/changes/f46-formatacao-1-casa-decimal-classe-e-carteira/`
Files: `src/omaha/templates/_patrimonio_class_section.html` (only template edits — formatters already accept decimals param)

---

## Recommended Execution Order

**Active queue:** F46 (única slice ativa — F41-F45 já archived)

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
