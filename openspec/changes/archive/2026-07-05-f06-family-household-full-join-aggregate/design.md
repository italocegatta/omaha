## Context

A slice F01 (arquivada 2026-07-04) introduziu `?view=household`
agregando posições de `Profile.user_id == viewer.id` em
`src/omaha/routes/pages.py:household_asset_classes`. Funciona quando o
viewer possui ≥2 profiles no mesmo `User` (caso do seed: Italo + Italo
RF2). Mas o seed canônico cria Italo e Ana Livia como **dois usuários
separados** (`src/omaha/seed.py:36`), portanto na prática o agregado
nunca representou "a família inteira" — Ana com 1 perfil nem via o
toggle, e Italo via `Italo + Italo RF2` (RF2 vazio), que é igual à sua
própria visão de perfil.

F06 corrige a semântica sem reescrever a infra de F01. O read-only
gate (`require_profile_writable` em 11 endpoints) é reusado, a
querystring `?view=household` é mantida (D-F06.4), e a estrutura de
resposta (`{"portfolio": {...}, "classes": [...]}`) bate byte-a-byte
com a do per-profile view, então o template consome a mesma forma com
um branch (`{% if view == 'family' %}`).

A invariante nova é **cross-User**: o agregador soma TODOS os profiles
ativos do banco (excluindo perfil de sistema, se houver), independente
de quem logou. Classes com mesmo `AssetClass.name` em profiles
distintos colapsam em 1 linha (full-join por `name`). Ativos com
mesmo `Asset.name` dentro da mesma classe agrupada também colapsam.

## Goals / Non-Goals

**Goals:**

- Substituir a semântica de `?view=household` por agregado cross-User
  (família inteira) com full-join por nome.
- Renomear o toggle `Casa` → `Família` e mover a condição de
  visibilidade para `len(all_profiles) >= 2`.
- Reusar o gate `require_profile_writable` de F01 sem refatorar.
- Preservar wire shape do JSON 409 (`{"reason": "household_read_only"}`).
- Suprimir coluna `target_pct` no agregado (read-only analítico).
- Manter uma única source of truth de agregação: `family_aggregates`
  é a função central; helpers privados agrupam classes e ativos.

**Non-Goals:**

- Não criar tabela nova de "agregado familiar" nem snapshot agregado.
- Não tocar `routes/classes.py` / `routes/assets.py` / `routes/imports.py`
  além do gate já aplicado em F01.
- Não mexer em `routes/rebalance.py` / solver / cotação.
- Não introduzir autenticação per-User diferenciada (escopo de outra
  fatia; o app é senha compartilhada por PRD §1.2).
- Não reusar `portfolio_aggregates` como generalização. F01 já cravou
  Decision 5 (sibling functions); F06 segue o mesmo padrão de manter
  `family_aggregates` espelhado.
- Não introduzir animações, drawers mobile, ou novos tokens visuais.

## Decisions

### Decision 1. `family_aggregates` é função-espelho de `household_aggregates`, não generalização.

**Por quê**: a forma da resposta bate byte-a-byte; o template `patrimonio.html`
consome `classes` com `{id, name, target_pct, color, current_pct,
current_value, assets}`, e uma classe colapsada por nome vira 1 entrada
no array com `id = None` (ou o primeiro `AssetClass.id` que apareceu)
e `assets` sendo a soma dos ativos de mesmo nome. Generalizar a função
existente explode blast radius e arrasta audit pipeline + testes já
escritos. F06 segue o precedente de F01 Decision 5: duplicação mínima
com invariante explícita.

**Alternativas**: parametrizar `portfolio_aggregates(iterable, scope=...)`
(recusado — explode blast radius; arrasta o audit pipeline que assume
per-profile). Reusar `household_aggregates` sem mudança (recusado — a
função dela filtra `viewer.profiles`, que é exatamente o que precisa
mudar). Rejected.

### Decision 2. Cross-User via query sem filtro `Profile.user_id`.

**Por quê**: garantir que a invariante "Italo logado == Ana logado ==
mesmo total" seja testável sem mock. A query em
`family_asset_classes` carrega `AssetClass.assets.positions` para
todo `Profile` no banco (excluindo perfil de sistema se houver). Sem
relacionamento com `viewer`. Reflete a semântica do PRD §1.2 onde os
dois operators compartilham a senha familiar — expor o total da
família não vaza dados para terceiros.

**Alternativas**: parametrizar `household_asset_classes(viewer, *, scope="family")`
(recusado — Decision 1 fecha duplicação). Filtrar por `User.username IN
("Italo", "Ana")` hardcoded (recusado — quebra em qualquer DB com nome
de usuário diferente). ACL com 2 grupos (`italo`, `ana`) (recusado —
infraestrutura nova para 2 operadores; sem ganho real). Rejected.

### Decision 3. Full-join por nome de classe/ativo via helpers privados.

**Por quê**: classes com mesmo nome em profiles distintos devem
colapsar (D-F06.2). Ativos com mesmo nome **dentro da mesma classe
agrupada** também colapsam. A operação é feita em helpers privados:

- `_aggregate_classes_by_name(asset_classes)` retorna
  `dict[str, list[AssetClass]]` agrupando por `name`, preserva
  `display_order` mínimo e cor da primeira occurrence.
- `_aggregate_assets_by_name(assets)` mesma operação dentro de uma classe.

A função `family_aggregates` reusa esses helpers e mantém a forma
de retorno idêntica a `portfolio_aggregates`. Cores colidem — first
write wins — documentado e aceitável porque agregado é analítico.

**Alternativas**: SQL `GROUP BY name` direto no banco (recusado —
perde eager loading de `positions`, causa N+1). Permitir `display_order`
média ponderada (recusado — bug de UX; colapso deve ser determinístico).
Permitir classes com nomes idênticos de perfis distintos manterem
linhas separadas (recusado — usuário pediu explicitamente "full join"
no grill 2026-07-04). Rejected.

### Decision 4. `target_pct` omitido, mas `current_pct` preservado.

**Por quê**: a coluna `target_pct` representa a alocação-alvo por
classe, e dois profiles divergem nesse alvo. Mostrar alvos divergentes
no agregado é ambíguo. `current_pct` continua válido (é a fração
atual do valor de cada classe em relação ao total agregado).
Alinhado com pedido literal do owner no grill ("sem target de
alocação, apenas o resultado da soma").

**Alternativas**: mostrar média ponderada de `target_pct` por valor
atual (recusado — adiciona coluna semântica nova; YAGNI). Mostrar
targets lado a lado por profile (recusado — explode layout). Rejected.

### Decision 5. Toggle `Casa` → `Família`, mesma querystring `?view=household`.

**Por quê**: F01 já cravou a decisão D1 (querystring > rota). F06
renomeia só a label visível e os data-testids (`data-testid="family-toggle"`,
`data-testid="family-chip"`). URL canônica da feature fica igual
(`/patrimonio?view=household`); o que muda é o que o backend agrega.

**Alternativas**: mudar querystring para `?view=familia` (recusado —
duas URLs canônicas da mesma feature; futuro confuso). Manter label
`Casa` (recusado — owner pediu "Família" explicitamente). Rejected.

### Decision 6. Condition de visibilidade do toggle movida para `len(all_profiles)`.

**Por quê**: a invariante F01 (toggle visível quando viewer tem ≥2
perfis) deixava Ana (1 perfil) sem acesso ao toggle. F06 muda para
"se o banco tem ≥2 profiles, exibe toggle" — sem importar quem logou.
O agregado é o mesmo independente de quem clica.

**Alternativas**: esconder toggle quando viewer tem 1 perfil mas DB
tem mais (recusado — é o cenário da Ana; sem toggle ela nunca vê o
agregado). Rejected.

### Decision 7. Gate read-only reusado sem refator; flag interna renomeada.

**Por quê**: F01 cravou 11 endpoints com `require_profile_writable`
retornando 409 + JSON `{"reason": "household_read_only"}`. Reusar
preserva todos os testes BDD/e2e e o wire shape externo (não-quebra).
A flag interna da sessão vai de `"view_mode" == "household"` para
`"view_mode" == "family"` (mais semântico). O JSON do 409 mantém
`"household_read_only"` para consumers existentes.

**Alternativas**: renomear o JSON para `family_read_only` (recusado —
quebra consumers + lógica de UI que checava a string anterior). Rejected.

### Decision 8. Sem renovação de tokens visuais.

**Por quê**: F06 não introduz cor, espaçamento, ou elevação nova.
Reusa `.is-read-only`, `.household-toggle`, `.app-header__household-chip`
(renomeado para `.app-header__family-chip`) — todos já presentes no
CSS de F01.

## Risks / Trade-offs

- **Color collision on shared class names** → documentado e aceito
  porque agregado é analítico. Mitigação: tooltip mostra
  `(profile_count)` ao lado do nome da classe colapsada (cabe em
  melhoria futura, não no escopo).
- **`display_order` após colapso** → o helper pega o mínimo entre os
  `display_order` das classes colapsadas. Pode colocar uma classe de
  ordem alta em primeiro se tiver `display_order` menor em outro perfil.
  Mitigação: aceitar como trade-off; ordem visual pós-colapso é
  alfabética por nome (a chave) ou pode ser parametrizada depois.
- **Performance da query cross-User** → com 2 profiles seed, eager
  loading via `selectinload` (mesma estratégia de F01) segura. Se
  virar gargalo com N profiles, cabe em `R03` (extract quote provider
  adapter) ou nova `R0X` dedicada a query audit.
- **Wire shape stability do 409** → consumers existentes (frontend +
  testes) continuam lendo `"reason": "household_read_only"`. Migração
  para `"family_read_only"` cabe em outra fatia.
- **Toggle visível para Ana (1 perfil) mas DB tem mais** → expõe a
  Ana o agregado familiar completo. Aceitável porque PRD §1.2
  enuncia os dois como operadores equivalentes com senha compartilhada.
  Se algum dia entrar ACL per-User, F06 precisa de gate (não nesta slice).

## Migration Plan

1. **Apply gate 2**:
   - `src/omaha/routes/pages.py` — adicionar `family_asset_classes(db)`
     sem filtro User; adicionar `family_aggregates(asset_classes)` +
     helpers `_aggregate_classes_by_name` /
     `_aggregate_assets_by_name`; branch `view == 'family'` em
     `_render_patrimonio` (reusa `household_aggregates` legado ou
     chama `family_aggregates` conforme D-F06.x).
   - `src/omaha/auth.py` — flag interna da sessão
     `view_mode == "family"`; comentários atualizados.
   - `templates/base.html` — label `Casa` → `Família`; data-testid
     renomeado para `family-toggle`; condition de visibilidade
     `len(all_profiles) >= 2`.
   - `templates/patrimonio.html` — suprimir coluna target_pct quando
     `view == 'family'` (cards e por-classe).
   - `tests/integration/test_household_aggregate.py` renomeado para
     `test_family_aggregate.py`; cenários: cross-User simétrico,
     classes mesmo nome colapsam, target_pct não vaza, toggle visível
     com 2 profiles mesmo se viewer tem 1.
   - `tests/bdd/features/profile_sharing.feature` — cenário do toggle
     reescrito para cross-User: loga Italo, toggle → total Italo+Ana;
     loga Ana, o mesmo total.
   - `tests/e2e/selectors.py` — alias `household-toggle` → `family-toggle`.
2. **Validation gate**:
   - `openspec validate f06-family-household-full-join-aggregate`
     retorna `valid: true`.
   - `task test-integration` cobre o novo aggregator + simetria
     cross-User.
   - `task test-bdd` cobre o cenário reescrito de profile_sharing.
3. **Archive gate 3**:
   - `openspec-archive-change`: change vai para
     `openspec/changes/archive/2026-07-04-f06-family-household-full-join-aggregate/`.
   - Spec deltas consolidados em
     `openspec/specs/cross-profile-sharing/spec.md`.
   - Rollback: reverter o PR; sem migração de DB.

## Open Questions

- O collapse por nome de classe deve respeitar um `mapping_name` de
  normalização (ex.: "RF" == "Renda Fixa") ou match exato? Decisão
  provisória: match exato (str_eq). Se gramática divergir entre
  profiles, simplifica com alias CLI numa R-fatia futura.
- O agregador deveria preservar a coluna `currency_code` (quando
  classes agregadas tiverem moedas diferentes) ou colapsar tudo em
  BRL? Decisão provisória: colapsa em BRL por enquanto; se entrar
  USD significativo, cabe em R-slice futura.
