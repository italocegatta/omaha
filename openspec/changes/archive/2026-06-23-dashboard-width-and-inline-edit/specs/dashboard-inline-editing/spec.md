## MODIFIED Requirements

### Requirement: Inline editing de target % da classe

The dashboard MUST allow editing the class target % by clicking the percentage
value, which becomes an inline input. O save faz PATCH /api/classes/{id} e atualiza o
valor local sem recarregar a página. The editor SHALL accept numeric input and
MUST update the displayed value on a 200 response. The editor MUST commit on
either Enter pressed inside the input or blur of the input, and MUST cancel on
Escape pressed inside the input. The editor MUST NOT render a save or cancel
button alongside the input.

#### Scenario: Clique no % abre input inline

- **WHEN** usuário clica no target % da classe (data-testid="class-target-pct-view")
- **THEN** o span some e um input numérico (data-testid="class-inline-edit-input") aparece
- **AND** o input contém o valor atual preenchido

#### Scenario: Enter salva e atualiza localmente

- **WHEN** usuário digita novo valor e pressiona Enter
- **THEN** PATCH /api/classes/{id} é enviado
- **AND** em caso de 200, o valor local (classTargetPct) é atualizado
- **AND** o input some e o novo valor aparece no span

#### Scenario: Blur do input salva e atualiza localmente

- **WHEN** usuário digita novo valor e move o foco para fora do input (clique
  em outra célula, Tab, ou clique fora da tabela)
- **THEN** PATCH /api/classes/{id} é enviado com o mesmo corpo do Enter
- **AND** em caso de 200, o valor local (classTargetPct) é atualizado
- **AND** o input some e o novo valor aparece no span

#### Scenario: Escape cancela a edição

- **WHEN** usuário digita novo valor e pressiona Escape
- **THEN** nenhuma requisição PATCH é enviada
- **AND** o input some e o valor anterior permanece no span

#### Scenario: Editor não renderiza botão salvar nem cancelar

- **WHEN** o input inline do target % da classe está aberto
- **THEN** nenhum elemento com data-testid="class-inline-edit-commit" ou
  data-testid="class-inline-edit-cancel" está presente no DOM

### Requirement: Edit acceptance is unconditional

The dashboard's inline editor MUST accept every commit and reflect
the new value locally. The inline input MUST commit on Enter or blur
without requiring any save button. The client MUST NOT block the commit when the local
preview's per-class sum differs from 100%. The PATCH /api/assets/{id}
endpoint MUST accept the write unconditionally (within per-row range
0-100) and MUST NOT return 422 for a per-class sum violation. The
resulting deviation, if any, is surfaced through the
`asset-allocation-alerts` spec, not by blocking the write.

#### Scenario: Off-100 edit is accepted

- **WHEN** the user commits a new target_pct that pushes the per-class
  sum to 110% by pressing Enter (or by blurring the input)
- **THEN** the PATCH call returns 200
- **AND** the asset's local target_pct updates to the new value
- **AND** the per-class badge (asset-group-header-alert) shows
  "Sobra X%"

#### Scenario: Add asset with off-100 sum is accepted

- **WHEN** the user submits a new asset with `target_pct` such that
  the per-class sum exceeds 100%
- **THEN** the POST /api/assets call returns 201
- **AND** the new row is added to the table
- **AND** the per-class badge reflects the new deviation

## ADDED Requirements

### Requirement: Editor inline do alvo % do ativo segue o mesmo padrão Enter-or-blur

The dashboard's per-asset inline editors (`alvo % classe` and `alvo % total` cells) MUST follow the same commit pattern as the class header editor: Enter OR blur of the input commits, Escape cancels, and no save / cancel button is rendered. The live confirm hint on the `alvo % total` editor and the inline error span on either editor MUST continue to render in edit mode.

#### Scenario: Enter no alvo % classe salva

- **WHEN** usuário clica na célula "Alvo % classe" do ativo (data-testid="asset-target-pct-class")
- **AND** digita novo valor e pressiona Enter
- **THEN** PATCH /api/assets/{id} é enviado com o novo target_pct
- **AND** o input some e o novo valor aparece no span

#### Scenario: Blur do alvo % classe salva

- **WHEN** usuário digita novo valor no input de "Alvo % classe" e move
  o foco para fora do input
- **THEN** PATCH /api/assets/{id} é enviado com o novo target_pct

#### Scenario: Enter no alvo % total salva e recalcula

- **WHEN** usuário digita novo valor no input de "Alvo % total" e
  pressiona Enter
- **THEN** o cliente calcula `new_target_pct = target_pct_total * 100 / classTargetPct`
- **AND** PATCH /api/assets/{id} é enviado com o target_pct derivado
- **AND** em 200, ambas as células (alvo % classe e alvo % total) refletem os novos valores

#### Scenario: Nenhum botão salvar/cancelar nos inputs de ativo

- **WHEN** qualquer input inline do ativo (alvo % classe ou alvo % total)
  está aberto
- **THEN** nenhum elemento com data-testid="asset-inline-edit-commit",
  data-testid="asset-inline-edit-cancel",
  data-testid="asset-target-pct-total-edit-commit", ou
  data-testid="asset-target-pct-total-edit-cancel" está presente no DOM

### Requirement: Layout do dashboard usa largura máxima de 1400px

The dashboard's `<main>` element MUST render with `max-width: 1400px`
so content occupies roughly 70% of a 1920px-class monitor with the
existing 2rem auto margin. The asset table and class sections MUST
stretch to fill the wider container. The pre-existing
`@media (max-width: 480px)` collapse rules MUST continue to apply on
small screens unchanged.

#### Scenario: Dashboard em monitor 1920px ocupa ~73% da largura

- **WHEN** o dashboard renderiza em viewport de 1920px
- **THEN** o `<main>` centraliza com `max-width: 1400px`
- **AND** a tabela de ativos ocupa toda a largura disponível do container
