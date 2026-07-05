# F07 — Família as profile option (tasks)

## 1. Model + migration

- [x] 1.1 Adicionar campo `is_family_sentinel: bool` (default False) ao
  `Profile` model em `src/omaha/models.py:84`.
- [x] 1.2 Migration Alembic: `alembic revision --autogenerate -m
  "add is_family_sentinel to profile"`; revisar o script gerado para
  garantir `NOT NULL DEFAULT 0` no PostgreSQL/SQLite.
- [x] 1.3 Adicionar User `family` (sem password_hash, sem ability
  de logar) em `src/oma_hama/seed.py`. Profile row `Família` com
  `is_family_sentinel=True` e `display_order=2`.
- [x] 1.4 Remover qualquer seed de `Italo RF2` em
  `src/omaha/seed.py` + `scripts/seed_from_csv.py`. O fixture F01
  morre — F06 não precisa (cross-User) e F07 também não.

## 2. Routes

- [x] 2.1 `get_active_profile` em `src/omaha/auth.py` retorna `None`
  quando `Profile.is_family_sentinel=True` (sentinel não pode ser
  "perfil ativo" no sentido de mutação).
- [x] 2.2 Helper `_real_profiles(db) -> list[Profile]` em
  `src/omaha/routes/pages.py` filtra sentinel — usado por
  `_common_context` e `_render_patrimonio` no lugar de
  `_all_family_profiles`.
- [x] 2.3 `_render_patrimonio` detecta `active_profile_id` apontando
  para sentinel (via flag) e força `view='family'` independente da
  querystring. Querystring `?view=household` continua funcionando
  (compat).
- [x] 2.4 `index` / `get_patrimonio` em `pages.py` aceitam
  `active_profile_id` apontando para sentinel; renderizam o
  agregado sem redirect (sentinel não é "perfil perdido" — é
  estado válido).
- [x] 2.5 `POST /profiles/{profile_id}/select` valida que o id
  existe e não-deleted (F01 contract). Quando o id é sentinel,
  seta `view_mode="family"` na sessão e redireciona para
  `/patrimonio?view=household`.
- [x] 2.6 `_resolve_view_mode` consulta `view=household` querystring
  E `active_profile_id` apontando para sentinel — qualquer um dos
  dois ativa Família.

## 3. Templates

- [x] 3.1 `templates/base.html`: profile-switcher renderiza
  `<option value="{{ p.id }}">` para cada `Profile` real + 1
  opção `Família` com `value="{{ familia_sentinel.id }}"`
  separada por `<optgroup label="—">` ou classe CSS de
  separador. O `onchange` continua enviando para
  `/profiles/{value}/select` (sem mudança no handler).
- [x] 3.2 Toggle `?view=household` no header sai (não há mais
  toggle — Família é peer). Os testids `family-toggle*` saem
  do template (e dos selectors).
- [x] 3.3 `templates/patrimonio.html`: o `<select>` de
  perfil inclui a opção Família com label distinto (ex:
  "Família (agregado)") + separador visual. Quando
  `view='family'`, o chip mostra "Família" como selected.
- [x] 3.4 Banner read-only (já existe F06) continua. Supressão
  de `target_pct` (F06) continua. Alert
  `asset-allocation-alert` suppression (F06 follow-up)
  continua.

## 4. CSS

- [x] 4.1 `src/omaha/static/app.css`: classe
  `.profile-switcher__optgroup` (separador visual) +
  highlight da opção Família com `--accent` quando
  selected. Cor da borda da opção Família:
  `var(--accent)`.
- [x] 4.2 Limpar `.family-toggle` / `.app-header__family-chip`
  se toggle sai (D2). Manter aliases CSS `.household-toggle*`
  para retrocompat temporária com qualquer CSS inline
  residual.

## 5. Tests

- [x] 5.1 `tests/test_family_aggregate.py`: cenário "selecting
  Família via profile-switcher triggers family view" — assert
  `POST /profiles/{familia_id}/select` seta view_mode +
  redireciona 303; `GET /patrimonio` renderiza aggregate
  cross-User com banner read-only + classes colapsadas.
- [x] 5.2 `tests/test_seed.py`: cenário "db-reset produces
  exactly 2 real profiles (Italo + Ana) + 1 sentinel Família
  profile". O fixture `Italo RF2` some dos asserts.
- [ ] 5.3 `tests/test_models.py` (se existir; senão novo):
  Profile com `is_family_sentinel=True` é filtrado por
  `_real_profiles(db)`. AssetClass com `profile_id=
  familia_id` é rejected pela invariante de seed.
- [x] 5.4 BDD `tests/bdd/features/profile_sharing.feature`:
  cenário "Operador seleciona Família no chip e vê agregado
  cross-User". Toggle "Família" como peer no chip. Os
  cenários `clico em "Família"` (F06) viram
  `seleciono "Família" no chip do header`.
- [x] 5.5 `tests/e2e/selectors.py`: ganha
  `profile_option_family` (`[data-testid="profile-option-family"]`).
  Os aliases `household_toggle*` saem (toggle não existe mais).
  `family_toggle*` saem (mesmo motivo).
- [ ] 5.6 Migration test: rodar a nova migration contra
  DB vazio + DB com F01 data existente (Italo RF2 presente)
  e confirmar que o default `0` é aplicado em todas as rows
  existentes.

## 6. Docs

- [x] 6.1 `openspec/roadmap.md`: adicionar entry F07 com
  status `Spec Proposed` ao abrir o change; ir para
  `Applying` neste apply; `Applied` após validação;
  `Archived` após archive.
- [x] 6.2 `openspec/PRD.md` §5.3: adicionar F07 na lista
  de "horizonte" e marcar como "em application" durante
  o apply. Após archive, mover para "delivered".
- [x] 6.3 `openspec/specs/cross-profile-sharing/spec.md`:
  MODIFIED o requirement "The patrimonio page exposes a
  household aggregate view mode" para refletir Família
  como peer de perfil (não toggle).

## 7. Validation

- [ ] 7.1 `openspec validate f07-familia-as-profile-option
  --json` retorna `valid: true`.
- [ ] 7.2 `task test-integration` cobre migration + seed +
  routes + helpers. Sem regressão em F01/F06.
- [ ] 7.3 `task test-bdd` roda o cenário reescrito
  profile_sharing (Família via chip) e mantém 49/49
  verdes (os 4 pre-existentes T05 fail fora do escopo).
- [ ] 7.4 `task test-e2e` valida 3-option profile-switcher
  + Família selected. Mantém 49/49 verdes (5 pre-existentes
  T01 chromium stalls fora do escopo).
- [ ] 7.5 Refresh via skill `refresh-for-test` antes de
  declarar done: DB reset (sem Italo RF2; com Família
  sentinel), server up, smoke:
  - `GET /patrimonio` → profile-switcher tem 3 opções.
  - Selecionar "Família" → redireciona, renderiza
    agregado cross-User (mesmo total que `?view=household`
    em F06).
  - Selecionar "Italo" → volta ao perfil individual.
  - Confirmar visualmente que NÃO há mais toggle no
    header.

## 8. Archive

- [ ] 8.1 `openspec-archive-change f07-familia-as-profile-option`
  move pasta para
  `archive/2026-07-05-f07-familia-as-profile-option/`. Spec
  deltas consolidados em
  `openspec/specs/cross-profile-sharing/spec.md` +
  `openspec/specs/direct-landing-with-header-profile-switcher/spec.md`
  (ou spec equivalente).
- [ ] 8.2 Atualizar `openspec/roadmap.md`: F07 status
  `Archived`; atualizar `Compacted history` e
  `Post-implementation reality check` bloco do F07.
