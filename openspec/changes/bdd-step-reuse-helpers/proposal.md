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
em N cenários". Esta change introduz **helper Python +
step-wrapper fino**: a sequência multi-step vira uma função
Python; o step text Gherkin vira um wrapper de 1 linha que chama
o helper.

## O que muda

- Adiciona `tests/bdd/step_defs/_workflows.py` com 3 helpers
  Python:
  - `login_and_pick_profile(page, live_url, profile)` —
    encapsula os 5 steps do fluxo `/login → /profiles → /`
  - `create_two_default_classes(page, live_url, pct_rfpos=50,
    pct_rfdinamica=50)` — encapsula os 8 steps do
    `POST /classes` snapshot
  - `create_four_assets_two_per_class(page, live_url,
    distribution=[(60,40), (30,70)])` — encapsula os 10 steps
    do modal de add ativo (RF Pós: 60/40, RF Dinâmica: 30/70)
- Adiciona step definitions finas em `tests/bdd/step_defs/`:
  - `Que estou logado como "<profile>"`
  - `Que criei as 2 classes padrão RF Pós <pct1>% e RF Dinâmica <pct2>%`
  - `Que adicionei 4 ativos com distribuição não-igual`
- Refatora os 8 feature files `.feature` para usar os novos
  steps (cenários ficam 5-10 linhas em vez de 15-25 linhas)
- `login.feature` e `profile_isolation.feature` ficam **intactos**
  (testam o login diretamente — não devem usar o wrapper)
- Adiciona capability `bdd-step-reuse` cobrindo o padrão "helper +
  wrapper" como contrato do projeto

## Capacidades

### Novas capacidades

- `bdd-step-reuse`: define o padrão de reuso para steps BDD do
  Omaha — qualquer sequência multi-step repetida em ≥3 cenários
  DEVE ser extraída como helper Python + step wrapper. Define o
  diretório de helpers (`tests/bdd/step_defs/_workflows.py`), o
  padrão de step text PT-BR, e o carve-out (cenários que testam
  o step NÃO devem usar o wrapper).

### Capacidades modificadas

(nenhuma — a refatoração é puramente interna à suite BDD)

## Impacto

- `tests/bdd/step_defs/_workflows.py` — NOVO arquivo (~150 linhas)
- `tests/bdd/step_defs/common_steps.py` — adiciona 3-4 step
  wrappers (~30 linhas)
- `tests/bdd/features/*.feature` (6 files: `class_crud`,
  `asset_crud`, `import`, `target_pct`, `derived_display`,
  `full_journey`) — refatora steps (cenários ficam menores)
- `tests/bdd/features/login.feature`,
  `tests/bdd/features/profile_isolation.feature` — INTACTOS
- `openspec/specs/bdd-step-reuse/spec.md` — NOVO
- `openspec/changes/bdd-step-reuse-helpers/{proposal,design,
  tasks}.md` — NOVO (esta change)

Sem mudança em `pyproject.toml`, sem mudança em backend, sem
mudança em templates. Zero risco operacional.

## Fora de escopo

- Composição de cenários via "Rule" do Gherkin — não suportada por
  pytest-bdd.
- Step generation programática via `stacklevel` — overkill para
  3 helpers.
- Helper Python para TODOS os steps (ex: `clico em "+ Nova
  classe"`) — só para sequências multi-step. Steps atômicos
  continuam como estão.
