## 1. Re-bind cenário órfão

- [x] 1.1 Em `tests/bdd/test_scenarios.py`, adicionar
  `@scenario("class_crud.feature", "Inline add + PATCH class target", features_base_dir="tests/bdd/features")`
  decorando uma `def test_inline_add_patch_class_target(): pass`.
  Posicionar logo abaixo dos outros 3 cenários de
  `class_crud.feature` (linhas ~49-73).
- [x] 1.2 Gate: `uv run pytest tests/bdd/test_scenarios.py --collect-only -q | grep -c "::test_"` retorna 18 (era 17).

## 2. Deletar `switch_profile` (dead code)

- [x] 2.1 Em `tests/bdd/step_defs/_workflows.py`, deletar a
  função `switch_profile` (linhas 128-150, ~23 linhas
  incluindo docstring).
- [x] 2.2 Em `tests/bdd/step_defs/common_steps.py`, deletar
  o import `switch_profile` (linha 28) e a função
  `_w_switched_profile` (linhas 81-83, ~3 linhas).
- [x] 2.3 Em `tests/bdd/test_workflow_contracts.py`, deletar
  a entrada `"switch_profile": r"troquei para o perfil"` do
  `WRAPPER_REGEXES` (linhas 57-60).
- [x] 2.4 Gate: `uv run python -c "from tests.bdd.step_defs._workflows import switch_profile"` falha com ImportError. `uv run grep -r "switch_profile\|troquei para" tests/bdd/` retorna 0 matches.

## 3. Deletar `create_four_assets` (1 caller, viola ≥2)

- [x] 3.1 Em `tests/bdd/step_defs/_workflows.py`, deletar a
  função `create_four_assets` (linhas 282-310, ~29 linhas).
- [x] 3.2 Em `tests/bdd/step_defs/asset_steps.py`, deletar o
  import `create_four_assets` (linha 23) e a função
  `_w_four_assets` (linhas 101-103, ~3 linhas).
- [x] 3.3 Em `tests/bdd/features/asset_crud.feature`, no
  cenário `Manual add 4 ativos não-igual por classe`
  (linha 12-18), substituir `Quando adicionei 4 ativos com
  distribuição não-igual` por 4 linhas:
  ```
  Quando adicionei o ativo "TESOURO_SELIC_2029" à classe "RF Pós" com "60%"
  E adicionei o ativo "CDB_LIQUIDEZ_2027" à classe "RF Pós" com "40%"
  E adicionei o ativo "FII_HSML11" à classe "RF Dinâmica" com "30%"
  E adicionei o ativo "ACAIO_PETR4" à classe "RF Dinâmica" com "70%"
  ```
- [x] 3.4 Gate: `uv run grep -r "create_four_assets\|_w_four_assets\|adicionei 4 ativos" tests/bdd/` retorna 0 matches. `task test-bdd -k asset_crud` verde.

## 4. Sincronizar threshold em AGENTS.md

- [x] 4.1 Em `AGENTS.md:203`, alterar "≥2 cenários com
  tendência de crescimento (≥3 cenários totais)" para
  "≥2 cenários com tendência de crescimento".
- [x] 4.2 Gate: `uv run grep -n "tendência de crescimento\|≥3 cenários" AGENTS.md` retorna exatamente 1 match (sem "≥3 cenários").

## 5. Reescrever design.md §Decisão 1 (snapshot editor → inline loop)

- [x] 5.1 No topo de
  `openspec/changes/archive/2026-06-23-bdd-workflow-reuse-helpers/design.md`,
  adicionar changelog header:
  ```
  > **Editado em 2026-06-23** por
  > `openspec/changes/fix-bdd-workflow-reuse-gaps/`:
  > §Decisão 1 reescrita — snapshot editor (`POST /classes`)
  > retirado pelo S02/T07; `create_two_default_classes`
  > agora loopa `create_one_class` (inline add form). Ver
  > tasks.md #5.2.
  ```
- [x] 5.2 Substituir o bloco "### Decisão 1" inteiro
  (linhas 38-138, ~100 linhas) por versão que descreve o
  loop inline-add com referência a `create_one_class`.
  Manter a estrutura "Por quê / Como / Feature file
  refatorado / Alternativas consideradas".
- [x] 5.3 Substituir o bloco "### Decisão 5" inteiro
  (linhas 223-277, ~55 linhas) por versão que distingue
  "redução Gherkin" (1 wrapper) de "trabalho de UI" (4
  ações inline × 2 iterações = 8 ações, escondidas atrás
  do wrapper).
- [x] 5.4 Gate: revisão visual do design.md — toda menção
  a "snapshot" / "POST /classes" no §Decisão 1 está
  removida ou anotada como "retired S02/T07".

## 6. Atualizar `add_one_asset` docstring/design

- [x] 6.1 Em `openspec/changes/archive/2026-06-23-bdd-workflow-reuse-helpers/design.md`
  §Decisão 1 (reescrita em #5), a subseção `add_one_asset`
  descreve: "1 botão global `dashboard-add-asset-open` no
  topo da Distribuição + `<select>` picker de classe, NÃO
  per-class button". Substituir qualquer menção a "per-
  class `+ Ativo` button".
- [x] 6.2 Gate: `uv run grep -n "per-class.*+ Ativo\|per-class button" openspec/changes/archive/2026-06-23-bdd-workflow-reuse-helpers/design.md` retorna 0 matches.

## 7. Renomear `_w_default_classes_pct`

- [x] 7.1 Em `tests/bdd/step_defs/class_steps.py`, renomear
  função `_w_default_classes_pct` (linhas 122-128) para
  `_w_rf_pos_rf_dinamica_pct`. Atualizar o `@given(...)`
  decorator se necessário (o texto Gherkin já menciona
  "RF Pós" e "RF Dinâmica" explicitamente, então não
  precisa mudar).
- [x] 7.2 Em `tests/bdd/README.md`, adicionar nota após a
  tabela de workflows:
  > **Nota:** `_w_rf_pos_rf_dinamica_pct` é hardcoded a
  > "RF Pós" e "RF Dinâmica". Para 2 classes com nomes
  > custom, chamar `create_two_default_classes(page,
  > live_url, [ClassSpec(name1, pct1), ClassSpec(name2,
  > pct2)])` diretamente de um `@given` inline no
  > `step_defs/`.
- [x] 7.3 Gate: `uv run grep -n "_w_default_classes_pct" tests/bdd/` retorna 0 matches. `task test-bdd -k class_crud` verde.

## 8. Marker-based carve-out

- [x] 8.1 Criar `tests/bdd/step_defs/_carve_out.py` com
  decorator trivial:
  ```python
  from dataclasses import dataclass

  @dataclass(frozen=True)
  class CarveOut:
      files: frozenset[str]
      step_regex: str

  def carve_out(*, files, step_regex):
      return CarveOut(files=frozenset(files), step_regex=step_regex)
  ```
- [x] 8.2 Em `tests/bdd/step_defs/_workflows.py`, anotar
  `login_and_pick_profile` (única workflow com carve-out
  restante após #2):
  ```python
  @carve_out(
      files=frozenset({"login.feature", "profile_isolation.feature"}),
      step_regex=r"estou logado como",
  )
  def login_and_pick_profile(...): ...
  ```
  Importar `carve_out` de `_carve_out`.
- [x] 8.3 Em `tests/bdd/test_workflow_contracts.py`,
  refatorar `test_carve_out_files_use_inline_steps`:
  - Parsear `_workflows.py` via AST; para cada função,
    ler o decorator `@carve_out(...)` se presente.
  - Para cada workflow com `CarveOut`, validar que cada
    arquivo em `files` NÃO contém `step_regex` no body.
  - Deletar `WRAPPER_REGEXES` dict hardcoded.
- [x] 8.4 Gate: `uv run pytest tests/bdd/test_workflow_contracts.py -v` verde (3 testes passam). Adicionar manualmente um `login.feature` step "Dado que estou logado como \"Italo\"" — teste deve falhar. Reverter.

## 9. Atualizar `tests/bdd/README.md`

- [x] 9.1 Na tabela de workflows (linhas 50-57), deletar
  linhas de `switch_profile` e `create_four_assets`.
- [x] 9.2 Na seção "Carve-out" (linhas 106-110), atualizar
  para mencionar marker-based enforcement via
  `@carve_out(...)` decorator (não mais "carve-out files
  keep login/switch steps inline" hardcoded).
- [x] 9.3 Gate: `uv run grep -n "switch_profile\|create_four_assets" tests/bdd/README.md` retorna 0 matches.

## 10. Verificação final

- [x] 10.1 `uv run pytest tests/bdd/test_workflow_contracts.py -v` verde (3 testes).
- [x] 10.2 `task test-unit` verde (inclui contract tests).
- [x] 10.3 `task test-integration` verde.
- [x] 10.4 `uv run python scripts/measure_bdd_reuse.py` ainda passa o floor 25%. Atualizar `scripts/baseline_gherkin_lines.json` se a contagem mudou (esperado: `asset_crud.feature::Manual add 4 ativos não-igual por classe` cresceu de 10 para 13 linhas após inlinear 4 wrappers).
- [x] 10.5 `task lint` verde.
- [x] 10.6 `task test-bdd -k asset_crud` verde (único caller de `_w_four_assets` antes da deleção).
- [x] 10.7 `task test-bdd -k class_crud` verde (incluindo cenário rebindado em #1).

**Nota (não bloqueante):** `task test-bdd` full suite tem 2
falhas pre-existing em `profile_isolation.feature`
(`test_italo_classes_invisible_to_ana` +
`test_ana_classes_invisible_to_italo`). Erro:
`AssertionError: campo 'Nome da classe' não encontrado` no
generic step `preencho o campo "Nome da classe" com "..."`
depois de `clico em "+ Nova classe"`. Verificado via
`git stash` que essas falhas existem SEM as mudanças desta
change — são Alpine timing race pre-existente na
interação `click_button` → `fill_field` no generic
step. Em escopo desta change? **Não.** Corrigir exigiria
mudar o generic step em `common_steps.py::fill_field`
para usar `expect(loc).to_be_visible()` com retry, ou
mudar `profile_isolation.feature` para usar o specific
step `preencho o campo "Nome da classe" da linha N`.
Spike separado.

## 11. Delta spec

- [x] 11.1 Em
  `openspec/changes/fix-bdd-workflow-reuse-gaps/specs/bdd-workflow-reuse/spec.md`,
  escrever delta com:
  - **MODIFIED Requirements**:
    - `Requirement: Workflow count ceiling` — manter texto,
      adicionar nota "(currently 4 workflows)".
    - `Requirement: Per-workflow carve-out table` — substituir
      texto por "workflows declare carve-out via
      `@carve_out(files=, step_regex=)` decorator; contract
      test `test_carve_out_files_use_inline_steps` deriva
      asserts do decorator automaticamente".
    - `Requirement: Python workflow for repeated multi-step sequences`
      — adicionar nota "(threshold is mandatory: 0-1 caller
      workflows are forbidden; deprovision before merge)".
  - **REMOVED Requirements**:
    - `Requirement: switch_profile workflow` — REMOVED:
      "0 callers as of 2026-06-23; deleted from
      `_workflows.py`. If mid-test profile switch is needed
      in the future, recreate the workflow + wrapper at
      that point."
    - `Requirement: create_four_assets workflow` — REMOVED:
      "1 caller as of 2026-06-23; deleted from
      `_workflows.py`. The single caller
      (`asset_crud.feature::Manual add 4 ativos não-igual por
      classe`) now uses 4× `_w_one_asset` inline."
  - **ADDED Requirements**:
    - `Requirement: Marker-based carve-out enforcement` —
      "The system SHALL provide `@carve_out` decorator in
      `tests/bdd/step_defs/_carve_out.py` that takes
      `files: Iterable[str]` and `step_regex: str` keyword
      args. The contract test SHALL derive carve-out
      assertions from this decorator (no hardcoded regex
      dict)."

## 12. Hand-off

- [x] 12.1 Confirmar nomes: change slug
  `fix-bdd-workflow-reuse-gaps`, capability
  `bdd-workflow-reuse` (modified). Sync delta spec com
  `openspec/specs/bdd-workflow-reuse/spec.md` quando
  arquivar.
- [x] 12.2 `git log --oneline -15` — verificar commits
  granulares (1 commit por arquivo modificado, idealmente
  agrupados por seção desta tasks.md).
- [x] 12.3 `openspec archive fix-bdd-workflow-reuse-gaps`.
