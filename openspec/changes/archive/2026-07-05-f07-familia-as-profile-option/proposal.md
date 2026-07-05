## Why

F06 introduziu `?view=household` como agregado familiar cross-User via
toggle no header. Funciona, mas o owner prefere que a visão Família
seja equivalente a **mais um perfil** no `profile-switcher`: o
operador escolhe entre `Italo` / `Ana` / `Família` no chip, e a
seleção dispara o agregado cross-User sem precisar de querystring
adicional. O fixture de seed `Italo RF2` (perfil #3, sem dono real —
existia só para o caso de teste F01 intra-User) também sai.

## What Changes

- **`src/omaha/templates/base.html`**: `profile-switcher` ganha uma
  opção sintética `Família` com `value="familia"`. Quando o
  operador escolhe essa opção, o `onchange` do `<select>` envia
  para uma nova rota `POST /familia/select` em vez de
  `/profiles/{id}/select`. Visualmente, a opção Família aparece
  com um separador visual (linha) e label distinto. Toggle
  `?view=household` removido — Família vira um peer dos perfis
  reais, não um modo alternativo.
- **`src/omaha/routes/pages.py`**: nova rota `POST /familia/select`
  que seta `view_mode="family"` na sessão e redireciona para
  `/patrimonio?view=household` (a querystring continua sendo a
  URL canônica da feature, mas deixa de ser a única porta de
  entrada). A flag interna da sessão passa de `"family"` para
  um discriminador mais explícito `"active_mode": "family"`,
  coexistindo com `active_profile_id` (que vira `None` quando
  Família está ativo).
- **`src/omaha/seed.py` + `scripts/seed_from_csv.py`**: o fixture
  `Italo RF2` (perfil #3 órfão no `db-reset` log) sai. `db-reset`
  lista só Italo (perfil #1) + Ana (perfil #2) + Família
  (perfil #4 sentinel).
- **`src/omaha/models.py` + migration Alembic**: novo campo
  `is_family_sentinel BOOLEAN NOT NULL DEFAULT 0` em
  `Profile`. O perfil Família (id=4) tem `is_family_sentinel=1`
  e `user_id` apontando para um novo User `family` (id=3) sem
  senha (não pode logar). `asset_classes` relationship fica
  vazia (família não tem classes próprias; ela agrega).
- **`src/omaha/auth.py` + `src/omaha/routes/pages.py`**:
  `get_active_profile` precisa detectar Família e retornar
  `None` (família não é um Profile real para mutação). A rota
  `/patrimonio` (e `/`) detecta "active_profile_id está setado
  mas o Profile é sentinel" e força `view='family'`. A
  visibilidade do toggle `?view=household` no header sai (não
  tem mais toggle — Família é peer dos perfis).
- **`src/omaha/templates/patrimonio.html`**: `profile-switcher`
  renderiza 3 opções: `Italo`, `Ana`, `Família` (separador
  entre as duas primeiras e a terceira). Quando Família está
  ativo, o chip mostra `Família` (selected) e o
  `viewer-vs-owner` label fica oculto (Família não tem
  "owner" no sentido de User).
- **`src/omaha/static/app.css`**: separador visual no
  `profile-switcher` (classe nova `.profile-switcher__optgroup`
  ou `<optgroup>` nativo com `label="—"`). Cor da opção Família
  usa `--accent` (mesmo verde-feto da tab ativa).
- **Tests**:
  - `tests/test_family_aggregate.py` ganha cenário
    "selecting Família via profile-switcher triggers family
    view" (assert: `POST /familia/select` seta view_mode +
    redireciona; `GET /patrimonio` renderiza aggregate
    cross-User com banner read-only + classes colapsadas).
  - `tests/test_seed.py` ganha cenário "db-reset produces
    exactly 2 real profiles (Italo + Ana) + 1 sentinel Família
    profile". O fixture `Italo RF2` some dos asserts.
  - `tests/bdd/features/profile_sharing.feature` ganha
    cenário "Operador seleciona Família no chip e vê agregado
    cross-User". Toggle "Família" como peer no chip.
  - `tests/e2e/selectors.py` ganha `family_option`
    (`[data-testid="profile-option-family"]`) e
    `profile_separator` (a linha visual). Os aliases
    `household_toggle*` saem (toggle não existe mais).

## Capabilities

### New Capabilities

- Nenhuma. F07 modifica contratos existentes.

### Modified Capabilities

- `cross-profile-sharing`: MODIFIED o requirement "The
  patrimonio page exposes a household aggregate view mode"
  para refletir que Família é peer dos perfis (não toggle).
  A invariante "família só pode ser acessada via
  `?view=household` querystring" sai; entra invariante
  "família é selecionável pelo chip do header como qualquer
  outro perfil".
- `direct-landing-with-header-profile-switcher` (ou
  spec equivalente que rege o `profile-switcher`): MODIFIED
  o requirement sobre o `<select>` para refletir 3 opções
  com a Família como peer sentinel.

## Impact

- **Auth**: nova rota `POST /familia/select` (não-autenticada
  via `require_user` — autenticação atual ainda via
  `user_id` na sessão; Família não loga). O `view_mode`
  interno coexiste com `active_profile_id`.
- **Read-only gate**: reusado de F01+F06 sem retrabalho. O
  gate `require_profile_writable` continua disparando 409
  `household_read_only` quando `view_mode == "family"` na
  sessão.
- **Templates**: patrimonio.html ganha lógica de render
  condicional por `view` (já existe). base.html perde o
  toggle `Casa`/`Família` e ganha a 3ª opção no
  `profile-switcher`.
- **BDD/e2e**: feature `profile_sharing.feature` reescrito.
  Aliases `household_toggle*` saem do selector inventory.
- **DB**: nova migration Alembic (campo `is_family_sentinel`).
  `seed.py` ajusta para criar o sentinel Família + remover
  Italo RF2. `scripts/seed_from_csv.py` ganha
  conhecimento de "ignore sentinel profiles" no aggregation.
- **Critical domain**: auth + profile routing = cap 1
  Applying. F07 não toca solver, cotação, nem rebalance.
