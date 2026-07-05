## 1. Aggregator (routes/pages.py)

- [ ] 1.1 Em `src/omaha/routes/pages.py`, adicionar `family_asset_classes(db: DbSession) -> list[AssetClass]` (sem parâmetro `viewer`). Query carrega `AssetClass → Asset → Position` para **todos** os `Profile` rows do banco (excluindo perfil de sistema, se houver, via `Profile.name != "system"`), `selectinload` idêntico a F01. Ordenação: `(Profile.display_order, AssetClass.display_order)`.
- [ ] 1.2 Adicionar `family_aggregates(asset_classes: list[AssetClass]) -> dict[str, Any]`. Espelha `portfolio_aggregates(...)`. Invariantes: soma `Position.total_invested` / `total_current` verbatim (`broker-csv-import-totals`); mesmo `Decimal` / `HUNDRED`; `gain_pct = None` em portfólio vazio.
- [ ] 1.3 Helper privado `_aggregate_classes_by_name(classes) -> list[AggregatedClass]` agrupa `AssetClass` rows por `name` (str_eq), soma `total_invested` / `total_current` das classes colapsadas, preserva `display_order = min(display_order)` e `color` da 1ª ocorrência. Retorna estrutura com `id = None` (ou primeira `AssetClass.id` se quiser manter retrocompat com consumidores que ainda esperam `id`).
- [ ] 1.4 Helper privado `_aggregate_assets_by_name(assets) -> list[AggregatedAsset]` colapsa `Asset` por `name` dentro de uma classe (somando `total_invested` / `total_current` das `Position` rows subjacentes). Mantém `buy_enabled` / `sell_enabled` da 1ª ocorrência; flag "ambos" se houver divergência.
- [ ] 1.5 Marcar `household_asset_classes` / `household_aggregates` como deprecated (mantidos por compat, mas internal calls migram para `family_*`). Não deletar — vai virar refator R-fatia futura.

## 2. Routes & querystring

- [ ] 2.1 Em `src/omaha/routes/pages.py` (`_render_patrimonio`), branch `view == 'family'` chama `family_asset_classes(...)` + `family_aggregates(...)` e seta `read_only=True`. Branch `view == 'profile'` continua byte-equivalente ao path F01.
- [ ] 2.2 `GET /patrimonio` parseia `?view=household` da querystring (mesmo que F01); passar `view` adiante para `_render_patrimonio`. Flag interna de sessão muda de `"household"` para `"family"` no contexto (mas o JSON 409 mantém `"household_read_only"` por wire-shape).
- [ ] 2.3 Condition de visibilidade do toggle em `base.html`: usar `len(all_profiles) >= 2` (query ao DB), não `len(viewer.profiles) >= 2`. Helper opcional `_all_family_profiles(db)` retorna todos os profiles.

## 3. Read-only gate (reuso F01, sem refator)

- [ ] 3.1 Confirmar que `require_profile_writable` (em `src/omaha/auth.py`) cobre `view=household` corretamente. Wire shape do 409 deve continuar `{"reason": "household_read_only"}` (não renomear). Já aplicado nos 11 endpoints de F01 — só verificar.
- [ ] 3.2 Atualizar nome interno da flag da sessão em `request.session` para `"view_mode": "family"` (mantendo compat com reading que checa `"view_mode" == "household"` também, durante cutover).
- [ ] 3.3 Rodar `task test-integration` para validar que nenhum dos 11 endpoints regrediu.

## 4. Templates

- [ ] 4.1 `templates/base.html`: botão toggle label `Casa` → `Família`. `data-testid="household-toggle"` → `data-testid="family-toggle"`. Visual class `.app-header__household-chip` → `.app-header__family-chip` (CSS atualizado em 4.5). Condition de visibilidade baseada em `len(all_profiles) >= 2`.
- [ ] 4.2 `templates/patrimonio.html`: quando `view == 'family'`, suprimir coluna `target_pct` no card `patrimonio-portfolio-header` (se aplicável) e o elemento `class-target-pct-view` dentro de cada classe agrupada. Manter `current_pct` e `current_value` por classe.
- [ ] 4.3 `templates/patrimonio.html`: quando `view == 'family'`, suprimir botão `class-section-delete-btn` (já feito por F01 — confirmar).
- [ ] 4.4 `templates/patrimonio.html`: o cabeçalho da classe colapsada mostra contagem de profiles ao lado do nome? Decisão: **não** nesta fatia (cabe em melhoria futura se virar reclamação). Apenas o nome colapsado é suficiente.
- [ ] 4.5 `src/omaha/static/app.css`: renomear `.household-toggle` → `.family-toggle`, `.app-header__household-chip` → `.app-header__family-chip`. Aliases `.household-toggle` (redirected) para retrocompat temporária com BDD/e2e selectors.

## 5. Tests

- [ ] 5.1 Renomear `tests/integration/test_household_aggregate.py` → `tests/integration/test_family_aggregate.py`. Atualizar nome interno das funções (`household_*` → `family_*`).
- [ ] 5.2 Adicionar cenário "family aggregate is symmetric across operators": cria 2 users (Italo + Ana) com classes+positions; loga como Italo, GET `?view=household`, salva totais; loga como Ana, mesma request, mesmos totais.
- [ ] 5.3 Adicionar cenário "classes with identical names collapse": Italo e Ana ambos têm classe "Renda Fixa" com totais diferentes; family aggregate tem 1 linha "Renda Fixa" com soma.
- [ ] 5.4 Adicionar cenário "assets with identical names collapse": dentro de "Renda Fixa" colapsada, Italo e Ana têm "Tesouro IPCA"; family aggregate tem 1 linha "Tesouro IPCA".
- [ ] 5.5 Adicionar cenário "target_pct not rendered in family mode": response HTML não contém `data-testid="class-target-pct-view"` quando `view=household`.
- [ ] 5.6 Atualizar `tests/bdd/features/profile_sharing.feature`: cenário "Operador ativa o modo agregado da casa" agora valida que Italo e Ana veem o **mesmo** total.
- [ ] 5.7 Atualizar `tests/e2e/selectors.py`: alias `data-testid="household-toggle"` → `data-testid="family-toggle"`. Manter alias para qualquer selector legado.

## 6. Docs & cleanup

- [ ] 6.1 Atualizar `openspec/roadmap.md`: mover fatia F06 status de `Ready` → `Spec Proposed` ao iniciar apply → `Applied` após validação → `Archived` após archive.
- [ ] 6.2 Adicionar post-implementation reality check na seção do `## Post-implementation reality check` quando `Applied`.
- [ ] 6.3 Atualizar `PRD §5.3` para refletir que `?view=household` agora é agregado familiar cross-User (full-join).

## 7. Validation

- [ ] 7.1 `openspec validate f06-family-household-full-join-aggregate --json` retorna `valid: true`.
- [ ] 7.2 `task test-integration` cobre nova shape + todas as invariantes cross-User.
- [ ] 7.3 `task test-bdd` roda o cenário reescrito de profile_sharing.
- [ ] 7.4 `task test-e2e` valida toggle + alias de testid (F01 já cobriu 49/49; meta é manter 49/49 verdes).
- [ ] 7.5 Refresh via skill `refresh-for-test` antes de declarar done (PRD §4.9): DB reset, seed, server up, smoke `/patrimonio?view=household` logando como Italo E como Ana para confirmar simetria visual.

## 8. Archive

- [ ] 8.1 `openspec-archive-change f06-family-household-full-join-aggregate` move pasta para `archive/2026-07-04-f06-family-household-full-join-aggregate/`. Spec deltas consolidados em `openspec/specs/cross-profile-sharing/spec.md`.
- [ ] 8.2 Atualizar `openspec/roadmap.md`: F06 status `Archived`; atualizar `Compacted history` e `Post-implementation reality check` bloco do F06.
