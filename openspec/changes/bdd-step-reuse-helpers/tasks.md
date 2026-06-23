## 1. Criar `_workflows.py` com helper de login

- [ ] 1.1 Criar `tests/bdd/step_defs/_workflows.py` (módulo vazio com docstring explicando o padrão).
- [ ] 1.2 Implementar `login_and_pick_profile(page, live_url, profile)` — encapsula `/login → fill username → fill password → submit → wait /profiles → click profile button → wait /`.
- [ ] 1.3 Implementar helper parametrizável com kwargs `username_password: str = "test-password"` (preparar para 2FA no futuro).
- [ ] 1.4 Adicionar docstring listando os data-testids usados.
- [ ] 1.5 Rodar `uv run ruff check tests/bdd/step_defs/_workflows.py` e `uv run ruff format --check` — devem passar.

## 2. Adicionar step wrapper de login em `common_steps.py`

- [ ] 2.1 Adicionar `@when(parsers.re(r'que estou logado como "(?P<profile>[^"]+)"'))` que chama `login_and_pick_profile`.
- [ ] 2.2 Re-exportar `_workflows` no `tests/bdd/conftest.py` (para garantir que o módulo seja carregado).
- [ ] 2.3 Rodar login scenario atual (`test_login_ok[Italo]`) com wrapper inline substituído — verificar que passa.

## 3. Adicionar helper de criar 2 classes

- [ ] 3.1 Implementar `create_two_default_classes(page, live_url, pct_rfpos=50, pct_rfdinamica=50, name_rfpos="RF Pós", name_rfdinamica="RF Dinâmica")` em `_workflows.py`.
- [ ] 3.2 Encapsula: `goto /classes → wait editor → click "Adicionar classe" → fill nome row 0 → fill pct row 0 → click add → fill nome row 1 → fill pct row 1 → click "Salvar classes"`.
- [ ] 3.3 Adicionar docstring + lista de data-testids.

## 4. Adicionar step wrappers de criar 2 classes

- [ ] 4.1 Adicionar `@when('criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%')` em `class_steps.py` — chama helper com defaults.
- [ ] 4.2 Adicionar versão parametrizada: `@when(parsers.parse('criei as 2 classes padrão RF Pós {p1:d}% e RF Dinâmica {p2:d}%'))` — chama helper com kwargs.

## 5. Adicionar helper de criar 4 ativos

- [ ] 5.1 Implementar `create_four_assets(page, live_url, distribution=[(("RF Pós", 60, 40), ("RF Dinâmica", 30, 70))])` em `_workflows.py`.
- [ ] 5.2 Encapsula: `for class_name, pct1, pct2 in distribution: open_asset_form(class_name) → fill name1 + pct1 → submit → open_asset_form(class_name) → fill name2 + pct2 → submit`.
- [ ] 5.3 Adicionar docstring + lista de data-testids.

## 6. Adicionar step wrapper de criar 4 ativos

- [ ] 6.1 Adicionar `@when('adicionei 4 ativos com distribuição não-igual')` em `asset_steps.py` — chama helper com defaults.
- [ ] 6.2 Versão parametrizada opcional: `@when(parsers.parse('adicionei {count:d} ativos'))` — para futuro.

## 7. Refatorar features para usar wrappers

- [ ] 7.1 `tests/bdd/features/class_crud.feature` — substituir 5-8 steps de login + 8 steps de criar classes por wrappers quando aplicável. Manter `Snapshot create 2 classes — soma 90%` e `...110%` usando o wrapper de criar classes (não o inline) para validar que o wrapper funciona com pct customizado.
- [ ] 7.2 `tests/bdd/features/asset_crud.feature` — substituir steps de login + criar classes + criar ativos por wrappers.
- [ ] 7.3 `tests/bdd/features/import.feature` — wrapper de login + criar classes; manter steps de import inline.
- [ ] 7.4 `tests/bdd/features/target_pct.feature` — wrappers para bootstrap; manter steps de PATCH inline.
- [ ] 7.5 `tests/bdd/features/derived_display.feature` — wrappers para bootstrap; manter steps de PATCH inline.
- [ ] 7.6 `tests/bdd/features/full_journey.feature` — wrappers para todos os bootstraps; manter steps do import + PATCH inline.
- [ ] 7.7 **NÃO MEXER** em `tests/bdd/features/login.feature` e `tests/bdd/features/profile_isolation.feature` (carve-out do spec).

## 8. Verificar

- [ ] 8.1 `task test-bdd` — login scenarios passam (carve-out mantido).
- [ ] 8.2 `task test-bdd` — class_crud scenarios passam via wrappers.
- [ ] 8.3 `task test-bdd` — asset_crud, import, target_pct, derived_display passam.
- [ ] 8.4 `task test-unit` verde.
- [ ] 8.5 `task test-integration` verde.
- [ ] 8.6 `task lint` verde.
- [ ] 8.7 Validar diff: features ficaram ~30-50% menores em linhas.

## 9. Atualizar AGENTS.md

- [ ] 9.1 Adicionar bullet em "Code style" / novo "BDD workflow helpers" — referenciar `_workflows.py` e o carve-out.
- [ ] 9.2 Documentar a regra "se sequência multi-step aparece ≥3 vezes, extrair helper".

## 10. Hand-off

- [ ] 10.1 Atualizar `openspec/PRD.md §5.4` mencionando o refactor de reuso.
- [ ] 10.2 Arquivar change via `openspec archive bdd-step-reuse-helpers`.
