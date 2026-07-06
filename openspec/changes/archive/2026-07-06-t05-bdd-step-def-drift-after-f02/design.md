## Context

`tests/bdd/step_defs/common_steps.py:130` define o step
`clico em "{label}"` que recebe um label PT-BR do Gherkin e tenta
resolver um elemento clicável via três candidatos em sequência:
`button:has-text("{label}")`, `[data-testid="{label}"]`,
`a:has-text("{label}")`. O F02 removeu a sidebar que carregava o
botão `<button>+ Nova classe</button>` literal; a nova affordance
fica em `src/omaha/templates/_patrimonio_actions.html:15-20` como
`<button data-testid="empty-state-create-class">Nova Classe</button>`
(sem o prefixo `+` no texto, e com testid dedicado em vez de texto
plano). O step def não reconhece nenhum dos dois alvos — falha com
`AssertionError: botão/link '+ Nova classe' não encontrado` em 4 step
calls (1 em `class_crud.feature`, 3 em `profile_sharing.feature`).

O mesmo padrão de drift é simétrico para `+ Novo ativo` (F02
substituiu por `data-testid="dashboard-add-asset-open"` com texto
`Novo ativo`) — não há step call quebrado no baseline 2026-07-06
(R04 archive), mas o risco de re-ocorrência é real toda vez que um
F-slice reorganiza affordances.

## Goals / Non-Goals

**Goals:**

- Fechar as 4 falhas pre-existentes do `task test-bdd` reportadas no
  T01 reality check (4 step invocations em 2 feature files).
- Introduzir um mecanismo explícito de alias chain no step def para
  que drifts futuros entre UI e Gherkin não virem falha de
  suíte — captura o precedente `+ Nova classe` (e o simétrico
  `+ Novo ativo`) como entradas explícitas de um map.
- Atualizar o vocabulário Gherkin nas 4 step calls para usar o
  label visível pós-F02 (`Nova Classe`) — leitura natural contra a
  UI atual.
- Manter o behavior atual do step def para labels que **não** têm
  alias (zero regressão em `task test-unit`, `task test-integration`,
  `task test-bdd`, `task test-e2e` fora dos 4 step calls afetados).

**Non-Goals:**

- Refator estrutural de `_workflows.py` (coberto por T01 /
  `bdd-workflow-reuse`).
- Mudança de produção: `src/omaha/**` intocado,
  `static/app.css` intocado, `tests/e2e/selectors.py` intocado.
- Renomear testid `empty-state-create-class` para `+ Nova classe` —
  o testid é o hook estável (PRD §4.6), o label visível pode (e
  deve) mudar entre F-slices sem que isso vire churn de e2e.
- Generalizar a alias chain para outros steps (`preencho o campo`,
  `pressiono`). Drift análogo pode existir mas está fora do
  escopo deste slice — o contract `bdd-step-def-aliases` é
  extensível, mas as entradas atuais cobrem só o step `clico em`.

## Decisions

### D-T05.1 — Alias map como dict literal no topo do step def

A alias chain vive como um `dict[str, tuple[str, ...]]` no topo de
`tests/bdd/step_defs/common_steps.py`, **acima** da definição do
`click_button`. Cada chave é o label herdado do Gherkin pré-F02; o
valor é uma tupla ordenada de seletores CSS a tentar **antes** dos
três candidatos atuais. Tentativa em ordem; primeiro match visível
vence.

**Rationale:** o map é lido em runtime (não em import time), o que
permite que testes futuros adicionem entradas via monkeypatch
(padrão já estabelecido em `test_seed_from_csv.py:665` —
`seed_mod.SEED_DIR = tmp_path`). A constante vive no mesmo módulo
do step def, então o escopo de import é trivial. Alternativa
considerada: externalizar para um `tests/bdd/step_defs/_aliases.py`
— rejeitada porque adiciona um arquivo para 2 entradas e a
constante é tão pequena que inline mantém o step def
auto-contido.

**Aliases atuais:**

```python
STEP_CLICK_ALIASES: dict[str, tuple[str, ...]] = {
    # F02 moved the create-class button out of the sidebar.
    # Post-F02 the affordance is `[data-testid="empty-state-create-class"]`
    # with visible text "Nova Classe" (no leading "+").
    "+ Nova classe": (
        '[data-testid="empty-state-create-class"]',
        # Fallback: the in-modal submit (Salvar) — only present
        # after the first click opened the modal. Listed for
        # safety in case a future step walks past the trigger.
        '[data-testid="new-class-modal-submit"]',
    ),
    # Symmetric preventive entry for the F02 add-asset button.
    "+ Novo ativo": (
        '[data-testid="dashboard-add-asset-open"]',
    ),
}
```

### D-T05.2 — Alias chain consultada antes dos candidatos originais

A ordem de resolução do `click_button` vira:

1. Se `label in STEP_CLICK_ALIASES`: para cada seletor da tupla,
   tenta o mesmo two-phase visibility filter
   (`wait_for(state="visible", timeout=5000)` + `locator("visible=true")`).
2. Senão, cai para a sequência atual:
   `button:has-text`, `[data-testid=label]`, `a:has-text`.

A semântica visível do step não muda para labels fora do map — o
fall-through garante que o matcher atual continua sendo o caminho
feliz.

**Rationale:** ordem de "alias primeiro" garante que entradas
explícitas prevalecem sobre heurística de text-match. Sem isso, um
label `+ Nova classe` casado via `button:has-text` poderia
resolver para um botão com substring (`Nova classe` está contido
em `Nova Classe`?) dependendo do case-sensitivity do Playwright.
Forçar testid match via alias elimina a ambiguidade.

### D-T05.3 — Gherkin atualizado para `Nova Classe` (sem `+`)

Os 4 step calls reescritos trocam `clico em "+ Nova classe"` por
`clico em "Nova Classe"`. A escolha por "Nova Classe" (sem o
prefixo `+`) alinha com o texto visível no botão
(`_patrimonio_actions.html:19`) e com o pattern da spec
`direct-landing-with-header-profile-switcher` que já referencia
o affordance como `Nova Classe` (PRD §5.3 + F02 decision D6).

**Rationale:** o matcher tem alias para o label legado (D-T05.1),
então a reescrita do Gherkin é cosmetic — mas o texto PT-BR mais
limpo (`Nova Classe`) lê melhor no relatório BDD. Custo: 4 linhas
de feature. Benefício: 0 step call quebrado no baseline + leitura
natural para novos cenários.

**Alternativa rejeitada:** introduzir um step dedicado
`clico no botão de criar classe` que mapeia direto para
`empty-state-create-class`. Mais semanticamente limpo, mas cria
um novo step def para um único elemento — quebra o pattern de
`bdd-workflow-reuse` (step wrapper only for workflows, não para
single-click helpers).

### D-T05.4 — Spec nova `bdd-step-def-aliases`, não delta em `bdd-workflow-reuse`

O contract da alias chain merece uma spec dedicada em vez de
amarrar em `bdd-workflow-reuse` (que cobre workflows Python e step
wrappers, não a chain de candidatos de um step individual).

**Rationale:** `bdd-workflow-reuse` tem 11 requirements focados
em (a) extração de workflows multi-step, (b) dataclasses, (c)
carve-out, (d) thin wrappers. Adicionar "o `clico em` tem alias
chain" dilui o foco da spec. Spec dedicada
(`bdd-step-def-aliases`) captura a invariante como contrato
isolado, com 1 requirement e 2 cenários (ver specs/).

**Alternativa rejeitada:** delta `ADDED` em `bdd-workflow-reuse` —
possível mas cria acoplamento de leitura. Spec nova segue o
precedente de `e2e-selector-pinning` (T01 archive) e
`patrimonio-template-partials` (R04 archive).

## Risks / Trade-offs

- **[R1] Alias map cresce sem governança** → cada F-slice que
  reorganiza affordances pode adicionar entradas avulsas. Mitigação:
  spec `bdd-step-def-aliases` requirement "Aliases are documented
  inline with a comment naming the originating F-slice" força
  PR review a olhar a tabela. Se a tabela passar de ~10 entradas,
  próximo T-slice promove para `tests/bdd/step_defs/_aliases.py`.

- **[R2] Fallback para `[data-testid="new-class-modal-submit"]`
  na entrada `+ Nova classe`** → se um step futuro acionar o
  alias com o modal já aberto, o matcher pula o trigger e clica
  direto no submit. Mitigação: documentado no comment do map
  ("only present after the first click opened the modal"). O
  cenário Gherkin atual não exercita esse caminho (clica uma vez
  no trigger, depois clica no Salvar que é text-match normal).

- **[R3] Reescrita do Gherkin quebra cenários que dependem do
  label `+ Nova classe` para asserção downstream** → mitigação:
  nenhum cenário atual faz asserção sobre o label do trigger;
  as asserções downstream são sobre o conteúdo do modal
  (campo `Nome da classe`, `Alocação alvo`, mensagem de erro
  `Já existe`). Verificado por `rg "Nova classe" tests/bdd/`
  (4 hits, todos nos step calls que estamos reescrevendo).

## Migration Plan

Aplicação é um único PR. Sem migration de dados, sem deploy
coordenado, sem rollback específico. O step def é parte do test
tooling (não deployado em prod); Gherkin é parte do test repo.
Smoke: `task test-bdd` deve fechar 47 pass + 4 fail → 49 pass
+ 2 skip (BDD roda serial, PRD §4.7).

## Open Questions

Nenhuma. As decisões acima cobrem todos os pontos do grill T01
reality check. O alias map é extensível para futuras
reorganizações de affordance sem reabrir este slice.
