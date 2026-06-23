# language: pt
## Por quê

A nova suite BDD em `tests/bdd/` (criada por
`openspec/changes/archive/2026-06-23-bdd-e2e-redesign/`) introduziu 30
cenários Gherkin em PT-BR. Cada cenário repete os mesmos blocos de
steps para os fluxos padrão:

- **Login + seleção de perfil** — 5 steps `Dado/Quando` repetidos em
  ~25 cenários. Mudança no fluxo de auth (2FA, OAuth, mudança no
  formulário de login) = reescrita de 25 cenários.
- **Criar 2 classes (`RF Pós` 50% + `RF Dinâmica` 50%)** — 8 steps
  `Quando` repetidos em ~10 cenários. Mudança na regra de negócio
  das classes (novo nome padrão, percentuais, classe extra) =
  reescrita de 10 cenários.
- **Criar 4 ativos com target_pct não-igual** — 10 steps `Quando`
  repetidos em 2 cenários hoje (vai crescer). Mudança na forma de
  cadastro de ativos = reescrita de N cenários.
- **Switch de perfil mid-test** — 6 steps logout + login repetidos
  em `profile_isolation.feature` e em cenários futuros que
  precisem de cross-profile visibility.
- **Criar 1 classe inline (`+ Nova classe`)** — 4 steps repetidos
  em ~3 cenários de `class_crud.feature`.
- **Criar 1 ativo (modal direto)** — 3 steps repetidos em ~2
  cenários (duplicate ticker, etc.).

Se a regra de negócio muda (e vai mudar — já vimos mudanças
recentes em `omaha.routes.classes` linhas 143-145 sobre sum-to-100),
cada mudança exige N edições manuais em arquivos `.feature`.

pytest-bdd NÃO suporta composição de cenários (chamar cenário X de
dentro de cenário Y) — confirmado via docs oficiais
(`https://pytest-bdd.readthedocs.io/en/latest/`). As opções de
reuso nativas são:

1. **`Contexto:` (Background Gherkin)** — reuso **dentro do
   arquivo** apenas.
2. **Step definitions em `conftest.py`** — reuso **cross-file**, mas
   cada step é UMA ação atômica.
3. **Step aliases** — uma função, múltiplos textos (não ajuda aqui).

Nenhuma cobre o caso "sequência de 5-10 steps que se repete inteira
em N cenários". Esta change introduz **workflow Python +
step-wrapper fino**: a sequência multi-step vira uma função
Python; o step text Gherkin vira um wrapper de 1 linha que chama
o workflow. O threshold de extração é "≥2 cenários com tendência
de crescimento" — pragmático para a fase atual da suite.

## O que muda

- Adiciona `tests/bdd/step_defs/_workflows.py` com:
  - 2 dataclasses imutáveis: `ClassSpec(name, target_pct)` e
    `AssetSpec(class_name, ticker, target_pct)`
  - 2 constantes reusáveis: `DEFAULT_TWO_CLASSES: list[ClassSpec]`
    e `DEFAULT_FOUR_ASSETS: list[AssetSpec]`
  - 6 workflows Python (1 por sequência multi-step repetida):
    - `login_and_pick_profile(page, live_url, profile,
      password="test-password")` — 5 steps do fluxo
      `/login → /profiles → /`
    - `switch_profile(page, live_url, other_profile)` — 6 steps
      logout + login (NOVO)
    - `create_one_class(page, live_url, name, target_pct)` —
      4 steps do `+ Nova classe` inline (NOVO)
    - `create_two_default_classes(page, live_url, classes=None)`
      — 8 steps do `POST /classes` snapshot
    - `add_one_asset(page, live_url, class_name, ticker,
      target_pct)` — 3 steps do modal de add ativo (NOVO)
    - `create_four_assets(page, live_url, assets=None)` — N
      steps do modal em loop
- Adiciona step definitions finas em `tests/bdd/step_defs/` com
  prefixo `_w_` (workflow-wrapper convention):
  - `common_steps.py`: `_w_logged_in_as` (`@given`) +
    `_w_switched_profile` (`@given`)
  - `class_steps.py`: `_w_one_class` (`@given`) +
    `_w_default_classes` (`@given`) + `_w_default_classes_pct`
    (`@given`, parametrizado)
  - `asset_steps.py`: `_w_one_asset` (`@when`) +
    `_w_four_assets` (`@when`)
- Refatora os 6 feature files `.feature` (exceto
  `login.feature` e `profile_isolation.feature`) para usar os
  novos steps (cenários ficam 5-10 linhas em vez de 15-25)
- `login.feature` e `profile_isolation.feature` ficam
  **parcialmente intactos** — carve-out per-workflow (não usam
  `login_and_pick_profile` / `switch_profile`); podem usar os
  outros wrappers se cenário futuro precisar
- Adiciona capability `bdd-workflow-reuse` cobrindo o padrão
  "workflow + wrapper" como contrato do projeto, incluindo
  dataclasses, pré-condições, carve-out per-workflow, e 3
  contract tests de enforcement
- Adiciona `tests/bdd/test_workflow_contracts.py` com 3 testes
  que enforçam: ceiling de 10 workflows, ausência de wrappers
  em arquivos carve-out, e wrapper-delegates-to-workflow

## Capacidades

### Novas capacidades

- `bdd-workflow-reuse`: define o padrão de reuso para steps BDD
  do Omaha — qualquer sequência multi-step repetida em ≥2
  cenários com tendência de crescimento DEVE ser extraída como
  workflow Python + step wrapper. Define o diretório de
  workflows (`tests/bdd/step_defs/_workflows.py`), as
  dataclasses `ClassSpec`/`AssetSpec` como input canônico, o
  padrão de pré-condição via assertion explícita, o carve-out
  per-workflow (não per-feature), e os 3 contract tests
  enforçando o contrato.

### Capacidades modificadas

(nenhuma — a refatoração é puramente interna à suite BDD)

## Impacto

- `tests/bdd/step_defs/_workflows.py` — NOVO arquivo
  (~250 linhas: 2 dataclasses + 2 constantes + 6 workflows +
  docstrings com pré-condições + data-testids)
- `tests/bdd/step_defs/common_steps.py` — adiciona 2 step
  wrappers (`_w_logged_in_as`, `_w_switched_profile`) (~20 linhas)
- `tests/bdd/step_defs/class_steps.py` — adiciona 3 step
  wrappers (`_w_one_class`, `_w_default_classes`,
  `_w_default_classes_pct`) (~25 linhas)
- `tests/bdd/step_defs/asset_steps.py` — adiciona 2 step
  wrappers (`_w_one_asset`, `_w_four_assets`) (~15 linhas)
- `tests/bdd/features/*.feature` (6 files: `class_crud`,
  `asset_crud`, `import`, `target_pct`, `derived_display`,
  `full_journey`) — refatora steps (cenários ficam menores)
- `tests/bdd/features/login.feature`,
  `tests/bdd/features/profile_isolation.feature` — INTACTOS
  (carve-out per-workflow)
- `tests/bdd/test_workflow_contracts.py` — NOVO (~80 linhas,
  3 contract tests)
- `tests/bdd/README.md` — NOVO (~120 linhas, spec operacional
  pra contribuidores)
- `scripts/measure_bdd_reuse.py` — NOVO (~30 linhas, métrica
  antes/depois)
- `AGENTS.md` — adiciona 1 bullet em "Testing conventions"
- `openspec/PRD.md §5.4` — adiciona link pro `tests/bdd/README.md`
- `openspec/specs/bdd-workflow-reuse/spec.md` — NOVO
- `openspec/changes/bdd-workflow-reuse-helpers/{proposal,design,
  tasks}.md` — NOVO (esta change)

Sem mudança em `pyproject.toml`, sem mudança em backend, sem
mudança em templates. Zero risco operacional.

## Fora de escopo

- Composição de cenários via "Rule" do Gherkin — não suportada
  por pytest-bdd.
- Step generation programática via `stacklevel` — overkill para
  6 workflows.
- Workflow Python para TODOS os steps (ex: `clico em "+ Nova
  classe"`) — só para sequências multi-step. Steps atômicos
  continuam como estão.
- pytest-xdist em `test-bdd` — autouse fixture
  `clean_seeded_profiles` compartilha SQLite session-scoped;
  paralelização causaria race. Hoje `test-bdd` roda serial;
  ticket separado se equipe quiser paralelizar no futuro.
- Migração de `_wipe_profile` do `tests/bdd/conftest.py` para
  `_workflows.py` — decidido: NÃO migra (é fixture de DB, não
  workflow de UI).
