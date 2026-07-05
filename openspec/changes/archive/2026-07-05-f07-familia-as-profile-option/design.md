## Context

F06 (archived 2026-07-05) introduziu `?view=household` como modo
alternativo que agrega todos os perfis do banco (cross-User
full-join por nome). Funciona, mas o owner pediu no grill
2026-07-05 que **Família seja um peer dos perfis** no
`profile-switcher` em vez de um toggle. O fixture de seed
`Italo RF2` (perfil #3, criado em F01 para o cenário
intra-User) também sai — não tem dono real e era só
muleta de teste F01.

A forma atual (querystring) obriga o operador a lembrar
"se quero ver a família, preciso clicar no toggle". A
forma nova (opção no chip) faz a escolha ser equivalente a
trocar de perfil: o operador escolhe `Família` no chip e o
dashboard mostra o agregado cross-User, sem modo
alternativo, sem toggle.

## Goals / Non-Goals

**Goals:**

- Substituir o toggle `?view=household` por uma opção
  `Família` no `profile-switcher` (peer de `Italo` e
  `Ana`).
- Drop do fixture `Italo RF2` no `db-reset`.
- Manter wire shape 409 + `{"reason": "household_read_only"}`
  (F01+F06 contract) — read-only gate reusado.
- Manter `target_pct` suprimido no agregado cross-User
  (F06 contract).
- Manter classes/ativos com mesmo nome colapsando (F06
  full-join contract).

**Non-Goals:**

- Não introduzir autenticação separada para Família (ela
  usa o mesmo `view_mode="family"` da sessão; auth ainda
  via `user_id`).
- Não mudar a forma de agregação (helper de full-join
  reusado de F06).
- Não criar tabela nova — Família é uma `Profile` row
  com flag `is_family_sentinel=1`.
- Não deletar `household_asset_classes` /
  `household_aggregates` (F06 deprecated; delete é
  R-slice futura).

## Decisions

### Decision 1. Família é uma `Profile` row com flag
`is_family_sentinel=1`.

**Por quê**: o `profile-switcher` template já renderiza
`<option>`s iterando sobre `Profile` rows. Adicionar uma
linha sentinel com flag é a integração de menor
blast-radius — nenhum JS novo, nenhuma rota alternativa,
nenhum branch no template para "Família é especial". A
rota `POST /profiles/{id}/select` já trata qualquer `id`
(numérico) e redireciona para `/`.

A flag `is_family_sentinel` existe para: (a) o template
puder renderizar a opção com separador visual e label
`Família`; (b) a rota `/patrimonio` detectar "active
profile é sentinel → força `view='family'`"; (c) o
`get_active_profile` retornar `None` para sentinel (não
dá pra mutar; sentinel não tem classes).

**Alternativas**: rota nova `POST /familia/select` (recusado
— duplica o path `/profiles/{id}/select` que já cobre
todos os casos). Option string-sentinel no `<select>` com
`value="familia"` (recusado — quebra a invariante "o
profile-switcher só lista Profile rows reais"). Rejected.

### Decision 2. Família é um perfil peer, não um "modo
alternativo" — toggle `?view=household` sai.

**Por quê**: o pedido literal do owner é "Família
equivalente a um novo perfil". Toggle + querystring =
conceito de "modo" (F01/F06); opção no chip = conceito de
"perfil" (F07). A querystring `?view=household` continua
sendo a URL canônica da feature, mas a única porta de
entrada vira `POST /profiles/{id}/select` (sentinel
incluso).

A flag interna da sessão passa de
`view_mode="family"` para `active_mode="family"` —
discriminador mais explícito e que coexiste com
`active_profile_id` (que vira o id do sentinel quando
Família está ativo).

**Alternativas**: manter toggle E opção no chip
(ambos funcionam) (recusado — duas portas de entrada
para a mesma feature, confuso). Manter toggle, adicionar
atalho via chip (recusado — não é o pedido). Rejected.

### Decision 3. `Italo RF2` sai do `db-reset`.

**Por quê**: o fixture existia só para F01 (multi-profile
intra-User). F06 supersedeu F01 com cross-User. F07
fecha o ciclo: a fixture é morta e o `db-reset` produz
exatamente 2 perfis reais (Italo + Ana) + 1 sentinel
(Família). As integrações que referenciavam
`Italo RF2` (F01 autouse fixture, T01 reality check
"43 assets") são atualizadas para não esperar esse
perfil.

**Alternativas**: manter `Italo RF2` para backward
compat (recusado — não tem dono real, é morta,
reintroduz confusão). Renomear para "Italo Plus" (recusado
— mesma confusão, novo nome). Rejected.

### Decision 4. `require_profile_writable` mantém wire
shape 409 `household_read_only` sem retrabalho.

**Por quê**: a invariante "Família é read-only" é a mesma
de F01 (F01 + F06 + F07 = 3 layers com mesmo gate). O
JSON `{"reason": "household_read_only"}` é a wire
contract desde F01 — não renomear para `family_read_only`
(mesmo rationale F01 → F06).

A flag `view_mode="family"` continua sendo o gatilho. A
sentinela Família seta essa flag no `select`. O gate
dispara 409 nas 5 rotas de mutação + `/rebalanceamento`.

**Alternativas**: criar gate `require_family_active`
separado (recusado — duplica a invariante read-only).
Renomear JSON reason para `family_read_only` (recusado —
quebra consumers). Rejected.

### Decision 5. Sem renovação de tokens visuais.

**Por quê**: F07 não introduz cor, espaçamento, ou
elevação nova. Reusa `--accent` (verde-feto) para
destacar a opção Família no chip. Reusa `.is-read-only`
do F01 para o banner. Reusa `.family-toggle*` aliases
do F06 — o toggle sai mas o CSS alias pode ficar para
retrocompat com qualquer CSS inline que referencie.

**Alternativas**: nova cor para Família (recusado — YAGNI,
a opção Família no chip já é distinta via label).
Drawer/dropdown de perfis (recusado — F02 cravou a forma
`<select>` nativa; reescrita para fora de escopo). Rejected.

## Risks / Trade-offs

- **Sentinel profile polui `Profile` queries** → toda
  query que itera `Profile` precisa filtrar
  `is_family_sentinel=False` (ou checar a flag). Mitigação:
  helper centralizado (`_real_profiles(db)`) que todas as
  rotas que precisam de "perfis reais" usam. Sentinel
  aparece só no chip.
- **URL `/patrimonio?view=household` ainda funciona**
  (decisão D2) — links antigos não quebram, mas o
  operador que cola a URL no browser hoje cai direto no
  agregado sem clicar em toggle. Mitigação: a sessão
  tem `view_mode` independente da querystring — o
  `POST /profiles/{id}/select` substitui o estado
  corretamente.
- **`Italo RF2` é deletado de seed e DB** — qualquer
  teste que esperava esse perfil quebra. Mitigação:
  `db-reset` regenera; o autouse fixture de
  `test_family_aggregate.py` é atualizado para
  re-adicionar se necessário (mas F07 não precisa dele,
  o agregado é cross-User nativo).
- **`active_profile_id` apontando para sentinel
  conflita com `require_active_profile` que exige
  Profile real** → mitiga: `get_active_profile` retorna
  `None` para sentinel, e a rota `/patrimonio` detecta
  o sentinel via flag e renderiza Família direto (sem
  redirect).
- **`profile-switcher` com 3 opções em PT-BR** →
  simples. Mitigação: a opção Família vai com label
  distinto + separador visual para não confundir com
  perfil real.

## Migration Plan

1. **Migration Alembic** (DDL): adicionar coluna
   `is_family_sentinel BOOLEAN NOT NULL DEFAULT 0` em
   `Profile`. Default 0 = compat com rows existentes.
2. **Seed update** (`src/omaha/seed.py` +
   `scripts/seed_from_csv.py`): criar User `family`
   (sem senha) + Profile `Família` com
   `is_family_sentinel=1`. Remover qualquer
   `Italo RF2` do seed. `db-reset` deve produzir: User
   Italo (1 perfil) + User Ana (1 perfil) + User
   family (1 perfil sentinel).
3. **Routes update** (`src/omaha/routes/pages.py`):
   `get_active_profile` filtra sentinel. A rota
   `index` / `get_patrimonio` detecta
   `active_profile_id` apontando para sentinel e força
   `view='family'`. O `_resolve_view_mode` agora
   consulta `active_profile_id` E `view=household`
   querystring (D2 — querystring ainda funciona).
4. **Template update** (`base.html`,
   `patrimonio.html`): profile-switcher renderiza
   3 opções com Família separada por `<optgroup>` ou
   classe CSS de separador. Toggle `Casa`/`Família`
   sai do header. Banner read-only + supressão
   `target_pct` continuam (F06).
5. **Tests** (5 cenários novos): seed produz
   exatamente 2 perfis reais + 1 sentinel;
   `POST /profiles/{sentinel_id}/select` seta
   `view_mode=family`; `GET /` com sentinel ativo
   renderiza agregado cross-User; toggle de header
   some; `Italo RF2` não é mais seedado.
6. **BDD** (1 cenário): "Operador seleciona Família
   no chip e vê agregado cross-User". Toggle test
   de F06 sai.
7. **E2E selectors**: ganha `profile-option-family`;
   aliases `household_toggle*` saem.
8. **Roadmap + PRD**: nova entry F07 no roadmap; PRD
   §5.3 adiciona F07 como "Aplicar F07 (Família as
   profile option)".

## Open Questions

- O sentinel Família deve aparecer no profile-switcher
  mesmo quando o viewer tem só 1 perfil real? Decisão
  provisória: sim (Família é peer, não condicional).
  Reverter é trivial.
- O sentinel Família tem `user_id` apontando para um
  User `family` (sem senha) ou aponta para um User
  existente (ex: Italo) com flag? Decisão provisória:
  User novo `family` (sem senha) — isola
  completamente e o `require_user` continua
  blindado.
- A querystring `?view=household` continua suportada
  (D2) ou só vira acessível via chip? Decisão
  provisória: continua (compat). Se o owner quiser
  remover, R-slice futura.
