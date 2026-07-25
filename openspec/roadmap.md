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
Candidate OpenSpec change id: `fix-5-failing-integration-tests`
Files: `tests/test_pages_routes.py`, `tests/test_real_csv_flow.py`
Archive: `openspec/changes/archive/2026-07-25-fix-5-failing-integration-tests/`
Progress: correção entregue no commit `064113c`; review independente aprovada; aguardando finalize/arquivamento. Seed não alterado. Relacionada: T29 (diagnóstico completo de falhas) pode revalidar ou complementar correções desta fatia.

### T28 - Corrigir 18 E2E/BDD tests (2 code bugs + 3 test drifts)
Status: `Archived` — 2026-07-25
Goal: corrigir 2 bugs de produção (stale filter bounds após PATCH, prefixo R$ duplicado no import modal) e 3 drifts de assertion (formato decimal F46, contagem de colunas F39, selector faltante). 13 testes BDD + 5 testes E2E.
Candidate OpenSpec change id: `fix-18-failing-e2e-bdd-tests`
Files: `src/omaha/templates/_patrimonio_add_asset_modal.html`, `tests/e2e/test_inline_edit.py`, `tests/e2e/test_asset_table.py`, `tests/e2e/test_user_journey_rebalance.py`, `tests/e2e/test_import_modal.py`
Archive: `openspec/changes/archive/2026-07-25-fix-18-failing-e2e-bdd-tests/`
Progress: correção entregue no commit `064113c` (mesmo commit que T27). E2E 49/49, BDD 51/51, unit 452, integration 377 — todos verdes. Arquivado 2026-07-25.

### T29 - Investigar e corrigir testes falhando (diagnóstico completo)
Status: `Applying` — 2026-07-25
Goal: rodar suite completa (unit, integration, e2e, bdd), catalogar todas as falhas atuais, classificar cada uma (regressão recente, drift de assertion, bug de produção, flaky), e aplicar correções mínimas preservando mudanças existentes do usuário. Diferente de T27 (já corrigido, pendente review) e T28 (proposto, não iniciado): esta fatia é diagnóstico primeiro, correção depois — sem assumir que T27 ou T28 estão concluídos.
Candidate OpenSpec change id: `t29-investigar-e-corrigir-testes-falhando`
Spec link: `openspec/changes/t29-investigar-e-corrigir-testes-falhando/`
Files: `tests/` (scope completo), `src/` (apenas se bug de produção for causa-raiz)
Dependencies: nenhuma hard dependency. T27 e T28 podem coexistir; esta fatia foca em falhas não cobertas por ambas ou revalida o que ambas propõem.
Notes: priorizar diagnóstico de regressões introduzidas entre HEAD e commits recentes (ab2e0aa, bcb68836, 064113c). Preservar código funcional do usuário — correções cirúrgicas apenas. Se falhas já estiverem cobertas por T27/T28, documentar e não duplicar esforço. T28 parcialmente obsoleto (T27 `064113c` cobre issues propostos). Commit `bcb68836` irresolvível — não referenciar.
Progress: proposta completa (2026-07-22). Aplicação iniciada (2026-07-25).

### F48 - PoC sincronização MyProfit via Playwright
Status: `Applying` — 2026-07-21
Goal: criar PoC assistida que autentica no MyProfit, recusa modal opcional de 2FA, navega até `StockDetail.aspx`, exporta posição CSV e captura o download; sem integração com botão, banco ou importação nesta fatia.
Candidate OpenSpec change id: `f48-poc-sincronizacao-myprofit-playwright`
Spec link: `openspec/changes/f48-poc-sincronizacao-myprofit-playwright/`
Files: `src/omaha/config.py`, `.env.example`, `pyproject.toml`, `scripts/` ou módulo de integração dedicado, `tests/`
Notes: a criação e calibração dos seletores/fluxo será acompanhada pelo owner etapa a etapa. Credenciais somente server-side via `.env`; nunca registrar valores em código, logs, screenshots ou traces. Reutilizar Playwright Python existente; validar download contra parser CSV existente sem persistir posições.
Progress: Playwright 1.61.0 instalado (pyproject.toml + lockfile). Chromium 1228 presente em ~/.cache/ms-playwright. Unit (452 passed) + integration (377 passed) + myprofit_poc (18 passed) verdes. E2E/BDD timeouts classificados como pré-existentes/fora de escopo (T28). Login/navegação real ainda não iniciados — aguardando confirmação do owner para prosseguir com tarefas 2.3 e 2.4.

### I07 - Profile-based model/provider/effort management for OpenCode agents
Status: `Archived` — 2026-07-25
Goal: fix profile config delivery — OpenCode ignores env vars; generate effective `opencode.json` per profile via template + atomic write.
Candidate OpenSpec change id: `i07-profile-based-model-provider-effort-management`
Spec link: `openspec/changes/i07-profile-based-model-provider-effort-management/`
Files: `scripts/oc_profile.py`, `scripts/opencode_template.json`, `.opencode-profiles/`, `.gitignore`, `AGENTS.md`
Archive: `openspec/changes/archive/2026-07-25-i07-profile-based-model-provider-effort-management/`
Notes: root cause confirmed — OpenCode doesn't read env vars for model override; `opencode.json` hardcoded prevalece. Correction: template + atomic config generation. Manual subagent ping confirmed `openai-balanced` effective.

### T30 - Investigar cards de classe, dados disponíveis e alternativas de chart lib
Status: `Ready` — investigação futura (nenhum código de produção alterado)
Goal: documentar em `openspec/.temp_assets/` toda a base técnica necessária para propor F49 (bridge graphic). Inclui: estrutura HTML/CSS atual dos cards, campos do schema `RebalanceCategoryPlanRow` (7 campos), cálculo de `projected_pct` no front, opções de lib de gráfico (Apache ECharts ~800KB vs SVG/CSS puro), gaps de dados, testes impactados, e riscos de regressão.
Candidate OpenSpec change id: `t30-investigar-cards-classes-dados-e-chart-lib`
Spec link: `openspec/changes/t30-investigar-cards-classes-dados-e-chart-lib/`
Files: `src/omaha/templates/_rebalance_plan.html`, `src/omaha/templates/rebalance.html`, `src/omaha/rebalance/schemas.py`, `src/omaha/rebalance/postprocessing.py`, `src/omaha/static/app.css`, `tests/test_rebalance_page.py`, `tests/test_rebalance_schemas.py`, `tests/visual/test_snapshots.py`

#### Objetivo
Produzir notas técnicas completas em `openspec/.temp_assets/t30-notes.md` que alimentem a proposta de F49 sem ambiguidade. Nenhum arquivo de produção é alterado; output é documento de referência.

#### Não-objetivos
- Implementar bridge graphic ou qualquer alteração visual.
- Alterar schema `RebalanceCategoryPlanRow` (apenas documentar campos existentes).
- Adicionar libs ao `pyproject.toml`.
- Alterar testes existentes.

#### Escopo funcional da investigação
1. **Cards atuais** — mapear HTML (`_rebalance_plan.html` L41-78), CSS (`app.css` L2855-2914), Alpine (`rebalance.html` L373-435: `_computeCategories`, `classCardClass`, `formatPct1`, `formatBRL`, `formatDeviationPp`).
2. **Schema** — listar os 7 campos de `RebalanceCategoryPlanRow`: `category_name`, `current_value`, `projected_value`, `delta`, `target_pct`, `current_pct`, `deviation_pct`. Documentar que `projected_pct` é computado no front (não existe no schema Pydantic).
3. **Cálculo de `projected_pct`** — `_computeCategories` em `rebalance.html` L373-384: `projected_pct = projected_value / totalProjected * 100` onde `totalProjected = sum(asset_plan.projected_value)`. Confirmar que é peso percentual projetado, não valor monetário.
4. **`delta`** — investigar se `delta` (= `projected_value - current_value`) representa resultado líquido de compra/venda por classe. Hipótese: sim, `delta > 0` = compra líquida, `delta < 0` = venda líquida. Confirmar com exemplos reais do solver.
5. **`net_action`** — verificar se campo `action` (buy/sell/hold) existe no schema de classe ou apenas no de ativo (`RebalanceAssetPlanRow.action`). Hipótese: não existe no schema de classe; precisa ser computado no front a partir de `delta` (ou `deviation_pct`).
6. **Chart lib** — comparar:
   - **Apache ECharts** (~800KB gzipped ~250KB): rich charts, animações, tooltips, accessibility built-in. Bundle size alto para 2 cards.
   - **SVG/CSS puro**: zero dependência, controle total, ~0KB extra. Mas: animações manuais, accessibility DIY.
   - **Recomendação preliminar**: SVG/CSS puro para bridge graphic horizontal (segmento colorido com marcadores); ECharts overkill para 2 retas horizontais por card.
7. **Testes impactados** — catalogar todos os testes que tocam cards de classe:
   - `test_rebalance_page.py::test_class_deviation_summary_renders` (integration)
   - `test_rebalance_schemas.py::test_category_plan_row_carries_exactly_seven_fields` (unit)
   - `tests/visual/test_snapshots.py::test_rebalance_plan_snapshot[desktop|mobile]` (visual baseline)
   - `tests/e2e/test_rebalance_page.py` (e2e — verificar se cards são inspecionados)
8. **Gaps de dados** — se F49 precisar de `net_action` (buy/sell/hold) no schema de classe, documentar impacto em `postprocessing._build_category_plan`, `glue.py`, `engine.py`, `solver_stub.py`, e testes de schema.
9. **Acessibilidade** — verificar se cards atuais têm `aria-label`, roles, contraste de cor adequado (WCAG AA). Documentar gaps para F49.
10. **Responsividade** — verificar comportamento dos cards em mobile (grid `auto-fit` com `minmax(13rem, 1fr)` em L2850). Documentar se bridge graphic cabe em viewport estreito.

#### Cenários de compra/venda líquida (para documentar)
- **Cenário A (compra)**: `delta > 0`, `deviation_pct < 0` (abaixo do alvo). Classe precisa de aporte. Bridge graphic mostra barra vermelha (atual) < barra verde (alvo), com seta verde apontando para gap.
- **Cenário B (venda)**: `delta < 0`, `deviation_pct > 0` (acima do alvo). Classe excedeu alvo. Bridge graphic mostra barra vermelha (atual) > barra verde (alvo), com seta vermelha apontando para redução.
- **Cenário C (hold)**: `delta ≈ 0`, `deviation_pct ≈ 0`. Classe no alvo. Bridge graphic mostra barras alinhadas, cor neutra.
- Documentar se `delta = 0` significa exatamente hold ou se há threshold (F19: `min_deviation_value` e `min_deviation_pct`).

#### Regras de cálculo e estados
- `current_pct` = `current_value / total_current_value * 100` (server-side, `postprocessing.py` L255-256)
- `target_pct` = `target_weight * 100` (server-side, `postprocessing.py`)
- `deviation_pct` = `current_pct - target_pct` (server-side)
- `delta` = `projected_value - current_value` (server-side)
- `projected_pct` = `projected_value / totalProjected * 100` (client-side, `rebalance.html` L377-380)
- Estados visuais atuais: `--above` (deviation >= 0, borda verde), `--below` (deviation < 0, borda vermelha)

#### Requisitos de escala interna por card
- Cada card mostra: nome da classe, Atual (%), Alvo (%), Desvio (pp), Valor (R$), Projetado (%).
- Bridge graphic substituirá ou complementará esses 6 campos.
- Card mínimo: ~13rem largura (CSS grid `minmax`). Bridge graphic deve caber nesse espaço.
- Número de cards = número de classes de ativos (tipicamente 4-8: Renda Fixa, Ações, FIIs, ETFs, Cripto, Exterior, etc.).

#### Acessibilidade e responsividade
- Cards atuais: sem `aria-label` individual (apenas `aria-label="Resumo por classe"` no container).
- Contraste: `--ink` sobre `--surface` OK; `--ink-muted` sobre `--surface` pode falhar WCAG AA (verificar).
- Mobile: grid `auto-fit` colapsa para 1 coluna em telas < 13rem. Bridge graphic deve ser legível nessa largura.
- Bridge graphic precisa de: `aria-label` descritivo por card, fallback textual se SVG não renderizar, contraste mínimo 4.5:1.

#### Decisão ECharts vs SVG/CSS
- **Favor SVG/CSS**: bridge graphic é 2 barras horizontais por card (atual vs alvo) + marcador de gap. Não precisa de tooltip, zoom, pan, ou animações complexas. SVG inline + CSS variables = zero dependência, bundle size zero, controle total de tema (dark mode via `var(--*)`).
- **Favor ECharts**: se owner quiser tooltips interativos, animações de transição, ou futuros gráficos mais complexos (pizza de composição, linha temporal). Bundle ~250KB gzipped.
- **Recomendação**: SVG/CSS puro. ECharts só se owner insistir após ver protótipo SVG.

#### Dados e campos esperados
| Campo | Tipo | Origem | Usado no card atual | Usado no bridge graphic (F49) |
|-------|------|--------|---------------------|-------------------------------|
| `category_name` | str | schema | sim (header) | sim (header) |
| `current_value` | float | schema | não diretamente | sim (barra atual, se escala monetária) |
| `projected_value` | float | schema | não diretamente | sim (barra projetada) |
| `delta` | float | schema | sim (Valor R$) | sim (seta de gap) |
| `target_pct` | float | schema | sim (Alvo %) | sim (barra alvo) |
| `current_pct` | float | schema | sim (Atual %) | sim (barra atual %) |
| `deviation_pct` | float | schema | sim (Desvio pp) | sim (cor da seta) |
| `projected_pct` | float | computado front | sim (Projetado %) | sim (barra projetada %) |
| `net_action` | str | **não existe** | — | precisa computar: `delta > 0 ? 'buy' : delta < 0 ? 'sell' : 'hold'` |

#### Arquivos a inspecionar
1. `src/omaha/templates/_rebalance_plan.html` — HTML dos cards (L41-78), container `rebalance-class-summary`
2. `src/omaha/templates/rebalance.html` — Alpine `_computeCategories` (L373-384), `classCardClass` (L434-436), formatters
3. `src/omaha/rebalance/schemas.py` — `RebalanceCategoryPlanRow` (L41-53), 7 campos
4. `src/omaha/rebalance/postprocessing.py` — `_build_category_plan` (L230-278), cálculo de weights/gaps
5. `src/omaha/rebalance/glue.py` — tradução de native para schema v1 (L193-233)
6. `src/omaha/rebalance/engine.py` — `_translate_category_plan` (L140-148)
7. `src/omaha/rebalance/solver_stub.py` — `RebalanceCategoryPlanRowNative` (L57-66)
8. `src/omaha/static/app.css` — estilos `.rebalance-class-card*` (L2850-2914)
9. `tests/test_rebalance_page.py` — `test_class_deviation_summary_renders` e testes de cards
10. `tests/test_rebalance_schemas.py` — `test_category_plan_row_carries_exactly_seven_fields` (L197-214)
11. `tests/visual/test_snapshots.py` — `test_rebalance_plan_snapshot` (L75-97)
12. `tests/e2e/test_rebalance_page.py` — verificar se cards são inspecionados nos e2e

#### Testes e aceitação da investigação
- [ ] Notas em `openspec/.temp_assets/t30-notes.md` cobrem todos os 10 pontos do escopo.
- [ ] Campos do schema documentados com tipos e origem.
- [ ] Cálculo de `projected_pct` documentado com referência a linha do código.
- [ ] `delta` confirmado como compra/venda líquida (ou documentada exceção).
- [ ] Decisão ECharts vs SVG/CSS documentada com prós/contras e recomendação.
- [ ] Testes impactados listados com caminhos exatos.
- [ ] Gaps de dados documentados (se `net_action` precisa ser adicionado).
- [ ] Nenhum arquivo de produção alterado.

#### Dependências
- Nenhuma hard dependency. Pode rodar em paralelo com T27, T28, T29, F48.
- F49 depende desta fatia (T30 deve completar antes de propor F49).

#### Riscos
- **Baixo**: investigação pura, zero risco de regressão.
- **Médio**: se `delta` não representar compra/venda líquida, F49 precisará de campo adicional no schema (impacto em postprocessing, glue, engine, stub, testes).

#### Critério de pronto
- Notas técnicas entregues em `openspec/.temp_assets/t30-notes.md`.
- Nenhum arquivo de produção ou teste alterado.
- F49 pode ser proposta com base nas notas sem ambiguidade restante.

Progress: pending

### F49 - Bridge graphic com linguagem visual para cards de classe
Status: `Ready` — implementação futura (depende de T30)
Goal: substituir conteúdo numérico dos cards de classe por bridge graphic horizontal (atual → alvo) sem escala entre cards, apenas dentro do card. Mostrar resultado líquido (compra ou venda) por classe com cores, ícones e efeitos para evidenciar acima/abaixo do alvo e contribuição do rebalanceamento para enquadramento. Cenário 1: abaixo do alvo, compra, gap residual. Cenário 2: acima do alvo, venda, gap 0. Cores: verde (abaixo/compra), vermelho (acima/venda).
Candidate OpenSpec change id: `f49-bridge-graphic-linguagem-visual-cards-classe`
Spec link: `openspec/changes/f49-bridge-graphic-linguagem-visual-cards-classe/`
Files: `src/omaha/templates/_rebalance_plan.html`, `src/omaha/templates/rebalance.html`, `src/omaha/static/app.css`, `src/omaha/rebalance/schemas.py`, `tests/test_rebalance_page.py`, `tests/test_rebalance_schemas.py`, `tests/visual/test_snapshots.py`
Dependencies: T30 (investigação deve completar antes de propor)

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

Notes: requer decisão de chart lib (ECharts vs SVG/CSS puro — preferência do owner por ECharts, mas propor alternativa simples). Atualizar visual baseline após implementação. Verificar impacto em `test_category_plan_row_carries_exactly_seven_fields` se schema mudar. Campos atuais: `current_pct`, `target_pct`, `deviation_pct`, `delta` — podem ser suficientes para bridge; `net_action` (buy/sell/hold) pode precisar ser computado ou adicionado ao schema.
Progress: pending

### D03 - Gate de performance de testes nos agentes apply e review
Status: `Spec Proposed`
Goal: atualizar docs dos agentes `apply` e `review` (e skills associadas) para exigir que rotina completa de testes rode abaixo de 3 minutos, nunca entregar slice com rotina acima de 5 minutos, e exigir investigação/otimização real quando limite estourar — sem simplesmente desabilitar testes.
Candidate OpenSpec change id: `d03-gate-de-performance-de-testes-nos-agentes`
Spec link: `openspec/changes/d03-gate-de-performance-de-testes-nos-agentes/`
Files: `.opencode/agents/apply.md`, `.opencode/agents/review.md`, `.opencode/skills/openspec-apply-change/SKILL.md`, `.opencode/skills/code-review/SKILL.md`
Notes: escopo é documentação/configuração dos agentes do repo, não código de produto. Regras novas se somam ao test gate existente (ZERO TOLERANCE). Limite de 3 min = target ideal; 5 min = teto absoluto de entrega. Quando suite exceder limites, agente DEVE investigar causa raiz (fixtures pesadas, setup repetido, testes serializáveis, markers incorretos) e otimizar — nunca desabilitar testes ou reduzir cobertura. Referenciar slices T16-T18 (já archived) como exemplos de otimização válida.
Progress: pending

---

## Recommended Execution Order

**Active queue:** T28 (Spec Proposed), T29 (Ready), F48 (Applying)

**New slices (bridge graphic feature):**
1. T30 (Ready) — investigar cards, dados e chart lib antes de propor
2. F49 (Ready) — bridge graphic + linguagem visual (depende de T30)

**New slices (dev tooling):**
1. I07 (Ready) — profile-based model/provider/effort management for OpenCode agents (standalone, no dependencies)
2. D03 (Ready) — gate de performance de testes nos agentes apply e review (doc-only, no dependencies)

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
