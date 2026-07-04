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

### F01 - Consolidação cross-profile (visão household agregada)
Status: `Ready`
Goal: Vista household que soma os dois perfis (Italo + Ana Livia) sem
quebrar isolamento per-profile. Spec base já vive em `cross-profile-sharing`.
Candidate OpenSpec change id: `f01-household-cross-profile-consolidation`
Spec link: `openspec/changes/f01-household-cross-profile-consolidation/`
Files:
- `openspec/specs/cross-profile-sharing/spec.md`
- `src/omaha/routes/pages.py`
- `src/omaha/templates/_sidebar.html`
Notes: Pré-requisito da série "páginas do sistema" (Patrimônio/Rentabilidade/
Proventos). Cuidado: `cross-profile-sharing` é comportamento, não vazamento.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### F02 - Top-level layout: tab nav + Patrimônio + Rebalanceamento + stubs
Status: `Ready`
Goal: Substituir o layout atual (logo + side panel + conteúdo) por uma
**top nav com 4 tabs** (Patrimônio | Rebalanceamento | Rentabilidade |
Proventos) persistente em todas as páginas autenticadas, com profile
picker + Sair à direita. **Side panel removida.** Botões `Importar CSV`,
`+ Classe`, `+ Ativo` migram para o topo do corpo da página Patrimônio,
alinhados à direita. Rebalanceamento permanece como rota top-level
própria — **não** é embutido em Patrimônio (corrige PRD §5.3, que
prevê embed; decisão do owner via mock 2026-07-03 ganha). Stubs
`/rentabilidade` e `/proventos` com "Em construção" entram agora (F03
e F04 substituem depois).
Candidate OpenSpec change id: `f02-top-level-tab-nav-and-patrimonio`
Spec link: `openspec/changes/f02-top-level-tab-nav-and-patrimonio/`
Files:
- `src/omaha/templates/base.html` (4-tab nav com `--accent` na tab ativa, remover slot do side panel)
- `src/omaha/templates/dashboard.html` (rename → `patrimonio.html`; remover sidebar; redistribuir `Importar CSV` / `+ Classe` / `+ Ativo` no topo do body; renderizar `patrimonio-portfolio-header` card)
- `src/omaha/templates/rebalance.html` (form de aporte + `Rebalancear` movidos para o body; remover slot de sidebar; rebind do header novo; drop chip `BUILDER_WARNING` do painel Avisos — D5)
- `src/omaha/templates/_sidebar.html` (deletar — sidebar não existe mais)
- `src/omaha/templates/rentabilidade.html` (novo, stub "Em construção" — D6)
- `src/omaha/templates/proventos.html` (novo, stub "Em construção" — D6)
- `src/omaha/routes/pages.py` (rotas: `/patrimonio`, `/rebalanceamento`, `/rentabilidade`, `/proventos` — D1; remover `/dashboard` e `/rebalance` legados sem alias)
- `src/omaha/static/app.css` (classes `.tab-nav`, `.tab-nav__btn`, `.tab-nav__btn--active` usando `--accent`; remover regras de `.app-sidebar`)
- `openspec/specs/patrimonio-portfolio-header/spec.md` (novo — D3)
- `openspec/specs/dashboard-sidebar/spec.md` (deprecate + archive — D7)
- `openspec/specs/rebalance-page/spec.md` (rewrite: form agora vive só no body de `/rebalanceamento`, sem slot lateral — D9)
- `openspec/PRD.md` §5.3 (reescrito para refletir 4 tabs top-level, Rebalanceamento próprio — D8)
- `DESIGN.md` §Component inventory (anotar `Tab nav` com tokens `--accent` / `--ink` / `--bg` — D2)
Notes: **Divergência com PRD §5.3 resolvida pelo mock 2026-07-03**: a
versão atual do PRD diz "Rebalanceamento embutido em Patrimônio"; este
slice registra a mudança. Atualizar PRD §5.3 no mesmo PR do `propose`.
Side panel removal + tab nav + button redistribution são uma única
passagem em `base.html`/`dashboard.html` para evitar dois cortes
sequenciais nos mesmos arquivos. Stubs Rentabilidade/Proventos
garantem que a tab nav aparece completa e clicável em F02 — F03/F04
substituem o conteúdo pelo real. **Decisões D1-D9** (ver §Decisions)
resolvem todos os pontos do grill. Tab nav reusa `--accent` (sem
token novo). Spec `dashboard-sidebar` sai do active set via
deprecate+archive.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### F03 - Página Rentabilidade
Status: `Ready`
Goal: Página top-level `/rentabilidade` mostrando série temporal de retorno
por perfil/household. Substitui o stub "Em construção" criado por F02.
Nova spec precisa ser escrita dentro da fatia
(`openspec/specs/rentabilidade/spec.md`).
Candidate OpenSpec change id: `f03-rentabilidade-page`
Spec link: `openspec/changes/f03-rentabilidade-page/`
Files:
- `openspec/specs/rentabilidade/spec.md` (novo)
- `src/omaha/routes/pages.py`
- `src/omaha/templates/rentabilidade.html` (substituir stub)
Notes: Escopo e definição de dados ainda não fechados — alinhar no proposal.
Depende de F02 (slot `/rentabilidade` precisa existir). Side panel já foi
removida em F02 — F03 não toca em `_sidebar.html`.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### F04 - Página Proventos
Status: `Ready`
Goal: Página top-level `/proventos` com dividendos/JCP recebidos por ativo,
classe e perfil. Substitui o stub "Em construção" criado por F02.
Nova spec a ser definida na fatia
(`openspec/specs/proventos/spec.md`).
Candidate OpenSpec change id: `f04-proventos-page`
Spec link: `openspec/changes/f04-proventos-page/`
Files:
- `openspec/specs/proventos/spec.md` (novo)
- `src/omaha/routes/pages.py`
- `src/omaha/templates/proventos.html` (substituir stub)
Notes: Depende de F02 (slot `/proventos` precisa existir). Side panel já foi
removida em F02. Dados: provider de cotação atual não cobre eventos; a
fatia vai precisar definir a fonte (CSV import novo, sentinela na
posição, ou skip até segunda iteração).
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### F05 - Dark mode palette swap
Status: `Ready`
Goal: Substituir register off-white (§4.10) por palette dark invertida.
Background escuro, foreground claro, mesma personalidade "domestic" (PRD
§4.10). Implica reescrita de §4.10 + `DESIGN.md` +
`src/omaha/static/app.css`.
Candidate OpenSpec change id: `f05-dark-mode-palette-swap`
Spec link: `openspec/changes/f05-dark-mode-palette-swap/`
Files:
- `openspec/PRD.md` (regras §4.10)
- `DESIGN.md`
- `src/omaha/static/app.css`
Notes: Direcionamento ativo do PRD §1.5 e §5.3. Tokens invertidos
respeitam pares com contraste WCAG AA (spec `color-tokens`).
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### R01 - Limpar arquivos órfãos / dumps / snapshots antigos
Status: `Ready`
Goal: Limpar o repo de fixtures órfãs, dumps temporários e snapshots
antigos em `backups/` e `data/` que vazaram do `.gitignore`.
Sem mudança de comportamento observável.
Candidate OpenSpec change id: `r01-clean-orphaned-files-and-snapshots`
Spec link: `openspec/changes/r01-clean-orphaned-files-and-snapshots/`
Files:
- `backups/` (purge)
- `data/portfolio.db` (preservar — está no .gitignore correto)
- `tmp/` e artefatos ad-hoc
Notes: Pré-auditoria rápida: `task backup` lista tudo em `backups/` para
conferir antes do wipe. Zero risk — não toca código/runtime.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### R02 - Revisar sistema de seed (caminho CSV)
Status: `Ready`
Goal: Tornar o caminho CSV (`scripts/seed_from_csv.py` + triplet em
`data/seed/`) mais simples e direto para manutenção dos valores de seed
na plataforma. Sem mudar invariantes: CSV continua sendo source of truth.
Candidate OpenSpec change id: `r02-revise-csv-seed-system`
Spec link: `openspec/changes/r02-revise-csv-seed-system/`
Files:
- `scripts/seed_from_csv.py`
- `data/seed/README.md`
- `data/seed/{italo,ana}_*.csv`
Notes: PRD §4.3 é invariante — `seed.py` continua user+profile only; ativo/
posição continuam só via CSV. Foco é DX, não contrato.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### R03 - Extrair `quote_provider` adapter para pacote
Status: `Ready`
Goal: Hoje só existe uma implementação implícita (`yfinance`). Promover
`QuoteProvider` para pacote com interface explícita de forma que trocar
provider não toque consumers (`QuoteCache`, `MarketPriceLookup`).
Candidate OpenSpec change id: `r03-extract-quote-provider-adapter`
Spec link: `openspec/changes/r03-extract-quote-provider-adapter/`
Files:
- `src/omaha/quotes/provider.py` (refactor)
- `src/omaha/quotes/cache.py`
- `src/omaha/rebalance/` (consumers)
Notes: Sem mudança de comportamento. Aplica-se melhor após ciclo F02-F04
(parada estrutural).
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### R04 - Partialize `templates/patrimonio.html`
Status: `Ready`
Goal: Quebrar `templates/patrimonio.html` (após rename de `dashboard.html`
em F02, ~1600 linhas) em partials. Já existem `_sidebar.html` (a ser
limpo em F02), `_rebalance_*`; estender o padrão.
Sem mudança de comportamento visível.
Candidate OpenSpec change id: `r04-partialize-patrimonio-template`
Spec link: `openspec/changes/r04-partialize-patrimonio-template/`
Files:
- `src/omaha/templates/patrimonio.html`
- `src/omaha/templates/_*.html`
Notes: Depende de F02 (template renomeado + side panel removido) para
não parcializar sobre mudança em voo. Id e título foram atualizados em
2026-07-03 após grill do mock de navegação — `dashboard.html` agora é
`patrimonio.html`.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### T01 - BDD + e2e suite a 100% green
Status: `Ready`
Goal: Spec `e2e-rework` está estável mas ainda com selectors pendentes.
Levar BDD+e2e a 100% green. `bdd-workflow-reuse-helpers` já documenta o
caminho.
Candidate OpenSpec change id: `t01-bdd-e2e-suite-100-green`
Spec link: `openspec/changes/t01-bdd-e2e-suite-100-green/`
Files:
- `tests/bdd/step_defs/_workflows.py`
- `tests/e2e/`
- `openspec/specs/e2e-rework/spec.md`
Notes: Subtarefa pesada — pode ser subdividida em N mudanças durante
`apply` se necessário. BDD roda serial (PRD §4.7).
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### T02 - Coverage report no CI
Status: `Ready`
Goal: `task coverage` existe; falta cabo no pipeline (GitHub Actions).
Wire `--cov-report=xml` + upload para o driver de coverage usado pelo
repo.
Candidate OpenSpec change id: `t02-coverage-report-in-ci`
Spec link: `openspec/changes/t02-coverage-report-in-ci/`
Files:
- `.github/workflows/*.yml`
- `pyproject.toml` (tool.coverage.*)
Notes: Verificar se já existe workflow de CI antes de propor; se não
existir, escopo da fatia vira "introduzir CI" e isso pode virar F/I.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### T03 - Mutation testing do rebalance engine
Status: `Ready`
Goal: Aplicar mutation testing sobre `src/omaha/rebalance/engine.py` e
`data_bridges.py`. Solver é crítico — invariant "soma 100" e limites de
classe precisam ser exercidos além de cobertura de linha.
Candidate OpenSpec change id: `t03-mutation-testing-rebalance-engine`
Spec link: `openspec/changes/t03-mutation-testing-rebalance-engine/`
Files:
- `src/omaha/rebalance/engine.py`
- `src/omaha/rebalance/data_bridges.py`
- `tests/rebalance/`
Notes: Domínio crítico — cap de 1 fatia Applying. Rodar após R03 (adapter)
se a fatia crescer.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### I01 - Agendamento automático de backup
Status: `Ready`
Goal: `task backup` existe (`scripts/backup.py` → SQLite snapshot em
`./backups/`); nenhum timer está cabeado. Adicionar timer systemd ou
cron para execução periódica no host.
Candidate OpenSpec change id: `i01-automatic-backup-scheduling`
Spec link: `openspec/changes/i01-automatic-backup-scheduling/`
Files:
- `prod.yml` (serviço de backup)
- `scripts/backup.py`
- `README.md` (seção de operação)
Notes: Em Docker compose, equivalente a um serviço `backup` com schedule.
PRD §3.4 lista modos; este slice adiciona o modo "scheduled".
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### I02 - Automação de renovação do cert TLS
Status: `Ready`
Goal: `nginx/` já está configurado com certbot; renovação ainda é manual.
Cabar `--deploy-hook` para que `certbot renew` rode unattended e recarregue
nginx.
Candidate OpenSpec change id: `i02-tls-cert-renewal-automation`
Spec link: `openspec/changes/i02-tls-cert-renewal-automation/`
Files:
- `prod.yml`
- `nginx/`
- `scripts/` (deploy hook se faltar)
Notes: Depende de I01 apenas se ambos usarem timer compartilhado. Sem
deps obrigatórias entre si.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### D01 - Refresh do README
Status: `Ready`
Goal: Atualizar README para refletir a surface atual. Em particular a
seção "Network access" (PRD §4.2) e o bloco de features (já fechado após
F01-F05). Garantir `bash scripts/print_lan_url.sh` referenciado.
Candidate OpenSpec change id: `d01-refresh-readme`
Spec link: `openspec/changes/d01-refresh-readme/`
Files:
- `README.md`
Notes: Doc-only — sem teste runtime, sem `src/omaha/`. Rodar por último
para refletir o estado pós-F-slice.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

## Dependencies

### F01
Depends on: none
Blocks: F02 (visa household precisa existir antes de virar nav item default)
Can run in parallel: yes

### F02
Depends on: none (F01 é paralela, não estritamente necessária para a tab nav)
Blocks: F03, F04 (precisam do slot na nav), R04 (partialização do template renomeado)
Can run in parallel: yes (com F01; F03/F04/R04 bloqueados)

### F03
Depends on: F02 (slot `/rentabilidade` precisa existir)
Blocks: none
Can run in parallel: yes (com F04)

### F04
Depends on: F02 (slot `/proventos` precisa existir)
Blocks: none
Can run in parallel: yes (com F03)

### F05
Depends on: none
Blocks: none
Can run in parallel: yes

### R01
Depends on: none
Blocks: none
Can run in parallel: yes (com qualquer outra)

### R02
Depends on: none
Blocks: none
Can run in parallel: yes

### R03
Depends on: none
Blocks: T03 (se durante apply se decidir refatorar junto)
Can run in parallel: yes

### R04
Depends on: F02 (template renomeado e side panel removido)
Blocks: none
Can run in parallel: yes (com qualquer outra pós-F02)

### T01
Depends on: none
Blocks: none
Can run in parallel: yes (mas e2e/BDD é flaky quando paralelizado — atenção)

### T02
Depends on: none (a menos que T02 introduza CI; nesse caso passa a ser bloco para tudo)
Blocks: none
Can run in parallel: yes

### T03
Depends on: none
Blocks: none
Can run in parallel: yes (mas solver é crítico — cap 1)

### I01
Depends on: none
Blocks: none
Can run in parallel: yes

### I02
Depends on: none
Blocks: none
Can run in parallel: yes (com I01)

### D01
Depends on: F01, F02, F03, F04, F05 (reflete surface pós-slice)
Blocks: none
Can run in parallel: yes

## Recommended Execution Order

Prioridade presume que o owner quer atacar mudanças estruturais primeiro
(rebalance + páginas), qualidade em paralelo, e docs/infra no fim.

1. R01 - cleanup (zero risk, prep do repo)
2. F02 - tab nav + side panel removal + stubs (foundation para F03-F04)
3. F01 - household cross-profile (paralela a F02 — não bloqueia)
4. F03 - rentabilidade page (substitui stub criado em F02)
5. F04 - proventos page (substitui stub criado em F02)
6. F05 - dark mode palette swap
7. R02 - revise CSV seed system
8. R03 - extract quote_provider adapter
9. R04 - partialize patrimonio template (depende de F02)
10. T01 - BDD + e2e 100% green
11. T02 - coverage in CI
12. T03 - mutation testing rebalance
13. I01 - backup scheduling
14. I02 - TLS cert renewal automation
15. D01 - README refresh (último — reflete tudo acima)

Notas de reordenamento:
- **F02 vem antes de F01** porque a tab nav + side panel removal é
  layout-foundation que F03/F04 dependem. F01 (household toggle) é
  independente da tab nav — pode correr em paralelo (entre F02 e F05).
- T03 fica depois de R03 porque a fatia de mutation testing pode
  aproveitar adapter mais limpo para mockar providers. Se durante
  apply de T03 essa vantagem não se confirmar, mover T03 para antes
  de R03 sem outra consequência.
- D01 no fim: doc precisa refletir surface pós-F-slice (regras §4.10
  e features block mudam com F05 e F01-F04; PRD §5.3 precisa refletir
  Rebalanceamento top-level após F02).

## Open questions (grill 2026-07-03)

Itens levantados pelo owner na revisão do mock de navegação. Cada um
foi resolvido em discussão 2026-07-03 e movido para **Decisions**.

## Decisions

Resolução das questões abertas durante o grill 2026-07-03. Cada item
indica onde a decisão vai ser aplicada (fatia + artefato).

- **D1 (Q1) — Slugs PT-BR.** Rotas finais: `/patrimonio`,
  `/rebalanceamento`, `/rentabilidade`, `/proventos`. Rompe com
  `/rebalance` legado (sem alias; rota legada deixa de responder).
  Aplicar em F02 — `src/omaha/routes/pages.py` + redirects 404.
  Decisão 2026-07-03.
- **D2 (Q2) — Cor da tab ativa.** Reusar `--accent` (verde-feto,
  `oklch(0.42 0.09 150)`). Token existente — sem adição em
  `color-tokens`. Inativo: `--bg` com `--ink` no texto (sem fill).
  Aplicar em F02 — `src/omaha/static/app.css` (classes `.tab-nav`,
  `.tab-nav__btn`, `.tab-nav__btn--active`) + `DESIGN.md` (anotar
  componente na tabela de Component Inventory). Decisão 2026-07-03.
- **D3 (Q3) — Spec nova `patrimonio-portfolio-header`.** Card
  perfil-nível (Investido / Valor Atual / Ganho) no topo de Patrimônio.
  `class-section-totals` continua classe-nível (não estende). DESIGN.md
  §Component inventory já descreve o componente como "Portfolio header
  — Invested / current / gain. The hero." — só falta a spec formal.
  Aplicar em F02 — criar `openspec/specs/patrimonio-portfolio-header/spec.md`.
  Decisão 2026-07-03.
- **D4 (Q4) — ✕ de delete por classe já existe.** Spec
  `dashboard-inline-editing` já cobre (req "× delete button is always
  visible (discreet by default, red on hover)" + "Remoção de classe com
  confirmação"). Nenhuma nova spec. F02 só precisa garantir que o ✕
  continua renderizando no header da classe após o rename. Decisão
  2026-07-03.
- **D5 (Q5) — Drop chip `BUILD_WARNING`.** Remover o chip do label;
  manter só a mensagem PT-BR como bullet no painel Avisos. Aplica-se a
  qualquer `<li>` com código de aviso do solver. Aplicar em F02
  (template `rebalance.html`, painel Avisos). Decisão 2026-07-03.
- **D6 (Q6) — F02 cria os stubs.** `/rentabilidade` e `/proventos`
  renderizam página "Em construção" como stub. F03 e F04 substituem
  pelo conteúdo real. Decisão 2026-07-03.
- **D7 (Q7) — Deprecate `dashboard-sidebar` spec.** Side panel some de
  vez — sem drawer mobile, sem formulário de rebalance no slot. Spec
  vira histórico; archive via `openspec-archive-change` no fluxo de F02.
  Off-canvas mobile drawer também some — não há mais nada off-canvas.
  Aplicar em F02 — delta spec `dashboard-sidebar` indica remoção + move
  ao archive. Decisão 2026-07-03.
- **D8 (Q8) — PRD §5.3 atualizado.** Texto atual diz "Rebalanceamento
  embutido em Patrimônio". Reescrever §5.3 para refletir direção do
  mock (4 tabs top-level, Rebalanceamento próprio). Aplicar em F02 —
  mesmo PR do `propose`. Decisão 2026-07-03.
- **D9 (Q9) — `rebalance-page` spec rewrite.** Req "Sidebar carries
  the rebalance form on every authenticated page" deixa de existir (não
  há mais sidebar). Form de aporte + botão Rebalancear vive só no body
  de `/rebalanceamento`. A spec passa a descrever: rota dedicada,
  form na página, sem slot lateral, sem drawer mobile. Aplicar em F02
  — delta spec `rebalance-page`. Decisão 2026-07-03.

---

## Compacted history

Últimas 8 fatias arquivadas (compile manualmente do diretório
`openspec/changes/archive/`):

- `2026-06-29-rebalance-engine` → solver CVXPY estável → `src/omaha/rebalance/engine.py`, `src/omaha/rebalance/data_bridges.py` → `task test-integration`
- `2026-06-29-dashboard-inline-edit-friction` → melhorias de UX na edição inline → `src/omaha/static/app.css`, `templates/dashboard.html` → `task test-e2e`
- `2026-06-29-add-db-snapshot` → adiciona `task db-snapshot` (DB → CSV) → `scripts/snapshot_to_csv.py`, `pyproject.toml` → `task db-snapshot`
- `2026-06-27-rebalance-route` → `POST /api/rebalance` → `src/omaha/routes/rebalance.py`, `tests/integration/` → `task test-integration`
- `2026-06-27-rebalance-page` → `GET /rebalance` render da página → `templates/rebalance.html`, `_rebalance_partials` → `task test-e2e`
- `2026-06-26-rebalance-infra` → wiring inicial CVXPY + lifecycle → `src/omaha/rebalance/`, `pyproject.toml` (cvxpy) → `task test-integration`
- `2026-06-26-fix-br-number-parser` → `_parse_brazilian_number` cobre `.` como milhar → `src/omaha/imports/`, `tests/` → `task test-unit`
- `2026-06-26-direct-landing-with-header-profile-switcher` → perfil default após login + header switcher → `src/omaha/routes/auth.py`, `templates/base.html` → `task test-e2e`

Onda recente: dominada por rebalance infra (5 fatias seguidas). Antes:
auth, dashboard, CSV seed driven, theme.

## Post-implementation reality check

Para cada fatia `Applied`, anexar antes de mover para `Archived`:

- What changed from original plan: …
- Unexpected issues: …
- Follow-up needed: …

(Campos vazios até a primeira fatia completar o ciclo.)

## Agent checklist (este registro)

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
