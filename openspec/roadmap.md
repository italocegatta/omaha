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

### T05 - BDD step-def drift after F02 sidebar removal
Status: `Ready`
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
Status: archived 2026-07-04 (`f01-household-cross-profile-consolidation`)

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

### D01
Depends on: F01, F02, F03, F04, F05 (reflete surface pós-slice)
Blocks: none
Can run in parallel: yes

## Recommended Execution Order

Prioridade presume que o owner quer atacar mudanças estruturais primeiro
(rebalance + páginas), qualidade em paralelo, e docs/infra no fim.

1. R01 - cleanup (zero risk, prep do repo) — archived
2. F02 - tab nav + side panel removal + stubs (foundation para F03-F04) — archived
3. F01 - household cross-profile (paralela a F02 — não bloqueia) — archived 2026-07-04 (superseded by F06)
4. F06 - family full-join aggregate cross-User (substitui semântica F01; arquivada 2026-07-05)
5. F07 - família como opção no profile-switcher (peer de Italo/Ana; dependente de F06; próxima fatia a executar)
6. F03 - rentabilidade page (substitui stub criado em F02)
7. F04 - proventos page (substitui stub criado em F02)
8. F05 - dark mode palette swap
9. R02 - revise CSV seed system
10. R03 - extract quote_provider adapter
11. R04 - partialize patrimonio template (depende de F02)
12. T05 - BDD step-def drift after F02 (promoted 2026-07-04 — fecha o loop de follow-up de T01; mudança mecânica pequena)
13. T01 - BDD + e2e 100% green — archived
14. T02 - coverage in CI
15. T03 - mutation testing rebalance
16. I01 - backup scheduling
17. I02 - TLS cert renewal automation
18. D01 - README refresh (último — reflete tudo acima)

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
- **T05 promovido 2026-07-04** (de T-block final para imediatamente
  após R04): o único follow-up aberto de T01, mudança mecânica
  pequena, depende só do slot F02 (já arquivado). Rodar antes de
  T02/T03 limpa a suíte BDD antes de investimento em tooling de
  coverage/mutation.
- T03 fica depois de R03 porque a fatia de mutation testing pode
  aproveitar adapter mais limpo para mockar providers. Se durante
  apply de T03 essa vantagem não se confirmar, mover T03 para antes
  de R03 sem outra consequência.
- D01 no fim: doc precisa refletir surface pós-F-slice (regras §4.10
  e features block mudam com F05 e F01-F04; PRD §5.3 precisa refletir
  Rebalanceamento top-level após F02; F06 adiciona "agregado cross-User
  família" no bloco de features).

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

---

## Compacted history

Últimas 8 fatias arquivadas (compile manualmente do diretório
`openspec/changes/archive/`):

- `2026-07-05-f07-familia-as-profile-option` → Família promoted from `?view=household` header toggle (F06) to peer `<option>` inside `profile-switcher` chip + new `Profile.is_family_sentinel` column + migration `0017` + User `family` (no password) + Família sentinel row seeded + `Italo RF2` fixture retired (CSV files deleted + `seed_from_csv.py` mapping dropped + `snapshot_to_csv.py` sentinel allow-list updated) + `auth.get_active_profile` short-circuits sentinel + `_real_profiles` helper + `_resolve_view_mode` also checks sentinel + `_sentinel_redirect` for non-patrimonio routes + `select_profile` flips `view_mode="family"` on sentinel bind + `_render_patrimonio` accepts `profile=None` for family view + rebalance/rentabilidade/proventos routes redirect to `/patrimonio?view=household` when sentinel bound + `base.html` 3-option profile-switcher with `<optgroup>` separator + toggle `?view=household` removido do header + CSS `.profile-switcher__optgroup` + Família accent + `household-toggle*` aliases kept for retrocompat + `tests/test_family_aggregate.py` rewrite (toggle tests → sentinel tests) + `tests/test_seed.py` Família sentinel assertions + `tests/test_db_reset_both_profiles.py` 2 real + 1 sentinel expectation + `tests/e2e/selectors.py` `profile_option_family` adds + `family_toggle*`/`household_toggle*` drop + BDD `profile_sharing.feature` scenarios reescritas ("clico em 'Família'" → "seleciono 'Família' no chip") + PRD §5.3 + roadmap slice updated → `src/omaha/models.py`, `alembic/versions/0017_is_family_sentinel.py`, `src/omaha/seed.py`, `src/omaha/auth.py`, `src/omaha/routes/pages.py`, `src/omaha/templates/base.html`, `src/omaha/static/app.css`, `scripts/seed_from_csv.py`, `scripts/snapshot_to_csv.py`, `scripts/reset_both_profiles.py`, `data/seed/italo_rf2_*.csv` (deleted), `tests/test_family_aggregate.py`, `tests/test_seed.py`, `tests/test_db_reset_both_profiles.py`, `tests/e2e/selectors.py`, `tests/bdd/features/profile_sharing.feature`, `tests/bdd/test_scenarios.py`, `openspec/roadmap.md`, `openspec/PRD.md`, `openspec/specs/cross-profile-sharing/spec.md` → `task test-integration`
- `2026-07-05-f06-family-household-full-join-aggregate` → `?view=household` cross-User full-join aggregate (family) + `family_asset_classes` + `family_aggregates` + helpers `_aggregate_classes_by_name` + `_aggregate_assets_by_name` + `view_mode="family"` session flag + `Família` toggle + target_pct suppression + CSS rename (com aliases retrocompat) + tests `test_family_aggregate.py` com cross-User + collapse-by-name + target_pct-not-rendered → `auth.py`, `routes/pages.py`, `templates/base.html`, `templates/patrimonio.html`, `static/app.css`, `tests/test_family_aggregate.py`, `tests/bdd/features/profile_sharing.feature`, `tests/bdd/test_scenarios.py`, `tests/e2e/selectors.py`, `tests/conftest.py` → `task test-integration`
- `2026-07-04-f01-household-cross-profile-consolidation` → `?view=household` querystring + household aggregator + `require_profile_writable` gate (409 `household_read_only`) em 11 mutation endpoints + read-only template branch + header toggle + CSS tokens → `auth.py`, `routes/pages.py`, `routes/classes.py`, `routes/assets.py`, `routes/imports.py`, `routes/rebalance.py`, `templates/base.html`, `templates/patrimonio.html`, `static/app.css`, `main.py` → `task test-integration`
- `2026-07-04-t04-e2e-class-section-alignment-baselines` → `.class-section-header` grid 8→11 cols (mirror `<colgroup>`) → `src/omaha/static/app.css` → `task test-e2e`
- `2026-07-04-t01-bdd-e2e-suite-100-green` → selector centralisation + 12 e2e red fixes + 1 CSS bug + 1 regression test → `tests/e2e/selectors.py`, `tests/e2e/test_selector_inventory.py`, `src/omaha/static/app.css` → `task test-e2e`
- `2026-07-04-f02-top-level-tab-nav-and-patrimonio` → 4 tabs top-level + sidebar removal + rename `/`→`/patrimonio` + new stubs + new spec `patrimonio-portfolio-header` → `templates/base.html`, `templates/patrimonio.html`, `templates/rebalance.html`, `templates/rentabilidade.html`, `templates/proventos.html`, `static/app.css`, `routes/pages.py` → `task test-e2e`
- `2026-07-03-r01-clean-orphaned-files-and-snapshots` → purge debug artefacts → `backups/`, `data/portfolio.db`, `tmp/` → no test
- `2026-06-29-rebalance-engine` → solver CVXPY estável → `src/omaha/rebalance/engine.py`, `src/omaha/rebalance/data_bridges.py` → `task test-integration`
- `2026-06-29-dashboard-inline-edit-friction` → melhorias de UX na edição inline → `src/omaha/static/app.css`, `templates/dashboard.html` → `task test-e2e`
- `2026-06-29-add-db-snapshot` → adiciona `task db-snapshot` (DB → CSV) → `scripts/snapshot_to_csv.py`, `pyproject.toml` → `task db-snapshot`

Onda recente: layout-foundation (F02 → T01 → T04) + BDD drift em
fila (T05). Antes: rebalance infra (5 fatias seguidas), auth,
dashboard, CSV seed driven, theme.

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
