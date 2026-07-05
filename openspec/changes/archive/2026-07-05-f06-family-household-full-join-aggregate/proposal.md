## Why

A slice F01 introduziu `?view=household` agregando posições dentro do
`User` logado (`Profile.user_id == viewer.id`), mas o seed canônico cria
Italo e Ana Livia como **dois usuários separados** (`src/omaha/seed.py:36`).
Resultado prático: o agregado nunca representou a família — Italo via só
o próprio perfil, Ana via só o próprio perfil, e o toggle nem
aparecia para Ana (única perfil). O owner reportou a fatia como
"muito ruim" no grill 2026-07-04. F06 substitui a semântica do
`?view=household` por agregado cross-User (família inteira) com
full-join por nome de classe/ativo e omissão de `target_pct`.

## What Changes

- **`src/omaha/routes/pages.py`** — `household_asset_classes` vira
  `family_asset_classes` sem o filtro `Profile.user_id`; query carrega
  todos os profiles do banco (excluindo perfil de sistema, se houver).
  `household_aggregates` vira `family_aggregates` retornando a mesma
  forma de resposta mas com classes agrupadas por `name` (full-join).
  Helper privado `_aggregate_assets_by_name` soma `Asset` rows
  dentro da mesma chave de nome. **BREAKING:** wire shape do
  agregador inalterado — `{"portfolio": {...}, "classes": [...]}` —
  mantém compat com templates que consomem a estrutura.
- **`src/omaha/templates/base.html`** — botão do toggle muda label
  de `Casa` para `Família`. Condition de visibilidade passa de
  `len(viewer.profiles) >= 2` para `len(all_profiles) >= 2`.
  Toggle continua oculto quando só existe 1 perfil no banco (não
  faz sentido agregar o que já é o todo).
- **`src/omaha/templates/patrimonio.html`** — quando `view == 'family'`
  omitir a coluna de `target_pct` no card `patrimonio-portfolio-header`
  (se aplicável) e suprimir o `class-target-pct-view` inline dentro
  de cada classe agrupada. Resto do markup idêntico.
- **`src/omaha/auth.py`** — `require_profile_writable` mantém forma;
  flag interna da sessão passa de `"household"` para `"family"`.
  Wire shape do JSON 409 permanece `{"reason": "household_read_only"}`
  para não quebrar consumers existentes.
- **`openspec/specs/cross-profile-sharing/spec.md`** —
  `MODIFIED` os 4 requirements F01 sobre `view=household` para
  refletir semântica cross-User + full-join + omissão target_pct.
- **`tests/integration/test_household_aggregate.py`** — renomeado para
  `test_family_aggregate.py`; cenários adicionados: cross-User é
  simétrico (Italo logado = Ana logada = mesmo total); classes com
  mesmo nome colapsam; target_pct não vaza; toggle visível com 2
  profiles mesmo quando viewer tem 1.
- **`tests/bdd/features/profile_sharing.feature`** — cenário
  "Operador ativa o modo agregado da casa" reescrito para
  cross-User: loga Italo, toggle deve mostrar total Italo+Ana;
  loga Ana, o mesmo total aparece.

## Capabilities

### New Capabilities

- Nenhuma. F06 modifica contratos existentes.

### Modified Capabilities

- `cross-profile-sharing`: os requisitos "The patrimonio page exposes a
  household aggregate view mode", "The header exposes a household mode
  toggle", "Household mode preserves per-profile isolation" e "Any
  logged-in user can view any profile's dashboard data" ganham delta
  em `specs/cross-profile-sharing/spec.md`. A invariante intra-User é
  removida; entra invariante cross-User (família inteira) + invariante
  de agrupamento por nome + invariante de omissão de target_pct.

## Impact

- **Auth**: a invariante "household aggregate é intra-User" do F01 é
  removida de propósito (decisão D-F06.1 documentada no roadmap).
  Hoje o app só tem dois Operators com senha compartilhada
  (`PRD §1.2`), então expor agregado cross-User não vaza dados para
  terceiros. **Atenção:** se algum dia entrar autenticação per-User
  diferenciada, F06 precisa de gate explícito (não cabe nesta slice).
- **Read-only gate**: reusado de F01, sem retrabalho.
  Mutações continuam retornando 409 com mesma wire shape.
- **Templates**: patrimonio.html adiciona **dois** branches suprimindo
  target_pct no agregado. Outras páginas não mudam.
- **BDD/e2e**: 1 feature file atualizado + 1 integration test
  renomeado/expandido. Sem novos artefatos Playwright.
- **PRT/PRD**: nenhum — PRD §5.3 não exige mudanças (modo household já
  existia, semântica só muda).
- **Critical domain**: tocamos `routes/pages.py` + `auth.py`, mas só
  leitura + branch flag. Não toca rebalance solver nem cotação.
  Cap `Applying` = 1 (default), ok paralelizar com R-slice.
