## MODIFIED Requirements

### Requirement: Revisão e commit de import (Step 2)

O modal SHALL exibir:
- Resumo de linhas auto-matched (data-testid="import-matched-summary")
- Tabela de linhas unmatched (data-testid="import-unmatched-table") com dropdowns de classe
- Botão "Confirmar importacao" (data-testid="import-confirm-btn")

O Step 2 SHALL aceitar tanto o payload de preview produzido pelo upload manual
quanto o payload `preview` retornado por um job MyProfit concluído com sucesso.
O cliente SHALL abrir a revisão somente para um job com status `succeeded` e
payload de preview válido. Um job `failed`, `expired`, `queued` ou `running`
SHALL permanecer como estado de página/job e SHALL NOT abrir o modal.

Ao confirmar, DEVE fazer POST /api/import/commit com os assignments e recarregar a página.
Sincronização MyProfit não substitui confirmação: ela nunca chama commit
automaticamente.

#### Scenario: Preview de sincronização bem-sucedida abre a mesma revisão

- **WHEN** o polling retorna status `succeeded` com `preview_id`, `auto_matched`, `unmatched`, e `asset_classes`
- **THEN** o cliente entrega esse payload ao `$store.importModal`
- **AND** o modal exibe Step 2 com revisão manual existente

#### Scenario: Falha de sincronização não abre modal

- **WHEN** o polling retorna status `failed` ou `expired`
- **THEN** a página exibe o erro/estado seguro do job
- **AND** `$store.importModal.open` permanece `false`
- **AND** nenhum POST `/api/import/commit` é feito

#### Scenario: Commit bem-sucedido recarrega dashboard

- **WHEN** usuário confirma import com assignments válidos
- **THEN** modal faz POST /api/import/commit
- **AND** em caso de sucesso, recarrega a página (window.location.reload())
- **AND** dashboard exibe os novos ativos com posições
