## MODIFIED Requirements

### Requirement: Botão "Importar CSV" no dashboard

O dashboard DEVE exibir (MUST) um botão "Importar CSV" dentro do
`<aside class="app-sidebar" data-testid="app-sidebar">` (a barra
lateral persistente introduzida pelo capability `dashboard-sidebar`).
O botão carrega `data-testid="dashboard-import-btn"` e abre o modal de
import via `@click="$store.importModal.openModal()"`. O antigo wrapper
`data-testid="dashboard-actions"` que continha o botão é removido do
markup.

#### Scenario: Botão no sidebar abre modal de import

- **WHEN** usuário está no dashboard com classes cadastradas
- **THEN** o botão "Importar CSV" (`data-testid="dashboard-import-btn"`)
  está visível dentro do `data-testid="app-sidebar"`
- **AND** nenhum elemento `data-testid="dashboard-actions"` está no DOM
- **AND** ao clicar no botão, o modal de import
  (`data-testid="import-modal-overlay"`) abre
- **AND** o modal exibe o step 1 (upload de arquivo) com input file +
  botão Enviar
