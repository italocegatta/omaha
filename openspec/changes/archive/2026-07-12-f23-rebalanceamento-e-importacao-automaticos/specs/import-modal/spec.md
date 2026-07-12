## MODIFIED Requirements

### Requirement: Upload de CSV no modal (Step 1)

O modal SHALL permitir upload de arquivo CSV via input file e enviar automaticamente para `POST /api/import/preview` quando o usuário selecionar um arquivo. O preview retorna JSON com `preview_id`, `auto_matched`, `unmatched`, e `asset_classes`.

#### Scenario: Upload bem-sucedido avança para Step 2 sem botão manual

- **WHEN** usuário seleciona um arquivo CSV
- **THEN** o modal faz POST /api/import/preview com FormData sem precisar de clique em "Enviar"
- **AND** em caso de sucesso (200), avança para step 2 (review)
- **AND** exibe resumo de auto-matched + tabela de linhas unmatched
- **AND** exibe mensagem de erro (data-testid="import-upload-error") em caso de falha

#### Scenario: Seleção mais nova vence preview atrasado

- **WHEN** usuário seleciona outro arquivo antes de preview anterior responder
- **THEN** resposta anterior não altera estado do modal
- **AND** somente preview do arquivo selecionado por último pode avançar modal para step 2
