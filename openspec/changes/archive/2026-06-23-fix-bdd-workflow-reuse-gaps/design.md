## Contexto

A change `bdd-workflow-reuse-helpers`
(`archive/2026-06-23-bdd-workflow-reuse-helpers/`) introduziu
6 workflows + 2 dataclasses + 2 constantes + 7 wrappers +
3 contract tests + measure script + README + delta spec.
A retrospectiva encontrou 10 gaps entre intenção declarada
e estado final. Esta change fecha os 10 gaps corrigíveis.

Os 4 workflows restantes após a limpeza:

| Workflow | Callers | Spec rule |
|---|---|---|
| `login_and_pick_profile` | 14 (7 features) | ✓ ≥2 |
| `create_one_class` | 6 (4 features) | ✓ ≥2 |
| `create_two_default_classes` | 5 (4 features, 2 wrappers) | ✓ ≥2 |
| `add_one_asset` | 4 (3 features) | ✓ ≥2 |

Os 2 removidos:

| Workflow | Callers | Spec rule |
|---|---|---|
| `switch_profile` | 0 | ✗ ≥2 |
| `create_four_assets` | 1 | ✗ ≥2 |

## Decisões

### Decisão 1: Deletar dead code em vez de esperar uso futuro

**Por quê:** o spec da capability `bdd-workflow-reuse`
proíbe explicitamente manter workflow sem ≥2 callers
(`Requirement: Workflow count ceiling` +
`Requirement: Python workflow for repeated multi-step
sequences` — "appears in ≥2 scenarios with growth
trend"). `switch_profile` (0 callers) e
`create_four_assets` (1 caller) violam o spec que a
própria change escreveu.

**Alternativas:**

- **Reativar `switch_profile` quando algum cenário
  precisar.** Rejeitado: adivinhação sobre futuro. O
  spec rejeita explicitamente "too specific to warrant
  inline steps" como justificativa para criar workflow
  sem uso. Quando alguém precisar de mid-test profile
  switch (não acontece hoje), recriar a workflow
  naquele momento.
- **Adicionar parametrized variant
  `_w_four_assets_pct`** para justificar
  `create_four_assets`. Rejeitado: speculative
  future-proofing. O caller atual usa a distribuição
  hardcoded `DEFAULT_FOUR_ASSETS`; sem 2º caller
  comprovado, é puro "talvez algum dia". Spec rejeita.
- **Adicionar mais 1 cenário artificial
  (`asset_crud.feature::Manual add 4 ativos
  com distribuição igual`) só para justificar o
  workflow.** Rejeitado: teste sem propósito. O teste
  atual já cobre a distribuição não-igual (D006 = off-100
  é aceito); duplicar com "igual" não cobre bug
  diferente, só infla suite.

**Decisão final:** delete. Inlinear as 4 chamadas
`_w_one_asset` no único caller
(`asset_crud.feature::Manual add 4 ativos não-igual por
classe`). Ganha 2 linhas Gherkin no único cenário que
perde o wrapper; perde 30 linhas de workflow órfão e 5
linhas de wrapper órfão. Liquido: suite fica mais
honesta.

### Decisão 2: Marker-based carve-out em vez de dict hardcoded

**Por quê:** o contract test atual lista 2 workflows
manualmente. Quando uma nova workflow com carve-out for
adicionada, o teste passa vacuosamente a menos que alguém
atualize `WRAPPER_REGEXES`. Isso é enforcement fraco.

**Como:** cada workflow com carve-out declara seu
carve-out no próprio código, via decorator:

```python
from tests.bdd.step_defs._carve_out import carve_out

@carve_out(
    files=frozenset({"login.feature", "profile_isolation.feature"}),
    step_regex=r"estou logado como",
)
def login_and_pick_profile(page, live_url, profile, password="test-password"):
    ...
```

`tests/bdd/test_workflow_contracts.py` itera pelas
workflows anotadas e gera os asserts. Adicionar nova
workflow com carve-out = adicionar o decorator; teste
pega automaticamente.

**Alternativas:**

- **AST parse de docstring** — extrair "Carve-out:
  arquivo1, arquivo2" do docstring via regex. Rejeitado:
  parsing de docstring é frágil (typos passam silenciosos,
  reformatação quebra).
- **YAML/TOML sidecar** — `tests/bdd/carve_outs.yaml`.
  Rejeitado: configuração fora do código de workflow
  quebra o principle of locality (quem lê a workflow não
  vê o carve-out).
- **Comment marker** — `# carve-out: login.feature,
  profile_isolation.feature`. Rejeitado: ainda parseável
  só por regex; tipagem/refactor tools não veem.

### Decisão 3: Renomear `_w_default_classes_pct` para
`_w_rf_pos_rf_dinamica_pct`

**Por quê:** o step text literal `"criei as 2 classes
padrão RF Pós {p1:d}% e RF Dinâmica {p2:d}%"` só funciona
com esses 2 nomes. Nome `_w_default_classes_pct` sugere
"qualquer 2 classes com pct parametrizado" — o que não é.

**Alternativas:**

- **Generalizar wrapper para aceitar nomes.** Rejeitado:
  o step text em PT-BR fica esquisito com 2 nomes
  parametrizados (`{c1} {p1}%` e `{c2} {p2}%` é
  ilegível). Para nomes custom, contribuidor deve chamar
  `create_two_default_classes(page, live_url, [...])`
  direto de um `@given` inline no `step_defs/`. Documentar
  isso na README.
- **Remover o wrapper parametrizado, deixar só o
  default.** Rejeitado: o cenário `class_crud.feature::
  Inline create 2 classes — soma 90%` e `...110%` usam
  pcts custom e ficariam sem equivalente. Aí teríamos que
  reverter para steps inline, perdendo o ganho de 6
  cenários Gherkin.

**Decisão:** rename. Mantém o wrapper, deixa claro o
acoplamento aos nomes. Adiciona nota no README sobre a
alternativa "chamar `create_two_default_classes` direto
para nomes custom".

### Decisão 4: Reescrever design.md em vez de criar errata

**Por quê:** `openspec/changes/archive/2026-06-23-bdd-workflow-reuse-helpers/design.md`
é citado pelo spec operacional `tests/bdd/README.md` e
pelos contract tests como fonte de verdade. Manter
"código diz X, design.md diz Y" confunde contribuidor.

**Alternativa:** deixar design.md histórico, criar
`design-errata.md` no novo change. Rejeitado: 2 fontes
de verdade para o mesmo conceito. Spec sempre diz "single
source of truth".

**Decisão:** editar o design.md do archive in-place. O
archive é histórico (change fechada) mas o `design.md`
dentro dele é referenciado — então o conteúdo importa.
Adicionar changelog header no topo do design.md
(`> Editado em 2026-06-23 por fix-bdd-workflow-reuse-gaps:
§Decisão 1 reescrita — snapshot editor retirado pelo
S02/T07; ver tasks.md #5`).

### Decisão 5: Threshold rule unificada = "≥2 cenários com
tendência de crescimento"

**Por quê:** o spec (`openspec/specs/bdd-workflow-reuse/spec.md`),
o README (`tests/bdd/README.md`), e a proposal original
todos dizem "≥2 cenários com growth trend". AGENTS.md
linha 203 adicionou "≥3 cenários totais" — qualificação
que não está em nenhum outro artefato, sem justificativa
documentada, e contradiz os 3 acima.

**Decisão:** AGENTS.md alinha com a maioria (3 vs 1).

## Riscos / Trade-offs

- **Reativar workflow deletada é trabalho manual
  futuro.** Se um cenário de mid-test profile switch
  aparecer, contribuidor recria `switch_profile` (não é
  caro — 1 workflow + 1 wrapper + 1 entrada no carve-out
  table ≈ 30 linhas). Custo baixo, isolamento claro.
- **Marker-based carve-out adiciona 1 arquivo novo
  (`_carve_out.py` com 1 decorator trivial).** Custo:
  ~15 linhas de boilerplate. Benefício: contrato
  enforceable automaticamente.
- **`@scenario(...)` adicionado no test_scenarios.py pode
  falhar** se o `.feature` foi editado sem rebind. Aceito:
  é um teste que deveria estar rodando. Falhar agora é
  correto (e já falharia se alguém rodasse
  `task test-bdd -k "inline_add_patch"` manualmente —
  atualmente retorna "no tests ran", o que esconde o bug).
- **Edit in-place em design.md do archive quebra
  noção de "archive é imutável".** Aceito: archive é
  imutável para `openspec list` purposes (não re-aparece
  como active change). O conteúdo do `design.md` dentro
  é leitura; pode ser editado se referenciado por outro
  artefato vivo.

## Não-mudanças explícitas

- `_workflows.py` mantém `@dataclass(frozen=True)` em
  `ClassSpec` e `AssetSpec` (sem mudança de contrato).
- `_workflows.py` mantém `DEFAULT_TWO_CLASSES` e
  `DEFAULT_FOUR_ASSETS` (não removidos — podem ser
  reusados em cenários futuros).
- `tests/bdd/conftest.py` mantém `--host 127.0.0.1` para
  o uvicorn interno (Playwright roda no mesmo host;
  Network access rule em AGENTS.md não se aplica a
  test fixtures).
- `tests/bdd/README.md` mantém o exemplo de uso
  (`task test-bdd -k class_crud`) — ainda funciona.
