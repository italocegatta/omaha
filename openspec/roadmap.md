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

`Applying` inclui apply e review. Apply retorna `READY_FOR_REVIEW`; somente
review `APPROVED` move a fatia para `Applied`. Owner valida antes de archive e
commit. Decisões de implementação, evidências e findings vivem na change, em
`design.md` e `tasks.md`, não neste roadmap.

## Parallelism and WIP limits

- Múltiplas fatias podem coexistir em `Spec Proposed`.
- Cap global: no máximo **2** fatias em `Applying` simultaneamente.
- Cap área crítica (auth, import, rebalance solver, backup): no máximo **1**
  fatia em `Applying`. Domínio crítico aqui = rebalance solver + cotação
  yfinance (ambos tocam o cálculo CVXPY em `src/omaha/rebalance/`).
- `next` permanece atômico: um comando move um gate de uma fatia.

## Spec verification gate (mandatory)

- Após `openspec-propose` → verificar spec antes de `openspec-apply-change`.
- Após `openspec-apply-change` → `review` verifica change antes de `Applied`.
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
Status: `Deprecated` — 2026-07-12 (split into F27-F29)

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
Goal: simplificar colunas compra/venda com emoji de acerto/bloqueio e toggle via clique.
Archive: `openspec/changes/archive/2026-07-15-f29-compra-e-venda-com-emoji-toggle/`

### R30 - Extrair padrão CSS compartilhado de tabelas
Status: `Archived` — 2026-07-15
Goal: extrair estilos comuns de tabelas em classes `.data-table-*` com variáveis CSS para troca de tema.
Archive: `openspec/changes/archive/2026-07-15-r30-extrair-padrao-css-compartilhado-de-tabelas/`

### R31 - Padronizar filter panel e header de tabelas
Status: `Archived` — 2026-07-15
Goal: unificar filter panel (teleport vs inline) e alinhar UX de filtros entre rebalance e portfolio.
Archive: `openspec/changes/archive/2026-07-15-r31-padronizar-filter-panel-e-header-de-tabelas/`

### F32 - Aplicar padrão de tabela rebalance em portfolio
Status: `Archived` — 2026-07-15
Goal: portar design visual da tabela rebalance para tabelas de ativos em portfolio.
Archive: `openspec/changes/archive/2026-07-15-f32-aplicar-padrao-de-tabela-rebalance-em-portfolio/`

### R33 - Refatorar formatters e comportamentos de tabela para reutilização
Status: `Archived` — 2026-07-15
Goal: centralizar formatação numérica, lógica de sinal e cell formatting em módulo compartilhado.
Archive: `openspec/changes/archive/2026-07-15-r33-refatorar-formatters-e-comportamentos-de-tabela-para-reutilizacao/`

### I05 - Otimizar hooks pre-commit e pre-push
Status: `Archived` — 2026-07-15
Goal: commit < 1 min, push < 3 min. Remover duplicações e trocar por variantes paralelas.
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
Goal: mover `test_audit_inventory.py` para `tests/audit_integration/` para não bloquear push.
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
Status: `Deprecated` — 2026-07-06 (owner deferiu)

### F04 - Página Proventos
Status: `Deprecated` — 2026-07-06 (owner: "F03 e F04 só no futuro")

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
Goal: tirar cobertura/XML de e2e, bdd e visual; manter coverage em unit + integration.
Archive: `openspec/changes/archive/2026-07-14-t13-cobertura-fora-dos-browsers/`

### T14 - Helpers compartilhados de setup e wipe
Status: `Archived` — 2026-07-14
Goal: extrair bootstrap, wipe de DB e helpers de browser/fixture para módulos de support compartilhados.
Archive: `openspec/changes/archive/2026-07-14-t14-helpers-compartilhados-de-setup-e-wipe/`

### T15 - Contratos e docs da suíte
Status: `Archived` — 2026-07-14
Goal: alinhar README, docs de BDD e performance baseline com behavior real da suíte.
Archive: `openspec/changes/archive/2026-07-14-t15-contratos-e-docs-da-suite/`

### T16 - Gate pré-merge sub-2m
Status: `Archived` — 2026-07-14
Goal: lane pré-merge abaixo de 2 min, separando fast gate de browser lanes.
Archive: `openspec/changes/archive/2026-07-14-t16-gate-pre-merge-sub-2m/`

### T17 - Paralelizar integration com DB por worker
Status: `Archived` — 2026-07-14
Goal: paralelismo seguro no lane integration via isolamento de banco por worker.
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
Goal: extrair lógica JS de filtros e painéis HTML para módulo compartilhado.
Archive: `openspec/changes/archive/2026-07-15-r34-extrair-logica-de-filtros-de-tabela-para-modulo-compartilhado/`

### F35 - Bug cadeado cinza na tabela ativos
Status: `Archived` — 2026-07-15
Goal: corrigir terceiro estado inválido (cadeado cinza) nos ícones compra/venda.
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
Goal: unificar margens e padding de todas as páginas full-width.
Archive: `openspec/changes/archive/2026-07-16-f38-padronizacao-de-margens-das-paginas/`

### F39 - Revisão de margens: meio termo entre antigo e novo
Status: `Archived` — 2026-07-16
Goal: meio termo entre margens F38 e versão anterior para patrimônio e rebalanceamento.
Archive: `openspec/changes/archive/2026-07-16-f39-revisao-de-margens-meio-termo/`

### F40 - Bug template tabelas ativos patrimonio
Status: `Archived` — 2026-07-17
Goal: corrigir 3 bugs (word wrap, colunas vazias, filtro clipado) + melhorias de filtro.
Archive: `openspec/changes/archive/2026-07-17-f40-bug-template-tabelas-ativos-patrimonio/`

### R41 - Limpar CSS duplicado e código morto
Status: `Archived` — 2026-07-17
Goal: remover seletores CSS duplicados, código morto, e consolidar blocos `:root` conflitantes em `app.css`.
Archive: `openspec/changes/archive/2026-07-17-r41-limpar-css-duplicado-e-codigo-morto/`

### F41 - Remover Atual e Alvo da linha de totais da classe
Status: `Archived` — 2026-07-17
Goal: remover Atual e Alvo (sempre 100%) da linha de totais, manter apenas Desvio.
Archive: `openspec/changes/archive/2026-07-17-f41-remover-atual-e-alvo-da-linha-de-totais-da-classe/`

### F42 - Desvio condicional na linha de totais
Status: `Archived` — 2026-07-17
Goal: exibir desvio na linha de totais apenas quando diferente de zero.
Archive: `openspec/changes/archive/2026-07-17-f42-desvio-condicional-na-linha-de-totais/`

### F43 - Corrigir tamanho da fonte na linha de totais
Status: `Archived` — 2026-07-17
Goal: alinhar fonte da linha de totais com o resto da tabela de patrimônio.
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

### T27 - Corrigir 5 integration tests desatualizados
Status: `Archived` — 2026-07-25
Goal: corrigir assertions defasadas após commits F46 e CSV alignment. Test-only.
Archive: `openspec/changes/archive/2026-07-25-fix-5-failing-integration-tests/`

### T28 - Corrigir 18 E2E/BDD tests (2 code bugs + 3 test drifts)
Status: `Archived` — 2026-07-25
Goal: corrigir 2 bugs de produção e 3 drifts de assertion. 13 BDD + 5 E2E.
Archive: `openspec/changes/archive/2026-07-25-fix-18-failing-e2e-bdd-tests/`

### T29 - Investigar e corrigir testes falhando (diagnóstico completo)
Status: `Archived` — 2026-07-26
Goal: garantir suite completa verde em até 5 minutos.
Archive: `openspec/changes/archive/2026-07-26-t29-investigar-e-corrigir-testes-falhando/`

### F48 - PoC sincronização MyProfit via Playwright
Status: `Archived` — 2026-07-27
Goal: encerrar PoC Playwright MyProfit após bloqueio pré-login, sem caminho automatizado suportado.
Archive: `openspec/changes/archive/2026-07-27-f48-poc-sincronizacao-myprofit-playwright/`

### I07 - Profile-based model/provider/effort management for OpenCode agents
Status: `Archived` — 2026-07-25
Goal: fix profile config delivery — generate `opencode.json` per profile via template + atomic write.
Archive: `openspec/changes/archive/2026-07-25-i07-profile-based-model-provider-effort-management/`

### T30 - Investigar cards de classe, dados disponíveis e alternativas de chart lib
Status: `Archived` — 2026-07-27
Goal: investigação técnica para propor F49 bridge graphic (SVG/CSS vs ECharts).
Archive: `openspec/changes/archive/2026-07-27-t30-investigar-cards-classes-dados-e-chart-lib/`

### F49 - Bridge graphic com linguagem visual para cards de classe
Status: `Archived` (superseded por F52) — 2026-07-28
Goal: waterfall/bridge monetária nos cards de classe. Abordagem SVG/CSS abandonada; substituída por ECharts em F52.
Archive: `openspec/changes/archive/2026-07-28-f49-bridge-graphic-linguagem-visual-cards-classe/`
Notes: Handoff preservado em `openspec/.temp_assets/f49-bridge-handoff.md`. Não retomar.

### F50 - Mock aprovado da ponte monetária dos cards de classe
Status: `Deprecated` — 2026-07-27 (absorvido por F49)

### F51 - Integrar ponte monetária aprovada nos cards de classe
Status: `Deprecated` — 2026-07-27 (absorvido por F49)

### D03 - Gate de performance de testes nos agentes apply e review
Status: `Archived` — 2026-07-26
Goal: separar validação focada do apply de suíte completa no review (teto 5 min).
Archive: `openspec/changes/archive/2026-07-26-d03-gate-de-performance-de-testes-nos-agentes/`

### F52 - Waterfall ECharts nos cards de classe
Status: `Archived` — 2026-07-28
Goal: waterfall ECharts (renderer SVG) nos cards de classe do `/rebalanceamento` — ponte `Atual → Compra/Venda → Desvio → Alvo`.
Archive: `openspec/changes/archive/2026-07-28-f52-waterfall-echarts-nos-cards-de-classe/`
Notes: Handoff normativo em `openspec/.temp_assets/f49-bridge-handoff.md`. Detalhes de gramática visual, mapeamentos numéricos e proibições no change folder arquivado.

### F53 - Ordem dos cards de classe no rebalanceamento
Status: `Archived` — 2026-07-29
Goal: ordem normativa dos cards de classe no `/rebalanceamento`.
Archive: `openspec/changes/archive/2026-07-29-f53-ordem-dos-cards-de-classe-no-rebalanceamento/`

### F54 - Ordem dos blocos de classe no patrimônio
Status: `Archived` — 2026-07-29
Goal: ordem normativa dos blocos de classe no `/patrimonio` via seed CSV.
Archive: `openspec/changes/archive/2026-07-29-f54-ordem-dos-blocos-de-classe-no-patrimonio/`

### F55 - Aumentar tamanho da fonte do menu principal
Status: `Archived` — 2026-07-29
Goal: aumentar em 50% o font-size dos nomes das páginas na tab nav superior.
Archive: `openspec/changes/archive/2026-07-29-f55-aumentar-tamanho-da-fonte-do-menu-principal/`

### D04 - Corrigir spec drift do POST /rebalanceamento
Status: `Archived` — 2026-07-29
Goal: corrigir spec `rebalance-page` para refletir PRG fix (200 → 303).
Archive: `openspec/changes/archive/2026-07-29-d04-corrigir-spec-drift-post-rebalanceamento/`

### F56 - Remover ativos bloqueados da tabela de rebalanceamento
Status: `Archived` — 2026-07-29
Goal: ativos com compra E venda bloqueadas não aparecem na tabela de ativos do `/rebalanceamento`.
Archive: `openspec/changes/archive/2026-07-29-f56-remover-ativos-bloqueados-tabela-rebalanceamento/`

---

### F57 - Configurar credenciais MyProfit por perfil
Status: `Archived` — 2026-08-20
Goal: parametrizar credenciais MyProfit por perfil real e bloquear sincronização em Família.
Archive: `openspec/changes/archive/2026-08-20-f57-configurar-credenciais-myprofit-por-perfil/`

### F61 - Documentar ambiente local e alinhar cookie seguro
Status: `Archived` — 2026-08-20
Goal: documentar ambiente local e alinhar cookie seguro à configuração carregada.
Archive: `openspec/changes/archive/2026-08-20-f61-documentar-ambiente-local-e-alinhar-cookie-seguro/`

### F62 - Remover destination do contrato MyProfit
Status: `Deprecated` — 2026-08-20 (owner folded removal into F58)
Goal: remover contrato F57-derived de destination por perfil; email/senha continuam isolados, e connector usa `StockDetail.aspx` sem selector de destino.
Candidate OpenSpec change id: `f62-remover-destination-do-contrato-myprofit`
Spec link: `openspec/changes/f62-remover-destination-do-contrato-myprofit/`
Files to inspect: `src/omaha/config.py`, `.env.example`, `README.md`, `tests/test_f57_myprofit_profile_config.py`, `openspec/specs/myprofit-profile-credentials/spec.md`
Notes: Follow-up owns removal only; do not mutate F57 archive. Remove `MYPROFIT_ITALO_DESTINATION`/`MYPROFIT_ANA_DESTINATION`, destination field/property, required/blank/placeholder validation, redaction assertions, README/.env template mentions, F57 tests, and F57-derived delta/stable-spec requirements. Update coupled `tests/test_auth.py` assertion as needed. Preserve profile isolation, email/password secrets, Família guard, and offline boundary. No Playwright, jobs, UI, secrets, or broad config cleanup. F58 remains non-actionable until F62 archives.
Progress log: deprecated — owner classified as small connector prerequisite; absorbed by F58 before Playwright implementation

### F58 - Integrar automação Playwright MyProfit
Status: `Archived` — 2026-08-22
Goal: integrar conector Playwright MyProfit com credenciais isoladas e download CSV seguro.
Archive: `openspec/changes/archive/2026-08-22-f58-integrar-automacao-playwright-myprofit/`

### F59 - Executar sincronização em background e entregar preview
Status: `Archived` — 2026-08-22
Goal: executar sincronização MyProfit em background e entregar preview seguro para revisão.
Archive: `openspec/changes/archive/2026-08-22-f59-executar-sincronizacao-background-e-entregar-preview/`
Notes: Archive/spec sync and supplemental fixture/spec repair complete; commits `67b0518` + `8a84680` pushed.

### F60 - Adicionar ação Atualizar posição no patrimônio
Status: `Archived` — 2026-08-22
Goal: exibir `Atualizar posição` ao lado de `Importar CSV`, iniciar job para perfil real e preservar revisão manual seguida do clique existente em `Importar`.
Archive: `openspec/changes/archive/2026-08-22-f60-adicionar-acao-atualizar-posicao-no-patrimonio/`
Notes: Archive/spec sync and local commit `24c32cb2` pushed with F59 supplemental delivery.

### R42 - Restaurar contrato get_logger
Status: `Archived` — 2026-08-22
Goal: restaurar compatibilidade de `get_logger` para permitir startup normal.
Archive: `openspec/changes/archive/2026-08-22-r42-restaurar-contrato-get-logger/`

### T31 - Validar sincronização MyProfit ponta a ponta
Status: `Applied`
Goal: cobrir contratos de configuração, connector Playwright fake, estados do job, erros sem modal, Família disabled e revisão/import manual sem tocar serviços externos ou DB prod.
Candidate OpenSpec change id: `t31-validar-sincronizacao-myprofit-ponta-a-ponta`
Spec link: `openspec/changes/t31-validar-sincronizacao-myprofit-ponta-a-ponta/`
Files to inspect: `tests/conftest.py`, `tests/test_imports_routes.py`, `tests/test_import_preview.py`, `tests/e2e/test_import_modal.py`, `tests/support/browser.py`
Notes: Usar fixtures/tmp DB e Playwright mock; registrar novo prefixo em `_INTEGRATION_PREFIXES` quando aplicável; validação final via `task test-unit`, `task test-integration`, `task test-e2e`/BDD conforme cobertura. Delivery runtime exige `refresh-for-test`, sem `db-reset` sem autorização explícita.
Progress log: pending — tests/spec alignment

### T32 - Revisar política de poda seletiva sob teto de testes
Status: `Archived` — 2026-08-20 (owner-authorized historical closure; superseded by T33)
Goal: registrar política de poda seletiva e preservar R3 como histórico.
Archive: `openspec/changes/archive/2026-08-20-t32-revisar-politica-de-poda-seletiva-sob-teto-de-testes/`

### T33 - Corrigir concorrência e ciclo de vida do harness BDD
Status: `Archived` — 2026-08-20 (commit/push pending)
Goal: tornar harness BDD determinístico sob execução concorrente.
Archive: `openspec/changes/archive/2026-08-20-t33-corrigir-concorrencia-e-ciclo-de-vida-do-harness-bdd/`
Notes: Archive/sync complete; stable specs 68/68. Commit/push blocked because `tests/scripts/test_t29_harness.py` mixes T33 and T32 hunks, preventing safe T33-only staging.

### D05 - Formalizar contrato operacional de limpeza e preflight
Status: `Archived` — 2026-08-24
Goal: formalizar contrato de ownership, limpeza limitada e preflight seguro para execuções de teste.
Archive: `openspec/changes/archive/2026-08-24-d05-formalizar-contrato-operacional-de-limpeza-e-preflight/`

### I08 - Corrigir runner taskipy para cleanup e telemetria por lane
Status: `Archived` — 2026-08-22
Goal: endurecer runner taskipy com cleanup ownership e telemetria completa por lane.
Archive: `openspec/changes/archive/2026-08-20-i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane/`
Notes: Review R5 APPROVED; canonical suite 240.60s green; stable specs 70/70; commit `3b1bce5` on `origin/main`.

### T34 - Diagnosticar e corrigir bloqueadores do runner/harness para F58
Status: `Archived` — 2026-08-22
Goal: corrigir boundaries confirmadas do runner/harness para F58.
Archive: `openspec/changes/archive/2026-08-22-t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58/`
Archive: `openspec/changes/archive/2026-08-22-t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58/`
Notes: Escopo único absorve T35 e I09; nenhuma alteração em F58, produto, DB, seed, host ou `/tmp` amplo. Plano faseado: (1) capturar evidência bounded de owner/run, PID/PGID/parent-child/exit/wait, readiness/port/log e temporários current-run; (2) reparar somente fault confirmado, usando `tests/support/server.py`/`tests/support/browser.py` para visual ou boundary equivalente do runner, sem reabrir T33; (3) adicionar/ajustar testes focados em `tests/scripts/test_t29_harness.py`; (4) executar uma única suíte canônica autorizada. Instrumentação não é deliverable separado: existe apenas para diagnosis/correction dentro desta fatia. Preservar seis lanes, ordem e entrypoints taskipy, fail-fast, coverage, todos testes/skips, isolamento DB, receipt/reconciliation e teto de 300s. Proibir retry, skip/xfail, remoção/serialização de lane, broad process discovery/kill, cleanup host-wide ou limpeza ampla de `/tmp`; correções fora de boundary runner/harness viram decisão de escopo, não nova fatia. T33 archived e I08 archived/preparado permanecem somente referências/constraints; não reabrir nem alterar. Owner deve confirmar este escopo antes de `propose`.
Notes: Escopo único absorve T35 e I09; nenhuma alteração em F58, produto, DB, seed, host ou `/tmp` amplo. Plano faseado: (1) capturar evidência bounded de owner/run, PID/PGID/parent-child/exit/wait, readiness/port/log e temporários current-run; (2) reparar somente fault confirmado, usando `tests/support/server.py`/`tests/support/browser.py` para visual ou boundary equivalente do runner, sem reabrir T33; (3) adicionar/ajustar testes focados em `tests/scripts/test_t29_harness.py`; (4) executar uma única suíte canônica autorizada. Instrumentação não é deliverable separado: existe apenas para diagnosis/correction dentro desta fatia. Preservar seis lanes, ordem e entrypoints taskipy, fail-fast, coverage, todos testes/skips, isolamento DB, receipt/reconciliation e teto de 300s. Proibir retry, skip/xfail, remoção/serialização de lane, broad process discovery/kill, cleanup host-wide ou limpeza ampla de `/tmp`; correções fora de boundary runner/harness viram decisão de escopo, não nova fatia. Acceptance: cada sintoma tem timeline/owner evidence; focused runner tests pass; uma única execução posterior de `uv run task test` sai 0 com seis lanes verdes, fail-fast preservado, coverage/skips/reconciliation e cleanup trusted, sem resíduo current-run, em <=300s. F58 só deixa `Blocked` após esse receipt. T33 archived e I08 archived/preparado permanecem somente referências/constraints; não reabrir nem alterar. Owner deve confirmar este escopo antes de `propose`.
Progress log: review R5 approved 2026-08-22 — exact temp ownership policy verified; 71 harness, 70 final focused, and 8 receipt tests green; lint/spec/diff checks pass. Canonical suite `NOT RUN — maintenance-suspended`; no open findings. Archived per recorded lifecycle; no active blocker.

### T35 - Provar readiness e ciclo de vida do servidor visual
Status: `Deprecated` — 2026-08-21 (absorvido por T34)
Goal: capturar child PID, exit code, readiness de `127.0.0.1:8768` e log de startup/teardown, corrigindo somente boundary visual confirmada sem alterar F58 connector.
Candidate OpenSpec change id: `t35-provar-readiness-do-servidor-visual`
Spec link: `openspec/changes/t35-provar-readiness-do-servidor-visual/`
Files to inspect: `tests/support/server.py`, `tests/support/browser.py`, `tests/visual/conftest.py`, `tests/scripts/test_t29_harness.py`
Notes: Evidence anchor: F58 R6 visual exit 1; eight nodes errored because `127.0.0.1:8768` never became ready after child exit, with empty server output (`reports/test-profile/20260820T214446-visual.log:39-135`). Record launch/readiness/poll/exit/port/log timeline and add controlled evidence before correction. T33 remains historical: do not reopen archive, alter BDD/8766 behavior, add browser retries, serialize lanes, weaken visual assertions, or edit F58.
Progress log: deprecated — visual `127.0.0.1:8768` diagnosis/correction now owned by consolidated T34; preserve T33 archive and do not create separate change.

### I09 - Reconciliar ownership de temporarios pytest por execução
Status: `Deprecated` — 2026-08-21 (absorvido por T34)
Goal: formalizar receipt e pós-execução para reconciliar temporários pytest criados na execução atual, distinguindo `absent`/`owned-cleaned` de resíduo estrangeiro sem limpeza ampla de `/tmp`.
Candidate OpenSpec change id: `i09-reconciliar-ownership-de-temporarios-pytest`
Spec link: `openspec/changes/i09-reconciliar-ownership-de-temporarios-pytest/`
Files to inspect: `scripts/run_full_suite.py`, `tests/conftest.py`, `tests/support/db.py`, `tests/scripts/test_t29_harness.py`
Notes: Evidence anchor: F58 R6 preflight had no `/tmp/pytest-of-juca`, runner receipt said cleanup complete, postflight found root created at 21:45 (`tasks.md:849-862`). Register current-run pytest temp roots with owner/run/timestamps, reconcile receipt with postflight, and report unknown/pre-existing roots without adopting, deleting, or traversing broad `/tmp`. Preserve prod-DB guard, dynamic temp DB isolation, all tests/coverage/skips, six lanes, fail-fast, taskipy entrypoints, and 300s ceiling. Do not reopen I08 or mutate F58/T33.
Progress log: deprecated — current-run pytest-temp receipt/reconciliation now owned by consolidated T34; no independent change or broad `/tmp` cleanup.

### I10 - Substituir Taskipy no boundary da suíte canônica
Status: `Archived` — 2026-08-22
Goal: substituir Taskipy apenas no boundary das seis lanes canônicas.
Archive: `openspec/changes/archive/2026-08-22-i10-substituir-taskipy-no-boundary-da-suite-canonica/`

### F63 - Hover e cabeçalho sticky na tabela de rebalanceamento
Status: `Spec Proposed`
Goal: portar exclusivamente para a única tabela de ativos de `/rebalanceamento` o destaque de linha no hover e o cabeçalho sticky já existentes em `/patrimonio`, preservando todo comportamento atual de ambas as páginas.
Candidate OpenSpec change id: `f63-hover-e-cabecalho-sticky-na-tabela-de-rebalanceamento`
Spec link: `openspec/changes/f63-hover-e-cabecalho-sticky-na-tabela-de-rebalanceamento/`
Files to inspect: `src/omaha/templates/_rebalance_plan.html`, `src/omaha/templates/_patrimonio_class_section.html`, `src/omaha/static/app.css`, `tests/test_rebalance_page.py`, `tests/visual/test_snapshots.py`
Notes: Fatia visual cirúrgica; nenhuma refatoração, melhoria adicional, alteração de colunas, filtros, ordenação, dados, ações ou comportamento de `/patrimonio`. Fidelity ledger: “destacar linha no hover” → feedback visual aplicado à linha inteira → células da linha mudam para estado hover coerente, sem alterar conteúdo/estado; fonte: seletor/classes da tabela e tokens CSS existentes; proibido tooltip, seleção persistente, mudança de ação/cor sem hover ou padrão genérico alternativo; evidência: comportamento equivalente `.asset-table` em `app.css`. “Cabeçalho sticky visível ao rolar” → `thead th` permanece preso no topo durante scroll → mesma tabela continua com cabeçalho legível e acima das linhas; fonte: regra sticky existente de `.asset-table`/`.table-sticky-header`; proibido sticky em outras tabelas, scroll interno novo, mudança de layout ou sobreposição que oculte filtros. Gramática visual: uma única tabela `rebalance-asset-table`, cabeçalho acima das linhas, hover temporário por linha; linhas continuam zebra/ações/filtros atuais; ausência de hover fora do cursor e ausência de dados não mudam semântica. Mapeamentos numéricos: N/A — nenhum valor, unidade, sinal ou escala é alterado; zero, limite e missing-data preservam renderização atual. Aceitação deve provar percepção visual no browser/renderização: hover distingue linha inteira; scroll mantém cabeçalho visível; `/patrimonio` e restante de `/rebalanceamento` permanecem sem alteração. Owner deve aprovar mock estático, protótipo ou browser rendering antes de Apply; aprovação registrada é dependência obrigatória de handoff e Apply fica bloqueado sem ela.
Progress log: proposal/design/tasks + delta specs created; change validation passed, stable specs 71/71, `git diff --check` passed. Apply blocked until F60 reaches `Applied` and owner visual validation/approval is recorded.

### F64 - Favicon de produção do Omaha
Status: `Archived` — 2026-08-22
Goal: entregar favicon de produção no browser com “O” geométrico teal sobre fundo escuro.
Archive: `openspec/changes/archive/2026-08-22-f64-favicon-de-producao-do-omaha/`

### F65 - Triagem de ativos por estado no preview de posição
Status: `Archived` — 2026-08-23
Goal: classificar preview de posições por estado com valores recebidos e diferenças acessíveis.
Archive: `openspec/changes/archive/2026-08-23-f65-triagem-de-ativos-por-estado-no-preview-de-posicao/`
Notes: Follow-up of F59/F60; preserve existing preview/commit, explicit confirmation, snapshot/audit, Família guard, and `auto_matched`/`unmatched` compatibility until replacement contract is proven. Classification candidate: no existing three-way classification found; current server returns only `auto_matched` (name-normalized match) and `unmatched`, preserving broker input order; current modal renders two sections and has no prior-value diff/hover. Fidelity ledger: “Novos/Alterados/Inalterados” → mutually exclusive triage groups → three visible sections with counts and rows; source = preview incoming row plus current `Asset`/`Position` state; forbidden = treating auto-match as unchanged, hiding changed rows, or generic unsorted bucket. “alfabetizar dentro de cada seção” → deterministic case/accent-insensitive asset-name order → each rendered group sorted by asset name, stable ticker tie-break; source = `row.name`; zero rows hide section, missing name sorts last. “incoming + previous on hover” → changed field shows incoming value by default and previous value through accessible hover/focus disclosure → source = field-level diff payload, including field label/unit/sign; forbidden = previous-only display, tooltip without keyboard focus, or fabricated previous value. “moderately wider” → text columns gain room without new page-wide layout → source = existing `.modal-panel--wide`/responsive rules; preserve mobile full-width. Visual grammar: section headers encode state, rows belong to exactly one state, changed fields carry persistent cue and reversible hover/focus reveal, unchanged rows carry no diff decoration, absence of a state has no empty placeholder. Numeric mappings: `qty`, `avg_price`, `current_price`, `invested`, `current_value` use broker incoming values and existing position values, with existing units/BRL formatting and signs; asset metadata fields use incoming preview versus existing asset; equal values → Unchanged/no previous reveal; zero remains zero; missing previous/incoming is explicit “não disponível”, never coerced to zero. Acceptance scenarios: fixture with existing rows having no changes, position-only changes, asset metadata changes, and unmatched rows yields correct exclusive groups; every group alphabetizes; changed cell hover and keyboard focus reveal exact old value while default shows new; sync-origin preview and upload-origin preview match; narrow viewport remains usable. Prohibitions: no auto-commit, no reclassification based only on match bucket, no loss of current assignment controls, no unrelated dashboard/rebalance redesign. Explore required before propose: owner must decide exact changed-field set (position values only, asset metadata, or both) and whether “previous” means pre-preview DB state for sync/import; owner must approve static mock/prototype/browser rendering before Apply, recorded as handoff gate. Dependency: F59 `Applied` supplies preview contract; F60 must reach `Applied` and owner-validated before this slice can Apply. F63 remains independent UI work but should not be applied concurrently to the same visual review surface without coordination.
Progress log: original proposal/design/tasks + delta specs passed and Review R1 approved. Owner-authorized surgical F65 follow-up on 2026-08-22 implemented copy, disclosure, and four-state `Ausentes` behavior. Remediation evidence recorded focused API/E2E/lint green, delivery refresh, and Review R3 `APPROVED`; owner authorized current Omaha delivery listener PID 1692 on 2026-08-23. F65 archive commit is at origin/main; pre-existing `data/test_e2e.db` preserved and not adopted.
Revision log: owner additive-preview triage requirement incorporated in F65 proposal/design/tasks/delta specs and static prototype; all eight production columns/controls remain visible per section, ticker remains hidden with `broker_ticker` assignment key preserved; revised prototype SHA-256 `6a2540a74067051eaacb1988af26cfba33d8ab075a6f6d76fe2373ea8f8002e6`; no implementation or owner approval claimed.

Remediation log: F65 remediation 1/2 fixed in-flow hover/focus prior disclosure, name-based `Ausentes` (ETH `ETH-OLD` versus batch `ETH-NEW`), scoped modal E2E selector, and owner-selected neutral-row/semantic-edge contrast. Focused API 16 passed, E2E 6 passed, lint and diff checks green; canonical suite `NOT RUN — maintenance-suspended`. Former port-8000 blocker resolved by owner authorizing current Omaha listener PID 1692; no foreign process was killed or adopted.

### I11 - Diagnosticar bloqueio de push e plano de regularização
Status: `Archived` — 2026-08-23
Goal: regularizar bloqueio confirmado do pre-push sem enfraquecer enforcement.
Archive: `openspec/changes/archive/2026-08-23-i11-diagnosticar-bloqueio-de-push-e-plano-de-regularizacao/`

### D06 - Inventariar superfícies do fluxo de atualização e importação
Status: `Archived` — 2026-08-24
Goal: remover superfícies D06 sem alterar revisão, erros ou confirmação.
Archive: `openspec/changes/archive/2026-08-24-d06-inventariar-superficies-do-fluxo-de-atualizacao-e-importacao/`
Notes: Review R2 approved; remediation 1/2 resolved PUSH-01.

### F67 - Ordenar grupos da revisão de posições
Status: `Archived` — 2026-08-24
Goal: ordenar grupos da revisão como `Novos`, `Ausentes`, `Alterados`, `Inalterados`.
Archive: `openspec/changes/archive/2026-08-24-f67-ordenar-grupos-da-revisao-de-posicoes/`
Notes: Review R1 APPROVED; owner autorizou archive em 2026-08-24.

### T36 - Medir duração e definir critério de timeout da sincronização
Status: `Archived` — 2026-08-24
Goal: medir duração offline e registrar critério de timeout sem justificar mudança em F68.
Archive: `openspec/changes/archive/2026-08-24-t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao/`
Notes: 15 tentativas fake são descritivas; 3 falhas foram rápidas e injetadas, não estouros de 60s. Polling atual permanece 60s; candidato 10s não justifica F68 nem implementação de timeout/monitoramento.

### F68 - Aumentar timeout efetivo da atualização com critério
Status: `Ready`
Goal: aplicar timeout de atualização definido por T36, evitando falso “A atualização demorou mais que o esperado” sem mascarar falhas reais.
Candidate OpenSpec change id: `f68-aumentar-timeout-efetivo-da-atualizacao-com-criterio`
Spec link: `openspec/changes/f68-aumentar-timeout-efetivo-da-atualizacao-com-criterio/`
Files to inspect: `src/omaha/templates/_patrimonio_add_asset_modal.html`, `src/omaha/routes/imports.py`, `tests/test_myprofit_sync_jobs.py`, `tests/e2e/test_import_modal.py`
Notes: Depende de T36 e da decisão de superfícies em D06; mudar somente limite comprovado, manter polling, status/job expiry, cancelamento, mensagens sanitizadas e revisão manual. Fidelidade: timeout → espera suficiente antes do erro → cálculo configurado por evidência → proibido retry infinito, ocultar falha, alterar mensagem truncada ou ampliar escopo para connector sem medida. Aceitar com cenários abaixo do limite, no limite, acima do limite e status failed/expired; owner aprova browser rendering antes de Apply se mensagem/superfície mudar.
Progress log: pending — waiting for T36 criterion

### T37 - Governança prática do DB E2E e processos Omaha
Status: `Ready` — deferred; fora da ordem ativa imediata
Goal: tornar preflight, ownership, cleanup/recreate e restart do único ambiente Omaha mais práticos sem adotar recursos estrangeiros nem proteger incorretamente dados efêmeros.
Candidate OpenSpec change id: `t37-governanca-pratica-do-db-e2e-e-processos-omaha`
Spec link: `openspec/changes/t37-governanca-pratica-do-db-e2e-e-processos-omaha/`
Files to inspect: `scripts/run_full_suite.py`, `tests/conftest.py`, `tests/support/db.py`, `tests/support/server.py`, `tests/scripts/test_t29_harness.py`
Notes: Contexto owner: `data/test_e2e.db` é efêmero, reproduzível por migrations/seed e pode ser apagado/sobrescrito automaticamente pelos testes sem autorização; `data/portfolio.db` é banco de produto e permanece protegido. Processos PID/PGID pertencentes ao único ambiente Omaha em execução podem ser reiniciados automaticamente quando necessário para novas funcionalidades, somente após ownership/identificação segura; proibido broad kill de processos não relacionados. Avaliar contrato de ownership/preflight, classificação test DB versus product DB, cleanup/recreate automático, lock/lease ou identificação de processo, restart gracioso, prevenção de adoção de recursos estrangeiros, receipts e recuperação de processos stale. Não alterar T36, F67 ou D06; não iniciar proposta, apply ou testes; não mutar `data/portfolio.db`, não apagar recursos estrangeiros, não ampliar para multiambiente, host-wide cleanup ou supervisor genérico. Owner quer retomar após T36 finalizar.
Progress log: pending — deferred until T36 archived

## Recommended Execution Order

**Active queue:**
  F63 → T31 → T36 → F68; T37 fica posteriormente a T36 archived, fora da ordem ativa imediata. D05, D06, F65, F60, F67, and I11 archived. I08 remains archived runner-hygiene history.

**Archived since prior queue:** F56, F55, F54, F53, F52, T27, T28, T29, I07, D03. Não são trabalho ativo.

Order note: F57/F61 archived; F62 deprecated because owner folded small destination removal into F58. T33/T32 remain archived; F50/F51 deprecated.

## Dependencies

- F57 bloqueia F61: follow-up corrige lacuna de documentação e consistência descoberta na validação de F57.
- F62 deprecated: its destination-removal scope is absorbed by F58 without reopening F57 archive.
- F61 bloqueava F58 e está archived; F58 inicia removendo configuration `destination` sem modulador antes da automação.
- F58 bloqueia F59: job depende do connector e de seu contrato de falhas/arquivo.
- F59 bloqueia F60: UI depende do endpoint/job status e da entrega do preview existente.
- F60 e T31 dependem de F59; T31 valida integração dos contratos concluídos e pode ser preparada em paralelo após F58.
- F60 tem gate adicional: aprovação owner de mock/protótipo/browser rendering antes de Apply; propose deve carregar gate e Apply fica bloqueado sem registro.
- T32 closed/superseded by T33; concurrent-BDD refusal is historical, and harness correction transferred to T33. Future pruning remains blocked without equivalent record.
- T33 não depende de T32; resolve somente concorrência, ciclo de vida de servidor/porta 8766 e determinismo da lane BDD antes das fatias seguintes.
- D06 precede F67 e F68: owner precisa decidir superfícies essenciais/desabilitáveis antes de alteração browser-visible; Apply bloqueado sem aprovação do inventário.
- T36 é independente de F67, mas precede F68: mede `pollDelay × maxPolls`, percentis e margem segura antes de aumentar timeout.
- F67 archived; T36 precedes F68 after D06.
- T37 depende de T36 archived e só deve ser retomada depois dele; registro futuro não altera lifecycle ou escopo de T36, F67 ou D06.
- D05 and I08 are test-runner hygiene follow-ups from F58/F61 review retries; they do not reopen, block, or alter F58, F61, T33, or F58 `R1-F02`.
- I08 normally depends on D05's approved ownership/stop vocabulary; owner
  explicitly authorizes I08 to consume D05's audited vocabulary while D05
  remains `Blocked` because documentation-only review full-suite noise is
  unrelated. I08 cannot claim D05 approved/archived and must preserve existing
  T33 lifecycle behavior and six-lane canonical ordering.
- T34 is the single bounded follow-up for all three F58 R6 runner/harness
  blockers: integration PID lineage, visual `8768` child/readiness/log lifecycle,
  and current-run pytest-temp ownership receipt reconciliation. T35 and I09 are
  deprecated as absorbed; no parallel changes or independent artifacts.
- T34 must first capture bounded ownership evidence, then correct only confirmed
  runner/harness faults, run focused harness tests, and finally obtain one trusted
  green canonical `uv run task test` with six lanes, fail-fast, coverage,
  tests/skips reconciliation, cleanup receipt, and <=300s. F58 remains `Blocked`
  until this acceptance is met; no F58 code changes belong in T34.
- I10 is prerequisite infrastructure exception for T34: its narrow direct-lane
  boundary must replace the unsupported Taskipy full-suite child invocation while
  preserving T34's six-lane/receipt/cleanup contract. During owner-authorized
  `maintenance-suspended`, T34 may continue bounded diagnosis/correction after
  I10 focused evidence; F58 remains blocked until reactivation yields T34's
  trusted canonical receipt. I10 must not alter Taskipy usage for serve, DB,
  lint, focused tasks, or unrelated commands.
- F63 depends on F60 reaching `Applied` and owner validation before Apply because
  both inspect the shared patrimônio visual surface and `app.css`; no semantic
  dependency on F59/T31. F63 also requires owner approval of static mock,
  prototype, or browser rendering before Apply.
- F65 depends on F59's preview contract and F60 reaching `Applied` plus owner
  validation before Apply; it owns the shared import-review surface and must
  coordinate with F63 to avoid concurrent `app.css`/visual-surface changes.
- T33 remains `Archived` historical and I08 remains `Blocked` with archive
  prepared. Neither lifecycle is reopened or altered; T34 consumes existing
  vocabulary/constraints only.

**Deferred/Deprecated** (owner decides):
- F03 (Rentabilidade) — closed.
- F04 (Proventos) — deprecated.


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
