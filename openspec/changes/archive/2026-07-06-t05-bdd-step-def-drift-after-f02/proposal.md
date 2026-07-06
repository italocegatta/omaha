## Why

Quatro invocações do step BDD `clico em "+ Nova classe"` quebraram após
o F02 remover a sidebar: a sidebar carregava um `<button>` com o texto
literal `+ Nova classe`. Pós-F02 o affordance migrou para o topo do
body de `/patrimonio` com **dois testids distintos**:

- `data-testid="empty-state-create-class"` (`_patrimonio_actions.html:17`,
  texto `Nova Classe` — sem o prefixo `+`), visível **apenas** quando o
  perfil não tem nenhuma classe; ou
- `data-testid="new-class-modal-submit"` (botão `Salvar` dentro do
  modal que abre após o primeiro click).

O step-def `clico em "{label}"` em
`tests/bdd/step_defs/common_steps.py:130` casa por `button:has-text`,
`[data-testid=...]`, e `a:has-text` nessa ordem. O literal
`+ Nova classe` (com `+` e espaço) não bate em nenhum dos três
candidatos pós-F02, então `task test-bdd` acusa 4 falhas com
`botão/link '+ Nova classe' não encontrado`. Sem este conserto o
loop de T01 (BDD+e2e 100% green) não fecha.

A correção é mecânica e restrita ao test-tooling: nenhum byte de
código de produção muda, nenhum requisito de spec precisa ser
revisado, nenhuma migração de dado rola. O slice existe só para
reconciliar o vocabulário Gherkin com a UI pós-F02 e blindar o
matcher contra re-ocorrências do mesmo drift de label.

## What Changes

- **Step def matcher extension** em
  `tests/bdd/step_defs/common_steps.py::click_button`: adicionar uma
  alias chain que reconheça o label legado `+ Nova classe` e mapeie
  para os candidatos pós-F02 (`[data-testid="empty-state-create-class"]`
  primeiro; cai para os candidatos atuais se não achar). Mesma
  forma para `+ Novo ativo` → `data-testid="dashboard-add-asset-open"`
  se a sidebar voltar a sumir (preventive — nenhuma quebra atual
  reportada aqui, mas o padrão é simétrico).
- **Vocabulário Gherkin** atualizado em 4 step calls:
  - `tests/bdd/features/class_crud.feature:65` — `clico em "+ Nova classe"`
    → `clico em "Nova Classe"` (lê como o botão visível).
  - `tests/bdd/features/profile_sharing.feature:17,21,37` — mesma troca.
- **Sem mudança de produção.** Sem migration, sem `src/omaha/**`
  tocado, sem `static/app.css` tocado, sem `selectors.py` tocado.
- **Sem mudança de spec.** O step matcher é detalhe de
  implementação do helper; não há requirement-level de
  `bdd-workflow-reuse` ou de qualquer outra spec que descreva o
  shape exato da chain de candidatos do `clico em`. A spec
  `bdd-workflow-reuse` continua válida sem delta.

## Capabilities

### New Capabilities
- `bdd-step-def-aliases`: define o contrato da **alias chain** que o
  step def `clico em "{label}"` consulta para reconciliar label
  drift entre F-slice e Gherkin. Captura o precedente
  `+ Nova classe` → `data-testid="empty-state-create-class"` (pós-F02)
  como um exemplo canônico, mas o requirement é genérico: qualquer
  label drift conhecido SHALL ter entrada no alias map, e o step
  def SHALL consultá-la antes dos candidatos `button:has-text` /
  `[data-testid]` / `a:has-text`.

### Modified Capabilities
<!-- Nenhuma ao nível de requirement. A correção é interna ao step
     def; a semântica visível do step (`clico em "{label}"` resolve
     um elemento clicável que case com o label) não muda. -->
(nenhuma)

## Impact

**Arquivos tocados (4):**

- `tests/bdd/step_defs/common_steps.py` — alias chain no
  `click_button` (≈10 LOC, comentário explicativo).
- `tests/bdd/features/class_crud.feature` — 1 step reescrito.
- `tests/bdd/features/profile_sharing.feature` — 3 steps
  reescritos.
- `openspec/roadmap.md` — slice status
  `Ready` → `Spec Proposed` → `Applying` → `Applied` → `Archived`
  + entry no compacted history.

**Fora de escopo (registrado para não esticar o slice):**

- A checagem de "label sem testid dedicado" que T01 introduziu
  (selector inventory + smoke) — passa sem regressão deste slice.
- As 5 falhas pre-existentes de `task test-e2e` (chromium stalls
  em `test_user_journey*`) — T01 follow-up, não T05.
- Drift de outros botões (`+ Novo ativo`, `+ Importar CSV`) — não
  relatado como failing em `task test-bdd` no baseline 2026-07-06
  (R04 archive); a alias chain fica simétrica como safety net, mas
  não há step call ativo para reescrever.

**Verificação de aceite:**

- `task test-bdd` verde: 47 pass + 4 fail → 49 pass + 2 skip
  (BDD roda serial, PRD §4.7). As 4 falhas pre-existentes
  do T01 reality check eram exatamente estas 4 invocações.
- `task test-unit`, `task test-integration`, `task test-e2e` sem
  regressão (step def só adiciona fallback; behavior atual
  preservado).
- `task lint` (ruff + prek) verde.
