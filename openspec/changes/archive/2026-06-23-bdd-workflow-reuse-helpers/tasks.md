## 1. Criar `_workflows.py` com dataclasses e constantes

- [x] 1.1 Criar `tests/bdd/step_defs/_workflows.py` com docstring explicando o padrão "workflow + wrapper".
- [x] 1.2 Definir `ClassSpec(frozen=True)` e `AssetSpec(frozen=True)` no topo do arquivo.
- [x] 1.3 Adicionar constantes `DEFAULT_TWO_CLASSES: list[ClassSpec]` e `DEFAULT_FOUR_ASSETS: list[AssetSpec]`.
- [x] 1.4 Rodar `uv run ruff check tests/bdd/step_defs/_workflows.py` e `uv run ruff format --check` — devem passar.

## 2. Implementar workflow `login_and_pick_profile`

- [x] 2.1 Função `(page, live_url, profile: str, password: str = "test-password")` com docstring listando pré-condição + data-testids.
- [x] 2.2 Encapsula: `goto /login → fill username → fill password → submit → wait /profiles → click profile button → wait /`.
- [x] 2.3 Sem assertion de precondição (entry point).

## 3. Adicionar step wrapper de login em `common_steps.py`

- [x] 3.1 Adicionar `@given(parsers.re(r'(que )?estou logado como "(?P<profile>[^"]+)"'))` que chama `login_and_pick_profile`. Nome da função: `_w_logged_in_as`.
- [x] 3.2 Rodar `task test-bdd --k "login"` — login scenarios passam (carve-out: usam inline, não wrapper).
- [x] 3.3 Rodar `task test-bdd --k "class_crud"` — class_crud usa wrapper novo e passa.

## 4. Implementar workflow `switch_profile`

- [x] 4.1 Função `(page, live_url, other_profile: str)`: assume login (assertion), clica logout → goto /login → `login_and_pick_profile`.
- [x] 4.2 Assertion de precondição: `page.url.endswith("/")` falha com RuntimeError mencionando `login_and_pick_profile`.
- [x] 4.3 Docstring com data-testids (logout button, login form).

## 5. Adicionar step wrapper de switch em `common_steps.py`

- [x] 5.1 Adicionar `@given(parsers.re(r'(que )?troquei para o perfil "(?P<other>[^"]+)"'))`. Nome: `_w_switched_profile`.

## 6. Implementar workflow `create_one_class`

- [x] 6.1 Função `(page, live_url, name: str, target_pct: int)`: assume login (assertion), goto /classes, preenche inline add form (nome + pct), clica Salvar.
- [x] 6.2 Assertion de precondição + docstring com data-testids.

## 7. Adicionar step wrapper de 1 classe em `class_steps.py`

- [x] 7.1 Adicionar `@given(parsers.parse('criei a classe "{name}" com "{pct:d}%"'))`. Nome: `_w_one_class`.

## 8. Implementar workflow `create_two_default_classes`

- [x] 8.1 Função `(page, live_url, classes: list[ClassSpec] | None = None)`: se None usa `DEFAULT_TWO_CLASSES`. Encapsula snapshot create (8 steps).
- [x] 8.2 Assertion de precondição + docstring com data-testids.

## 9. Adicionar step wrappers de 2 classes em `class_steps.py`

- [x] 9.1 `@given('criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%')` — chama `create_two_default_classes(page, live_url)`. Nome: `_w_default_classes`.
- [x] 9.2 `@given(parsers.parse('criei as 2 classes padrão RF Pós {p1:d}% e RF Dinâmica {p2:d}%'))` — preenche `list[ClassSpec]` programaticamente. Nome: `_w_default_classes_pct`.

## 10. Implementar workflow `add_one_asset`

- [x] 10.1 Função `(page, live_url, class_name: str, ticker: str, target_pct: int)`: assume login + classes (assertion), abre modal, preenche, submit.
- [x] 10.2 Assertion de precondição + docstring com data-testids.

## 11. Adicionar step wrapper de 1 ativo em `asset_steps.py`

- [x] 11.1 Adicionar `@when(parsers.parse('adicionei o ativo "{ticker}" à classe "{cls}" com "{pct:d}%"'))`. Nome: `_w_one_asset`.

## 12. Implementar workflow `create_four_assets`

- [x] 12.1 Função `(page, live_url, assets: list[AssetSpec] | None = None)`: se None usa `DEFAULT_FOUR_ASSETS`. Loop chama `add_one_asset`.
- [x] 12.2 Assertion de precondição + docstring com data-testids.

## 13. Adicionar step wrapper de 4 ativos em `asset_steps.py`

- [x] 13.1 `@when('adicionei 4 ativos com distribuição não-igual')` — chama `create_four_assets(page, live_url)`. Nome: `_w_four_assets`.

## 14. Refatorar features (1 commit por arquivo)

- [x] 14.0 Antes: `git checkout -b bdd-refactor-login` — branch nova; 1 commit por arquivo refatorado.
- [x] 14.1 `tests/bdd/features/class_crud.feature` — substituir login + criar-classes onde aplicável. Manter `Snapshot create 2 classes — soma 90%` e `...110%` usando o wrapper de criar classes parametrizado (valida que wrapper funciona com pcts custom).
  - **Gate:** `task test-bdd --k "class_crud"` verde antes do próximo.
- [x] 14.2 `tests/bdd/features/asset_crud.feature` — wrappers de login + classes + ativos.
  - **Gate:** `task test-bdd --k "asset_curd"` verde.
- [x] 14.3 `tests/bdd/features/import.feature` — wrapper de login + criar classes; manter steps de import inline.
  - **Gate:** `task test-bdd --k "import"` verde.
- [x] 14.4 `tests/bdd/features/target_pct.feature` — wrappers para bootstrap; manter steps de PATCH inline.
  - **Gate:** `task test-bdd --k "target_pct"` verde.
- [x] 14.5 `tests/bdd/features/derived_display.feature` — wrappers para bootstrap; manter steps de PATCH inline.
  - **Gate:** `task test-bdd --k "derived_display"` verde.
- [x] 14.6 `tests/bdd/features/full_journey.feature` — wrappers para todos os bootstraps; manter steps do import + PATCH inline.
  - **Gate:** `task test-bdd --k "full_journey"` verde.
- [x] 14.7 **NÃO MEXER** em `tests/bdd/features/login.feature` e `tests/bdd/features/profile_isolation.feature` (carve-out).

## 15. Adicionar contract tests

- [x] 15.1 Criar `tests/bdd/test_workflow_contracts.py` (módulo de testes puro, não BDD).
- [x] 15.2 `test_workflow_count_under_ceiling`: importa `tests.bdd.step_defs._workflows`, conta public callables (nome não inicia com `_`), assert ≤10.
- [x] 15.3 `test_carve_out_files_use_inline_steps`: parse `login.feature` + `profile_isolation.feature` via `pytest-bdd` scenarios; assert nenhum step contém regex `estou logado como` ou `troquei para o perfil`.
- [x] 15.4 `test_wrappers_delegate_to_workflows`: para cada função em `tests/bdd/step_defs/` cujo nome inicia com `_w_`, parse AST do body, assert contém `Call` para função definida em `_workflows.py`.
- [x] 15.5 Marcar o arquivo com `pytestmark = pytest.mark.unit` no topo para rodar em `task test-unit` (não `task test-bdd`).
- [x] 15.6 `task test-unit` verde — contract tests rodam.

## 16. Verificação final

- [x] 16.1 `task test-bdd` verde (todos os scenarios).
- [x] 16.2 `task test-unit` verde (inclui contract tests).
- [x] 16.3 `task test-integration` verde.
- [x] 16.4 `task lint` verde.
- [x] 16.5 Script `scripts/measure_bdd_reuse.py`: conta linhas-Gherkin-por-cenário nos 6 features refatorados, compara com baseline pré-refactor, assert redução ≥25%.

## 17. Documentação

- [x] 17.1 Criar `tests/bdd/README.md` (NOVO):
  - Lista os 6 workflows com assinatura, pré-condição, data-testids
  - Tabela de carve-out copiada do design.md
  - Exemplo de uso: "para adicionar novo cenário, importe workflow X de `_workflows`"
  - Regra ≥2 com tendência + ceiling 10
  - Link pros contract tests
- [x] 17.2 `AGENTS.md`: bullet em "Testing conventions" — "BDD workflows em `tests/bdd/step_defs/_workflows.py`. Regra ≥2 com tendência. Carve-out em design.md §Decisão 2. BDD roda serial — não adicionar xdist."
- [x] 17.3 `openspec/PRD.md §5.4`: link "BDD workflow reuse pattern: ver `tests/bdd/README.md`".

## 18. Hand-off

- [x] 18.1 Confirmar nomes: change slug `bdd-workflow-reuse-helpers`, capability `bdd-workflow-reuse` (renomeação aplicada nesta revisão).
- [x] 18.2 `git log --oneline -10` — verificar 1 commit por arquivo `.feature` refatorado.
- [x] 18.3 `openspec archive bdd-workflow-reuse-helpers`.
