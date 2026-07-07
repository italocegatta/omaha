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
Status: `Archived` (superceded by F06 2026-07-04)
Goal: Vista household que soma os dois perfis (Italo + Ana Livia) sem
quebrar isolamento per-profile. Spec base já vive em `cross-profile-sharing`.
Candidate OpenSpec change id: `f01-household-cross-profile-consolidation`
Spec link: `openspec/changes/archive/2026-07-04-f01-household-cross-profile-consolidation/`
Files:
- `openspec/specs/cross-profile-sharing/spec.md` (delta: ADDED 3 requirements sobre `?view=household`, toggle UI, isolamento intra-User)
- `src/omaha/routes/pages.py` (helper `household_aggregates`, branch `view=household` em `_render_patrimonio`)
- `src/omaha/auth.py` (novo `require_profile_writable` raising 409 `household_read_only`)
- `src/omaha/routes/classes.py`, `assets.py`, `imports.py`, `rebalance.py` (aplicar `Depends(require_profile_writable)`)
- `src/omaha/templates/base.html` (toggle `Casa` ao lado do profile picker; visível só quando `len(profiles) >= 2`)
- `src/omaha/templates/patrimonio.html` (branch read-only)
- `src/omaha/static/app.css` (`.household-toggle`, `.app-header__household-chip`, `.is-read-only`)
- `openspec/PRD.md §5.3` (marcar F como entregue)
Notes: Pré-requisito da série "páginas do sistema" (Patrimônio/Rentabilidade/
Proventos). Cuidado: `cross-profile-sharing` é comportamento, não vazamento.
Modo household é read-only — decisaõ D3 do design.md; mutações retornam 409.
Toggle usa querystring (`?view=household`), não rota dedicada (decisão D1).
**Superseded by F06** 2026-07-04: agregador F01 era intra-User
(`Profile.user_id == viewer.id`); mas seed cria Italo e Ana como Users
separados, então "ambos os perfis" nunca agregava de verdade. Toggle
visível só quando viewer tinha ≥2 perfis (Italo RF2 era fixture), e
sempre somava o viewer's profiles — não cross-User. F06 substitui a
semântica do `?view=household` por agregado cross-User (família inteira)
com full-join por nome de classe/ativo. F01 fica no histórico de
auditoria; o spec `cross-profile-sharing` recebe o delta na F06.
Progress:
- Proposed: done (2026-07-04; 3 ADDED requirements + delta parsed)
- Applying: done (2026-07-04)
- Applied: done (2026-07-04)
- Archived: done (2026-07-04; archive `2026-07-04-f01-household-cross-profile-consolidation/`)

### F02 - Top-level layout: tab nav + Patrimônio + Rebalanceamento + stubs
Status: `Archived`
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
- Proposed: done
- Applying: done
- Applied: done
- Archived: done

### F03 - Página Rentabilidade
Status: `Closed` 2026-07-06 (proposal archived without apply; D-F03-defer
tornou-se permanente por pedido do owner)
Goal: Página top-level `/rentabilidade` mostrando série temporal de retorno
por perfil/household. Substitui o stub "Em construção" criado por F02.
Nova spec precisa ser escrita dentro da fatia
(`openspec/specs/rentabilidade/spec.md`).
Candidate OpenSpec change id: `f03-rentabilidade-page`
Spec link: `openspec/changes/archive/2026-07-06-f03-rentabilidade-page/`
Files:
- `openspec/specs/rentabilidade/spec.md` (novo — não sincronizado; capability nunca implementada)
- `src/omaha/calculation/rentabilidade.py` (novo — helpers puros `compute_window_summary`, `compute_class_breakdown`, `compute_monthly_series`, `quote_stale_assets`)
- `src/omaha/routes/pages.py` (substituir handler `/rentabilidade`)
- `src/omaha/routes/rentabilidade.py` (novo — endpoints `/api/rentabilidade/{summary,series}`)
- `src/omaha/templates/rentabilidade.html` (substituir stub; hero + 3 tabelas + refresh btn)
- `src/omaha/static/app.css` (regras `.rentabilidade-*`)
- `tests/test_rentabilidade_summary.py` (novo, unit)
- `tests/test_rentabilidade_series.py` (novo, unit)
- `tests/test_rentabilidade_quote_carry.py` (novo, unit)
- `tests/integration/test_rentabilidade_route.py` (novo)
- `tests/bdd/features/rentabilidade.feature` (novo)
- `tests/bdd/test_scenarios.py` (bindings)
- `tests/e2e/selectors.py` (data-testids)
- `tests/conftest.py` (adicionar prefixos `test_rentabilidade_*` em `_INTEGRATION_PREFIXES`)
Notes: Escopo alinhado no proposal: 6 janelas fixas (1M/3M/6M/12M/YTD/All) +
série mensal de 12 pontos + tabela por classe (All-time). Sem chart lib
(PRD §1.5 "página pode ser pequena"). Carry-forward de quote para cobrir
buracos sem inventar dados sintéticos; ativos com quote_kind='manual' usam
`Position.current_price`. Família mode reusa agregação F06 (full-join por
nome) + omite `target_pct` (D-F06.3). Sem migration Alembic — `Position` +
`Quote` já cobrem o necessário. Não toca solver CVXPY nem provider yfinance
em runtime (lê cache só). Critical-area cap 1 não aplicável.

**DEFERIDO 2026-07-05** — owner pediu para não mexer em
Rentabilidade/Proventos por enquanto (D-F03-defer). Move F03 + F04
para o final do execution order. Mudar títulos das abas ou mexer em
stub corrente também fica congelado. Quando owner retomar o tema,
reativar via `start f03` ou `start f04` — proposal draft fica
preservado em `openspec/changes/f03-rentabilidade-page/` (valid:
true em 2026-07-05).

**CLOSED 2026-07-06** — owner pediu para fechar a spec. Proposal
draft movido para
`openspec/changes/archive/2026-07-06-f03-rentabilidade-page/`
(via `openspec-archive-change`). Delta spec **não** sincronizada
em `openspec/specs/rentabilidade/spec.md` — capability nunca foi
implementada, então o spec não pode viver nos main specs
(spec-driven: spec descreve comportamento existente). Stub
`/rentabilidade` em `templates/rentabilidade.html` permanece
intocado (regra D-F03-defer). F04 (Proventos) segue no mesmo
estado de deferral — owner decide separadamente.

**Reactivation path (se o owner retomar o tema):** (a) mover a
pasta de `archive/2026-07-06-f03-rentabilidade-page/` de volta
para `openspec/changes/`; (b) re-validar a proposal (escopo pode
ter envelhecido em ~2026-07-06 baseline: F06/F07 archived +
R02/R03/R04 archived mudaram invariantes que o proposal
original assumia); (c) revisar e atualizar tasks.md
(`as_of=2024-03-15` no cenário principal pode precisar de data
fresca); (d) rodar `openspec validate
f03-rentabilidade-page --json` para confirmar `valid: true`
antes de delegar `openspec-apply-change`. **NÃO** re-propor via
`openspec-propose` — o proposal draft é reutilizável.
Progress:
- Proposed: done (2026-07-05; 4 artifacts completos;
  `openspec validate` retorna `valid: true`).
- Applying: skipped (nunca rolou — D-F03-defer)
- Applied: skipped (nunca rolou)
- Archived: done 2026-07-06 (folder movido para
  `archive/2026-07-06-f03-rentabilidade-page/`; delta spec
  descartada — capability não implementada)

### F04 - Página Proventos
Status: `Deprecated` 2026-07-06 (owner: "F03 e F04 só iremos fazer no
futuro, ainda incerto. então não quero eles no roadmap")
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
removido em F02. Dados: provider de cotação atual não cobre eventos; a
fatia vai precisar definir a fonte (CSV import novo, sentinela na
posição, ou skip até segunda iteração).

**DEFERIDO 2026-07-05** — mesmo motivo de F03 (D-F03-defer).
Proventos depende de escolha de fonte de dados ainda em aberto
(provider de cotação yfinance não cobre eventos); sem decisão do
owner sobre a fonte, F04 não pode ser proposta sem ambiguidade
significativa. Reativar via `start f04` quando o tema voltar.

**DEPRECATED 2026-07-06** — owner pediu para remover do roadmap
ativo. Razão: incerto se/ quando o tema Rentabilidade/Proventos
volta a ser prioridade; enquanto incerto, F03+F04 ficam fora do
queue. **Reactivation path**: `restore f04` quando owner retomar o
tema. Slice preservada para auditoria; folder
`openspec/changes/f04-proventos-page/` permanece vazio (proposal
draft nunca foi criado — `start f04` abre `openspec-propose`
quando reativar). Stub `/proventos` em `templates/proventos.html`
permanece intocado por enquanto.
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

### F05 - Dark mode palette swap
Status: `Archived`
Goal: Substituir register off-white (§4.10) por palette dark invertida.
Background escuro, foreground claro, mesma personalidade "domestic" (PRD
§4.10). Implica reescrita de §4.10 + `DESIGN.md` +
`src/omaha/static/app.css`.
Candidate OpenSpec change id: `f05-dark-mode-palette-swap`
Spec link: `openspec/changes/archive/2026-07-05-f05-dark-mode-palette-swap/`
Files:
- `openspec/PRD.md` (regras §4.10)
- `DESIGN.md`
- `src/omaha/static/app.css`
- `tests/test_dark_mode_tokens.py` (novo — substitui `tests/test_tokens.py`)
Notes: Direcionamento ativo do PRD §1.5 e §5.3. Tokens invertidos
respeitam pares com contraste WCAG AA (spec `color-tokens`).
Progress:
- Proposed: done (2026-07-05; folder `openspec/changes/f05-dark-mode-palette-swap/`; 4 artifacts: `proposal.md` (inversão por lightness, hue 60 preservado) + `design.md` (10 decisions D-F05.1..D-F05.10) + `tasks.md` (6 grupos, 40 checkboxes) + `specs/color-tokens/spec.md` (delta: 3 MODIFIED requirements, nenhum ADDED/REMOVED, hue-shift swatch 2 documentado). `openspec validate f05-dark-mode-palette-swap` retorna `valid: true`).
- Applying: done (2026-07-05; token swap em `app.css :root` — 14 tokens + `color-scheme: dark` + remocao do hex fallback `, #2563eb` nos 2 `outline: 2px solid var(--color-focus)` rules; `tests/test_dark_mode_tokens.py` reescrito com 17 assertions cobrindo body warmth, lightness lifts em swatches e status fills, swatch-2 hue-shift, error pair, surface lift/sink, color-focus, legacy aliases, `color-scheme: dark` e ausencia de `prefers-color-scheme`; `tests/test_tokens.py` deletado; `tests/conftest.py::_UNIT_FILES` recebe `test_dark_mode_tokens.py`; DESIGN.md §Color strategy + tabela de tokens + §Component inventory intro + §Migration path reescritas; PRD §4.10 + §5.3 atualizadas).
- Applied: done (2026-07-05; `task test-unit` 233 pass/2 skip; `task test-integration` 369 pass/2 skip; `task test-bdd` 47 pass (4 pre-existentes T05 confirmados via `git stash`); `task lint` verde; `openspec validate f05-... --json` `valid: true`; `refresh-for-test` smoke OK: server 0.0.0.0:8000, `/healthz ok`, `db-reset` 6/48/47 Italo + 6/52/52 Ana, dashboard renderiza com Família option no chip + `body { background: var(--bg) }` aplica surface dark warm-neutral).
- Archived: done (2026-07-05; archive `2026-07-05-f05-dark-mode-palette-swap/`; `color-tokens` spec MODIFIED ×3 consolidada em `openspec/specs/color-tokens/spec.md` — requisitos re-derivados com surface dark warm-neutral; sem ADDED/REMOVED; PRD §4.10 (off-white → dark warm-neutral) é a fonte visível).

### F06 - Agregado família inteira (cross-User, full-join por nome)
Status: `Archived`
Goal: Substituir a semântica household de F01 (que era intra-User e
inútil porque Italo/Ana são Users separados). Vista nova agrega TODOS os
`Profile` rows do banco (`profile_id NOT IN (root "system")`) — não
filtra por `Profile.user_id` — independente de quem logou. Classes e
ativos com **mesmo nome** entre perfis distintos colapsam em uma única
linha (full-join por `name`, soma de investido/valor). `target_pct` é
**omitido** no agregado (sem alocação-alvo cross-User). Toggle `Casa`
do header vira `Família`. Modo read-only mantido; mutações retornam 409.
Candidate OpenSpec change id: `f06-family-household-full-join-aggregate`
Spec link: `openspec/changes/archive/2026-07-05-f06-family-household-full-join-aggregate/`
Files:
- `openspec/specs/cross-profile-sharing/spec.md` (delta `MODIFIED`: os 4 requisitos de F01 sobre `view=household` ganham semântica cross-User + agrupamento por nome + omissão de target_pct; `ADDED` requirement sobre "F06 collapses classes and assets by name")
- `src/omaha/routes/pages.py` (substituir `household_asset_classes` por `family_asset_classes` sem filtro User; `household_aggregates` vira `family_aggregates` que agrupa classes por `name` e enriquece com `_aggregate_assets_by_name`; passar `view="family"` no template branch)
- `src/omaha/auth.py` (`require_profile_writable` mantém a forma 409 — único gate muda é o nome interno da flag `view_mode == "family"`)
- `src/omaha/templates/base.html` (toggle `Casa` → `Família`; reusa infra HTML; condição de visibilidade vira `len(all_family_profiles) >= 2`, não `viewer.profiles`)
- `src/omaha/templates/patrimonio.html` (suprimir coluna `target_pct` no card `patrimonio-portfolio-header` quando `view == 'family'`; suprimir `class-target-pct-view` por classe no agregado)
- `tests/integration/test_household_aggregate.py` (renomear para `test_family_aggregate.py`; cenários: cross-User sempre soma, classes com mesmo nome colapsam, target_pct não vaza)
- `tests/bdd/features/profile_sharing.feature` (atualizar cenário "Operador ativa o modo agregado da casa" para cross-User: loga Italo, toggle mostra total Italo+Ana; loga Ana, mesmo total)
Notes: Decisão deliberada quebrar invariante F01 "intra-User" (D-F06.1).
Toggle aparece sempre que existir >1 perfil no banco, mesmo se viewer
tem 1 só — agregado cross-User continua agregando (não some). **Atenção
PRD §1.2**: hoje os dois usuários compartilham a mesma senha familiar,
então expor cross-User não vaza dados para terceiros. Se algum dia
acrescentar autenticação per-User, F06 precisa de gate adicional.
Reusa o read-only F01 (`require_profile_writable`) — não é refator.
Collapse por nome tem colisão de cor: duas classes "Renda Fixa" só
terão 1 cor visual (a da primeira occurrence). Aceitável porque
agregado é analítico, não operacional (mesmo trade-off da D-F01.5).
Não toca em `routes/imports.py` / `routes/assets.py` além do gate já
aplicado pela F01. **Critical area = auth reads** — cap 1 Applying.
Progress:
- Proposed: done (2026-07-04; via `openspec new change`; folder
  `openspec/changes/f06-family-household-full-join-aggregate/`; 4
  artifacts: `proposal.md` (BREAKING wire shape mantido) +
  `design.md` (8 decisions, herança F01 D5) + `tasks.md` (33
  checkboxes, 8 grupos) + `specs/cross-profile-sharing/spec.md`
  (delta: 2 MODIFIED + 1 REMOVED + 1 ADDED requirement)).
  `openspec validate` retorna `valid: true`.
- Applying: done (2026-07-04; §1-§5 implementation landed —
  family_asset_classes + family_aggregates + _aggregate_classes_by_name
  + _aggregate_assets_by_name em `routes/pages.py`; view=family
  branch em `_render_patrimonio`; `view_mode="family"` session flag
  com read-back de `"household"` no `require_profile_writable` para
  cutover; toggle `Família` em `base.html`; target_pct suppression
  no patrimonio.html; CSS rename com aliases retrocompat;
  tests/test_family_aggregate.py renomeado + cenários cross-User
  + collapse-by-name + target_pct-not-rendered; BDD profile_sharing
  reescrito; e2e selectors com alias `family_toggle` + `household_toggle`).
- Applied: done (2026-07-05; `task test-integration` 368 passed /
  2 skipped; `task test-unit` 223 passed / 2 skipped; `task test-bdd`
  45 passed (4 fail pre-existentes do T05 — `+ Nova classe`
  selector drift, sem regressão F06); `task test-e2e` 42 passed
  (5 fail pre-existentes do T01 — chromium stalls em long journeys,
  sem regressão F06); `openspec validate f06-...` retorna
  `valid: true`; BDD scenarios F06
  `test_operador_ativa_modo_agregado_da_familia` +
  `test_agregado_familiar_simetrico_entre_operadores` passam;
  e2e selector_inventory smoke passa (aliases OR-pattern
  `family-toggle*` + `household-toggle*` reconciliam sem
  duplicar testids no template)).
- Archived: done (2026-07-05; archive
  `2026-07-05-f06-family-household-full-join-aggregate/`;
  spec delta consolidada: 2 MODIFIED
  ("patrimonio page exposes household aggregate view mode" +
  "header exposes household mode toggle") + 1 REMOVED
  ("Household mode preserves per-profile isolation") + 1 ADDED
  ("Family aggregate collapses classes and assets by name
  (full-join)") em `openspec/specs/cross-profile-sharing/spec.md`).
  O nome do header do requirement F01 "household" foi mantido
  (requisito F01 foi MODIFIED, não renomeado) — coerência com o
  nome da querystring `?view=household` que continua sendo a
  URL canônica da feature. O label visível (`Família`) e o
  internal context (`view == "family"`) ficam em UI/code,
  não na spec.

### F07 - Família como opção no profile-switcher (peer de Italo/Ana)
Status: `Archived`
Goal: Promover Família de toggle (`?view=household`) para **opção
no profile-switcher** — peer dos perfis reais Italo + Ana. O
operador escolhe entre `Italo` / `Ana` / `Família` no chip, e a
seleção dispara o agregado cross-User sem precisar de querystring
adicional. Toggle no header sai. Fixture de seed `Italo RF2`
(perfil #3 órfão) também sai. Familia vira um `Profile` row
sentinel com flag `is_family_sentinel=True` + User `family` sem
senha — não autentica, só aparece como opção no chip.
Candidate OpenSpec change id: `f07-familia-as-profile-option`
Spec link: `openspec/changes/f07-familia-as-profile-option/`
Files:
- `openspec/specs/cross-profile-sharing/spec.md` (delta
  `MODIFIED`: "household aggregate view mode" + "household mode
  toggle" viram peer-via-chip; "Household mode preserves
  per-profile isolation" REMOVED; "Family aggregate collapses
  classes and assets by name" já consolidada em F06 fica)
- `openspec/specs/direct-landing-with-header-profile-switcher/spec.md`
  (delta `MODIFIED` se a spec existir — requirement sobre o
  `<select>` ganha 3 opções com Família como peer)
- `src/omaha/models.py` (`Profile.is_family_sentinel: bool` +
  novo User `family` sem password_hash)
- `alembic/versions/..._add_is_family_sentinel_to_profile.py`
  (nova migration)
- `src/omaha/seed.py` + `scripts/seed_from_csv.py` (criar
  Família sentinel; remover Italo RF2; `db-reset` produz
  exatamente 2 perfis reais + 1 sentinel)
- `src/omaha/auth.py` (`get_active_profile` retorna `None` para
  sentinel)
- `src/omaha/routes/pages.py` (helper `_real_profiles` filtra
  sentinel; `_render_patrimonio` detecta `active_profile_id`
  apontando para sentinel e força `view='family'`; querystring
  `?view=household` continua funcionando)
- `src/omaha/templates/base.html` (profile-switcher com 3
  opções: Italo / Ana / Família, separador visual; toggle
  `Casa`/`Família` no header sai)
- `src/omaha/templates/patrimonio.html` (label "Família
  (agregado)" + separador visual no `<select>`; banner
  read-only + supressão target_pct + alert suppression do F06
  ficam)
- `src/omaha/static/app.css` (separador visual
  `.profile-switcher__optgroup`; highlight com `--accent` para
  opção Família)
- `tests/test_family_aggregate.py` (cenário "selecting Família
  via profile-switcher triggers family view")
- `tests/test_seed.py` (cenário "db-reset produces exactly 2
  real profiles + 1 sentinel Família profile")
- `tests/bdd/features/profile_sharing.feature` (cenário
  "Operador seleciona Família no chip e vê agregado
  cross-User"; cenários F06 `clico em "Família"` viram
  `seleciono "Família" no chip do header`)
- `tests/bdd/test_scenarios.py` (novos bindings)
- `tests/e2e/selectors.py` (`profile_option_family` ganha;
  aliases `household_toggle*` + `family_toggle*` saem)
- `tests/conftest.py` (atualizar prefix list se novos
  test files)
Notes: Decisão deliberada remover toggle (D-F07.2) — peer-via-chip
é o pedido literal do owner no grill 2026-07-05. Reusa wire shape
409 `household_read_only` sem retrabalho (D-F07.4). Migration
Alembic adiciona `is_family_sentinel` com `DEFAULT 0` — backward
compat com F01 data existente (incluindo Italo RF2 rows legadas
que viram `0` = não-sentinel, e podem ser filtradas/dropadas
explicitamente no apply). `Italo RF2` sai do seed mas pode
continuar em DBs existentes até a próxima reset; o sentinel
Família é criado no apply, não precisa dropar Italo RF2
retroativamente. Critical area = profile routing + auth. Cap 1
Applying. Não toca solver, cotação, nem rebalance. T05 (BDD
selector drift) e T01 (chromium stalls) continuam fora do
escopo F07 — slices independentes.
Progress:
- Proposed: done (2026-07-05; via `openspec new change`; folder
  `openspec/changes/f07-familia-as-profile-option/`; 4
  artifacts: `proposal.md` + `design.md` (5 decisions) +
  `tasks.md` (8 grupos) + `specs/cross-profile-sharing/spec.md`
  (delta: 2 MODIFIED + 1 REMOVED + 1 ADDED requirement
  reaproveitado de F06)). `openspec validate` retorna
  `valid: true`.
- Applying: done (2026-07-05; §1-§6 implementation landed —
  model `Profile.is_family_sentinel` + migration `0017`; seed
  layer creates User `family` (no password) + Profile `Família`
  sentinel + drops `Italo RF2`; `auth.get_active_profile`
  short-circuits sentinel; routes `_real_profiles` +
  `_resolve_view_mode` + `_sentinel_redirect` +
  `select_profile` set `view_mode="family"` on sentinel bind;
  `_render_patrimonio` accepts `profile=None` for family view;
  rebalance/rentabilidade/proventos routes redirect to
  `/patrimonio?view=household` when sentinel is bound;
  base.html profile-switcher renders 3 options with Família
  inside `<optgroup>`; CSS `.profile-switcher__optgroup` +
  Família accent; `data/seed/italo_rf2_*.csv` files deleted;
  `snapshot_to_csv.py` sentinel allow-list updated;
  `scripts/seed_from_csv.py` drops `italo_rf2` mapping;
  `tests/test_family_aggregate.py` rewrite (toggle tests →
  sentinel tests); `tests/test_seed.py` Família sentinel
  assertions + no Italo RF2; `tests/e2e/selectors.py` adds
  `profile_option_family` + drops `family_toggle*` /
  `household_toggle*`; `tests/bdd/features/profile_sharing.feature`
  scenarios reescritas ("clico em 'Família'" →
  "seleciono 'Família (agregado)' no chip"); PRD §5.3 + roadmap
  slice updated; tests/conftest prefix list unchanged
  (test_family_aggregate.py já na lista))
- Applied: done (2026-07-05; `task test-integration` 369 passed
  / 2 skipped (no regressão); `task test-unit` 223 passed /
  2 skipped; `task test-bdd` 47 passed (4 pre-existing T05
  selector drift fail fora do escopo F07 — `+ Nova classe`
  matcher não atualizado); `task test-e2e` 42 passed (5
  pre-existing T01 chromium stalls fora do escopo);
  `selector_inventory` smoke passa; `openspec validate
  f07-familia-as-profile-option --json` retorna `valid: true`;
  refresh-for-test smoke OK: `GET /` renderiza chip com 3
  opções (Italo, Ana, Família dentro de optgroup) +
  `data-testid="profile-option-family"` presente + Família
  option rendered; DB Italo: 6 classes + 48 assets + 47
  positions; Ana: 6 classes + 52 assets + 52 positions)
- Archived: done (2026-07-05; archive
  `2026-07-05-f07-familia-as-profile-option/`; spec delta
  consolidada em `openspec/specs/cross-profile-sharing/spec.md`:
  MODIFIED "The patrimonio page exposes a household aggregate
  view mode" (querystring + sentinel are co-equal entry points;
  Família via profile-switcher is the first-class affordance) +
  MODIFIED "The header exposes a household mode toggle"
  (header SHALL NOT render toggle; Família é peer do
  profile-switcher via sentinel `<option>`); REMOVED "Household
  mode preserves per-profile isolation" já consolidado em F06
  archive; ADDED "Family aggregate collapses classes and assets
  by name" reaproveitado de F06 archive. Label do option
  Família simplificado de "Família (agregado)" para "Família"
  em iteração pós-archive via task do owner)
Goal: Substituir a semântica household de F01 (que era intra-User e
inútil porque Italo/Ana são Users separados). Vista nova agrega TODOS os
`Profile` rows do banco (`profile_id NOT IN (root "system")`) — não
filtra por `Profile.user_id` — independente de quem logou. Classes e
ativos com **mesmo nome** entre perfis distintos colapsam em uma única
linha (full-join por `name`, soma de investido/valor). `target_pct` é
**omitido** no agregado (sem alocação-alvo cross-User). Toggle `Casa`
do header vira `Família`. Modo read-only mantido; mutações retornam 409.
Candidate OpenSpec change id: `f06-family-household-full-join-aggregate`
Spec link: `openspec/changes/f06-family-household-full-join-aggregate/`
Files:
- `openspec/specs/cross-profile-sharing/spec.md` (delta `MODIFIED`: os 4 requisitos de F01 sobre `view=household` ganham semântica cross-User + agrupamento por nome + omissão de target_pct; `ADDED` requirement sobre "F06 collapses classes and assets by name")
- `src/omaha/routes/pages.py` (substituir `household_asset_classes` por `family_asset_classes` sem filtro User; `household_aggregates` vira `family_aggregates` que agrupa classes por `name` e enriquece com `_aggregate_assets_by_name`; passar `view="family"` no template branch)
- `src/omaha/auth.py` (`require_profile_writable` mantém a forma 409 — único gate muda é o nome interno da flag `view_mode == "family"`)
- `src/omaha/templates/base.html` (toggle `Casa` → `Família`; reusa infra HTML; condição de visibilidade vira `len(all_family_profiles) >= 2`, não `viewer.profiles`)
- `src/omaha/templates/patrimonio.html` (suprimir coluna `target_pct` no card `patrimonio-portfolio-header` quando `view == 'family'`; suprimir `class-target-pct-view` por classe no agregado)
- `tests/integration/test_household_aggregate.py` (renomear para `test_family_aggregate.py`; cenários: cross-User sempre soma, classes com mesmo nome colapsam, target_pct não vaza)
- `tests/bdd/features/profile_sharing.feature` (atualizar cenário "Operador ativa o modo agregado da casa" para cross-User: loga Italo, toggle mostra total Italo+Ana; loga Ana, mesmo total)
Notes: Decisão deliberada quebrar invariante F01 "intra-User" (D-F06.1).
Toggle aparece sempre que existir >1 perfil no banco, mesmo se viewer
tem 1 só — agregado cross-User continua agregando (não some). **Atenção
PRD §1.2**: hoje os dois usuários compartilham a mesma senha familiar,
então expor cross-User não vaza dados para terceiros. Se algum dia
acrescentar autenticação per-User, F06 precisa de gate adicional.
Reusa o read-only F01 (`require_profile_writable`) — não é refator.
Collapse por nome tem colisão de cor: duas classes "Renda Fixa" só
terão 1 cor visual (a da primeira occurrence). Aceitável porque
agregado é analítico, não operacional (mesmo trade-off da D-F01.5).
Não toca em `routes/imports.py` / `routes/assets.py` além do gate já
aplicado pela F01. **Critical area = auth reads** — cap 1 Applying.
Progress:
- Proposed: done (2026-07-04; via `openspec new change`; folder
  `openspec/changes/f06-family-household-full-join-aggregate/`; 4
  artifacts: `proposal.md` (BREAKING wire shape mantido) +
  `design.md` (8 decisions, herança F01 D5) + `tasks.md` (33
  checkboxes, 8 grupos) + `specs/cross-profile-sharing/spec.md`
  (delta: 2 MODIFIED + 1 REMOVED + 1 ADDED requirement)).
  `openspec validate` retorna `valid: true`.
- Applying: done (2026-07-04; §1-§5 implementation landed —
  family_asset_classes + family_aggregates + _aggregate_classes_by_name
  + _aggregate_assets_by_name em `routes/pages.py`; view=family
  branch em `_render_patrimonio`; `view_mode="family"` session flag
  com read-back de `"household"` no `require_profile_writable` para
  cutover; toggle `Família` em `base.html`; target_pct suppression
  no patrimonio.html; CSS rename com aliases retrocompat;
  tests/test_family_aggregate.py renomeado + cenários cross-User
  + collapse-by-name + target_pct-not-rendered; BDD profile_sharing
  reescrito; e2e selectors com alias `family_toggle` + `household_toggle`).
- Applied: done (2026-07-05; `task test-integration` 368 passed /
  2 skipped; `task test-unit` 223 passed / 2 skipped; `task test-bdd`
  45 passed (4 fail pre-existentes do T05 — `+ Nova classe`
  selector drift, sem regressão F06); `task test-e2e` 42 passed
  (5 fail pre-existentes do T01 — chromium stalls em long journeys,
  sem regressão F06); `openspec validate f06-...` retorna
  `valid: true`; BDD scenarios F06
  `test_operador_ativa_modo_agregado_da_familia` +
  `test_agregado_familiar_simetrico_entre_operadores` passam;
  e2e selector_inventory smoke passa (aliases OR-pattern
  `family-toggle*` + `household-toggle*` reconciliam sem
  duplicar testids no template)).
- Archived: done (2026-07-05; archive
  `2026-07-05-f06-family-household-full-join-aggregate/`;
  spec delta consolidada: 2 MODIFIED
  ("patrimonio page exposes household aggregate view mode" +
  "header exposes household mode toggle") + 1 REMOVED
  ("Household mode preserves per-profile isolation") + 1 ADDED
  ("Family aggregate collapses classes and assets by name
  (full-join)") em `openspec/specs/cross-profile-sharing/spec.md`).
  O nome do header do requirement F01 "household" foi mantido
  (requisito F01 foi MODIFIED, não renomeado) — coerência com o
  nome da querystring `?view=household` que continua sendo a
  URL canônica da feature. O label visível (`Família`) e o
  internal context (`view == "family"`) ficam em UI/code,
  não na spec.

### R01 - Limpar arquivos órfãos / dumps / snapshots antigos
Status: `Archived`
Goal: Limpar o repo de fixtures órfãs, dumps temporários e snapshots
antigos em `backups/` e `data/` que vazaram do `.gitignore`.
Sem mudança de comportamento observável.
Candidate OpenSpec change id: `r01-clean-orphaned-files-and-snapshots`
Spec link: `openspec/changes/archive/2026-07-03-r01-clean-orphaned-files-and-snapshots/`
Files:
- `backups/` (purge)
- `data/portfolio.db` (preservar — está no .gitignore correto)
- `tmp/` e artefatos ad-hoc
Notes: Pré-auditoria rápida: `task backup` lista tudo em `backups/` para
conferir antes do wipe. Zero risk — não toca código/runtime.
Progress:
- Proposed: done
- Applying: done
- Applied: done
- Archived: done

### R02 - Revisar sistema de seed (caminho CSV)
Status: `Archived`
Goal: Tornar o caminho CSV (`scripts/seed_from_csv.py` + triplet em
`data/seed/`) mais simples e direto para manutenção dos valores de seed
na plataforma. Sem mudar invariantes: CSV continua sendo source of truth.
Candidate OpenSpec change id: `r02-revise-csv-seed-system`
Spec link: `openspec/changes/archive/2026-07-06-r02-revise-csv-seed-system/`
Files:
- `scripts/seed_from_csv.py` → `scripts/seed_from_csv/` package (loaders, validation, profiles, modes, __main__, __init__)
- `data/seed/README.md`
- `tests/test_seed_from_csv_loaders.py` (novo)
- `tests/test_seed_from_csv_validation.py` (novo)
- `tests/conftest.py` (`_UNIT_FILES` add dos 2 novos test files)
- `openspec/specs/csv-seed-internals/spec.md` (nova capability, internal layout — consolidada 2026-07-06)
Notes: PRD §4.3 é invariante — `seed.py` continua user+profile only; ativo/
posição continuam só via CSV. Foco é DX, não contrato. Refactor puro —
contract `data-driven-seed` byte-preserved. Quatro consumers externos
mantidos sem mudança: `scripts/snapshot_to_csv.py`,
`scripts/reset_both_profiles.py`, `tests/test_seed_from_csv.py`,
`tests/scripts/test_reset_both_profiles.py`. `python -m
scripts.seed_from_csv` continua resolvendo via novo `__main__.py`.
**Late-binding fix**: `loaders.py` e `validation.py` resolvem
`SEED_DIR` via `scripts.seed_from_csv.SEED_DIR` (call-time lookup),
não captura estática, para preservar o padrão de monkeypatch do test
`test_seed_from_csv.py:665` (`seed_mod.SEED_DIR = tmp_path`).
Progress:
- Proposed: done (2026-07-05; folder
  `openspec/changes/r02-revise-csv-seed-system/`; 4 artifacts
  completos; `openspec validate` retorna `valid: true`).
- Applying: done (2026-07-05; package criado — `__init__.py`
  re-export + `__main__.py` CLI + `loaders.py` (dataclasses +
  helpers + load_* + SEED_DIR late-binding) + `validation.py`
  (`validate()` cross-refs + sum invariants, SEED_DIR via
  late-binding) + `profiles.py` (PROFILES + Família-sentinel
  one-liner, F01-fixture narrative dropped) + `modes.py`
  (`_wipe_profile` + `run_reset` + `run_upsert` + `run_diff`);
  `scripts/seed_from_csv.py` deletado; `tests/test_seed_from_csv_loaders.py`
  (22 cases) + `tests/test_seed_from_csv_validation.py` (7 cases) +
  `tests/conftest.py::_UNIT_FILES` extended; `data/seed/README.md`
  note do package layout).
- Applied: done (2026-07-05; `task test-unit` 261 passed / 2
  skipped (+28 from new tests vs pre-refactor 233);
  `task test-integration` 369 passed / 2 skipped (no regressão;
  `tests/test_seed_from_csv.py` 20 tests passam via subprocess +
  module import); `task test-bdd` 47 passed / 4 failed (4 fail
  pre-existentes do T05 BDD step-def drift — `+ Nova classe`
  selector não atualizado após F02 sidebar removal, fora do
  escopo R02); ruff check + ruff format verdes nos refactored
  files; `task db-reset` ok com `italo=6/48/47 ana=6/52/52`
  (mesmo baseline F07 archive); `openspec validate
  r02-revise-csv-seed-system` retorna `valid: true`; server
  healthz `200`; `python -m scripts.seed_from_csv --profile
  italo --mode diff` retorna `would_create=0 would_update=0
  would_orphan=0`).
- Archived: done (2026-07-06; archive
  `2026-07-06-r02-revise-csv-seed-system/`; spec
  `csv-seed-internals` consolidada em
  `openspec/specs/csv-seed-internals/spec.md` com 5 ADDED
  requirements — package layout, one-module-per-concern,
  private underscore helpers, dead F01-fixture narrative
  removal, per-layer unit tests. Sync feita manualmente
  antes do `--skip-specs` archive; `openspec validate
  csv-seed-internals` retorna `valid: true`. 8 specs
  pre-existentes continuam falhando (broker-csv-*,
  dashboard-*, import-*) — não relacionado a R02)

### R03 - Extrair `quote_provider` adapter para pacote
Status: `Archived`
Goal: Hoje só existe uma implementação implícita (`yfinance`). Promover
`QuoteProvider` para pacote com interface explícita de forma que trocar
provider não toque consumers (`QuoteCache`, `MarketPriceLookup`).
Candidate OpenSpec change id: `r03-extract-quote-provider-adapter`
Spec link: `openspec/changes/r03-extract-quote-provider-adapter/`
Files:
- `src/omaha/quotes/provider.py` (refactor → `provider/` package: `protocol.py`, `mapper.py`, `yfinance.py`, `stub.py`, `__init__.py` + selector)
- `src/omaha/quotes/cache.py` (sem mudança; re-export preserva import)
- `src/omaha/rebalance/` (sem mudança; já só fala com Protocol)
- `src/omaha/config.py` (`QUOTE_PROVIDER: Literal["yfinance", "stub"]`)
- `src/omaha/main.py` (`_start_quote_service` chama `get_quote_provider()` em vez de importar `YFinanceProvider` direto)
- `tests/test_quote_provider_selector.py` (novo)
- `tests/test_quote_provider_stub.py` (novo)
- `tests/conftest.py` (`_UNIT_FILES` estendido)
Notes: Sem mudança de comportamento — yfinance permanece default.
Scope refinado após inspeção do código atual: o `QuoteProvider` Protocol
já existe; o gap real é que `main.py:97` é o único import direto de
`YFinanceProvider`. Slice adiciona package layout + selector +
`StubProvider` + 1 setting + 1 spec delta (`quote-provider`, 3 ADDED) +
1 spec nova (`quote-provider-factory`). Critical area = rebalance
solver + cotação yfinance (cap 1 Applying).
Progress:
- Proposed: done (2026-07-05; folder
  `openspec/changes/r03-extract-quote-provider-adapter/`; 4
  artifacts completos: `proposal.md` (Why + What Changes + 1 NEW +
  1 MODIFIED capability + Impact) + `design.md` (Context + Goals/
  Non-Goals + 6 decisions D-R03.1..D-R03.6 + Risks/Trade-offs) +
  `tasks.md` (8 grupos, 27 checkboxes) +
  `specs/quote-provider/spec.md` (delta: 3 ADDED requirements:
  "Provider selector resolves from settings", "StubProvider
  exists in the package for tests + offline", "Provider lives
  in a package, public names preserved") +
  `specs/quote-provider-factory/spec.md` (NEW capability, 3
  ADDED requirements: selector entry point, StubProvider is
  the test/offline impl, settings drive the selector).
  `openspec validate r03-extract-quote-provider-adapter` retorna
  `valid: true`. `quote-provider` spec delta valid: true;
  `quote-provider-factory` é nova (não tem top-level spec até
  archive). 8 specs pre-existentes continuam falhando
  (broker-csv-*, dashboard-*, import-*) — não relacionado a
  R03).
- Applying: done (2026-07-05; `src/omaha/quotes/provider/`
  package criado com `__init__.py` (re-export + `get_quote_provider()`)
  + `protocol.py` (Quote + QuoteProvider) + `mapper.py`
  (map_symbol + regex) + `yfinance.py` (verbatim move,
  import path atualizado para `omaha.quotes.provider.mapper` /
  `omaha.quotes.provider.protocol`) + `stub.py` (StubProvider
  novo com `responses` + `default`); `src/omaha/quotes/provider.py`
  deletado; `src/omaha/main.py:_start_quote_service` agora chama
  `get_quote_provider()` em vez de importar `YFinanceProvider`
  direto (verificado: `rg "YFinanceProvider|StubProvider"
  src/omaha/main.py` retorna 0 matches); `src/omaha/config.py`
  ganha `QUOTE_PROVIDER: Literal["yfinance", "stub"] = "yfinance"`
  (pydantic-settings Literal — falha no boot em valor inválido);
  `tests/test_quote_provider_selector.py` (4 casos: default
  → YFinanceProvider, stub → StubProvider, valor inválido
  bypass-pydantic → ValueError com offender quoted, sem cache —
  duas chamadas retornam instâncias distintas); `tests/test_quote_provider_stub.py`
  (6 casos: mapped → Quote, unmapped → None, unmapped +
  configured default, fetch_many preserva ordem, per-symbol
  None não aborta batch, isolamento entre instâncias);
  `tests/test_yfinance_provider.py` patch target atualizado
  de `omaha.quotes.provider.yf.Ticker` → `omaha.quotes.provider.yfinance.yf.Ticker`
  (6 ocorrências; import no topo continua resolvendo via
  re-export); `tests/conftest.py::_UNIT_FILES` estendido com
  os 2 novos test files; `tests/test_quote_service.py` e
  `tests/test_market_prices_adapter.py` inalterados — re-export
  preserva imports `from omaha.quotes.provider import Quote`).
- Applied: done (2026-07-05; `task test-unit` 271 passed /
  2 skipped (+10 vs pre-slice 261: 4 selector + 6 stub, all
  green sem regressão); `task test-integration` 369 passed /
  2 skipped (sem regressão; `test_yfinance_provider.py` rola
  contra o moved code com paths atualizados);
  `ruff check` + `ruff format --check` verde no package +
  novos tests + `main.py` + `config.py` + `test_yfinance_provider.py`
  + `conftest.py`; `openspec validate r03-extract-quote-provider-adapter
  --json` retorna `valid: true`; smoke selectors via bypass
  pydantic: default → `YFinanceProvider`,
  `Settings(QUOTE_PROVIDER="stub")` → `StubProvider`,
  `Settings(); settings.QUOTE_PROVIDER = "brapi";
  get_quote_provider()` → `ValueError: unknown QUOTE_PROVIDER:
  'brapi'` (defense-in-depth path; L1 pydantic já bloqueia
  `Settings(QUOTE_PROVIDER="brapi")` no construtor);
  refresh-for-test smoke OK: server 0.0.0.0:8000, `/healthz`
  `{"status":"ok","db":"ok"}`, `db-reset` produz Italo=6/48/47
  + Ana=6/52/52 (3 users, 3 profiles — Família sentinel intacta),
  dashboard renderiza classes seeded ("RF Din" substring match
  count=5), Família option no chip renderiza.))
- Archived: done (2026-07-06; archive
  `2026-07-06-r03-extract-quote-provider-adapter/`; spec
  consolidation manual pre-archive (skip-specs flag): 3 ADDED
  requirements em `openspec/specs/quote-provider/spec.md` final
  (selector resolves from settings + StubProvider exists + lives
  in a package, public names preserved — Purpose TBD substituído
  por Purpose real cobrindo o fetch contract) + novo arquivo
  `openspec/specs/quote-provider-factory/spec.md` com Purpose
  (cobre runtime seam vs. fetch contract) + 3 ADDED requirements
  (selector is single entry point + StubProvider is the
  test/offline implementation + settings drive the selector);
  `openspec list --specs`: 39 total (38 pre + 1 new
  quote-provider-factory), `quote-provider` requirementCount=10
  (7 base + 3 delta), sem specs com errors. F03 active change
  preservado (Ready slice com proposal draft válido por D-F03-defer).

### R04 - Partialize `templates/patrimonio.html`
Status: `Archived` 2026-07-06
Goal: Quebrar `templates/patrimonio.html` (após rename de `dashboard.html`
em F02, ~1600 linhas) em partials. Já existem `_sidebar.html` (a ser
limpo em F02), `_rebalance_*`; estender o padrão.
Sem mudança de comportamento visível.
Candidate OpenSpec change id: `r04-partialize-patrimonio-template`
Spec link: `openspec/changes/r04-partialize-patrimonio-template/`
Files:
- `src/omaha/templates/patrimonio.html`
- `src/omaha/templates/_patrimonio_*.html` (6 novos partials)
- `openspec/specs/patrimonio-template-partials/spec.md` (novo capability — captura o layout interno)
Notes: Depende de F02 (template renomeado + side panel removido) para
não parcializar sobre mudança em voo. Id e título foram atualizados em
2026-07-03 após grill do mock de navegação — `dashboard.html` agora é
`patrimonio.html`. Refactor puro — sem mudança de comportamento
visível. Novo capability `patrimonio-template-partials` segue o
precedente de `csv-seed-internals` (R02 archive): internal layout
spec que descreve a organização file-level sem tocar nos contratos
externos. 8 specs pre-existentes continuam falhando
(broker-csv-*, dashboard-*, import-*) — não relacionado a R04.
Progress:
- Proposed: done (2026-07-05; folder `openspec/changes/r04-partialize-patrimonio-template/`; 4 artifacts: `proposal.md` (refactor puro, 1 NEW capability `patrimonio-template-partials`, 0 MODIFIED) + `design.md` (7 decisions D-R04.1..D-R04.7 + Risks + Migration + Open Questions) + `tasks.md` (6 grupos: pre-refactor capture + extract partials + rewrite shell + render verification + test gate + spec cleanup, 28 checkboxes) + `specs/patrimonio-template-partials/spec.md` (4 ADDED requirements: shell + partials layout, per-section verbatim rendering, underscore-prefix naming, rendered-HTML byte-equivalence). `openspec validate r04-partialize-patrimonio-template --json` retorna `valid: true`.)
- Applying: done (2026-07-05; §1-§6 implementation landed — `src/omaha/templates/patrimonio.html` shell (~60 lines) + 6 partials: `_patrimonio_actions.html` (21 LOC, 4 testids) + `_patrimonio_portfolio_header.html` (20 LOC, 5 testids) + `_patrimonio_distribution.html` (23 LOC, 3 testids) + `_patrimonio_class_section.html` (331 LOC, 60 testids) + `_patrimonio_empty_states.html` (18 LOC, 2 testids) + `_patrimonio_add_asset_modal.html` (1682 LOC, 45 testids) — total 119 testids in partials + 3 in shell (`class-summary` + `dashboard-distribution` + `patrimonio-read-only-note`) = 122 original testid count preserved. Shell wraps patrimonio-page + class-summary + dashboard-distribution sections; modals + Alpine `<script>` live in the add-asset-modal partial. Render diff vs pre-refactor baselines (Italo default view, Italo `?view=household` family view, Ana default view) = whitespace-only differences (zero non-blank-line differences); testid counts match exactly (423 occurrences / 134 unique in both pre and post); x-data declarations preserved (17 occurrences, 2 distinct forms). Total 2186 LOC → 97.7KB shell + 2095 LOC across 6 partials (largest is add-asset-modal at 70KB due to 3 modals + 1247-line Alpine script block). Critical area cap not applicable (template-only refactor, no auth / rebalance solver / yfinance touched).)
- Applied: done (2026-07-05; `task test-unit` 271 passed / 2 skipped (no regressão); `task test-integration` 369 passed / 2 skipped (no regressão — `test_patrimonio_route`, `test_class_section_*`, `test_family_aggregate.py` passam byte-equivalente); `task test-bdd` 47 passed / 4 failed (4 fail pre-existentes T05 — `+ Nova classe` selector drift, fora do escopo R04, confirmado via `git stash` que render pré-refactor tem o mesmo testid `empty-state-create-class` + texto `Nova Classe`); `task test-e2e` 42 passed / 5 failed (5 fail pre-existentes chromium stalls em `test_user_journey.py` + `test_user_journey_rebalance.py` + `test_visual_gate.py`, fora do escopo R04 — `test_class_crud` + `test_class_section_alignment` + `test_selector_inventory` passam verde com 12/12); `task lint` verde (ruff + prek hooks); `openspec validate r04-partialize-patrimonio-template --json` retorna `valid: true`; `openspec list --specs` count 39 inalterado (refactor puro, 0 spec deltas); refresh-for-test smoke OK: server 0.0.0.0:8000 + `/patrimonio` 200 + `/patrimonio?view=household` 200 + Família option no chip intacta + `db-reset` Italo=6/48/47 Ana=6/52/52 (mesmo baseline F07 archive).
- Archived: done (2026-07-06; archive `2026-07-06-r04-partialize-patrimonio-template/`; new capability `patrimonio-template-partials` consolidada em `openspec/specs/patrimonio-template-partials/spec.md` com Purpose (internal file layout, cross-references) + 4 ADDED requirements (shell + partials layout + per-section verbatim rendering + underscore-prefix naming + rendered-HTML byte-equivalence — 14 cenários no total). `openspec list --specs` agora reporta 40 specs (39 pre + 1 new). 8 specs pre-existentes continuam falhando (broker-csv-*, dashboard-*, import-*) — não relacionado a R04).

### T01 - BDD + e2e suite a 100% green
Status: `Archived`
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
- Proposed: done
- Applying: done
- Applied: done
- Archived: done

### T02 - Coverage report no CI
Status: `Archived` (GH Actions deferred per owner 2026-07-06; infra
dormente no repo, será reativada quando owner retomar o tema)
Goal: `task coverage` existe; falta cabo no pipeline (GitHub Actions).
Wire `--cov-report=xml` + upload para o driver de coverage usado pelo
repo. **Repo não tem CI** (verificado `ls .github/workflows/` → não
existe), então escopo da fatia absorve "introduzir workflow mínimo":
lint + unit + integration + BDD + coverage job, cache de `uv`, sem
e2e/audit (ficam fora por decisão D-T02.9 / D-T02.4 — gate de threshold
fica para slice futura owner-driven).
Candidate OpenSpec change id: `t02-coverage-report-in-ci`
Spec link: `openspec/changes/archive/2026-07-06-t02-coverage-report-in-ci/`
Files:
- `.github/workflows/ci.yml` (novo — 5 jobs: lint, test-unit, test-integration, test-bdd, coverage)
- `pyproject.toml` (`[tool.coverage.run]` com `source = ["src/omaha"]` + `[tool.coverage.report]` com `exclude_lines` + `addopts` ganha `--cov-report=xml:reports/coverage.xml` + `task coverage` reescrito para `-m "unit or integration"`)
- `.gitignore` (acrescentar `reports/coverage.xml`)
Notes: Sem `fail_under` — gate de threshold é decisão owner-separada.
E2E (`task test-e2e`) e audit integration ficam fora do workflow (D-T02.9).
Reports XML vai para `reports/coverage.xml` (D-T02.3); diretório `reports/`
já existe vazio no repo. Cache de `uv` via `astral-sh/setup-uv@v4` +
`actions/cache@v4` (D-T02.8 fix pós-run 1 — `setup-python@v5` não
aceita `cache: "uv"`). Coverage roda como job separado que
re-invoca pytest com `--cov` (D-T02.2) — desacopla signal de cobertura
dos jobs de teste puro (preserva `task test-unit` limpo como gate de
pre-push via prek).
Progress:
- Proposed: done 2026-07-06; folder
  `openspec/changes/t02-coverage-report-in-ci/`; 4 artifacts
  completos (`proposal.md` + `specs/ci-coverage-pipeline/spec.md`
  com 10 ADDED requirements + `design.md` com 9 decisions
  D-T02.1..D-T02.9 + `tasks.md` com 6 grupos, 28 checkboxes);
  `openspec validate t02-coverage-report-in-ci` retorna `valid: true`
- Applying: done 2026-07-06; §1-§4 implementation landed —
  `pyproject.toml` ganha bloco `[tool.coverage.run]` (source =
  `["src/omaha"]`, branch=false, omit `__main__.py`) + bloco
  `[tool.coverage.report]` (exclude_lines para `pragma: no cover`
  / `if __name__ == "__main__":` / `raise NotImplementedError`
  / `if TYPE_CHECKING:`; sem fail_under); `addopts` da
  `[tool.pytest.ini_options]` estendido para
  `--cov=src/omaha --cov-report=xml:reports/coverage.xml`
  (preserva `-q --ignore=tests/e2e/_disabled` anterior); `task
  coverage` em `[tool.taskipy.tasks]` reescrito para usar
  `-m "unit or integration"` (BDD/e2e excluídos — passa de 10+
  min de timeout para 3 min, preserva scope "code coverage"
  separando de "behavior coverage"); `.gitignore` ganha
  `reports/coverage.xml` e `reports/.coverage` (preserva
  `coverage/` entry pré-existente); `.github/workflows/ci.yml`
  criado com 5 jobs (`lint` sem `needs`, `test-unit` /
  `test-integration` / `test-bdd` com `needs: lint`,
  `coverage` com `needs: [test-unit, test-integration]`),
  triggers `push` em `[main]` + `pull_request` em `[main]`,
  Python via `astral-sh/setup-uv@v4` +
  `python-version: "3.12"` + `actions/cache@v4` keyed em
  `hashFiles('uv.lock')`, `actions/upload-artifact@v4` para
  `coverage-report` com `retention-days: 30`; coverage job
  chama `pytest -m "unit or integration" -q
  --ignore=tests/e2e/_disabled` (sem `--cov=...` explícito —
  addopts fornece); test-integration + test-bdd + coverage
  jobs ganham step `Reset database` (`uv run task db-reset`)
  com `env: SECRET_KEY + ADMIN_PASSWORD` injetados; CI
  verification local: `task test-unit` 271 pass / 2 skip
  (R04 baseline match), `task test-integration` 369 pass /
  2 skip (R02/R03/R04 baseline match), `task test-bdd` 51
  pass (T05 baseline match), `task coverage` 640 pass / 4
  skip / **92% line coverage** com `reports/coverage.xml`
  Cobertura-compatible (`<coverage version=... line-rate="0.9163" ...>`
  + `<package name=...>` structure), `ruff check` +
  `ruff format --check` ambos verdes em `src tests alembic`
- Applied: done 2026-07-06; **CI verification parcial** —
  5 Actions runs tentadas durante a sessão (registro completo em
  `archive/2026-07-06-t02-coverage-report-in-ci/tasks.md` §5):
  - Run 1 (`99fcc5c`): falha `lint/Setup Python` —
    `setup-python@v5 cache: "uv"` inválido → trocado por
    `setup-uv@v4` + `actions/cache@v4`
  - Run 2 (`d232f19`): falha `lint/Setup Python` —
    `setup-uv@v4 python-version-file` inválido → trocado por
    `python-version: "3.12"`
  - Run 3 (`07c7f46`): falha `lint/Install dependencies` —
    `uv sync --extra dev` → `Extra 'dev' is not defined`
    (dev em `[dependency-groups]`, não em `[project.optional-dependencies]`)
    → trocado por `--group dev`
  - Run 4 (`e9df2d5`): **lint ✓ + test-unit ✓**. Falha
    `test-integration` (28 errors: `no such table: positions`
    — CI runner sem DB) + `test-bdd` (1 fail pre-existente
    `test_import_happy_auto_match[Ana]` flake + mesmo DB issue) →
    adicionado `db-reset` step
  - Run 5 (`bac8b47`): falha `Reset database` —
    `RuntimeError: SECRET_KEY is not set` → injetado `SECRET_KEY` +
    `ADMIN_PASSWORD` env vars. **Último run antes da decisão
    de pausar.** Estado pós-run 5: workflow com fixes
    acumulados, ainda não validado end-to-end.
- Archived: done 2026-07-06; archive
  `openspec/changes/archive/2026-07-06-t02-coverage-report-in-ci/`
  (4 artifacts preservados + tasks.md com 22/27 checkboxes
  marcados + bloco §5 registrando as 5 runs de CI tentadas +
  reactivation path explícito). Spec `ci-coverage-pipeline`
  consolidada em `openspec/specs/ci-coverage-pipeline/spec.md`
  (10 ADDED requirements + Purpose). **Decisão owner 2026-07-06:**
  GH Actions fica dormente no repo (workflow file commitado
  mas não exercitado); reativação só quando owner retomar o
  tema. Slice sai da fila ativa — próximas fatias a executar
  são T03 (mutation testing rebalance) ou I01 (backup
  scheduling) ou I02 (TLS cert) ou D01 (README refresh) ou
  F04 (Proventos, deferida).

### T03 - Mutation testing do rebalance engine
Status: `Archived` 2026-07-06
Goal: Aplicar mutation testing sobre `src/omaha/rebalance/solver.py` e
`validation.py`. Solver é crítico — invariant "soma 100" e limites de
classe precisam ser exercidos além de cobertura de linha.
Candidate OpenSpec change id: `t03-mutation-testing-rebalance-engine`
Spec link: `openspec/changes/archive/2026-07-06-t03-mutation-testing-rebalance-engine/`
Files:
- `src/omaha/rebalance/solver.py`
- `src/omaha/rebalance/validation.py`
- `pyproject.toml` (`mutmut>=3.0,<4` em `[dependency-groups].dev` + 3 entries em `[tool.taskipy.tasks]`: `mutation`, `mutation-report`, `mutation-baseline` + novo bloco `[tool.mutmut]` com `source_paths` + `only_mutate` + `also_copy` + `pytest_add_cli_args` + `pytest_add_cli_args_test_selection`)
- `.gitignore` (`mutants/`)
- `scripts/mutation_report.py` (novo)
- `scripts/mutation_baseline.py` (novo)
- `.mutmut-baseline` (commitado — baseline inicial)
- `openspec/specs/rebalance-mutation-testing/spec.md` (novo — 4 ADDED requirements)
Notes: Domínio crítico — cap de 1 fatia Applying. Rodar após R03 (adapter)
se a fatia crescer. **Escopo restrito a 2 arquivos** (D-T03.3) —
`solver.py` (CVXPY LP) + `validation.py` (11 checks, "soma 100%")
são o par canônico coberto pelos unit tests
(`tests/test_rebalance_*.py` sem DB/TestClient). Outros arquivos
do pacote (`engine.py` shim + `glue.py` orchestration + `policy.py`
+ `postprocessing.py` + `builders.py`) ficam fora da primeira
baseline — extensão vira slice futura (engine/glue exigem
TestClient+DB; demais são auxiliares). Sem `fail_under` gate
(D-T03.2) — mutation score é signal, promoção a gate é owner-
separada mesmo padrão de T02 com `coverage fail_under`. Sem CI
integration (D-T03.7) — tool roda só local por enquanto (timing
proibitivo + sem cache de mutants). Tool escolhido: `mutmut3`
(D-T03.1) sobre `cosmic-ray` por footprint/curva/integração
pytest nativa; trade-off aceito: AST-based não captura mutações
de bytecode, suficiente para o domínio isolado. Primeira baseline:
**869 mutants, killed=556, survived=301, no_tests=12** (killed_share
0.649 — captured em `.mutmut-baseline` 2026-07-06).
Progress:
- Proposed: done 2026-07-06; folder
  `openspec/changes/t03-mutation-testing-rebalance-engine/`; 4
  artifacts completos (`proposal.md` 5.0K + `design.md` 7.0K com
  7 decisions D-T03.1..D-T03.7 + `tasks.md` 5.5K com 7 grupos /
  23 checkboxes + `specs/rebalance-mutation-testing/spec.md` com
  4 ADDED requirements / 12 scenarios). `openspec validate
  t03-mutation-testing-rebalance-engine --json` retorna
  `valid: true`
- Applying: done 2026-07-06; §1-§5 implementation landed —
  `pyproject.toml` ganhou dep `mutmut>=3.0,<4` no grupo dev +
  bloco `[tool.mutmut]` com `source_paths=["src"]` +
  `only_mutate=["src/omaha/rebalance/solver.py",
  "src/omaha/rebalance/validation.py"]` + `also_copy` (17
  paths: scripts/, alembic/, alembic.ini, data/seed/, prod.yml,
  docker-compose.yml, Dockerfile, nginx/, tests/scripts/,
  tests/fixtures/, tests/posicao_italo.csv) +
  `pytest_add_cli_args` (--no-cov, no cacheprovider, ignore e2e +
  bdd) + `pytest_add_cli_args_test_selection` (6 rebalance unit
  test files); `[tool.taskipy.tasks]` ganhou 3 entries
  (`mutation`, `mutation-report`, `mutation-baseline`);
  `scripts/mutation_report.py` (99 LOC — coleta `.meta` JSONs
  em `mutants/**/*.meta` recursivo, render counts + killed_share)
  + `scripts/mutation_baseline.py` (55 LOC — render baseline
  com 7 linhas incluindo UTC ISO-8601 timestamp); `.gitignore`
  ganhou `mutants/`; `uv run task lint` verde; `task test-unit`
  271 pass / 2 skip; `task test-integration` 369 pass / 2 skip;
  `task test-bdd` 51 pass; `task coverage` 92%; `openspec
  validate` retorna `valid: true`. **Decision flip (escopo
  corrigido em apply):** slice-text original mencionava
  `engine.py` + `data_bridges.py` (que não existe); o par
  canônico coberto pelos unit tests é `solver.py` +
  `validation.py`. Justificativa registrada em proposal §Impact
  e design.md §D-T03.3.
- Applied: done 2026-07-06; baseline capture executado —
  `task mutation` gerou 869 mutants em `solver.py` +
  `validation.py` (~3 min wall-clock, 5.12 mutations/sec);
  `task mutation-baseline` escreveu `.mutmut-baseline` com
  7 linhas (killed=556, survived=301, no_tests=12, timeout=0,
  skipped=0, killed_share=0.649, generated_at=2026-07-06T
  21:25:16+00:00). 301 survived mutants é sinal de test gap —
  registrado como follow-up slice (provável prefixo `R` ou `T`)
  fora do escopo do T03. 12 no_tests indica que `validation.py`
  tem algumas funções puras que nem os unit tests exercitam
  (heurística de assoc). Nenhum regressão nos baselines
  archive (`task test-unit` 271 pass, `task test-integration`
  369 pass, `task test-bdd` 51 pass, coverage 92%).
- Archived: done 2026-07-06; archive
  `openspec/changes/archive/2026-07-06-t03-mutation-testing-rebalance-engine/`;
  spec `rebalance-mutation-testing` consolidada em
  `openspec/specs/rebalance-mutation-testing/spec.md` (4 ADDED
  requirements + Purpose + drift correction: `mutants/` no lugar
  de `.mutmut-cache/` — mutmut3 não expõe `report`/`html`
  subcommands; HTML scenario substituído por "Mutant-level
  details são readable via `.meta` JSONs"). `openspec list --specs`
  agora reporta 41 specs (40 pre + 1 new). 8 specs pre-existentes
  continuam falhando (broker-csv-*, dashboard-*, import-*) —
  não relacionado a T03.

### T05 - BDD step-def drift after F02 sidebar removal
Status: `Archived` 2026-07-06
Goal: 4 BDD scenarios fail with `botão/link '+ Nova classe' não
encontrado` because the F02 sidebar (which carried that button)
was removed. The step definition `clico em "{label}"` in
`tests/bdd/step_defs/common_steps.py` matches on visible text /
data-testid / anchor — but no DOM element still carries the
label `+ Nova classe`. Production moved the affordance to two
new testids: `empty-state-create-class` (only when the profile
has zero classes) and the in-modal
`new-class-modal-submit` (after the user opens the modal).
Fix: extend the step matcher to recognise the post-F02 alias
chain (label → empty-state testid → modal submit), and update
the four affected feature files (`class_crud.feature`,
`profile_sharing.feature`) so the Gherkin reads naturally
against the new UI vocabulary.
Candidate OpenSpec change id: `t05-bdd-step-def-drift-after-f02`
Spec link: `openspec/changes/t05-bdd-step-def-drift-after-f02/`
Files:
- `tests/bdd/step_defs/common_steps.py` (matcher extension)
- `tests/bdd/features/class_crud.feature`
- `tests/bdd/features/profile_sharing.feature`
Notes: Out of T01 scope (test selector drift vs. step-def drift).
Small mechanical change. Run after the next live
`refresh-for-test` to confirm BDD suite closes at 49/49.

(Reactivation path: trivial. Move folder de volta para
`openspec/changes/t05-bdd-step-def-drift-after-f02/` e rode
`openspec validate` — slice e files são byte-equivalentes ao
estado pré-archive.)
Progress:
- Proposed: done (2026-07-06; folder
  `openspec/changes/t05-bdd-step-def-drift-after-f02/`; 4
  artifacts completos: `proposal.md` (Why + What Changes +
  new capability `bdd-step-def-aliases`) + `design.md` (4
  decisions D-T05.1..D-T05.4) + `tasks.md` (4 grupos, 15
  checkboxes) + `specs/bdd-step-def-aliases/spec.md` (1 ADDED
  requirement + 3 scenarios). `openspec validate
  t05-bdd-step-def-drift-after-f02 --json` retorna
  `valid: true`)
- Applying: done (2026-07-06; §1-§3 implementation landed —
  `STEP_CLICK_ALIASES: dict[str, tuple[str, ...]]` const added at
  the top of `tests/bdd/step_defs/common_steps.py` (above
  `click_button`) with 2 entries (F02 comment-cited): `+ Nova
  classe` → `('[data-testid="empty-state-create-class"]',
  '[data-testid="new-class-modal-submit"]')` and `+ Novo ativo` →
  `('[data-testid="dashboard-add-asset-open"]',)`; `click_button`
  body updated to consult the alias chain before the 3 default
  candidates — same two-phase visibility filter
  (`wait_for(state="visible", timeout=5000)` + `locator("visible=true")`)
  applied to each alias selector, fallthrough to default
  candidates on no-match; signature byte-identical
  `(page: Page, label: str)` verified via `inspect.signature`;
  Gherkin rewrites em 2 files: `class_crud.feature:65`
  (`clico em "+ Nova classe"` → `clico em "Nova Classe"`) +
  `profile_sharing.feature:17, 21, 37` (3 step calls no mesmo
  padrão). Sem toq em `src/omaha/**`, `static/app.css`,
  `tests/e2e/selectors.py`. Critical area cap não aplicável
  (test-tooling only).)
- Applied: done (2026-07-06; `task test-bdd` **51 passed** (vs
  baseline R04 archive 47+4 fail — fechou 100% das 4 falhas
  pre-existentes; projetado 49+2 skip, realizado 51+0 skip por
  nenhuma cenário ativo cair no fallback do
  `new-class-modal-submit`); `task test-unit` 271 pass / 2 skip
  (vs baseline R04 — sem regressão); `task test-integration` 369
  pass / 2 skip (sem regressão); `task test-e2e` 43 pass / 4 fail
  (mesmo class de pre-existing T01 chromium stalls — `test_user_journey*`
  + `test_visual_gate.py`, **sem regressão T05**: nenhum test e2e
  exercita o step `clico em`); `task lint` verde (prek hooks all
  pass); `openspec validate t05-bdd-step-def-drift-after-f02 --json`
  retorna `valid: true`; spec nova `bdd-step-def-aliases`
  consolidada em `openspec/specs/bdd-step-def-aliases/spec.md`
  (Purpose + 1 requirement + 3 scenarios); `openspec validate
  bdd-step-def-aliases --json` retorna `valid: true`;
  `openspec list --specs` mostra `bdd-step-def-aliases
  requirements 1` (1 spec nova, 0 regressão).)
- Archived: done (2026-07-06; folder `openspec/changes/t05-bdd-step-def-drift-after-f02/` → `openspec/changes/archive/2026-07-06-t05-bdd-step-def-drift-after-f02/`; spec `bdd-step-def-aliases` já consolidada em `openspec/specs/bdd-step-def-aliases/spec.md` antes do archive — delta file vs. main spec byte-identical confirmado via `diff`; nenhum sync adicional necessário; `openspec validate bdd-step-def-aliases --json` `valid: true`; 15/15 tasks marcadas; 0 incomplete artifacts)

### I01 - Agendamento automático de backup
Status: `Archived` (archive gate done 2026-07-06 — `next` call; sync + move + spec gate passed)
Goal: `task backup` existe (`scripts/backup.py` → SQLite snapshot em
`./backups/`); nenhum timer está cabeado. Adicionar timer systemd ou
cron para execução periódica no host.
Candidate OpenSpec change id: `i01-automatic-backup-scheduling`
Spec link: `openspec/changes/archive/2026-07-06-i01-automatic-backup-scheduling/`
Files:
- `prod.yml` (serviço de backup)
- `scripts/backup.py`
- `README.md` (seção de operação)
Notes: Em Docker compose, equivalente a um serviço `backup` com schedule.
PRD §3.4 lista modos; este slice adiciona o modo "scheduled".
Progress:
- Proposed: done (2026-07-06; folder + proposal.md + design.md + tasks.md + spec delta; `openspec validate` `valid: true`)
- Applying: done (2026-07-06; §1-§5 implementation landed — `scripts/backup_scheduler.py` (~125 LOC, loop infinito com `BACKUP_INTERVAL`/`BACKUP_DEST_DIR` env override + FATAL validation + ISO-8601 UTC log prefix + failure-tolerant wrapper) + `prod.yml` ganha serviço `backup-scheduler` (~45 LOC: image `omaha:prod`, `restart: unless-stopped`, no profile, `BACKUP_INTERVAL: ${BACKUP_INTERVAL:-86400}`, `command: python -m scripts.backup_scheduler`, `omaha-data:/app/data:ro` + `./backups:/backups` mounts, comment block com D-I01.1/4/5) + README.md "Backup & restore" ganha "Scheduled backups (default in prod)" subseção com tail/stop/override commands + nota de retenção; header comment block do prod.yml reescrito de "Three services" para "Four services" + Usage block estendido com `logs -f backup-scheduler` e `stop backup-scheduler`. Decision-flip em apply: tasks 1.4 → 3.1 originalmente previam "command = backup one-shot" como placeholder → rewire para scheduler; implementei com `command = scripts.backup_scheduler` direto no §1 (sem placeholder) — diff mínimo, mesma spec coverage, comportamento equivalente. Adicionei `BACKUP_DEST_DIR` env override (não estava no proposal) para permitir smoke test local apontando para `./backups/` sem root — decisão registrada em smoke test §5.1.)
- Applied: done (2026-07-06; `task lint` verde (prek + ruff format/check); `openspec validate i01-automatic-backup-scheduling --json` `valid: true`; `docker compose -f prod.yml config --quiet` exit 0 (substitui tarefa 5.3 — não precisa `--dry-run`); `task test-unit` 271 pass / 2 skip (sem regressão vs baseline T05); `task test-integration` 369 pass / 2 skip (sem regressão vs baseline R04; `test_dockerfile.py` continua verde — `prod.yml` ainda tem `web`+`nginx`+`backup` + novo `backup-scheduler`, profiles preservados); smoke test local 5.1 (`BACKUP_INTERVAL=5 BACKUP_DEST_DIR=./backups`): 4 backups criados a 5s interval, todos 172KB SQLite válido; smoke test local 5.2 (`BACKUP_INTERVAL=3 BACKUP_DEST_DIR=/nonexistent-dir-x9q`): 5 ERROR log lines consecutivos, container não exit (matado por SIGINT após 5 falhas); FATAL validation 2.4: `BACKUP_INTERVAL=abc`/`-5`/`0`/`""` todos exit 2 com mensagem clara. **Caveat**: `Dockerfile` NÃO copia `scripts/` para `omaha:prod` — pré-existing gap que afeta tanto o serviço `backup` (one-shot, profile-gated) quanto o novo `backup-scheduler`. Em produção ambos falham com `ModuleNotFoundError: No module named 'scripts'`. D-I01.2 ("reuse verbatim") mantém consistência com o bug latente; fix = `COPY scripts ./scripts` no Dockerfile = slice separada (fora do escopo I01, registrado como follow-up).)
- Archived: done (2026-07-06; spec delta synced → `openspec/specs/backup-scheduling/spec.md` (Purpose + 6 ADDED requirements, 12 scenarios, `openspec validate backup-scheduling --json` `valid: true`); `mv openspec/changes/i01-automatic-backup-scheduling/ openspec/changes/archive/2026-07-06-i01-automatic-backup-scheduling/`; `openspec validate i01-automatic-backup-scheduling --json` `valid: true` pós-archive; `openspec list --specs` agora inclui `backup-scheduling` (40 → 41))

### I02 - Automação de renovação do cert TLS
Status: `Archived`
Goal: `nginx/` já está configurado com certbot; renovação ainda é manual.
Cabar `--deploy-hook` para que `certbot renew` rode unattended e recarregue
nginx.
Candidate OpenSpec change id: `i02-tls-cert-renewal-automation`
Spec link: `openspec/changes/archive/2026-07-07-i02-tls-cert-renewal-automation/`
Files:
- `prod.yml` (novo serviço `certbot` + nginx ganha mount `./certs/webroot:/var/www/certbot:ro` + header comment block reescrito de "Four services" para "Five services" + Usage block estendido)
- `scripts/certbot_loop.sh` (novo — bash wrapper: loop infinito `certbot renew --deploy-hook "..."`, validar `CERTBOT_RENEW_INTERVAL` + `CERTBOT_DOMAIN` + `CERTBOT_EMAIL` fail-fast, log ISO-8601 UTC, failure-tolerant)
- `certs/webroot/.gitkeep` (novo — bind mount precisa de diretório mesmo vazio)
- `.gitignore` (whitelist `certs/webroot/` + `certs/webroot/.gitkeep` ao lado do `certs/.gitkeep` existente)
- `README.md` (nova seção "TLS renewal" com runbook de bootstrap + scheduler behaviour + filesystem layout; pequeno tweak no parágrafo "Production deploy" para cross-ref a nova seção)
Notes: Depende de I01 apenas se ambos usarem timer compartilhado. Sem
deps obrigatórias entre si.
Progress:
- Proposed: done (2026-07-06; folder + proposal.md + design.md + tasks.md + spec delta; `openspec validate` `valid: true`)
- Applying: done 2026-07-06; §1-§6 implementation landed — `prod.yml` ganha serviço `certbot` (image `certbot/certbot:latest`, `entrypoint: []`, `restart: unless-stopped`, envs `${CERTBOT_RENEW_INTERVAL:-43200}` + `${CERTBOT_DOMAIN:?…}` + `${CERTBOT_EMAIL:?…}`, `command: /bin/bash /scripts/certbot_loop.sh`, 5 mounts: `./certs:/etc/letsencrypt` rw + `./certs/webroot:/var/www/certbot:ro` + `./prod.yml:/app/prod.yml:ro` + `./scripts/certbot_loop.sh:/scripts/certbot_loop.sh:ro` + `/var/run/docker.sock:/var/run/docker.sock:ro`; nginx ganha mount `./certs/webroot:/var/www/certbot:ro`; comment block do header reescrito de "Four services" para "Five services" com 5ª sub-bullet documentando o certbot) + `scripts/certbot_loop.sh` novo (107 LOC bash: log helper, valida interval — fail-fast exit 2 em non-int/non-positive, valida CERTBOT_DOMAIN e CERTBOT_EMAIL via `${VAR:?…}`, constrói `DEPLOY_HOOK` interpolando `CERTBOT_DOMAIN` em três `cp` + `docker compose -f /app/prod.yml exec -T nginx nginx -s reload` — `--deploy-hook` só corre quando o cert foi mesmo renovado; loop infinito com `sleep "$CERTBOT_RENEW_INTERVAL"` após cada run; logs timestamped `ISO-8601 UTC + level + message`; captura exit code via `set +e; certbot renew …; rc=$?; set -e` + log OK/ERROR sem matar o loop) + `certs/webroot/` criado + `certs/webroot/.gitkeep` empty file + `.gitignore` ganha `!certs/webroot/` + `!certs/webroot/.gitkeep` whitelist (preserva `certs/*` ignore; só `certs/.gitkeep` continua na whitelist original) + README §TLS renewal com 4 sub-seções (First-time setup com 6 passos numerados incluindo `mkdir -p ./certs/webroot` + one-shot certonly + cp manual na primeira vez + reload; Scheduler behaviour com `docker compose logs -f certbot` + override interval + stop/start; Filesystem layout com árvore `.git` + bind-mount map)
- Applied: done 2026-07-06; §6 spec gate + lint + tests — `openspec validate i02-tls-cert-renewal-automation --json` `valid: true`; `docker compose -f prod.yml config --quiet` exit 0 (com `CERTBOT_DOMAIN` + `CERTBOT_EMAIL` exportados; sem eles, falha-fast conforme design — `${CERTBOT_DOMAIN:?CERTBOT_DOMAIN must be set in the environment}` enforced pelo compose antes do container subir); `task lint` verde (prek check-merge-conflict + check-yaml + check-toml + check-json + check-added-large-files + pytest-unit stub + detect-private-key + validate-pyproject + detect-hardcoded-secrets); `task test-unit` 271 pass / 2 skip (R02/R04 baseline match; sem regressão — zero `src/omaha/**` tocado); `task test-integration` 369 pass / 2 skip (R02/R03/R04 baseline match; warning `Solution may be inaccurate` em `solver.py:511` é pré-existente, fora do escopo I02). 6.2 (sync + archive) deferred to next manual `next` → archive gate.
- Archived: done 2026-07-07; `openspec archive i02-tls-cert-renewal-automation --yes` moveu folder para `openspec/changes/archive/2026-07-07-i02-tls-cert-renewal-automation/` e sincronizou delta → `openspec/specs/tls-cert-renewal/spec.md` (7 ADDED requirements: scheduled certbot renew + deploy hook reloads nginx + interval configurable + failed renewal does not stop scheduler + certbot container has write access to certificate directory + ACME http-01 challenge webroot shared + certbot service can be disabled without affecting other services; 14 scenarios totais); `openspec validate tls-cert-renewal --json` `valid: true`; `openspec validate --specs` confirma só as 8 falhas pre-existentes (broker-csv-*, dashboard-*, import-*) sem regressão; `openspec list --specs` 43 → 44 specs.

### D01 - Refresh do README
Status: `Archived`
Goal: Atualizar README para refletir a surface atual. Em particular a
seção "Network access" (PRD §4.2) e o bloco de features (já fechado após
F01-F05). Garantir `bash scripts/print_lan_url.sh` referenciado.
Candidate OpenSpec change id: `d01-refresh-readme`
Spec link: `openspec/changes/archive/2026-07-07-d01-refresh-readme/`
Files:
- `README.md`
Notes: Doc-only — sem teste runtime, sem `src/omaha/`. Rodar por último
para refletir o estado pós-F-slice.
Progress:
- Proposed: done (2026-07-06; folder + proposal.md + design.md + tasks.md + spec delta; `openspec validate` `valid: true`)
- Applying: done 2026-07-07; 8-section rewrite landed — intro rewritten (Família aggregate, dark warm-neutral palette, 4-tab nav `/patrimonio`+`/rebalanceamento`+`/rentabilidade`+`/proventos`, M002 deferral removed, quotes + rebalancing shipped) + Quick start promotes `task serve` as canonical (raw `uvicorn` form shown as equivalent) + adds `task db-migrate`/`db-seed`/`db-reset` blocks with current baseline (italo=6/48/47, ana=6/52/52) + Dev tasks table expanded from 30 → 46 rows (added `test-bdd`, `test-integration`, `mutation`, `mutation-report`, `mutation-baseline`, `db-seed-from-csv`, `db-seed-diff`, `db-seed-upsert`, `db-clear-assets`, `prek-install`; tightened descriptions of `test-unit`/`test`/`coverage`/`db-snapshot`) + Production deploy §3 manual certbot block removed, replaced by cross-reference to **Operação / TLS renewal** (added by I02) + Backup section verified (host-cron block already gone per I01; scheduler section already cross-references the I01-owned path; Restore subsection kept verbatim) + Testing the app URL flipped to `/patrimonio`, sidebar Importar CSV instruction replaced by patrimonio-body buttons, profile-switcher lists `Italo` / `Ana` / `Família` (read-only aggregate), `db-snapshot` expected output updated to current ana counts (52/52), Patrimonio empty-state copy for Ana + Família clarified + Project layout tree fully rewritten (templates: `patrimonio.html` + six `_patrimonio_*.html` partials from R04, dropped `dashboard.html`/`_sidebar.html`; new top-level dirs: `nginx/`, `openspec/`, `prod.yml`; new `src/omaha/` subdirs `audit/`, `quotes/`, `rebalance/` + new files `logging_config.py`, `middleware.py`, `validators.py`; `scripts/dev_reset.py` (stale) replaced by `scripts/seed_from_csv/` package + `reset_both_profiles.py` + the new backup/certbot/mutation scripts) + Project specs section rewritten (`.gsd/` bullet list dropped — `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`, `DECISIONS.md`, `KNOWLEDGE.md`, `milestones/M001/slices/`; replaced by `openspec/` list: `PRD.md` (10 standing rules §4), `roadmap.md` (F/R/T/D/I slice register), `specs/<capability>/` (44 stable contracts), `changes/<change-id>/` (1:1 slice mapping) + one-line pointer to `AGENTS.md` for agent routing table).
- Applied: done (8.1 `openspec validate d01-refresh-readme --json` `valid: true`; 8.3 `task lint` green — prek checks all pass; 8.4 `bash scripts/print_lan_url.sh` → `http://192.168.1.6:8000`; `openspec validate --specs` 36 pass / 8 fail — same 8 pre-existing failures from I02 archive (broker-csv-*, dashboard-*, import-*) — no D01 regression; 8.2 deferred — spec lived in delta until archive sync)
- Archived: done 2026-07-07; `openspec archive d01-refresh-readme --yes` moveu folder para `openspec/changes/archive/2026-07-07-d01-refresh-readme/` e sincronizou delta → `openspec/specs/readme-freshness/spec.md` (6 ADDED requirements — sem MODIFIED/REMOVED — sobre freshness do README refletindo a surface atual); `openspec validate readme-freshness --json` `valid: true`; `openspec validate --specs` 37 pass / 8 fail (sem regressão — mesmas 8 falhas pré-existentes); `openspec list --specs` agora inclui `readme-freshness`. Caveat pré-existente preservado: warning non-blocking em `proposal.md` ("Why section should not exceed 1000 characters") é noise estilístico, não bloqueia gate.

### D02 - Decisão de register do design system (Status Invest inspired)
Status: `Archived` 2026-07-07
Goal: Owner decide entre A (Status Invest puro fintech-pro), B (híbrido
estrutura SI + warmth Omaha), C (Moleskine+ caderno com dados vivos), D
(outra referência que owner traz). Saída é um documento de direção:
PRD §4.10 vira memorial descritivo (não prescritivo) e DESIGN.md
§Color strategy + §Typography + §Component inventory refletem o register
escolhido. Sem implementação de código — só decisão + atualização
documental. Gate absoluto de F08+.
Candidate OpenSpec change id: `d02-design-register-decision`
Spec link: `openspec/changes/archive/2026-07-07-d02-design-register-decision/`
Files:
- `openspec/PRD.md` (§4.10 reescrita como memorial + §5.3 marcada)
- `DESIGN.md` (§Color strategy + §Typography + §Component inventory
  reescritos per register escolhido)
- `openspec/.temp_assets/design-system-redesign-session-2026-07-06.md`
  (sessão exploratória que alimenta a decisão; contém matriz
  Roubar/Rejeitar/Reframear, opções A/B/C/D com mockups ASCII, 4
  bugs concretos, 7 gates abertos)
Notes: Doc-only — sem teste runtime, sem `src/omaha/`. **Gates
resolvidos 2026-07-07**: (1) register = **SI maximal, sidebar NÃO**;
(2) class-3 hue = **350 magenta-red**; (3) display face = **Red Hat
Display**; (4) sidebar = **NÃO**; (5) light/dark toggle = **NÃO**;
(6) body warmth = **hue 60 mantém**; (7) escopo = **3 fatias
(F08+F09+F10)** + 2 conditionals (F12 icons yes; F11/F13 blocked).
Section dividers hairline + eyebrow labels + compare bar + portfolio
hero refinement + tabelas sticky/hover/total-row + rebalance warnings
border-left + form R$ prefix todos INCLUSOS (per gate 1 maximal, sem
sidebar). F11 Blocked (register ≠ A); F12 unblock (icons yes per
register); F13 Blocked (owner não pediu). Sessão exploratória em
temp file.

**Apply landed 2026-07-07** — PRD §4.10 reescrita como memorial
descritivo do register (sem prescrever tokens; tokens vivem em
DESIGN.md); PRD §5.3 ganhou bullet "Gate D02 resolvido" listando
F08-F10+F12 unblocked + F11/F13 effectively blocked; DESIGN.md §Register
atualizado para "Status Invest maximal, sidebar não reintroduzida";
DESIGN.md §Color strategy ganhou subseção "Target register (D02) — to
materialize in F08" com diretrizes (emerald accent 0.68/0.20/152, fern
positive 0.79/0.19/145, coral negative 0.69/0.20/25, class-3 magenta-red
hue 350, warning amber 0.78/0.16/75, surface hue 60 mantida, 4 bugs a
resolver); DESIGN.md §Typography reescrita (Inter variable body + Red
Hat Display 700+ display; feature-settings `tnum, cv01, ss01, ss02`;
scale com display Red Hat 700); DESIGN.md §Iconography reescrita
("Material Symbols Outlined, scoped" com catalog de 10 icons: add,
add_circle, upload, logout, close, warning, expand_more, expand_less,
check_circle, help); DESIGN.md §Anti-patterns ganhou 3 entries
(reintroduzir sidebar, adicionar light/dark toggle, estado implícito
silencioso, action column sempre visível) + excȩção warning border-left
4px; DESIGN.md §Migration path ganhou D02 row listando F08-F10+F12 que
materializam as decisões; DESIGN.md §Components (initial inventory)
ganhou vocabulário 5-state feedback (idle/hover/focus/disabled/error)
+ 4 extras (sticky `<thead>`, hover row bg lift, total row emphasis,
action column só-on-hover) + 6 extras (section dividers, ::selection,
form autofill override, eyebrow labels, compare bar 3 fills, form R$
prefix, warning border-left 4px allow). Zero runtime code tocado.
Sessão exploratória permanece em `openspec/.temp_assets/
design-system-redesign-session-2026-07-06.md`.

Progress:
- Proposed: done 2026-07-07 (change folder
  `openspec/changes/d02-design-register-decision/`; 4 artifacts
  completos: `proposal.md` (Why + 7 gates resolved + Impact sobre
  PRD + DESIGN) + `design.md` (5 decisions D-D02.1..D-D02.5) +
  `tasks.md` (5 grupos, 22 checkboxes) + `specs/design-register-
  decision/spec.md` (2 ADDED requirements: memorialize register in
  PRD/DESIGN + D02 unblocks F08/F09/F10/F12; 7 scenarios total).
  `openspec validate d02-design-register-decision --json` retorna
  `valid: true`. Mudança entra no roadmap como D02 — gate absoluto
  da frente visual registrado no slice.)
- Applying: done 2026-07-07 (doc-only apply: 22/22 tasks
  marcadas; PRD §4.10 + §5.3 + DESIGN.md §Register + §Color
  strategy + §Typography + §Scale + §Iconography + §Components
  inventory + §Anti-patterns + §Migration path atualizadas;
  zero código runtime tocado; zero testes a rodar; zero
  `refresh-for-test` necessário — registry é doc-only).
- Applied: done 2026-07-07 (gate 5: `openspec validate d02-
  design-register-decision --json` continua `valid: true`; nenhuma
  spec runtime regrediu — 8 specs pré-existentes continuam
  falhando (broker-csv-*, dashboard-*, import-*) — não relacionado
  a D02; `task lint` verde — prek check-merge-conflict +
  check-yaml + check-toml + check-json + check-added-large-files +
  pytest-unit stub + detect-private-key + validate-pyproject +
  detect-hardcoded-secrets todos passam; nenhuma test-suite
  rodada necessária porque D02 não toca `src/omaha/**`).
- Archived: done 2026-07-07; `mv openspec/changes/d02-design-
  register-decision/ → openspec/changes/archive/2026-07-07-d02-
  design-register-decision/`; spec delta synced via pré-sync
  para `openspec/specs/design-register-decision/spec.md`
  (Purpose section adicionada — doc-only register memorial com
  descrição do register escolhido + papel de gate da frente
  visual; `## ADDED Requirements` da delta promovido para
  `## Requirements` da spec canônica; 2 requirements + 7
  scenarios totais: PRD §4.10 memorial + DESIGN.md sections
  + PRD §5.3 gate marker + D02 unblocks F08/F09/F10/F12 +
  F11/F13 remain blocked). `openspec validate
  design-register-decision --json` retorna `valid: true`
  pós-archive sync; `openspec list --specs` agora reporta 46
  specs (45 pre + 1 new `design-register-decision`); `task lint`
  verde; 8 specs pré-existentes continuam falhando
  (broker-csv-*, dashboard-*, import-*) — não relacionado a D02.
  Consequências: F08 + F09 + F10 + F12 passam de "Ready (gate
  D02)" para Ready puro (gate atendido) — próximos `next` calls
  podem propor essas fatias; F11 + F13 promoted a Blocked
  formal (sidebar reintroduce e light/dark toggle incompatíveis
  com register SI maximal sem sidebar e dark-only respectivamente).

### F08 - Palette overhaul v2 (apply D02 decision)
Status: `Archived` (2026-07-07; **proposal-only — no implementation**)
Goal: Aplica novos tokens per register escolhido em D02. Resolve 4 bugs
identificados na sessão 2026-07-06: (1) colisão `--class-3` vs
`--negative` (ambos hue 25, chroma 0.18 — classe vermelha e loss
number são indistinguíveis); (2) `--positive` sem punch (L 0.70 →
0.74-0.78 para "data signal" legível em body escuro); (3) `_CLASS_COLORS`
Python hex drift vs CSS OKLCH (swatch usa inline hex, CSS tem token
OKLCH paralelo, dois sistemas); (4) `--accent` vs `--positive`
ambiguidade cromática (hue gap 5° + chroma invertido — verde de marca
vs verde de ganho indistinguíveis). Adiciona `--bg-secondary` se 3-tier
surface escolhido em D02. Re-deriva tokens em `app.css :root`,
sincroniza `_CLASS_COLORS` em `routes/pages.py`, atualiza
`tests/test_dark_mode_tokens.py`, sincroniza spec `color-tokens`.
Candidate OpenSpec change id: `f08-palette-overhaul-v2`
Spec link: `openspec/changes/archive/2026-07-07-f08-palette-overhaul-v2/`
Files:
- `src/omaha/static/app.css` (:root tokens re-derivados + possível
  adição `--bg-secondary` + `--class-N-tint`)
- `src/omaha/routes/pages.py` (`_CLASS_COLORS` tuple alinhada com
  tokens OKLCH — substituir hex por `oklch(...)` strings)
- `tests/test_dark_mode_tokens.py` (atualizar pares WCAG + adicionar
  asserts pros novos tokens)
- `openspec/specs/color-tokens/spec.md` (delta MODIFIED — pares
  re-derivados per register escolhido)
Notes: **D02 archived 2026-07-07** — gate resolvido; pode propor
via `next` agora. Depende da direção D02 memorializada em PRD §4.10
+ DESIGN.md. Pode coexistir com F09 e F10 em Applying (cap 2
global). Critical-area = visual surface = cap 1 Applying (dentro do
domínio visual, F08 é a slice fundamental). Re-derivar tokens preserva
invariantes da spec (hue family warmth preservado, AA contrast em
todos os pares). **Alvos do D02** a materializar: emerald accent
`0.68 0.20 152`, fern positive `0.79 0.19 145`, coral negative
`0.69 0.20 25`, warning amber `0.78 0.16 75`, class-3 hue 350
magenta-red (resolve colisão com `--negative`), `--positive`
lightness-lifted (data signal legível em dark). 4 bugs pré-D02 a
resolver: (1) colisão `--class-3` vs `--negative`; (2) `--positive`
sem punch; (3) `_CLASS_COLORS` Python hex drift vs CSS OKLCH; (4)
`--accent` vs `--positive` ambiguidade cromática. `--bg-secondary`
se 3-tier surface escolhido (default mantém 2-tier).
Progress:
- Proposed: done 2026-07-07 (folder
  `openspec/changes/f08-palette-overhaul-v2/`; 4 artifacts
  completos: `proposal.md` (4 bugs do polish pass + D02 targets +
  Impact sobre CSS/Python tuple/tests/DESIGN/spec) + `design.md`
  (Context + Goals/Non-Goals + 8 decisions D-F08.1..D-F08.8 +
  Risks/Trade-offs + Migration Plan + Open Questions) + `tasks.md`
  (7 grupos, 38 checkboxes: CSS token re-derivação + Python tuple
  alignment + test extension + spec sync + DESIGN.md sync + render
  verification + archive) + `specs/color-tokens/spec.md` delta
  (MODIFIED × 3 — bodies + scenarios estendidos com 4 invariantes
  de ambiguidade: hue gap ≥320° class-3 vs negative + positive L
  ≥ 0.74 + lightness-positive > lightness-accent + Python-vs-CSS
  parity assertion + hue gap accent/positive ≥ 6°).
  `openspec validate f08-palette-overhaul-v2 --json` retorna
  `valid: true`. `openspec validate --specs` reporta 38 pass / 8
  fail — mesmas 8 falhas pré-existentes (broker-csv-*, dashboard-*,
  import-*) sem regressão F08.
- Applying: **skipped** 2026-07-07 (owner pediu sync + archive
  sem apply — proposta preservada como registro dos D02
  materialization targets; implementação fica para futura
  retomada. Reactivation path: `start f08` abre novo OpenSpec
  change reaproveitando este proposal + design + tasks intactos;
  ou `openspec-apply-change` contra o folder arquivado se owner
  decidir reativar via restore. 0/38 tasks marcadas no apply;
  tasks.md preservado como blueprint da implementação futura.)
- Applied: **skipped** (proposal-only archive; nenhum código
  tocado — `src/omaha/static/app.css` mantém tokens F05;
  `_CLASS_COLORS` em `routes/pages.py` + `audit/inventory.py`
  mantém hex literals pré-F08; `tests/test_dark_mode_tokens.py`
  inalterado)
- Archived: done 2026-07-07 (folder movido para
  `archive/2026-07-07-f08-palette-overhaul-v2/`; spec delta
  sincronizada manualmente pre-archive via sync-specs —
  `openspec/specs/color-tokens/spec.md` agora descreve invariantes
  post-F08 com 3 requirements + 12 scenarios + Purpose real
  substituindo TBD; `openspec validate color-tokens --json` retorna
  `valid: true` com 1 INFO não-bloqueante sobre requirement text
  length). `openspec archive --yes --skip-specs` usado — flag
  justificada porque sync foi feito manualmente antes do archive
  command. `openspec validate --specs` continua 38 pass / 8 fail
  pré-existentes sem regressão F08.

### F09 - Typography refresh (display face + Inter feature-settings)
Status: `Archived` (archive gate landed 2026-07-07;
`openspec/changes/archive/2026-07-07-f09-typography-refresh/`; spec
delta synced to `openspec/specs/typography-tokens/spec.md` with
Purpose + 5 ADDED requirements, 11 scenarios; `openspec validate
typography-tokens --json` retorna `valid: true` (1 INFO
non-blocking sobre requirement text length); `openspec validate
--specs` agora reporta 47 total (46 pre + 1 new `typography-tokens`),
39 pass / 8 fail — mesmas 8 falhas pré-existentes sem regressão).
Goal: Implementar escolha de display face de D02. Candidatos:
Source Serif 4 (atual serif), Red Hat Display (sans Status Invest),
IBM Plex Sans (character sans), Fraunces (optical sizing serif, mais
"voz"). Adicionar Inter feature-settings completos: `tnum` (já tem)
+ `cv01` (1 com base serif), `ss01` (open digits 6/9), `ss02`
(zero/O disambiguation). Atualizar font loading em `base.html`.
Validar display face com `tnum` em portfolio header (serif pode ter
tnum fraco — testar antes). Atualizar DESIGN.md §Typography +
§Component inventory.
Candidate OpenSpec change id: `f09-typography-refresh`
Spec link: `openspec/changes/f09-typography-refresh/`
Files:
- `src/omaha/templates/base.html` (Google Fonts URL estendido com
  Inter variable + display face escolhido)
- `src/omaha/static/app.css` (font-family chain atualizada +
  feature-settings `tnum, cv01, ss01, ss02` em `body`)
- `DESIGN.md` (§Typography reescrita per face escolhido)
- `tests/test_typography_tokens.py` (novo, unit — 8 assertions per
  D-F09.8)
- `tests/conftest.py` (`_UNIT_FILES` estendido com o test file novo —
  per PRD §4.6 explicit allow-list)
Notes: **D02 archived 2026-07-07** — gate resolvido (display face =
**Red Hat Display** 700+; sans, não serif). Pode propor via `next`
agora. Independente de F08 (paleta) e F10 (componentes) — pode
rodar em paralelo (cap 2). Implementa Red Hat Display 700+ em
`.portfolio-stat-value` (e otras hero numerals) + Inter variable body
com feature-settings `tnum, cv01, ss01, ss02`. Remove Source Serif 4
do plano anterior (D02 §Gate 3 = sem serif). Validação pré-apply: tnum
em Red Hat Display é default — verificar se mantém tabular figures em
700+ (testar render antes de shipping; se fraco, abrir `font-feature-
settings: "tnum"` no seletor). Self-host vs Google Fonts é decisão de
implementação — Google Fonts é default (mesmo padrão atual). Custo
1-2h.
Progress:
- Proposed: done 2026-07-07
- Applying: done 2026-07-07 (32/32 tasks; `task lint` verde;
  `task test-unit` 284 pass / 2 skip (+13 novos: 8 unique + 3
  parametrized retired-family cases + 5 parametrized display-selector
  cases); `task test-integration` 369 pass / 2 skip sem regressão;
  `task test-bdd` 51 pass sem regressão; `openspec validate
  f09-typography-refresh --json` `valid: true`; `openspec validate
  --specs` continua 38 pass / 8 fail sem regressão; refresh-for-test
  smoke OK: `/healthz` ok, `db-reset` italo=6/48/47 ana=6/52/52,
  Italo+Ana+Família views renderizam, `/static/app.css` servido
  contém 9× Red Hat Display / 0× Source Serif 4 / 0× IBM Plex Serif
  / 0× Georgia, body `font-feature-settings: "tnum", "cv01", "ss01",
  "ss02"` confirmado, `.portfolio-stat-value` agora
  `font-family: "Red Hat Display", "Inter", ...; font-weight: 700;`)
- Applied: done 2026-07-07 — **post-apply bug fix same day**: a
  duplicate `.portfolio-stat-value { font-size: 1.4rem; font-weight:
  600; color: var(--fg); font-feature-settings: "tnum"; letter-spacing:
  -0.01em; }` rule further down `app.css` (line 989, before fix)
  silently overrode the Red Hat Display + 700 declarations from the
  base rule at line 167 via CSS cascade (last rule wins). User
  flagged "font still looks like Inter" in browser — investigation
  found the duplicate. Fix: consolidated the two rule bodies into one
  at the line 167 location (with all properties), deleted the bare
  line 989 duplicate. Test `test_red_hat_display_on_display_selector`
  strengthened to use `re.findall` over every rule body targeting the
  selector (was using `re.search` first-match-only — would have
  passed green while the page rendered Inter). Re-verified: served
  `/static/app.css` has exactly 1 base `.portfolio-stat-value` rule
  + 3 color-only variants; `task test-unit` 284 pass / 2 skip
  unchanged; hard refresh in browser should now show Red Hat Display
  on `.portfolio-stat-value`. Headless chromium smoke 2026-07-07
  (`/tmp/f09-smoke.py`) confirma computed style live: 3 selectors
  visíveis em `/patrimonio` (`.portfolio-stat-value`,
  `.app-header-wordmark`, `.tab-nav__btn--active`) renderizam
  `"Red Hat Display", Inter, -apple-system, ... sans-serif` /
  `font-weight: 700`; 2 condicionais (`.empty-state-step-number`,
  `.rebalance-stat-value`) só renderizam em empty-state / após
  submeter `/rebalanceamento`, mas CSS rule está correta em ambos.
- Archived: done 2026-07-07; archive
  `2026-07-07-f09-typography-refresh/`; spec delta synced →
  `openspec/specs/typography-tokens/spec.md` (Purpose + 5
  Requirements: display face / Inter body feature-settings / Google
  Fonts URL single source / no serif in display chain /
  base.html + app.css pair synchronization; 11 scenarios — requisitos
  corrigidos para 5 seletores implementados vs 6 originalmente
  listados no delta; `.profile-name` e `.patrimonio-section-title`
  não existem no CSS atual — references ajustadas para os 5
  seletores reais: `.portfolio-stat-value`, `.app-header-wordmark`,
  `.empty-state-step-number`, `.rebalance-stat-value`,
  `.tab-nav__btn--active`). `openspec validate typography-tokens`
  `valid: true` (1 INFO non-blocking sobre requirement text length);
  `openspec list --specs` agora reporta 47 specs (46 pre + 1 new
  `typography-tokens`); 8 specs pré-existentes continuam falhando
  (broker-csv-*, dashboard-*, import-*) — não relacionado a F09.
Goal: Implementar escolha de display face de D02. Candidatos:
Source Serif 4 (atual serif), Red Hat Display (sans Status Invest),
IBM Plex Sans (character sans), Fraunces (optical sizing serif, mais
"voz"). Adicionar Inter feature-settings completos: `tnum` (já tem)
+ `cv01` (1 com base serif), `ss01` (open digits 6/9), `ss02`
(zero/O disambiguation). Atualizar font loading em `base.html`.
Validar display face com `tnum` em portfolio header (serif pode ter
tnum fraco — testar antes). Atualizar DESIGN.md §Typography +
§Component inventory.
Candidate OpenSpec change id: `f09-typography-refresh`
Spec link: `openspec/changes/f09-typography-refresh/`
Files:
- `src/omaha/templates/base.html` (Google Fonts URL estendido com
  Inter variable + display face escolhido)
- `src/omaha/static/app.css` (font-family chain atualizada +
  feature-settings `tnum, cv01, ss01, ss02` em `body`)
- `DESIGN.md` (§Typography reescrita per face escolhido)
- `tests/test_typography_tokens.py` (novo, unit — 8 assertions per
  D-F09.8)
- `tests/conftest.py` (`_UNIT_FILES` estendido com o test file novo —
  per PRD §4.6 explicit allow-list)
Notes: **D02 archived 2026-07-07** — gate resolvido (display face =
**Red Hat Display** 700+; sans, não serif). Pode propor via `next`
agora. Independente de F08 (paleta) e F10 (componentes) — pode
rodar em paralelo (cap 2). Implementa Red Hat Display 700+ em
`.portfolio-stat-value` (e otras hero numerals) + Inter variable body
com feature-settings `tnum, cv01, ss01, ss02`. Remove Source Serif 4
do plano anterior (D02 §Gate 3 = sem serif). Validação pré-apply: tnum
em Red Hat Display é default — verificar se mantém tabular figures em
700+ (testar render antes de shipping; se fraco, abrir `font-feature-
settings: "tnum"` no seletor). Self-host vs Google Fonts é decisão de
implementação — Google Fonts é default (mesmo padrão atual). Custo
1-2h.
Progress:
- Proposed: done 2026-07-07

### F10 - Component state language (5-state) + data table pattern upgrade
Status: `Archived`
Goal: Implementar vocabulário completo de 5 estados (idle/hover/focus/
disabled/error) em inputs, buttons, tabs, table rows. Implementar
data table pattern upgrade: sticky headers, hover row bg lift, total
row emphasis, action column só-on-hover. Adicionar section dividers
hairline entre blocos. Adicionar selection color (`::selection` em
`--accent`). Adicionar form autofill override. Polish barato, alto
impacto. Aplicar em 10 templates: base, login, patrimonio (+4
partials), classes, assets, rebalance (+2 partials), import +
import_review, rentabilidade (F03 deferred — só se retomado), proventos
(F04 deferred).
Candidate OpenSpec change id: `f10-component-state-language-and-table-pattern`
Spec link: `openspec/changes/f10-component-state-language-and-table-pattern/` (criada no propose)
Files:
- `src/omaha/static/app.css` (estados de 8 elementos + sticky
  `.class-table thead` + `.asset-table thead` + hover row + total
  row + dividers + `::selection` + `:-webkit-autofill` override)
- `src/omaha/templates/base.html` (tab states idle/hover/focus)
- `src/omaha/templates/login.html` (input states)
- `src/omaha/templates/patrimonio.html` + 4 partials
  (`_patrimonio_actions`, `_patrimonio_portfolio_header`,
  `_patrimonio_class_section`, `_patrimonio_distribution`)
- `src/omaha/templates/classes.html` (class table)
- `src/omaha/templates/assets.html` (asset editor rows)
- `src/omaha/templates/rebalance.html` + 2 partials (`_rebalance_plan`,
  `_rebalance_placeholder`)
- `src/omaha/templates/import.html` + `import_review.html`
- `DESIGN.md` (§Component inventory + §Anti-patterns atualizado —
  adicionar tabela de state feedback vocabulary)
Notes: **D02 archived 2026-07-07** — gate resolvido (SI maximal =
5-state vocabulary + table pattern upgrade INCLUÍDO). Pode propor
via `next` agora. Independente de F08/F09 — pode rodar em paralelo
(cap 2). Maior slice em volume de mudança (10 templates × 5 estados
× 8 elementos = 40 micro-decisões visuais). **Vocabulário explícito
(D02 §Gate 1)**: idle/hover/focus/disabled/error com fg/bg documentados
em DESIGN.md §Components. **Table pattern upgrade**: sticky `<thead>`,
hover row bg lift, total row emphasis (border-top 2px +
font-weight 600), action column só-on-hover (`opacity: 0` idle →
`1` no `tr:hover`). **Extras**: section dividers hairline,
`::selection { background: var(--accent); color: var(--accent-ink) }`,
form autofill override (`-webkit-text-fill-color: var(--ink)` + box-
shadow inset), eyebrow labels `.label-xs`, form R$ prefix em aporte.
Estima 4-6h de CSS. Não altera spec contracts — apenas polish visual
em superfícies existentes. Requer regressão visual (T06) rodando
contra baseline antes de apply.
Progress:
- Proposed: done 2026-07-07 (folder
  `openspec/changes/f10-component-state-language-and-table-pattern/`;
  4 artifacts completos: `proposal.md` (10 templates × 5 estados × 8
  elementos = 40 micro-decisões; new capability
  `component-state-language` sem MODIFIED em specs runtime) +
  `design.md` (12 decisions D-F10.1..D-F10.12 + Risks +
  Migration + Open Questions) + `tasks.md` (6 grupos: pre-audit +
  CSS + templates + DESIGN.md + verification gate + sync+archive,
  47 checkboxes) + `specs/component-state-language/spec.md` (8
  ADDED Requirements, 22 scenarios — vocabulário 5-state + table
  pattern + section dividers + ::selection + form autofill override
  + eyebrow labels + form R$ prefix + prefers-reduced-motion).
  `openspec validate f10-component-state-language-and-table-pattern --json`
  retorna `valid: true`. `openspec validate --specs` reporta 39
  pass / 8 fail — mesmas 8 falhas pré-existentes (broker-csv-*,
  dashboard-*, import-*) sem regressão F10.
- Applying: done 2026-07-07; §1-§5 implementation landed — `src/omaha/static/app.css`
  ganhou bloco F10 ao final (10 grupos de regras: `prefers-reduced-motion`
  override global, `::selection` accent, autofill override Chromium/WebKit,
  `.label-xs` eyebrow, `.section-divider` hairline, sticky `<thead>`
  para `.asset-table`/`.class-table` (sem mexer na string de classes —
  hook vai pelo seletor), `tr:hover td` row lift com 80ms transition,
  `.row-actions` opacity 0 / hover 1 / mobile sempre visível,
  `.table-total` + `.class-total` total row emphasis,
  `.is-numeric` tabular-nums + right-align, `.input-prefix-wrap` +
  `.input-prefix` flex wrapper para R$, `.warning-line` border-left 4px
  rebalance warning) + 5 templates tocados: `patrimonio.html` (2
  `<hr class="section-divider">` entre portfolio header / classes
  summary / distribution), `_patrimonio_class_section.html` (sem
  mudança de classe — hook vai pelo seletor `.asset-table`), `classes.html`
  (sem mudança de classe + `.class-total` ganha alias `.table-total`),
  `rebalance.html` (aporte input wrapped em `<label class="input-prefix-wrap">`
  com `<span class="input-prefix">R$</span>`), `_rebalance_plan.html`
  (warning `<li>` ganha `.warning-line`) + `DESIGN.md` §Component
  inventory ganha row cross-linking nova spec + §Anti-patterns
  "Action column sempre visível" reforçado com referência ao padrão
  `.row-actions` + mobile breakpoint. Zero `src/omaha/**` runtime
  tocado (CSS + Jinja only). Pre-audit 1.1: 8 ocorrências de
  `outline: none` no CSS — todas acompanham `:focus` (não `:focus-visible`)
  com visual replacement (border-color + box-shadow) — base `:focus-visible`
  rule continua intacta para keyboard navigation; sem regressão de
  acessibilidade. Visual smoke §5.7: `/healthz` ok, `/patrimonio`
  renderiza 2 dividers + classes seeded ("RF Din" count=5), `/rebalanceamento`
  form R$ prefix renderiza, `/import` form intacto, `/login` auth-card
  intacto.
- Applied: done 2026-07-07; §5 verification gate + spec sync + archive —
  `task lint` verde (prek hooks all pass: merge-conflict + yaml + toml +
  json + large-files + pytest-unit stub + private-key + pyproject +
  hardcoded-secrets); `task test-unit` **284 passed / 2 skipped**
  (+13 vs F09 archive baseline 271: 13 do F09 typography tests; sem
  regressão F10); `task test-integration` **369 passed / 2 skipped**
  (R02/R03/R04/F09 baseline match — 0 F10 regression; warning
  `Solution may be inaccurate` em `solver.py:511` pré-existente, fora
  do escopo F10); `task test-bdd` **51 passed** (T05 baseline match);
  `openspec validate f10-component-state-language-and-table-pattern --json`
  `valid: true`; `openspec validate component-state-language --json`
  `valid: true` pós-sync; `openspec validate --specs` reporta **40 pass
  / 8 fail** (mesmas 8 falhas pré-existentes broker-csv-* + dashboard-*
  + import-* — sem regressão F10); `task db-reset` ok com
  `italo=6/48/47 ana=6/52/52` (R02/F07 baseline match). Smoke
  live 5.7: `bash scripts/print_lan_url.sh` → `http://192.168.1.6:8000`;
  `curl /healthz` `{"status":"ok","db":"ok","service":"omaha"}`; login
  Italo + select profile + GET `/` renderiza 2 `<hr class="section-divider">`
  + 5 ocorrências de "RF Din" (classes seeded); GET `/rebalanceamento`
  renderiza `<label class="input-prefix-wrap">` + `<span class="input-prefix">R$</span>`
  + input intacto; GET `/import` form intacto.
- Archived: done 2026-07-07; folder `openspec/changes/f10-component-state-language-and-table-pattern/`
  → `openspec/changes/archive/2026-07-07-f10-component-state-language-and-table-pattern/`
  via `openspec archive --yes --skip-specs` (sync manual pre-archive —
  delta file promoted para `## Requirements` + Purpose section em
  `openspec/specs/component-state-language/spec.md`); `openspec validate
  component-state-language --json` continua `valid: true` pós-sync;
  `openspec list --specs` agora reporta **48 specs** (47 pre + 1 new
  `component-state-language`); `openspec list` zero active changes.
  Consequências: T06 (visual regression baseline) promoted a Ready
  puro (gate F08+F09+F10 atendido — F08 archived proposal-only, F09
  applied, F10 applied); F11/F13 permanecem Blocked (D02 §Gate 4/5).

### F11 - Sidebar reintroduce (conditional on register A)
Status: `Blocked` 2026-07-07 (register D02 = SI maximal; register ≠ A
→ effectively blocked per dependency. Slice preservada para
auditoria; reactivate via `restore f11` apenas se owner ativamente
pedir outra direção de design.)
Goal: Reverter F02 — reintroduzir sidebar fixa 272px com logo SVG no
topo + nav vertical (4 itens: Patrimônio / Rebalanceamento /
Rentabilidade / Proventos) + ações (+ Classe, + Ativo, Importar) +
Sair no rodapé. Top nav com 4 tabs sai. Sidebar persiste em todas as
páginas autenticadas. Logo "Omaha" vira wordmark SVG (atualmente é
texto serif em h1). Mobile: sidebar colapsa em drawer (toggle
hamburger) ou esconde — decisão de implementação. Reverte D7
(`dashboard-sidebar` spec REMOVED).
Candidate OpenSpec change id: `f11-sidebar-reintroduce`
Spec link: `openspec/changes/f11-sidebar-reintroduce/` (criada quando
reativada; por ora não é proposta — slice Blocked)
Files:
- `src/omaha/templates/base.html` (sidebar substitui top nav)
- `src/omaha/templates/_sidebar.html` (recriar — deletado em F02)
- `src/omaha/static/app.css` (`.app-sidebar`, `.app-sidebar__item`,
  `.app-sidebar__item--active` com left-border 4px accent,
  `.app-sidebar__logo`, mobile drawer)
- `src/omaha/templates/patrimonio.html` + 4 partials (ajustar
  margin-left ou padding-left)
- `src/omaha/templates/rebalance.html` + 2 partials (ajustar)
- `src/omaha/templates/classes.html` + `assets.html` + `import.html`
  + `import_review.html` + `login.html` (ajustar)
- `static/logo.svg` (novo — wordmark, opcional)
- `openspec/specs/dashboard-sidebar/spec.md` (delta reverter REMOVED)
Notes: **Bloqueada por decisão D02 archived 2026-07-07** — owner
escolheu register SI maximal sem sidebar (gate D02 §Gate 4 = NÃO).
Top nav com 4 tabs de F02 é permanente. PRD §4.10 reescrito como
memorial registrando a decisão; DESIGN.md §Anti-patterns ganhou
"Reintroduzir sidebar" como entry formal. Slice preservada no
roadmap como histórico/auditoria. Reactivation path: owner pedir
explicitamente reverter o register → `restore f11` promove a Ready →
propose/apply/archive. Critical-area = layout = cap 1 Applying se
um dia voltar. Reverte decisão D7 do grill 2026-07-03 quando landa.
Quebra alias `_sidebar.html` — verificar tests que importam o partial
no apply. Estima 3-4h.
Progress:
- 2026-07-07: Blocked formal per D02 gate. Sem progress de execução.

### F12 - Material Symbols icon system (conditional on register A/B)
Status: `Ready` (Blocked se register C/D sem icons)
Goal: Adicionar Material Symbols Outlined font (Google Fonts ou
self-host). Substituir glyphs textuais (`×`, `−`, `▾`, `▶`) por icons.
Adicionar icons em: action buttons (+ Classe, + Ativo, Importar, Sair),
warnings (triangular), delete confirm (`close`), expand chevron
(`expand_more`), theme toggle (sun/moon, se F13 também rodar).
Stroke-based 1.5px conforme padrão anterior se mantido.
Candidate OpenSpec change id: `f12-material-symbols-icons`
Spec link: `openspec/changes/f12-material-symbols-icons/` (criada no propose)
Files:
- `src/omaha/templates/base.html` (Google Fonts URL para Material
  Symbols Outlined)
- `src/omaha/static/app.css` (`.icon`, `.icon--sm` 16px, `.icon--md`
  20px, `.icon--lg` 24px)
- `src/omaha/templates/_patrimonio_actions.html` (icons em buttons)
- `src/omaha/templates/_patrimonio_class_section.html` (delete icon)
- `src/omaha/templates/_rebalance_plan.html` (warning icon)
- `src/omaha/templates/_patrimonio_add_asset_modal.html` (close icon)
- `src/omaha/templates/import_review.html` (status icons)
- `src/omaha/templates/login.html` (icon em botão submit, opcional)
- `DESIGN.md` (§Iconography — atualmente "None required" vira
  "Material Symbols, scoped")
Notes: **D02 archived 2026-07-07** — gate resolvido (SI maximal
INCLUI icons; catalog definido em D02 §Iconography / DESIGN.md
§Iconography). Pode propor via `next` agora. Implementa Material
Symbols Outlined (Google Fonts) com 10 icons: `add`, `add_circle`,
`upload`, `logout`, `close`, `warning`, `expand_more`,
`expand_less`, `check_circle`, `help`. Tamanhos CSS `.icon--sm`
16px / `.icon--md` 20px / `.icon--lg` 24px; cor `currentColor`.
Stroke-based SVG ad-hoc anterior fica deprecado. Cobre: action
buttons (`+ Classe`, `+ Ativo`, `Importar`, `Sair` em
`_patrimonio_actions` + `base.html`), delete confirm (`close` em
`_patrimonio_class_section`), warning triangle (`warning` em
`_rebalance_plan`), modal close (`close` em
`_patrimonio_add_asset_modal`), expand chevron (`expand_more` /
`expand_less` em `_patrimonio_class_section`), import status
(`check_circle` / `help` em `import_review.html`). Custo 2-3h.
Stroke-based 1.5px anterior não se mantém — Material Symbols é
filled por default (variants do font).
Progress: (vazio)

### F13 - Light/dark toggle (conditional on owner request)
Status: `Blocked` 2026-07-07 (D02 archived sem light/dark toggle —
gate = NÃO; owner não pediu). Slice preservada para auditoria;
reactivate via `restore f13` apenas se owner ativamente pedir.
Goal: Reintroduzir light mode. Re-derivar TODOS os tokens em variante
light (body off-white warm, surface lift via claridade inversa, ink
dark warm-neutral, accent fern chroma-down para AA em light). Adicionar
UI toggle no header (sun/moon icons). Persistir preferência em cookie
ou localStorage. Adicionar `prefers-color-scheme` media query fallback.
Reverte decisão D-F05.10 ("F05 dropped light/dark toggle
deliberadamente").
Candidate OpenSpec change id: `f13-light-dark-toggle`
Spec link: `openspec/changes/f13-light-dark-toggle/` (criada quando
reativada; por ora não é proposta — slice Blocked)
Files:
- `src/omaha/static/app.css` (`:root` light + `.dark` overrides +
  `prefers-color-scheme` media query)
- `src/omaha/templates/base.html` (toggle UI no header com icons
  Material Symbols `light_mode` / `dark_mode`)
- `src/omaha/static/theme.js` (novo — preference persistence + early
  init script pra evitar FOUC)
- `tests/test_dark_mode_tokens.py` (renomear + estender pra cobrir
  light + dark)
- `tests/test_light_mode_tokens.py` (novo)
- `openspec/specs/color-tokens/spec.md` (delta ADDED — light variant
  requirements)
- `DESIGN.md` (§Color strategy estendido com light + dark)
Notes: **Bloqueada por decisão D02 archived 2026-07-07** — owner
escolheu register SI maximal sem light/dark toggle (gate D02 §Gate
5 = NÃO). Dark-only D-F05.10 mantido. PRD §4.10 reescrito como
memorial registrando a decisão; DESIGN.md §Anti-patterns ganhou
"Adicionar light/dark toggle" como entry formal. Slice preservada
no roadmap como histórico/auditoria. Reactivation path: owner pedir
explicitamente toggle → `restore f13` promove a Ready → propose/apply
/archive. Critical-area = visual surface = cap 1 Applying se um dia
voltar. Maior slice em custo (4-6h estimadas) porque re-deriva TODOS
os 17+ tokens em duas variantes + adiciona JS de persistência.
**Não-default**: nunca promove automaticamente.
Progress:
- 2026-07-07: Blocked formal per D02 gate. Sem progress de execução.

### R05 - Audit + migração de literais hex legados (residual F05)
Status: `Ready`
Goal: Migrar literais hex legados em `app.css` pra tokens. Identificado
em polish pass F05 §Polish pass item 1+2 (residual documentado em
DESIGN.md linhas 326-336). Inclui: 8 ocorrências `background: #fff`
em `.class-color-swatch`, `.btn`, `.import-page`, `.class-table` etc.
(calibrados pra `--surface = white`, agora sobre `--surface = dark
warm-neutral` ficam ilhas brancas isoladas); 8 linhas `color-mix(in
srgb, #<hex> 38%, var(--surface))` em `.import-class-cell--cls-{0..7}`
(tints calibrados pra surface white, agora ficam saturados demais).
Migra pra `var(--surface)` e `--class-N-tint` (novo token derivado
de `--class-N` com lightness lift para AA em dark surface).
Candidate OpenSpec change id: `r05-hex-literal-audit-and-migration`
Spec link: `openspec/changes/r05-hex-literal-audit-and-migration/` (criada no propose)
Files:
- `src/omaha/static/app.css` (migra `background: #fff` → `var(--surface)`
  nos 8 sites; migra `color-mix(... #<hex> 38% ...)` →
  `color-mix(in srgb, var(--class-N) 38%, var(--surface))` ou novo
  `--class-N-tint` token)
- `src/omaha/templates/_patrimonio_add_asset_modal.html` (se hex
  inline existir)
- `openspec/specs/color-tokens/spec.md` (delta ADDED — `--class-N-tint`
  requirement, 1 slot × 6 variants)
- `DESIGN.md` (§Polish pass item 1+2 marcado done; §Migration path
  atualizado)
Notes: **D02 archived 2026-07-07** — gate resolvido. Depende de
F08 (precisa dos novos tokens OKLCH pra derivar `--class-N-tint`
corretamente) — gate D02 não era blocker direto, F08 é. Residual do
polish pass F05 registrado em DESIGN.md §Polish pass items 1+2 antes
de D02; após D02, esses items permanecem como candidates of R05.
Mecânico, baixo risco. Estima 1-2h. Confirma pre-condition com
`grep -nE '#fff|#ffffff' src/omaha/static/app.css` antes de propor
pra contar sites exatos.
Progress: (vazio)

### T06 - Visual regression baseline (screenshot diffs)
Status: `Ready`
Goal: Adicionar baseline de testes de regressão visual via Playwright.
Captura snapshot de 10 páginas em viewport padrão (1440×900) e
viewport mobile (375×667). Baseline commitado em
`tests/visual/baselines/`. Diff threshold 0.5% pixels diferentes por
página (sugestão — owner decide). Roda como gate separado em CI (não
bloqueia dev local por default). Cobre: login, patrimonio (logged in),
classes, assets, rebalance (form + plan), import (form + review),
rentabilidade, proventos, audit_report. Pre-requisito: F08 + F09 + F10
já aplicados (captura baseline do design NOVO, não do atual — se rodar
antes, baseline captura o velho e perde utilidade).
Candidate OpenSpec change id: `t06-visual-regression-baseline`
Spec link: `openspec/changes/t06-visual-regression-baseline/` (criada no propose)
Files:
- `tests/visual/` (novo diretório)
- `tests/visual/conftest.py` (Playwright fixture + viewport config +
  auth helper pra logar antes de capturar páginas autenticadas)
- `tests/visual/test_snapshots.py` (10 page snapshot tests)
- `tests/visual/baselines/` (PNGs baseline, committed)
- `pyproject.toml` (taskipy `task test-visual`)
- `.gitignore` (não ignorar `tests/visual/baselines/`)
- `DESIGN.md` (§Polish pass — testing strategy)
Notes: **D02 archived 2026-07-07** — gate resolvido. Depende de
F08 + F09 + F10 (precisa do design novo aplicado pra capturar baseline
significativa — se rodar antes, baseline captura o velho e perde
utilidade). Rodar DEPOIS das 3 F-slice. Threshold 0.5% é sugestão
inicial — owner ajusta conforme sensibilidade desejada. Custo 3-4h.
Pode rodar em paralelo com R05 (não tocam nos mesmos arquivos).
Progress: (vazio)

## Dependencies

### F01
Depends on: none
Blocks: F02 (visa household precisa existir antes de virar nav item default)
Can run in parallel: yes
Status: archived 2026-07-04 (`f01-household-cross-profile-consolidation`)

### F02
Depends on: none (F01 é paralela, não estritamente necessária para a tab nav)
Blocks: F03, F04 (precisam do slot na nav), R04 (partialização do template renomeado)
Can run in parallel: yes (com F01; F03/F04/R04 bloqueados)

### F03
Depends on: F02 (slot `/rentabilidade` precisa existir)
Blocks: none
Can run in parallel: yes (com F04)
Status: closed 2026-07-06 (archive/2026-07-06-f03-rentabilidade-page/)

### F04
Depends on: F02 (slot `/proventos` precisa existir)
Blocks: none
Can run in parallel: yes (com F03)

### F05
Depends on: none
Blocks: none
Can run in parallel: yes

### F06
Depends on: F02 (template `/patrimonio` e base.html já existem), F01 (read-only gate `require_profile_writable` reusado — sem retrabalho)
Blocks: D01 (README precisa refletir toggle `Família`), F07 (Família-as-profile refina o toggle num peer do chip)
Can run in parallel: yes (com R-slice, T-slice, I-slice)

### F07
Depends on: F06 (toggle `?view=household` existe; F07 reusa a flag `view_mode="family"` e os helpers `family_aggregates` / `family_asset_classes`), F02 (profile-switcher + base.html layout)
Blocks: D01 (README precisa refletir Família como peer no chip)
Can run in parallel: yes (com R-slice, T-slice, I-slice)

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

### T05
Depends on: none
Blocks: none
Can run in parallel: yes

### I01
Depends on: none
Blocks: none
Can run in parallel: yes

### I02
Depends on: none
Blocks: none
Can run in parallel: yes (com I01)
Status: archived 2026-07-07 (`i02-tls-cert-renewal-automation`)

### D01
Depends on: F01, F02, F05 (reflete surface pós-slice entregue; F03/F04
deprecated 2026-07-06 saem do gate)
Blocks: none
Can run in parallel: yes

### D02
Depends on: none (sessão exploratória 2026-07-06 já capturada em
`openspec/.temp_assets/design-system-redesign-session-2026-07-06.md`;
owner precisa resolver 7 gates antes de propor)
Blocks: F08, F09, F10, F12, R05, T06 (toda a série visual
depende da decisão de register — R05 depende de F08 que depende de D02;
T06 depende das 3 F-slice)
Can run in parallel: yes (com qualquer F/R/T/I slice não-visual)
Status: Applied pending archive 2026-07-07 (`d02-design-register-decision/`)

### F08
Depends on: D02 archived (gate resolvido 2026-07-07; register SI
maximal memorializado em PRD §4.10 + DESIGN.md §Color strategy). F08
precisa do register escolhido pra re-derivar tokens.
Blocks: R05 (precisa dos novos tokens pra derivar `--class-N-tint`),
T06 (precisa do design novo aplicado pra capturar baseline)
Can run in parallel: yes (com F09, F10 em Applying — cap 2)

### F09
Depends on: D02 archived (gate resolvido 2026-07-07; display face
Red Hat Display + Inter feature-settings completos).
Blocks: T06
Can run in parallel: yes (com F08, F10 em Applying — cap 2)

### F10
Depends on: D02 archived (gate resolvido 2026-07-07; 5-state + table
pattern + extras INCLUSOS no register SI maximal).
Blocks: T06
Can run in parallel: yes (com F08, F09 em Applying — cap 2)

### F11
Depends on: D02 archived + register = A (sidebar só faz sentido em A)
Blocks: T06
Can run in parallel: yes (Blocked 2026-07-07 — register D02 = SI maximal,
≠ A; slice preservada no roadmap como histórico)

### F12
Depends on: D02 archived (gate resolvido 2026-07-07; catalog Material
Symbols definido em D02 §Iconography / DESIGN.md §Iconography).
Icons INCLUSOS no register SI maximal (gate §Gate 1 = maximal inclui
icons).
Blocks: T06
Can run in parallel: yes (com F08/F09/F10 — cap 2)

### F13
Depends on: D02 archived + owner explícito pedir light/dark toggle
Blocks: T06
Can run in parallel: yes (Blocked 2026-07-07 — owner não pediu toggle,
D-F05.10 mantido; slice preservada como histórico)

### R05
Depends on: D02 archived (gate OK) + F08 (precisa dos novos tokens
OKLCH pra derivar `--class-N-tint` corretamente; hex sweep só funciona
pós-palette overhaul)
Blocks: none
Can run in parallel: yes (com T06, que não toca nos mesmos arquivos)

### T06
Depends on: F08 + F09 + F10 (precisa do design novo aplicado pra
capturar baseline significativa — se rodar antes, baseline captura
o velho e perde utilidade)
Blocks: none
Can run in parallel: yes (com R05)

## Recommended Execution Order

Prioridade presume que o owner quer atacar mudanças estruturais primeiro
(rebalance + páginas), qualidade em paralelo, e docs/infra no fim.
**F03 + F4 movidas para o final** (deferral 2026-07-05, D-F03-defer).

### Fila ativa — design system redesign (gate D02 archived)

Owner abriu frente visual 2026-07-06 (sessão exploratória capturada
em `openspec/.temp_assets/design-system-redesign-session-2026-07-06.md`).
Queixa: paleta "não está bonita" + "não ajuda a entender informação".
Referência: Status Invest (investidor.statusinvest.com.br). PRD §4.10
liberado como restrição; §4.1-§4.9 inalterados. **D02 archived
2026-07-07** — gate resolvido; owner escolheu register SI maximal com
7 decisões aplicadas (sidebar NÃO, class-3 hue 350, Red Hat Display,
dark-only, hue 60 mantém, escopo 3 fatias). F11 + F13 promoted a
Blocked (per register decision); F08 + F09 + F10 + F12 promoted a
Ready puro (gate atendido).

1. **D02 - design register decision** — archived 2026-07-07 (gate)
2. F08 - palette overhaul v2 (tokens per register SI maximal; resolve
   4 bugs concretos da paleta atual; alvos: emerald 0.68/0.20/152,
   fern positive 0.79/0.19/145, coral negative 0.69/0.20/25, warning
   amber, class-3 magenta-red hue 350)
3. F09 - typography refresh (Red Hat Display 700+ + Inter feature-
   settings `tnum, cv01, ss01, ss02`; pode rodar em paralelo com
   F08/F10)
4. F10 - component state language + table pattern (5-state feedback
   idle/hover/focus/disabled/error + sticky `<thead>` + hover row bg
   lift + total row emphasis + section dividers + form R$ prefix;
   maior slice em volume, ~6h, 10 templates)
5. F11 - sidebar reintroduce — **Blocked** (register ≠ A)
6. F12 - material symbols icons (catalog definido em D02 §Iconography:
   add / add_circle / upload / logout / close / warning / expand_*
   / check_circle / help; roda em paralelo com F08/F09/F10)
7. R05 - hex literal audit (mecânico; depende de F08 pra novos tokens;
   pode rodar em paralelo com T06)
8. T06 - visual regression baseline (Playwright screenshots; depende
   de F08+F09+F10 aplicados; roda em paralelo com R05)
9. F13 - light/dark toggle — **Blocked** (owner não pediu; D-F05.10
   dark-only mantido)

### Fila histórica (já arquivada — referência)

1. R01 - cleanup (zero risk, prep do repo) — archived
2. F02 - tab nav + side panel removal + stubs (foundation para F03-F04) — archived
3. F01 - household cross-profile (paralela a F02 — não bloqueia) — archived 2026-07-04 (superseded by F06)
4. F06 - family full-join aggregate cross-User (substitui semântica F01; arquivada 2026-07-05)
5. F07 - família como opção no profile-switcher (peer de Italo/Ana; dependente de F06) — archived 2026-07-05
6. F05 - dark mode palette swap — archived 2026-07-05
7. R02 - revise CSV seed system — archived 2026-07-06
8. R03 - extract quote_provider adapter — archived 2026-07-06
9. R04 - partialize patrimonio template (depende de F02) — archived 2026-07-06
10. T05 - BDD step-def drift after F02 (promoted 2026-07-04 — fecha o loop de follow-up de T01; mudança mecânica pequena) — archived 2026-07-06
11. T01 - BDD + e2e 100% green — archived
12. **T02 - coverage in CI — archived 2026-07-06 (GH Actions deferred per owner; workflow file dormente no repo)**
13. T03 - mutation testing rebalance
14. I01 - backup scheduling — archived 2026-07-06
15. I02 - TLS cert renewal automation — archived 2026-07-07
16. D01 - README refresh (último — reflete tudo acima; deferred atrás da fila visual)

- **Fila visual D02-F08-F09-F10-F11-F12-R05-T06-F13 promoted 2026-07-06**:
  owner abriu frente de redesign visual em sessão exploratória usando
  Status Invest (investidor.statusinvest.com.br) como referência
  primária. Queixas: paleta "não está bonita" + "em muitos casos não
  ajuda o usuário a entender a informação". PRD §4.10 (register
  "domestic, Moleskine, sem ornamento") foi liberado pelo owner como
  restrição — pode ser reescrito. Constraints PRD §4.1-§4.9 (auth,
  bind, seed, test markers, BDD, taskipy, refresh-for-test)
  permanecem. Sessão completa em
  `openspec/.temp_assets/design-system-redesign-session-2026-07-06.md`
  (matriz Roubar/Rejeitar/Reframear, opções A/B/C/D com mockups
  ASCII, 4 bugs concretos, 7 gates abertos). D02 é gate absoluto: sem
  decisão de register, F08+ não podem propor. F11/F12/F13 são
  conditional (dependem da direção D02 escolher). F08/F09/F10
  podem correr em paralelo (cap 2). R05 é mecânico e roda em paralelo
  com T06. T06 captura baseline visual do design NOVO, por isso
  depende de F08+F09+F10 aplicados. D01 (README) deferido atrás da
  fila visual — README precisa refletir surface pós-redesign.

**Removidos da fila ativa 2026-07-06:**
- F03 - rentabilidade page (Closed 2026-07-06 — D-F03-defer permanente)
- F04 - proventos page (Deprecated 2026-07-06 — incerto)

Notas de reordenamento:
- **F02 vem antes de F01** porque a tab nav + side panel removal é
  layout-foundation que F03/F04 dependem. F01 (household toggle) é
  independente da tab nav — pode correr em paralelo (entre F02 e F05).
- **F06 promoted 2026-07-04** (imediatamente após F01, antes de F03): owner
  flagged F01 como "muito ruim" porque a agregação intra-User nunca
  funcionou (Italo e Ana são Users separados no seed). F06 substitui a
  semântica do `?view=household` por agregado cross-User com full-join
  por nome. Toca em auth read-only (gate F01) — domínio crítico, cap 1
  Applying, mas não toca no solver.
- **F07 promoted 2026-07-05** (imediatamente após F06, antes de F03):
  owner pediu no grill 2026-07-05 que Família deixe de ser um toggle
  (`?view=household`) e vire **opção no profile-switcher** peer de
  Italo/Ana. F07 adiciona `Profile.is_family_sentinel` + User `family`
  sem senha, drop do fixture `Italo RF2`, e rework do `profile-switcher`
  para 3 opções. Migration Alembic + cap 1 Applying (profile routing
  + auth são críticos). Não toca solver nem cotação.
- **F03 + F04 adiada para o final** (D-F03-defer, 2026-07-05): owner
  pediu para não mexer nas páginas Rentabilidade/Proventos por
  enquanto. Reordenadas para depois de D01 (último); rationale: o
  doc final (D01) precisa do surface pós-tudo, e F03/F04 só fazem
  sentido quando o owner retomar o tema. Proposal draft de F03
  em `openspec/changes/f03-rentabilidade-page/` (valid: true
  2026-07-05) fica intacto para reuso — reativar via
  `start f03` não exige re-propose. F04 ainda não tem proposal;
  reativar via `start f04` abre propose.
- **F03 closed 2026-07-06**: owner pediu para fechar a spec.
  Proposal draft movido para
  `archive/2026-07-06-f03-rentabilidade-page/`; delta spec
  descartada (capability nunca implementada). Slice sai da fila
  ativa; reativação requer mover o folder de volta + re-validar
  (ver bloco F03 "Reactivation path"). F04 segue deferida —
  owner decide separadamente.
- **T02 archived 2026-07-06 (GH Actions deferred)**: implementação
  local landou (pyproject.toml + .gitignore + workflow file em
  `.github/workflows/ci.yml`); 5 Actions runs tentadas com
  progresso (lint + test-unit verdes; test-integration + bdd
  pendentes pós-db-reset/env-fix); owner decidiu pausar GH
  Actions porque desenvolvimento ainda é local. Workflow file
  fica commitado como infra dormente ("útil no futuro"). Slice
  sai da fila ativa com reactivation path explícito (mover
  folder de `archive/2026-07-06-t02-coverage-report-in-ci/` de
  volta + re-validar). Próxima execução: T03 (mutation testing
  rebalance) ou I01/I02 (infra) ou D01 (doc) ou F04 (Proventos
  deferida).
- T03 fica depois de R03 porque a fatia de mutation testing pode
  aproveitar adapter mais limpo para mockar providers. Se durante
  apply de T03 essa vantagem não se confirmar, mover T03 para antes
  de R03 sem outra consequência.
- D01 antes de F03+F04: doc pode refletir surface até I02 sem
  aguardar as páginas deferidas; quando F03/F04 retomarem, D01 ganha
  delta de features block (re-ordenado depois do apply).

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
- **D-F06.1 — Agregado cross-User sempre.** `family_asset_classes` NÃO
  filtra por `Profile.user_id == viewer.id`. Soma TODOS os profiles do
  banco (excluindo o de sistema, se houver). Login de Italo ou Ana
  produz **o mesmo** total agregado. Quebra deliberadamente o contrato
  "intra-User" herdado de F01 — registrado como supercession. Aplicar
  em F06 — `routes/pages.py:family_asset_classes`. Decisão 2026-07-04.
- **D-F06.2 — Full-join por nome de classe/ativo.** Classes com mesmo
  `AssetClass.name` em profiles distintos colapsam em 1 linha
  (`AssetClass.id` distinto, `name` idêntico). Mesma regra para
  `Asset.name` dentro de cada classe. Mesma regra
  `broker-csv-import-totals` (soma `total_invested` /
  `total_current` verbatim — sem `qty * price`). Cor visual: 1ª
  ocorrência vence (lossy, documentado). Aplicar em F06 —
  `family_aggregates` + `_aggregate_assets_by_name`. Decisão 2026-07-04.
- **D-F06.3 — `target_pct` omitido no agregado.** Nenhuma coluna
  `target_pct` aparece quando `view == 'family'`. Justificativa:
  dois profiles têm alvos divergentes, "alvo do agregado" é ambíguo.
  Modo família é só leitura analítica (soma investido/valor/ganho).
  Aplicar em F06 — `patrimonio.html` (suprimir
  `patrimonio-portfolio-header` target_pct se houver e
  `class-target-pct-view` por classe); spec ganha requirement
  "family view omits target allocation columns". Decisão 2026-07-04.
- **D-F06.4 — Toggle renomeado `Casa` → `Família`.** Mesma
  querystring `?view=household` (internamente renomeada no contexto
  F06 para `view == 'family'` no template), mesmo form HTML, mesma
  posição. Condição de visibilidade: `len(all_profiles) >= 2` (não
  `viewer.profiles`). Aplicar em F06 — `templates/base.html` (label
  e data-testid passam a `data-testid="family-toggle"` /
  `data-testid="family-chip"`); `tests/e2e/selectors.py` ganha alias
  `household-toggle → family-toggle`. Decisão 2026-07-04.
- **D-F06.5 — Gate read-only reusado, sem refator.** F01 já cravou
  `require_profile_writable` retornando 409 `household_read_only` em
  11 endpoints. F06 mantém o gate e só renomeia a flag interna de
  session (`view_mode == "family"`) — wire shape do JSON 409 continua
  `{"reason": "household_read_only"}` para não quebrar consumers
  existentes. Decisão 2026-07-04.
- **D-F06.6 — F01 fica no histórico (não deletado).** Slice
  archived mantém valor de auditoria ("tentamos intra-User,
  aprendemos que seed separa Users"). Spec `cross-profile-sharing`
  recebe `MODIFIED` (semântica cross-User + full-join) e `REMOVED`
  nos requirements "intra-User" + "preserve per-profile isolation
  on household" (substituídos pelos novos). Decisão 2026-07-04.
- **D-F03-defer — F03 e F04 movidas para o final do execution order
  por pedido do owner em 2026-07-05.** Razão: foco atual está no
  rearranjo da nav/profile-switcher (F02+F06+F07 já archived); páginas
  Rentabilidade/Proventos são leitura analítica que pode esperar.
  F03 tem proposal draft válido (`openspec/changes/f03-rentabilidade-page/`,
  `valid: true` em 2026-07-05) — preservar artifacts intactos, não
  re-propor quando reativar; usar `start f03` para retomar direto do
  `apply`. F04 ainda sem proposal — `start f04` abre
  `openspec-propose`. Stubs F02 (`Em construção`) permanecem
  clicáveis na tab nav durante o deferral. Mudar a UI das tabs ou
  renomear rótulos também fica congelado até owner retomar o tema.
  Decisão 2026-07-05.

---

## Compacted history

Últimas 15 fatias arquivadas (compile manualmente do diretório
`openspec/changes/archive/`; aspiracional: limite confortável para revisão humana):

- `2026-07-07-i02-tls-cert-renewal-automation` → `prod.yml` ganha serviço `certbot` (image `certbot/certbot:latest`, `restart: unless-stopped`, envs `${CERTBOT_RENEW_INTERVAL:-43200}` + `${CERTBOT_DOMAIN:?…}` + `${CERTBOT_EMAIL:?…}`, `command: /bin/bash /scripts/certbot_loop.sh`, 5 mounts: `./certs:/etc/letsencrypt` rw + `./certs/webroot:/var/www/certbot:ro` + `./prod.yml:/app/prod.yml:ro` + `./scripts/certbot_loop.sh:/scripts/certbot_loop.sh:ro` + `/var/run/docker.sock:/var/run/docker.sock:ro`) + nginx ganha mount `./certs/webroot:/var/www/certbot:ro` + header comment block reescrito "Five services" + `scripts/certbot_loop.sh` novo (107 LOC bash: valida interval/domain/email fail-fast, constrói `DEPLOY_HOOK` interpolando `CERTBOT_DOMAIN` + `docker compose -f /app/prod.yml exec -T nginx nginx -s reload`, loop infinito com `sleep`, ISO-8601 UTC logs, failure-tolerant wrapper) + `certs/webroot/` + `certs/webroot/.gitkeep` + `.gitignore` ganha `!certs/webroot/` + `!certs/webroot/.gitkeep` whitelist (preserva `certs/*` ignore) + README nova seção "TLS renewal" (4 sub-seções: First-time setup runbook + Scheduler behaviour + Filesystem layout + cross-ref "Production deploy") → `prod.yml`, `scripts/certbot_loop.sh`, `certs/webroot/.gitkeep`, `.gitignore`, `README.md`, `openspec/specs/tls-cert-renewal/spec.md` (Purpose + 7 ADDED requirements: scheduled certbot renew + deploy hook reloads nginx + interval configurable + failed renewal does not stop scheduler + certbot container has write access to certificate directory + ACME http-01 challenge webroot shared + certbot service can be disabled without affecting other services; 14 scenarios totais) → `openspec validate i02-tls-cert-renewal-automation --json` `valid: true`; `docker compose -f prod.yml config --quiet` exit 0; `task lint` verde; `task test-unit` 271 pass/2 skip; `task test-integration` 369 pass/2 skip (sem regressão — zero `src/omaha/**` tocado); `openspec archive i02-tls-cert-renewal-automation --yes` 2026-07-07 sincronizou delta → `tls-cert-renewal` (7 ADDED), moveu folder → `archive/2026-07-07-i02-tls-cert-renewal-automation/`; `openspec validate tls-cert-renewal --json` `valid: true`; spec count 43 → 44.
- `2026-07-06-i01-automatic-backup-scheduling` → `scripts/backup_scheduler.py` (~125 LOC: loop infinito com `BACKUP_INTERVAL` (default 86400) + `BACKUP_DEST_DIR` env override (decision-flip em apply) + FATAL validation 2.4 + ISO-8601 UTC log prefix + failure-tolerant wrapper) + `prod.yml` ganha serviço `backup-scheduler` (image `omaha:prod`, `restart: unless-stopped`, sem profile, `command: python -m scripts.backup_scheduler`, mounts `omaha-data:/app/data:ro` + `./backups:/backups`, comment block D-I01.1/4/5; header reescrito "Four services"; Usage block estendido com `logs -f backup-scheduler` + `stop backup-scheduler`) + README "Backup & restore" ganha "Scheduled backups (default in prod)" subseção + nota de retenção → `scripts/backup_scheduler.py`, `prod.yml`, `README.md`, `openspec/specs/backup-scheduling/spec.md` (Purpose + 6 ADDED requirements + 12 scenarios) → `task lint` verde (prek + ruff format/check); `openspec validate i01-automatic-backup-scheduling` + `openspec validate backup-scheduling` ambos `valid: true`; `docker compose -f prod.yml config --quiet` exit 0; `task test-unit` 271 pass/2 skip (R02/R04 baseline); `task test-integration` 369 pass/2 skip (R02/R03/R04 baseline); smoke test local 5.1 (`BACKUP_INTERVAL=5 BACKUP_DEST_DIR=./backups`): 4 backups criados a 5s interval, todos 172KB SQLite válido; smoke test local 5.2 (`BACKUP_INTERVAL=3 BACKUP_DEST_DIR=/nonexistent-dir-x9q`): 5 ERROR log lines consecutivos, container não exit (matado por SIGINT após 5 falhas); FATAL validation 2.4: `BACKUP_INTERVAL=abc`/`-5`/`0`/`""` todos exit 2 com mensagem clara. **Caveat**: `Dockerfile` NÃO copia `scripts/` para `omaha:prod` — pré-existing gap que afeta tanto o serviço `backup` quanto o novo `backup-scheduler`; em produção ambos falham com `ModuleNotFoundError: No module named 'scripts'`. Fix = `COPY scripts ./scripts` no Dockerfile = slice separada (follow-up fora do escopo I01).
- `2026-07-06-t03-mutation-testing-rebalance-engine` → dep `mutmut>=3.0,<4` em `[dependency-groups].dev` + bloco `[tool.mutmut]` em `pyproject.toml` (`source_paths = ["src"]` + `only_mutate = ["src/omaha/rebalance/solver.py", "src/omaha/rebalance/validation.py"]` + `also_copy` (17 paths: scripts/, alembic/, alembic.ini, data/seed/, prod.yml, docker-compose.yml, Dockerfile, nginx/, tests/scripts/, tests/fixtures/, tests/posicao_italo.csv) + `pytest_add_cli_args = ["--no-cov", "-p", "no:cacheprovider", "--ignore=tests/e2e", "--ignore=tests/bdd"]` + `pytest_add_cli_args_test_selection = [6 rebalance unit test files]`) + `[tool.taskipy.tasks]` ganha 3 entries (`mutation` → `uv run mutmut run`, `mutation-report` → `python -m scripts.mutation_report`, `mutation-baseline` → `python -m scripts.mutation_baseline`) + `scripts/mutation_report.py` (99 LOC — recursive `mutants/**/*.meta` glob + per-status counts + killed_share) + `scripts/mutation_baseline.py` (55 LOC — 7-line `.mutmut-baseline` com UTC ISO-8601 timestamp) + `.gitignore` ganha `mutants/` (mutmut3 cache) + `.mutmut-baseline` (baseline committed) → `pyproject.toml`, `.gitignore`, `scripts/mutation_report.py`, `scripts/mutation_baseline.py`, `openspec/specs/rebalance-mutation-testing/spec.md` (4 ADDED requirements + Purpose), `.mutmut-baseline`, `openspec/roadmap.md` → 869 mutants gerados em ~3 min wall-clock (5.12 mutations/sec) sobre `solver.py` (21K) + `validation.py` (8.4K); baseline capturada: `killed=556, survived=301, no_tests=12, timeout=0, skipped=0, killed_share=0.649, generated_at=2026-07-06T21:25:16+00:00` → 301 survived mutants é sinal de test gap (provável follow-up `R`/`T` slice fora do escopo T03); 12 no_tests = funções puras em `validation.py` que nenhum unit test exercita → `task test-unit` 271 pass / 2 skip (R02/R04 baseline); `task test-integration` 369 pass / 2 skip (R02/R03/R04 baseline); `task test-bdd` 51 pass (T05 baseline); `task coverage` 92% line (T02 baseline); `task lint` verde; `openspec validate t03-mutation-testing-rebalance-engine --json` e `openspec validate rebalance-mutation-testing --json` ambos `valid: true`; `openspec list --specs` reporta **41 specs** (40 pre + 1 new `rebalance-mutation-testing`). **Drift correction no archive:** slice-text original mencionava `engine.py` + `data_bridges.py` (que não existe no package rebalance); durante apply escopo corrigido para `solver.py` + `validation.py` (par coberto pelos unit tests sem TestClient+DB) — registrado no proposal §Impact e design.md §D-T03.3. Spec main e delta divergem em algumas referências mutmut2 (`mutmut run --paths-to-mutate`, `mutmut report`/`html` subcommands) que mutmut3 não suporta; main spec foi escrita alinhada com o que realmente shipped (`mutants/**/*.meta` JSONs em vez de `.mutmut-cache/`, e "per-mutant details via `.meta` JSONs" no lugar do "HTML view" scenario).
- `2026-07-06-t02-coverage-report-in-ci` → **GH Actions deferred per owner 2026-07-06** (desenvolvimento local, CI não exercitado). Implementação local landou: `pyproject.toml` ganha `[tool.coverage.run]` (source=`["src/omaha"]`, branch=false, omit `__main__.py`) + `[tool.coverage.report]` (exclude_lines para 4 padrões; sem fail_under) + `addopts` em `[tool.pytest.ini_options]` estendido para `--cov=src/omaha --cov-report=xml:reports/coverage.xml` + `task coverage` reescrito para `-m "unit or integration" --cov=src/omaha --cov-report=term-missing --cov-report=xml:reports/coverage.xml` (BDD/e2e excluídos — passa de 10+ min timeout para 3 min); `.gitignore` ganha `reports/coverage.xml` + `reports/.coverage`; `.github/workflows/ci.yml` criado com 5 jobs (lint standalone + test-unit/integration/bdd com `needs: lint` + coverage com `needs: [test-unit, test-integration]`), triggers `push`/`pull_request` em `[main]`, `astral-sh/setup-uv@v4` com `python-version: "3.12"` + `actions/cache@v4` keyed em `hashFiles('uv.lock')`, `actions/upload-artifact@v4` para `coverage-report`, test-integration/test-bdd/coverage ganham step `Reset database` (`uv run task db-reset`) com `env: SECRET_KEY + ADMIN_PASSWORD` injetados → `src/omaha/static/app.css` (não tocado), `pyproject.toml`, `.gitignore`, `.github/workflows/ci.yml`, `openspec/specs/ci-coverage-pipeline/spec.md` (nova, 10 ADDED requirements + Purpose), `openspec/roadmap.md` → 5 Actions runs tentadas: (1) `setup-python@v5 cache:"uv"` inválido, (2) `setup-uv@v4 python-version-file` inválido, (3) `uv sync --extra dev` inválido (dev em `[dependency-groups]`), (4) **lint + test-unit verdes** + test-integration/bdd falhas por DB ausente, (5) db-reset falha por `SECRET_KEY` ausente (fix aplicado); última versão do workflow (commit `bac8b47`) tem os 5 fixes acumulados mas não foi exercitada end-to-end → `task test-unit` 271 pass/2 skip (R04 match); `task test-integration` 369 pass/2 skip (R02/R03/R04 match); `task test-bdd` 51 pass (T05 match); `task coverage` 640 pass/4 skip + **92% line coverage** com `reports/coverage.xml` Cobertura-compatible (`<coverage version=... line-rate="0.9163" ...>` + `<package name=...>` structure); `ruff check` + `ruff format --check` verdes em `src tests alembic`; `openspec validate t02-coverage-report-in-ci --json` `valid: true`; `openspec list --specs` 40 → 41 (nova spec `ci-coverage-pipeline`); GH Actions runner **não exercitado** end-to-end por decisão do owner; workflow file fica commitado como infra dormente ("útil no futuro" per owner); reactivation path explícito em `archive/2026-07-06-t02-coverage-report-in-ci/tasks.md` §5
- `2026-07-06-t05-bdd-step-def-drift-after-f02` → `STEP_CLICK_ALIASES` dict adicionada em `tests/bdd/step_defs/common_steps.py` (topo, acima de `click_button`, com 2 entries: `+ Nova classe` → `('empty-state-create-class', 'new-class-modal-submit')` + `+ Novo ativo` → `'dashboard-add-asset-open'`) + `click_button` body estendido para consultar alias chain antes dos 3 default candidates (mesmo two-phase visibility filter) + Gherkin rewrites: `class_crud.feature:65` + `profile_sharing.feature:17,21,37` (4 step calls trocadas de `+ Nova classe` para `Nova Classe`) + nova spec `bdd-step-def-aliases` consolidada (Purpose + 1 ADDED requirement + 3 scenarios) → `tests/bdd/step_defs/common_steps.py`, `tests/bdd/features/class_crud.feature`, `tests/bdd/features/profile_sharing.feature`, `openspec/specs/bdd-step-def-aliases/spec.md` → `task test-bdd` 51 pass (vs 47+4 pre-T05; fechou as 4 falhas pre-existentes T01-follow-up) / 0 skip; `task test-unit` 271 pass / 2 skip (sem regressão); `task test-integration` 369 pass / 2 skip (sem regressão); `task test-e2e` 43 pass / 4 fail (mesmas chromium stalls pre-existentes do T01, fora escopo); `task lint` verde; `openspec validate t05-...` + `openspec validate bdd-step-def-aliases` ambos `valid: true`; delta spec == main spec byte-identical pré-archive (sync already done no apply)
- `2026-07-06-f03-rentabilidade-page` → CLOSED sem apply (D-F03-defer permanente 2026-07-06) — `openspec-archive-change` moveu folder `openspec/changes/f03-rentabilidade-page/` → `openspec/changes/archive/2026-07-06-f03-rentabilidade-page/`. Delta spec `rentabilidade` **não** sincronizada (capability nunca implementada; spec-driven principle: spec descreve comportamento existente). 0 tasks roladas; 0 código tocado; stub `/rentabilidade` em `templates/rentabilidade.html` permanece. Reactivation path documentada no bloco F03 (mover folder de volta + re-validar). F04 (Proventos) segue deferida em `Ready` — owner decide separadamente.
- `2026-07-06-r04-partialize-patrimonio-template` → `src/omaha/templates/patrimonio.html` (2186 LOC → 60 LOC shell) extraído em 6 partials `_patrimonio_*.html` (actions 21 + portfolio_header 20 + distribution 23 + class_section 331 + empty_states 18 + add_asset_modal 1682) + nova spec `patrimonio-template-partials` (Purpose + 4 ADDED requirements, 14 cenários) + 0 spec deltas (refactor puro, mesmo public contract preservado) → `src/omaha/templates/patrimonio.html`, `src/omaha/templates/_patrimonio_actions.html`, `src/omaha/templates/_patrimonio_portfolio_header.html`, `src/omaha/templates/_patrimonio_distribution.html`, `src/omaha/templates/_patrimonio_class_section.html`, `src/omaha/templates/_patrimonio_empty_states.html`, `src/omaha/templates/_patrimonio_add_asset_modal.html`, `openspec/specs/patrimonio-template-partials/spec.md` → render diff: zero non-blank-line differences em 3 variants (Italo default / family / Ana); testid count preservado (122 = 119 em partials + 3 em shell wrappers); x-data declarations preservadas (17) → `task test-unit` 271 pass/2 skip; `task test-integration` 369 pass/2 skip; `task test-bdd` 47 pass/4 fail pre-existentes T05 (fora escopo); `task test-e2e` 42 pass/5 fail pre-existentes chromium stalls (fora escopo); `task lint` verde; `openspec validate r04-partialize-patrimonio-template` `valid: true`; `openspec list --specs` 39 → 40 (nova spec `patrimonio-template-partials`); refresh-for-test smoke: server 0.0.0.0:8000 + `/patrimonio` 200 + Família option chip intacta + `db-reset` Italo=6/48/47 Ana=6/52/52
- `2026-07-06-r03-extract-quote-provider-adapter` → `src/omaha/quotes/provider.py` (239 LOC) deletado e substituído por pacote `provider/` (`__init__.py` 80 LOC com 6 re-exports + `get_quote_provider()` selector + L2 `ValueError` defense-in-depth; `protocol.py` 36 LOC Quote + Protocol; `mapper.py` 60 LOC map_symbol + B3/crypto regex; `yfinance.py` verbatim move 105 LOC; `stub.py` 56 LOC StubProvider novo com `responses` + `default`) + `Settings.QUOTE_PROVIDER: Literal["yfinance","stub"] = "yfinance"` (L1 pydantic-settings gate) + `_start_quote_service` rewired via selector (`main.py:94` agora `get_quote_provider()`; 0 referências diretas a `YFinanceProvider|StubProvider`) + 2 unit-test files novos (selector 4 cases incluindo L2 bypass test + stub 6 cases) + `tests/conftest.py::_UNIT_FILES` estendido + `tests/test_yfinance_provider.py` patch targets `omaha.quotes.provider.yf.Ticker` → `omaha.quotes.provider.yfinance.yf.Ticker` (6 ocorrências; import `from omaha.quotes.provider import YFinanceProvider, map_symbol` intacto via re-export) + 2 specs: `quote-provider` de 7→10 reqs (3 ADDED: selector resolves from settings + StubProvider exists + lives in a package, public names preserved; Purpose TBD substituído), `quote-provider-factory` nova (Purpose + 3 ADDED: selector is single entry point + StubProvider is the test/offline implementation + settings drive the selector) → `task test-unit` 271 pass/2 skip; `task test-integration` 369 pass/2 skip; `task lint` verde; `openspec validate r03-extract-quote-provider-adapter` `valid: true`; refresh-for-test smoke: server 0.0.0.0:8000 + dashboard renderiza + Família option no chip intacta + `db-reset` Italo=6/48/47 Ana=6/52/52
- `2026-07-05-f05-dark-mode-palette-swap` → Register off-white invertido para dark warm-neutral (`--bg: oklch(0.18 0.01 60)`, hue 60 preservado) + 14 tokens em `app.css :root` re-derivados (surface lifts via claridade +0.04, surface-sunk -0.03, accent/positive/negative lightness-lifted com hue idem, swatch 2 hue-shifted para 130, error-bg afundado + error-fg lifted, color-focus hex → OKLCH, status inks invertidos para dark-on-lifted-fills) + `color-scheme: dark` + hex fallback `, #2563eb` removido nos 2 `outline: 2px solid var(--color-focus)` rules + `tests/test_dark_mode_tokens.py` substituiu `tests/test_tokens.py` (17 assertions: body warmth + 6x class swatch contrast + swatch-2 hue ≤ 135 + 4 status-ink pair surfaces + 2 surface lift/sunk + color-focus + body-text contrast + legacy aliases + color-scheme: dark + no prefers-color-scheme + aggregate documented pairs sweep) + `tests/conftest.py::_UNIT_FILES` ganha `test_dark_mode_tokens.py` + DESIGN.md §Color strategy + tabela de tokens + intro §Component inventory + §Migration path reescritas (Phase 2 vira historico; F05 vira current) + PRD §4.10 (off-white → dark warm-neutral; "Inverter nao e introduzir ornamento") + PRD §5.3 (F05 marcado como entregue) + `color-tokens` spec MODIFIED ×3 (sem ADDED/REMOVED, requisitos re-derivados com surface dark warm-neutral) → `src/omaha/static/app.css` (tokens), `tests/test_dark_mode_tokens.py` (novo), `tests/test_tokens.py` (deletado), `tests/conftest.py`, `DESIGN.md`, `openspec/PRD.md`, `openspec/specs/color-tokens/spec.md`, `openspec/roadmap.md` → `task test-unit` 233 pass/2 skip; `task test-integration` 369 pass/2 skip; `task test-bdd` 47 pass (4 pre-existentes T05, fora do escopo); `task lint` verde; `openspec validate` em change e spec `valid: true`; refresh-for-test smoke: server 0.0.0.0:8000 + dashboard renderiza com surface dark + Família option no chip intacta
- `2026-07-05-f07-familia-as-profile-option` → Família promoted from `?view=household` header toggle (F06) to peer `<option>` inside `profile-switcher` chip + new `Profile.is_family_sentinel` column + migration `0017` + User `family` (no password) + Família sentinel row seeded + `Italo RF2` fixture retired (CSV files deleted + `seed_from_csv.py` mapping dropped + `snapshot_to_csv.py` sentinel allow-list updated) + `auth.get_active_profile` short-circuits sentinel + `_real_profiles` helper + `_resolve_view_mode` also checks sentinel + `_sentinel_redirect` for non-patrimonio routes + `select_profile` flips `view_mode="family"` on sentinel bind + `_render_patrimonio` accepts `profile=None` for family view + rebalance/rentabilidade/proventos routes redirect to `/patrimonio?view=household` when sentinel bound + `base.html` 3-option profile-switcher with `<optgroup>` separator + toggle `?view=household` removido do header + CSS `.profile-switcher__optgroup` + Família accent + `household-toggle*` aliases kept for retrocompat + `tests/test_family_aggregate.py` rewrite (toggle tests → sentinel tests) + `tests/test_seed.py` Família sentinel assertions + `tests/test_db_reset_both_profiles.py` 2 real + 1 sentinel expectation + `tests/e2e/selectors.py` `profile_option_family` adds + `family_toggle*`/`household_toggle*` drop + BDD `profile_sharing.feature` scenarios reescritas ("clico em 'Família'" → "seleciono 'Família' no chip") + PRD §5.3 + roadmap slice updated → `src/omaha/models.py`, `alembic/versions/0017_is_family_sentinel.py`, `src/omaha/seed.py`, `src/omaha/auth.py`, `src/omaha/routes/pages.py`, `src/omaha/templates/base.html`, `src/omaha/static/app.css`, `scripts/seed_from_csv.py`, `scripts/snapshot_to_csv.py`, `scripts/reset_both_profiles.py`, `data/seed/italo_rf2_*.csv` (deleted), `tests/test_family_aggregate.py`, `tests/test_seed.py`, `tests/test_db_reset_both_profiles.py`, `tests/e2e/selectors.py`, `tests/bdd/features/profile_sharing.feature`, `tests/bdd/test_scenarios.py`, `openspec/roadmap.md`, `openspec/PRD.md`, `openspec/specs/cross-profile-sharing/spec.md` → `task test-integration`
- `2026-07-05-f06-family-household-full-join-aggregate` → `?view=household` cross-User full-join aggregate (family) + `family_asset_classes` + `family_aggregates` + helpers `_aggregate_classes_by_name` + `_aggregate_assets_by_name` + `view_mode="family"` session flag + `Família` toggle + target_pct suppression + CSS rename (com aliases retrocompat) + tests `test_family_aggregate.py` com cross-User + collapse-by-name + target_pct-not-rendered → `auth.py`, `routes/pages.py`, `templates/base.html`, `templates/patrimonio.html`, `static/app.css`, `tests/test_family_aggregate.py`, `tests/bdd/features/profile_sharing.feature`, `tests/bdd/test_scenarios.py`, `tests/e2e/selectors.py`, `tests/conftest.py` → `task test-integration`
- `2026-07-04-f01-household-cross-profile-consolidation` → `?view=household` querystring + household aggregator + `require_profile_writable` gate (409 `household_read_only`) em 11 mutation endpoints + read-only template branch + header toggle + CSS tokens → `auth.py`, `routes/pages.py`, `routes/classes.py`, `routes/assets.py`, `routes/imports.py`, `routes/rebalance.py`, `templates/base.html`, `templates/patrimonio.html`, `static/app.css`, `main.py` → `task test-integration`
- `2026-07-04-t04-e2e-class-section-alignment-baselines` → `.class-section-header` grid 8→11 cols (mirror `<colgroup>`) → `src/omaha/static/app.css` → `task test-e2e`
- `2026-07-04-t01-bdd-e2e-suite-100-green` → selector centralisation + 12 e2e red fixes + 1 CSS bug + 1 regression test → `tests/e2e/selectors.py`, `tests/e2e/test_selector_inventory.py`, `src/omaha/static/app.css` → `task test-e2e`
- `2026-07-04-f02-top-level-tab-nav-and-patrimonio` → 4 tabs top-level + sidebar removal + rename `/`→`/patrimonio` + new stubs + new spec `patrimonio-portfolio-header` → `templates/base.html`, `templates/patrimonio.html`, `templates/rebalance.html`, `templates/rentabilidade.html`, `templates/proventos.html`, `static/app.css`, `routes/pages.py` → `task test-e2e`

- `2026-06-29-rebalance-engine` → solver CVXPY estável → `src/omaha/rebalance/engine.py`, `src/omaha/rebalance/data_bridges.py` → `task test-integration`
- `2026-06-29-dashboard-inline-edit-friction` → melhorias de UX na edição inline → `src/omaha/static/app.css`, `templates/dashboard.html` → `task test-e2e`
- `2026-06-29-add-db-snapshot` → adiciona `task db-snapshot` (DB → CSV) → `scripts/snapshot_to_csv.py`, `pyproject.toml` → `task db-snapshot`

Onda recente: layout-foundation (F02 → T01 → T04) + household
evolution (F01 → F06 → F07) + theme swap (F05) + refator
estrutural (R03 — quote provider package; R04 — patrimonio
partials) + infra backup (I01) + TLS renewal (I02) +
mutation testing (T03) + CI coverage (T02, deferred) + BDD
step-def (T05) + README refresh (D01). **D02-applied 2026-07-07**
abre frente visual pós-D02: F08 (palette overhaul v2) +
F09 (typography refresh) + F10 (component state language +
table pattern) + F12 (Material Symbols icons) ficam unblocked;
F11 + F13 promoted a Blocked per register decision. Próxima
`next` esperada: F08 (gate D02 resolvido).

## Post-implementation reality check

Para cada fatia `Applied`, anexar antes de mover para `Archived`:

- What changed from original plan: …
- Unexpected issues: …
- Follow-up needed: …

### F01 (archived 2026-07-04)

- **What changed from original plan:** Spec delta clean (3 ADDED requirements, zero MODIFIED/REMOVED on `cross-profile-sharing`). Implementation followed the design's "sibling function" pattern for `household_aggregates` (Decision 5) — kept the function as a thin wrapper over `portfolio_aggregates` to preserve the parallel surface rather than generalising the existing helper. Mutation gating flipped from `HTTPException(detail=...)` to a custom `HouseholdReadOnlyError` + Starlette handler so the wire shape stays exactly `{"reason": "household_read_only"}` with no FastAPI `{"detail": ...}` wrapping. PRD §5.3 marked the candidate as delivered inline (no separate change file).
- **Unexpected issues:** (a) The integration autouse fixture initially deleted Ana's profile in `test_toggle_hidden_with_one_profile` but didn't restore it on the next run — leaked into later tests in the suite. Fixed by making the fixture re-add Ana's profile + drop synthetic Italo profiles + restore the canonical "Italo RF2" before each test. (b) The default app seed creates two separate Users (Italo + Ana), not one user with two profiles — the F01 spec scenario ("viewer owns two profiles") doesn't match the seed. Tests add a synthetic "Italo RF2" profile to Italo's User row to exercise the multi-profile scenario; the cross-profile leakage test (intra-User invariant) uses the actual seeded two-User setup.
- **Follow-up needed:** None blocking. The BDD scenario "Operador ativa o modo agregado da casa via toggle" was added but the live BDD suite wasn't executed (out of scope for `next`). R04 (partialize `patrimonio.html`) now operates on a template that has one extra branch (`{% if view == 'profile' %}`); the partialization should preserve the read-only conditional.

### T01 (archived 2026-07-04)

- **What changed from original plan:** Slice landed in two phases.
  Phase 1 was the original scope (selector centralisation +
  `profile-name` → `profile-switcher` + URL regex + inventory
  smoke + patrimonio-actions regression + align baselines). Phase
  2 was triggered by the live `task test-e2e` run after the F02
  archive: 12 red tests expanded to 15 once the Playwright session
  fixture could actually exercise the post-F02 UI. Resolved in
  this phase: Bem-vindo assertion (h1 chip retired), rebalance
  test class-name mismatch (RF Pós vs Renda Fixa), CVXPY engine
  policy strings (vs stub-fixture-v1), per-page selector subset
  for the inventory smoke, and a real **CSS bug** — F02 widened
  the asset table from 8 → 11 columns but `<colgroup>` rules
  were never extended. Test was rewritten to the structural
  invariant (sum-to-table-width + no-collapsed-column).
- **Unexpected issues:** (a) `test_user_journey_rebalance.py`
  hangs in this environment after seeding 43 assets via import —
  chromium stalls with no progress markers, even after `kill -9`.
  Excluded from this verification; investigate on next CI run.
  (b) The rebalance e2e tests assumed the legacy stub solver's
  `applied_policy == "stub-fixture-v1"`; production swapped to
  CVXPY long before this slice. Same drift class as (a): tests
  weren't tracking production surface changes. (c) The class
  name created by `_create_three_classes` is `"RF Pós"` not
  `"Renda Fixa"`; e2e tests that used the latter silently dropped
  one asset per run because the CSV class auto-match failed.
  All three are symptoms of "tests written once, never
  re-validated against the actual UI" — T01's selector
  inventory smoke + BDD rework are the structural mitigations.
- **Follow-up needed (resolution log):**
  - BDD feature-text drift (4 failures: `+ Nova classe` step no
    longer matches because the sidebar is gone) →
    **slice T05** (`t05-bdd-step-def-drift-after-f02`).
    Promoted in Recommended Execution Order; awaiting execution.
  - `test_class_section_alignment.py` pixel baselines →
    **resolved in T04** (CSS bug, not a baseline drift). T04
    archived 2026-07-04.
  - `test_user_journey_rebalance.py` hang → **deferred**.
    Likely environmental (chromium stalls under the BDD
    suite's parallel uvicorn; passes in isolation).
    Investigate on next CI run.

### F02 (archived 2026-07-04)

- **What changed from original plan:** Sin cambios funcionales —
  el layout entregue coincide con el mock 2026-07-03. Stub pages
  `/rentabilidade` y `/proventos` renderizan "Em construção" según
  D6. Routes finales PT-BR (`/patrimonio`, `/rebalanceamento`,
  `/rentabilidade`, `/proventos`) sin alias para legacy.
- **Unexpected issues:** Tasks file en
  `openspec/changes/archive/2026-07-04-f02-top-level-tab-nav-and-patrimonio/tasks.md`
  quedó con 53/53 checkboxes sin marcar (`- [ ]`) al momento del
  archive — el roadmap marcaba `Applied` pero el archivo no se
  había actualizado durante el apply. No bloqueó el archive (skill
  guardrail: no bloquear por warnings, sólo informar). Si vuelve a
  pasar, promover checkmark automático en `openspec-apply-change`.
- **Follow-up needed:** F03 (Rentabilidade) y F04 (Proventos)
  substituien los stubs. R04 (partialize `patrimonio.html`)
  depende de F02 — ahora desbloqueado.

### F06 (archived 2026-07-05)

- **What changed from original plan:** Sibling function pattern
  (F01 Decision 5) carried over — `family_aggregates` is a fresh
  function, not a parametrization of `portfolio_aggregates`.
  Decided to write `_aggregate_classes_by_name` +
  `_aggregate_assets_by_name` as private helpers in `pages.py`
  rather than touch `_compute_class_totals` (which is the shared
  inner kernel). The F01 `household_asset_classes` /
  `household_aggregates` were kept and marked DEPRECATED rather
  than deleted, per task 1.5 — delete is a follow-up R-slice
  refator. The session flag rename (`view_mode` from `"household"`
  to `"family"`) was implemented with a compat read-back in
  `require_profile_writable` so any stale in-flight request or
  session cookie from a previous deploy does not silently bypass
  the gate. The JSON 409 wire body stays exactly
  `{"reason": "household_read_only"}` (D-F06.5) — no consumer
  breakage. The CSS rename kept the legacy `.household-toggle` /
  `.app-header__household-chip` selectors as CSS aliases so any
  hand-rolled `<form class="household-toggle">` markup survives
  the cutover.
- **Unexpected issues:** (a) The e2e selector inventory
  (`tests/e2e/test_selector_inventory.py`) flagged the new
  `family_toggle*` + `household_toggle*` entries on the first
  apply run because the legacy testid (`data-testid="household-toggle"`)
  was removed from the template. The fix: use an OR-pattern in
  the SELECTORS dict (`[data-testid="family-toggle"],
  [data-testid="household-toggle"]`) so both names resolve
  against the same element. Plus `family_toggle_exit` /
  `household_toggle_exit` are excluded from `DASHBOARD_SELECTORS`
  because they only render in family mode. (b) The BDD feature
  rewrite initially used "E estou logado como 'Ana'" (And step)
  after a `Quando` — pytest-bdd inherited the @when key from the
  previous step and rejected the @given step. Replaced the And
  with `Dado` to keep the Given/When/Then type chain clean. (c)
  The OpenSpec archive command failed on the first attempt
  because the F06 delta's MODIFIED header
  ("family-wide aggregate view mode") did not match the main
  spec's existing header
  ("household aggregate view mode"). The spec reuses the F01
  header and marks it MODIFIED rather than renaming the
  requirement — keeps the `?view=household` querystring name
  coherent with the spec identifier.
- **Follow-up needed:** (a) The pre-existing 4 BDD failures
  (`+ Nova classe` selector drift) and 5 e2e timeouts (chromium
  stalls on long journeys) are unchanged by F06 — they are T05
  and T01 follow-ups, not F06 regressions. (b) Delete
  `household_asset_classes` / `household_aggregates` in a future
  R-slice refator once consumers are migrated. (c) If
  per-User authentication is ever introduced, F06 needs a gate
  (D-F06.1 caveat) — the cross-User aggregate currently
  leverages the shared family password (PRD §1.2).

### F07 (archived 2026-07-05)

- **What changed from original plan:** Sentinel profile landed
  in place of the F06 header toggle. Two infra surprises:

  (a) The F06 `view_mode` session flag was kept (not renamed to
  `active_mode` per the proposal's Decision 2) because the
  `require_profile_writable` dep already accepts both `"family"`
  and `"household"` for cutover (D-F06.5) and the rename would
  have touched every wire-level assertion in
  `tests/test_family_aggregate.py`. The `select_profile` handler
  sets `view_mode="family"` on sentinel bind; the read-only gate
  fires the same as F06 — no audit-log regression.

  (b) The `_resolve_view_mode` helper grew a `db: DbSession` arg
  so it can resolve the Família sentinel directly from
  `active_profile_id` without relying on `get_active_profile`
  (which short-circuits to `None` for sentinel rows). Same shape
  as the F06 querystring check — adds one DB roundtrip on
  every request, but the sentinel query is a primary-key lookup
  on a tiny table and the route's main work is the eager-loaded
  class walk. Not a measured bottleneck.

  (c) The Família option's visible label was originally
  "Família (agregado)" (per task 3.3) and got simplified to
  "Família" via an immediate owner-driven follow-up
  (post-archive), confirmed in `tests/test_family_aggregate.py`
  + BDD `profile_sharing.feature`. The internal `data-testid`
  ("profile-option-family") stays as-is — the testid is the
  stable hook.

  (d) `data/seed/italo_rf2_*.csv` files were deleted (not just
  the canonical seed `HOUSEHOLD_FIXTURE_PROFILES`) because the
  wrapper `scripts/reset_both_profiles.py` iterates only the
  canonical `PROFILES` tuple (D3 — keep it clean). The
  `snapshot_to_csv.py` allow-list moved from `{"Italo RF2"}` to
  `{"Família"}` (F07 sentinel doesn't own CSV triplets).

- **Unexpected issues:** (a) The autouse fixture in
  `tests/test_family_aggregate.py` initially failed to re-create
  the Família sentinel because SQLAlchemy's identity map
  returned the pending-deleted `User("family")` from a flush-less
  delete. Fixed by adding `db.flush()` before
  `_ensure_family_sentinel(db)` so the sentinel-detection query
  sees a clean state. Same class of bug as F01's "Ana profile
  leak between tests" — autouse fixtures that delete-and-recreate
  rows in the same session need an explicit flush.

  (b) `test_db_reset_both_profiles.py` was anchored on the F01
  "3 profiles including Italo RF2" expectation. The post-F07
  shape is "2 real + 1 sentinel" — the test was rewritten to
  assert `[Italo, Ana, Família]` and exempt the Família row
  from the "classes > 0" check (sentinel is intentionally
  empty).

  (c) The chip-select onchange handler (`this.form.action = ...;
  this.form.submit()`) still works unchanged — the Família
  sentinel is just another `<option value="N">` and the same
  client-side pattern handles it. No JS rewiring was needed.

  (d) `task test-e2e` still has 5 pre-existing chromium stalls
  (`test_user_journey.py` + `test_user_journey_rebalance.py`)
  and `task test-bdd` still has 4 pre-existing T05 failures.
  Neither is an F07 regression. F07 added 2 new BDD scenarios
  (chip-Família activate + symmetry) and they pass cleanly.

- **Follow-up needed:** (a) Delete `household_asset_classes` /
  `household_aggregates` in a future R-slice (F07 inherits the
  F06 deferred cleanup). (b) The `_sentinel_redirect` helper
  for /rebalanceamento, /rentabilidade, /proventos currently
  redirects to `/patrimonio?view=household` — these routes
  could grow their own family-view templates in a future slice
  if owner wants Família to have its own Rentabilidade/Proventos
  surfaces. Out of scope for F07. (c) The `Profile.is_family_
  sentinel` flag is advisory (no DB CHECK); if a future slice
  ever creates a second Família row by accident, the
  `_resolve_view_mode` helper picks the first match. The
  canonical seed is the single producer — non-issue today.


### F05 (archived 2026-07-05)

- **What changed from original plan:** F05 deliverou o swap planejado integral — 14 tokens em `:root` invertidos (bg → L≈0.18 hue 60, surface lifts por claridade, status fills lightness-lifted, swatch 2 hue-shifted para 130), `color-scheme: dark`, `tests/test_dark_mode_tokens.py` substituiu `tests/test_tokens.py` com 17 assertions, e o contrato visual da `color-tokens` spec foi re-derivado com 3 requirements MODIFIED (sem ADDED/REMOVED). Plan vs real divergiu em um ponto: a task list mencionava `tests/test_phase02_tokens.py` mas o arquivo real era `tests/test_tokens.py` (Phase 2 PALT-01/02 era o suite active; o nome do arquivo tinha sido encurtado em algum momento pré-F05). Adaptei in-loco sem reabrir o proposal — o contract testado é o mesmo.
- **Unexpected issues:** (a) As linhas `outline: 2px solid var(--color-focus, #2563eb)` (2 ocorrências) carregavam um fallback hex herdado da era pré-F05 que sobreviveu ao Phase 2. Com `--color-focus` agora sempre presente, o fallback é morto e potencialmente confuso. Removi o fallback nas duas linhas durante o apply (estava dentro do escopo "limpar hex hardcodes moribundos" do §1 audit, não no proposal explícito). (b) Os tokens `--bg-hover` e `--alert-warn` (sem task explícita na F05) também foram lightness-lifted para o novo contexto escuro, porque sem o lift eles ficam invisíveis: `--bg-hover` original `oklch(0.93 0.003 60)` sobre `--bg` escuro praticamente some (delta de L ≈ 0.75), e `--alert-warn` original `oklch(0.70 0.12 85)` continua legível mas perde contraste sobre o novo `--bg`. Ambos lifts sigam o pattern das outras superfícies (sem hue-shift). (c) O `outline: 2px solid var(--color-focus)` ainda é o único consumer de `--color-focus` que vi nos templates — o token continua sendo só "para este outline + outline-offset". Se futuro render de focus border em inputs reusar esse token, já está pronto.
- **Follow-up needed:** (a) Auditoria hex legacy sobrevivente (proposta no Polish pass): `background: #fff` (8 ocorrências em `.class-color-swatch`, `.btn`, `.import-page`, `.class-table` etc.) e `color-mix(in srgb, #<hex> 38%, var(--surface))` em `.import-class-cell--cls-{0..7}` (8 linhas). Esses 38% tints eram calibrados para `--surface = white`; agora sobre `--surface = dark warm-neutral` eles provavelmente ficam mais saturados que o desejado. R-slice dedicada: migrar `background: #fff` para `var(--surface)` e o color-mix para `var(--class-N)` ou um novo `--class-N-tint`. Fora do escopo F05 (F05 era só token swap, não hex sweep) — registrei no §Polish pass da DESIGN.md como residual. (b) Visualmente, o owner ainda precisa confirmar no browser que o surface lê como "domestic warm-neutral dark" e não como "GitHub cold dark"; o feedback entra via conversa + iterar swatch-2 hue ou focus chroma se colidir visualmente. (c) Nenhum regressão funcional: `task test-integration` mantém 369 pass / 2 skip (mesmo número pré-F05); `task test-unit` subiu de 223 para 233 pass (10 dark-mode tests novos); `task test-bdd` mantém as 4 fail pre-existentes do T05 selector drift — confirmado com `git stash` que essas falhas nada têm a ver com F05.

### T02 (archived 2026-07-06 — GH Actions deferred per owner)

- **What changed from original plan:** Slice landed the local infra (pyproject.toml coverage config + .gitignore + workflow file) as planned. **Two divergences** documented in `archive/2026-07-06-t02-coverage-report-in-ci/tasks.md` §5: (a) `task coverage` was rewritten to use `-m "unit or integration"` (not in the original proposal). Reason: with the global `addopts` adding cov machinery to every pytest call, running the full `pytest` (no marker filter) hit a 10+ min timeout because BDD serial adds heavy coverage instrumentation overhead. Restricting to unit+integration keeps `task coverage` at 3 min and preserves the "code coverage vs behavior coverage" split from D-T02.2. (b) **GH Actions verification was attempted but not finalized.** 5 runs were pushed to `main`; lint + test-unit went green from run 4; test-integration/test-bdd/coverage stalled on db-reset + env-config issues; fixes were committed at every step but the final end-to-end green never happened. Owner decision 2026-07-06: pause GH Actions entirely because "desenvolvimento ainda é local". Workflow file stays in `.github/workflows/ci.yml` as dormant infra ("útil no futuro").
- **Unexpected issues:** (a) `actions/setup-python@v5` does NOT accept `cache: "uv"` — only pip/pipenv/poetry. Had to swap for `astral-sh/setup-uv@v4` + manual `actions/cache@v4` keyed on `hashFiles('uv.lock')`. The design.md D-T02.8 explicitly considered this trade-off and chose wrong. (b) `astral-sh/setup-uv@v4` accepts `python-version` (string, e.g. "3.12"), not `python-version-file`. `.python-version` file is still the single source of truth locally — workflow just hardcodes the resolved version. (c) `uv sync --extra dev` fails because the project uses PEP 735 `[dependency-groups]` (not `[project.optional-dependencies]`). Correct flag is `--group dev`. (d) CI runner has no DB schema. Tests assumed `data/portfolio.db` exists. Fix: add explicit `Reset database` step (`uv run task db-reset`) before every test run that hits the DB; inject `SECRET_KEY` + `ADMIN_PASSWORD` env vars (CI-only, never reach production config). (e) Pre-existing BDD flake `test_import_happy_auto_match[Ana]` ("esperava 0 linhas unmatched, vi 4") surfaced at run 4 — same class of flake documented in F07 follow-up; out of scope T02.
- **Follow-up needed:** (a) Reactivation path documented in `archive/2026-07-06-t02-coverage-report-in-ci/tasks.md` §5. Last committed workflow (commit `bac8b47`) has all 5 fixes accumulated; next push should pass — barring new flakes. (b) Investigate the BDD flake separately (pre-existing, surfaced only because T02 made the integration job fail loudly). (c) Decide whether to add `--cov-fail-under` threshold once owner picks a coverage floor (D-T02.4 deferred — separate slice). (d) If/when GH Actions reactivates, consider pinning `actions/checkout@v4` to a major-version commit SHA per repo security baseline (out of scope T02; latent risk). (e) The `addopts` global change has a small DX cost: every `pytest` invocation now triggers cov machinery (overhead ~1s per single test). Acceptable per D-T02.5 trade-off; can be revisited if devs complain. (f) **GH Actions is OFF for now** — repo runs no CI. Pre-push pytest hook (per `prek.toml`) still gates local pushes with unit + integration tests; BDD + coverage remain taskipy commands.

### T05 (applied 2026-07-06)

- **What changed from original plan:** T05 lands 1:1 com o proposal — `STEP_CLICK_ALIASES` dict declarada no topo de `tests/bdd/step_defs/common_steps.py` (acima de `click_button`) com 2 entradas (`+ Nova classe` → `(empty-state-create-class, new-class-modal-submit)` e `+ Novo ativo` → `dashboard-add-asset-open`), cada uma com comment inline citando F02 como o slice de origem (D-T05.1 + spec requirement "Aliases are documented inline"). `click_button` body estendido: alias chain consultada **antes** dos 3 default candidates, mesmo two-phase visibility filter (5s `wait_for` + `locator(visible=true)`), fallthrough para o default sequence se nenhum alias casar (D-T05.2). Signature byte-idêntica ao pré-T05 verificada via `inspect.signature` — `(page: Page, label: str)` literal. Gherkin rewrites: 4 step calls trocadas (`clico em "+ Nova classe"` → `clico em "Nova Classe"`) em 2 feature files (`class_crud.feature:65` + `profile_sharing.feature:17, 21, 37`). Spec nova `bdd-step-def-aliases` consolidada em `openspec/specs/bdd-step-def-aliases/spec.md` (Purpose + 1 requirement + 3 scenarios). **Zero divergência de plano.** Detalhe cosmético: o docstring da dict ficou mais comprido do que os exemplos em `design.md` D-T05.1 (11 LOC vs 5 LOC) porque inclui o rationale F02 + um parágrafo sobre a tuple `'+ Novo ativo'` ser preventive entry, não reaction. Byte-equivalente ao spec contract.
- **Unexpected issues:** (a) O `STEP_CLICK_ALIASES` ficou declarado **entre** `_PT_LABEL_TO_TESTID_SLUG` (F01/F02 era usada pelo `fill_field`) e `click_button` — não acima dos 4 @given/@when de auth profile-pick. Isso é o que o spec requirement diz ("above the `click_button` function definition"), então conforms ao contract, mas a posição pode confundir futuros leitores que esperariam "no topo do módulo". Mitigação: o header do map inclui 3 linhas de docstring explicando o que é + a referência da spec. (b) O segundo tuple entry `[data-testid="new-class-modal-submit"]` (fallback do modal Salvar) é citado no design mas não exercitado no suite BDD atual — todos os 4 step calls reescritos clicam no trigger antes do modal abrir, então o fallback é safety net nunca acionado. Confirmado em `task test-bdd` (51 passed / 0 fallthrough path exercised). (c) A grep por `+ Nova classe` ainda retorna 6 hits após as 4 reescritas, mas o task 2.3 sanity check considerava apenas step calls em `.feature` files: os 6 hits remanescentes são (1) a própria chave do alias map em `common_steps.py:118` (intencional), (2) 2 docstrings em `_workflows.py` (historical narrative), (3) 2 docstrings/comment headers em `class_steps.py:9, 76` (historical narrative), (4) `tests/bdd/README.md:57` (referência à affordance da era sidebar). Nenhum é step call Gherkin — intent do sanity check passa; contagem literal não.
- **Follow-up needed:** (a) O spec `bdd-step-def-aliases` requirement "Aliases are documented inline with the originating F-slice" força PR review sobre o alias map — mitigação do R1 em design.md. Se a tabela passar de ~10 entradas, próximo T-slice promove para `tests/bdd/step_defs/_aliases.py`. (b) Drift de outros botões (`+ Novo ativo`, `+ Importar CSV`) não está sendo prevenido por step calls ativos hoje; se algum cenário E2E/BDD futuro exercitar `clico em "+ Importar CSV"` contra a affordance pós-F02 (`data-testid="dashboard-import-csv-open"` ou similar), adicionar a entrada. Por ora a entrada `+ Novo ativo` é o único preventive simétrico. (c) **Archived 2026-07-06** via `next` gate: folder `openspec/changes/t05-.../` → `archive/2026-07-06-t05-.../`; spec delta já consolidada em main spec antes do archive (diff == empty); `openspec validate bdd-step-def-aliases` `valid: true` pós-archive. Próximo gate executivo do roadmap → T02 (coverage in CI, T-slice `Ready` por Recommended Execution Order). (d) Se o owner decidir reabrir F03/F04 (proventos/rentabilidade) no futuro, o matcher pode precisar de aliases para "Salvar" / "Confirmar" (botões de modais de evento) — fora do escopo T05.

### R03 (archived 2026-07-06)

- **What changed from original plan:** Slice landed in two halves aligned with the design's split between "fetch contract" (the package itself) and "runtime seam" (the selector). The package split into four submodules landed as designed (protocol + mapper + yfinance + stub + re-exporting __init__). The L1/L2 defense pattern also landed (pydantic `Literal` rejects at construction time; selector raises `ValueError` defense-in-depth). Two divergences from the plan: (a) `tests/test_yfinance_provider.py` was NOT a no-op as task 7.1 speculated — the test patches `omaha.quotes.provider.yf.Ticker`, and after the move `yf` lives at `omaha.quotes.provider.yfinance.yf`. All six patch targets had to flip. Caught at the first `task test-unit` run (collection-time `AttributeError`). (b) `tests/test_quote_provider_selector.py::test_unknown_provider_name_raises_value_error` initially tried `Settings(QUOTE_PROVIDER="brapi")` — pydantic-settings Literal already raises at construction, so the test never reached the selector's L2 path. Fixed by mutating the attribute directly to bypass L1 (`fake_settings.QUOTE_PROVIDER = "brapi"`). The bypass shape is the precise case the L2 `ValueError` exists for (per D-R03.2 / R-R03.b rationale).
- **Unexpected issues:** (a) `tests/test_quote_provider_selector.py` originally imported `from typing import TYPE_CHECKING` with a stub `if TYPE_CHECKING: pass` block — removed during ruff format pass (F401 unused-import + dead-block). (b) `src/omaha/quotes/provider/__init__.py` originally imported `from omaha.config import Settings` inside `if TYPE_CHECKING:` for the docstring `:attr:` cross-reference — ruff F401 flagged it as unused. Dropped the TYPE_CHECKING block entirely; the docstring still references `Settings.QUOTE_PROVIDER` and reads correctly. (c) `src/omaha/config.py` import order had `from typing import Literal` placed between `import sys` and the third-party imports — ruff I001 sorted it above `from pydantic import Field` (correct Python 3 convention: stdlib before third-party). One-line `--fix`. (d) `pgrep` post-launch initially showed two uvicorn PIDs (the `uv run` wrapper + the actual python child) but only the python child held the port — both are gone after kill -9 via the next refresh-for-test cycle.
- **Follow-up needed:** (a) Delete `household_asset_classes` / `household_aggregates` and the F01 `view_mode="household"` session key helpers in a future R-slice — `require_profile_writable` still has the read-back for `"household"` because the cutover kept backwards compat, but the F01 surface is no longer reached (F06 + F07 archived before R03). (b) `_quote_provider_selector_stub` test never runs against a real network outage — unit-only means the L2 `ValueError` path is exercised by the bypass test, not by an env var. A future integration test (under `tests/integration/`) could set `os.environ["OMAHA_QUOTE_PROVIDER"]` before app boot and assert the pydantic gate fires; out of scope for R03. (c) `tests/conftest.py::_UNIT_FILES` continues to grow — T05 + R03 + future R-track slices may push past the 25-item frozenset; the marker rule still tags unknown paths as `unit` with an `UnknownTestPath` warning. No blocker today.

### R04 (archived 2026-07-06)

- **What changed from original plan:** Slice landed clean. The proposal's 6-partial structure held (actions / portfolio_header / distribution / class_section / empty_states / add_asset_modal) but the **`add_asset_modal` partial ended up carrying all three modals + the Alpine `<script>` block** instead of just the add-asset modal — the line range "511-end" in the proposal expanded to 2186 (vs the original 600 estimate) because the class-section loop grew past 300 lines and the modals + Alpine script already lived in that range. Splitting per modal would have forced the Alpine `<script>` block to live in a separate partial from the modals that depend on `$store.addAssetModal` / `$store.newClassModal` / `$store.importModal`, and would have required either re-declaring the same `window.__assetClasses` array in each partial or splitting the Alpine init event listener. Both options would have created a worse file-level organisation than keeping the three modals + script together as a single "modals + Alpine" partial. The proposal's intent (6 partials, one section each) is preserved; the section name is slightly broader (`add_asset_modal` covers all three modals + the script). Documented in `tasks.md` 2.6 notes.

- **Unexpected issues:** (a) The first round of partials used the original source indentation (2 spaces inside the partial content), but `{% include %}` does not modify leading whitespace — the shell's indentation before the include directive adds to the partial's content. The first draft produced visible-DOM whitespace bloat (extra 2 spaces of indent per line). Fixed by adjusting shell indentation at each include site and accepting the partial-content-as-written indent (the byte-equivalence requirement is "modulo whitespace inside Jinja control tags", so the diff is whitespace-only and acceptable). (b) The `_patrimonio_add_asset_modal.html` partial is 1682 lines — about 80% of the original file size. It is dominated by the 1247-line Alpine `<script>` block (sort comparator + `classSection` factory + 3 Alpine stores). Splitting this block into its own file would break the rendering-context coupling (`{% for c in class_aggregates %}` inside the script needs the same Jinja context the modals use) and create an artificial boundary inside one Alpine init event. The design pattern from `_rebalance_plan.html` (one partial per section, no further splits) supports keeping the script inline. (c) The render-diff comparison used `grep -v '^[[:space:]]*$'` to filter blank lines first — that returned 0 differences for all three variants (Italo default / family / Ana), proving the refactor is semantically byte-equivalent at the rendered HTML level. The full diff (with blank lines) shows ~6500 lines of whitespace-only changes, which is within the "modulo whitespace inside Jinja control tags" tolerance the task explicitly allows.

- **Follow-up needed:** (a) `_patrimonio_class_section.html` (331 lines) is the largest "real" partial — if a future slice needs to add substantial logic (e.g. a chart per class, multi-asset bulk edit), split it further into `_patrimonio_class_section_header.html` + `_patrimonio_class_section_table.html` + `_patrimonio_class_section_modals.html`. Out of scope for R04; future R-slice follow-up. (b) The 4 BDD failures (`+ Nova classe` selector drift) and 5 e2e chromium stalls remain unchanged post-R04 — confirmed via `git stash` baseline diff. They are T05 and T01 follow-ups respectively, not R04 regressions. (c) `openspec/specs/patrimonio-template-partials/spec.md` was added via sync — 4 ADDED requirements (shell + partials layout, per-section verbatim rendering, underscore-prefix naming, rendered-HTML byte-equivalence). Spec count went from 39 → 40.

### I01 (archived 2026-07-06)

- **What changed from original plan:** Slice landed with one decision-flip in the apply gate. Tasks 1.4 + 3.1 originally assumed a one-shot `backup` command as a placeholder to be replaced by the scheduler — I rewired the `prod.yml` `backup-scheduler.command` to `python -m scripts.backup_scheduler` directly in §1 (skipped the placeholder) to avoid a two-step cutover that would have left a non-functional service between the apply and the rewire. Diff cost: zero, spec coverage unchanged. Also added `BACKUP_DEST_DIR` env override (not in the original proposal) to enable the local smoke test (5.1) — without it the scheduler would write to `/backups` and need root in dev; with it, the smoke test writes to `./backups` matching the manual `task backup` convention.
- **Unexpected issues:** (a) **`Dockerfile` does not copy `scripts/` into `omaha:prod`** — pre-existing gap. Both the manual `backup` service (profile `backup`, one-shot) and the new `backup-scheduler` (default up) fail in production with `ModuleNotFoundError: No module named 'scripts'`. This was out of scope for I01 (the spec does not require touching the Dockerfile) but it materially blocks the slice's primary value (scheduled backups). Recorded in caveat on `Applied` progress + follow-up needed below. (b) The validation 2.4 case `BACKUP_INTERVAL=""` initially allowed an empty string through because `int("")` raises `ValueError` (caught by the generic handler) but I wanted a clear "must be a positive integer" message; rewrote to check `not s.isdigit()` first. (c) Smoke test 5.2 (`/nonexistent-dir-x9q`) confirmed the failure-tolerant loop works as designed — 5 ERROR log lines, container does not exit, killed by SIGINT after 5 failures. Side note: subprocess output from `scripts/backup.py` is not captured to the log (only the exit code is), so the operator sees the exit code but not the failure reason — registered as a future enhancement (could pipe `stderr` to the log line).
- **Follow-up needed:** (a) **`Dockerfile COPY scripts ./scripts`** — required to make both `backup` and `backup-scheduler` actually function in production. Slice candidate `I03 - Copy scripts/ into prod image` (or merge with I02 if both touch the Dockerfile). (b) Pipe `scripts/backup.py` stderr to the scheduler log line so operators see the failure reason, not just the exit code. Trivial change in `backup_scheduler.py` (capture `subprocess.run(..., capture_output=True)` and prepend `stderr.decode()` to the ERROR log). (c) Schedule jitter — `sleep BACKUP_INTERVAL` blocks a strict 86400s cadence; a backup that takes 30s shifts every run by 30s. Not a correctness issue today (no exact-time expectations) but worth a future note if cadence guarantees tighten. (d) `openspec/specs/backup-scheduling/spec.md` created from delta at archive — 6 ADDED requirements (scheduled service, configurable interval, failure tolerance, timestamped filename, disable without touching other services, restart policy). Spec count: 40 → 41. (e) Pre-existing `backup` service (one-shot, profile `backup`) retains its `command: python -m scripts.backup` — I01 did not touch it; if a future slice retires the profile-based manual backup in favour of the always-on scheduler, that retirement is a separate decision (D-F01.1-style).

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
