## Purpose

Modal de import CSV no dashboard com upload, preview (auto-matched +
unmatched), e commit. Substitui as páginas standalone /import e
/import/review.

## Requirements

### Requirement: Botão "Importar CSV" no dashboard

O dashboard DEVE exibir um botão "Importar CSV" na área de ações (data-testid="dashboard-actions")
que abre o modal de import via `@click="$store.importModal.openModal()"`.

#### Scenario: Botão abre modal de import

- **WHEN** usuário está no dashboard com classes cadastradas
- **THEN** o botão "Importar CSV" (data-testid="dashboard-import-btn") está visível
- **AND** ao clicar, o modal de import (data-testid="import-modal-overlay") abre
- **AND** o modal exibe o step 1 (upload de arquivo) com input file + botão Enviar

### Requirement: Upload de CSV no modal (Step 1)

O modal DEVE permitir upload de arquivo CSV via input file e enviar para
`POST /api/import/preview`. O preview retorna JSON com `preview_id`, `auto_matched`,
`unmatched`, e `asset_classes`.

#### Scenario: Upload bem-sucedido avança para Step 2

- **WHEN** usuário seleciona um arquivo CSV
- **AND** clica "Enviar"
- **THEN** o modal faz POST /api/import/preview com FormData
- **AND** em caso de sucesso (200), avança para step 2 (review)
- **AND** exibe resumo de auto-matched + tabela de linhas unmatched
- **AND** exibe mensagem de erro (data-testid="import-upload-error") em caso de falha

### Requirement: Revisão e commit de import (Step 2)

O modal DEVE exibir:
- Resumo de linhas auto-matched (data-testid="import-matched-summary")
- Tabela de linhas unmatched (data-testid="import-unmatched-table") com dropdowns de classe
- Botão "Confirmar importacao" (data-testid="import-confirm-btn")

Ao confirmar, DEVE fazer POST /api/import/commit com os assignments e recarregar a página.

#### Scenario: Sessão expirada mostra estado de erro

- **WHEN** preview expirou (previewError = true)
- **THEN** modal exibe mensagem "Sessao expirada. Reenvie o arquivo."
- **AND** botão "Reenviar" volta para step 1

#### Scenario: Commit bem-sucedido recarrega dashboard

- **WHEN** usuário confirma import com assignments válidos
- **THEN** modal faz POST /api/import/commit
- **AND** em caso de sucesso, recarrega a página (window.location.reload())
- **AND** dashboard exibe os novos ativos com posições

### Requirement: Alpine store global importModal

O estado do modal DEVE viver em um Alpine store global (`$store.importModal`) para
que o botão trigger (fora do escopo x-data do modal) possa abri-lo.

#### Scenario: Store expõe métodos openModal e closeModal

- **WHEN** `$store.importModal.openModal()` é chamado
- **THEN** `$store.importModal.open` = true
- **AND** o estado é resetado (step = 1, file = null, etc.)
- **WHEN** `$store.importModal.closeModal()` é chamado
- **THEN** `$store.importModal.open` = false
- **AND** o estado é resetado
