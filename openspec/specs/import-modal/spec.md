## Purpose

Modal de import CSV no dashboard com upload, preview (auto-matched +
unmatched), e commit. Substitui as páginas standalone /import e
/import/review.

## Requirements

### Requirement: Botão "Importar CSV" no dashboard

O dashboard DEVE exibir (MUST) um botão "Importar CSV" dentro do
`<aside class="app-sidebar" data-testid="app-sidebar">` (a barra
lateral persistente introduzida pelo capability `dashboard-sidebar`).
O botão carrega `data-testid="dashboard-import-btn"` e abre o modal de
import via `@click="$store.importModal.openModal()"`. O antigo wrapper
`data-testid="dashboard-actions"` que continha o botão é removido do
markup.

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

### Requirement: Estado de seleção de classe por linha tem 2 modos visuais distintos

Para cada linha das tabelas de revisão (`data-testid="import-existing-table"` e `data-testid="import-unmatched-table"`), a coluna "Classe" MUST distinguir visualmente entre dois estados de seleção:

1. **Com classe selecionada (matched row com `asset_class_id`, OU unmatched com `suggested_class_id`, OU classe escolhida manualmente pelo usuário):** o `<select>` exibe a classe; o `<td class="import-class-cell">` tem classe CSS modificadora `.import-class-cell--cls-N` (N = índice da classe no `assetClasses`); o background e a border-left refletem a cor da classe via regra CSS fixa; o swatch à esquerda mostra a cor cheia.
2. **Pendente (perfil sem `asset_classes`):** o `<select>` exibe o placeholder "Selecione..."; o `<td>` tem classe CSS modificadora `.import-class-cell--pending` (borda dashed + fundo neutro) comunicando que o usuário precisa escolher — e que o backend não tem classes para sugerir.

A comunicação visual entre os 2 estados DEVE ser inequívoca: linhas com classe ficam coloridas; linhas pendentes ficam com borda dashed. Nunca há sobreposição (uma linha está em exatamente um estado por vez).

**Importante:** linhas unmatched sem `suggested_class_id` mas COM `asset_classes` no payload NÃO são consideradas "pendentes" — o sistema não inventa uma classe para elas (pre-seleção de fallback foi explicitamente rejeitada pelo usuário). O estado "pendente" é exclusivo para o caso "perfil sem classes configuradas".

#### Scenario: Linha matched com asset_class_id é colorida

- **WHEN** a linha está em `auto_matched[]` e tem `asset_class_id` não-nulo
- **THEN** o `<select>` exibe o nome da classe
- **AND** o `<td>` tem classe CSS `import-class-cell--cls-N` (N correto)
- **AND** o background computado é `color-mix(in srgb, <color> 38%, var(--surface))`
- **AND** o swatch tem `style="background: <color>"`

#### Scenario: Linha unmatched com categoria casada é colorida pela sugestão

- **WHEN** a linha está em `unmatched[]` com `suggested_class_id` não-nulo
- **THEN** o `<td>` tem classe CSS `import-class-cell--cls-N` (N da classe sugerida)
- **AND** o background computado reflete a cor da classe sugerida

#### Scenario: Linha unmatched sem categoria casada E sem asset_classes no payload é pendente

- **WHEN** a linha está em `unmatched[]` com `suggested_class_id === null`
- **AND** o payload tem `asset_classes[].length === 0`
- **THEN** `assignments[ticker].class_id` permanece `''`
- **AND** o `<td>` tem classe `import-class-cell--pending`
- **AND** o swatch tem `style="background: transparent"`
- **AND** o `<select>` exibe o placeholder "Selecione..."

#### Scenario: Trocar classe manualmente atualiza a cor visualmente

- **WHEN** o usuário troca a classe via `<select>` (de classe A para classe B)
- **THEN** o `<td>` muda de `import-class-cell--cls-A` para `import-class-cell--cls-B`
- **AND** o background computado muda de `color-mix(...cor A...)` para `color-mix(...cor B...)`
- **AND** o swatch muda de `style="background: <cor A>"` para `style="background: <cor B>"`

### Requirement: Separação visual entre ativos existentes e novos

As duas seções do Step 2 do modal (`data-testid="import-existing-table"` e `data-testid="import-unmatched-table"`) MUST ser visualmente distintas. Cada seção DEVE ter:
1. Um título (`h3`) com cor de destaque: verde para "Ativos existentes na carteira" e azul para "Novos ativos" (ou outro par de cores consistente com `--positive` / `--accent`).
2. Uma borda lateral espessa (3-4px) colorida na lateral esquerda do bloco `.import-review-section`.
3. Fundo levemente tingido (color-mix da cor de destaque com `var(--surface)`) para reforçar o agrupamento.

#### Scenario: Seção "Ativos existentes" tem destaque verde

- **WHEN** o Step 2 renderiza `autoMatched.length > 0`
- **THEN** a seção "Ativos existentes na carteira" exibe o título com cor de destaque positivo e borda lateral verde

#### Scenario: Seção "Novos ativos" tem destaque azul

- **WHEN** o Step 2 renderiza `unmatched.length > 0`
- **THEN** a seção "Novos ativos" exibe o título com cor de destaque azul e borda lateral azul

#### Scenario: Apenas uma seção presente mantém o destaque

- **WHEN** o CSV só tem linhas auto-matched (zero unmatched)
- **THEN** a seção "Novos ativos" NÃO é renderizada (`x-show="false"`)
- **AND** a seção "Ativos existentes na carteira" mantém o destaque visual

### Requirement: Largura do modal 1100px no desktop

O modal de import MUST ter largura máxima de pelo menos 1100px no breakpoint desktop (acima de 768px) para acomodar nomes de classe longos (ex: "Renda Fixa Pós-Fixada") E as novas colunas de preço/total. No mobile (≤768px), o painel DEVE ocupar 100% da largura.

#### Scenario: Modal no desktop exibe 1100px

- **WHEN** o usuário abre o modal em viewport ≥768px
- **THEN** o painel (`.import-modal-panel`) tem `max-width: 1100px`
- **AND** a coluna "Classe" exibe o nome completo sem truncamento

#### Scenario: Modal no mobile ocupa a tela inteira

- **WHEN** o usuário abre o modal em viewport <768px
- **THEN** o painel ocupa 100% da largura (classe `.import-modal-panel` com `max-width: 100%`)

### Requirement: Coluna "Preço médio" e "Total atual" formatadas como moeda sem casas decimais

A coluna "Preço médio" das tabelas de revisão (`data-testid="import-existing-table"` e `data-testid="import-unmatched-table"`) MUST ser rotulada "Preço médio" (não "P. Médio") e MUST exibir `row.avg_price` formatado como moeda brasileira (`R$ 1.234`) com 0 casas decimais. A coluna "Total atual" MUST exibir `qty * current_price` formatado como moeda brasileira com 0 casas decimais (`R$ 3.250`, não `R$ 3.250,00`). A formatação é feita no frontend via função `formatBRL(v, decimals)` do Alpine store `importModal`.

#### Scenario: Cabeçalho da coluna de preço médio usa o nome completo

- **WHEN** o Step 2 renderiza qualquer uma das duas tabelas
- **THEN** o `<th>` da coluna de preço exibe `Preço médio` (não `P. Médio`)

#### Scenario: Preço médio formatado como moeda sem casas decimais

- **WHEN** uma linha tem `avg_price = "32.50"`
- **THEN** a célula exibe `R$ 33` (0 casas decimais, arredondamento HALF_UP)

#### Scenario: Total atual sem casas decimais

- **WHEN** uma linha tem `qty = 100` e `current_price = "32.50"`
- **THEN** a célula exibe `R$ 3.250` (sem vírgula decimal)

### Requirement: Colunas "Ticker" e "Nome do ativo" removidas das tabelas

As tabelas do Step 2 (`data-testid="import-existing-table"` e `data-testid="import-unmatched-table"`) MUST NOT renderizar as colunas `Ticker` e `Nome do ativo`. O `broker_ticker` continua sendo usado como chave do `<template x-for>` e como chave do objeto `assignments` no Alpine store — só a coluna visual é removida. O nome editável do ativo continua persistido no payload de commit via `assignments[ticker].asset_name`.

#### Scenario: Tabela não contém coluna Ticker

- **WHEN** o Step 2 renderiza qualquer uma das duas tabelas
- **THEN** o `<thead>` NÃO contém `<th>Ticker</th>`
- **AND** o `<tbody>` NÃO contém `<td x-text="row.broker_ticker">`

#### Scenario: Tabela não contém coluna Nome do ativo

- **WHEN** o Step 2 renderiza qualquer uma das duas tabelas
- **THEN** o `<thead>` NÃO contém `<th>Nome do ativo</th>`
- **AND** o `<tbody>` NÃO contém `<input data-testid="import-existing-name">` nem `data-testid="import-assignment-name"`

#### Scenario: Loop continua usando broker_ticker como chave

- **WHEN** o Alpine renderiza `<template x-for="(row, i) in $store.importModal.autoMatched" :key="row.broker_ticker">`
- **THEN** o `:key` continua sendo `row.broker_ticker` mesmo com a coluna Ticker removida do DOM

### Requirement: Ortografia corrigida nos textos do modal

Os textos visíveis do modal de import MUST estar corretamente acentuados. As correções MUST incluir:
- `Importar posicoes` → `Importar posições` (header do modal)
- `posicoes` → `posições` (texto de ajuda do Step 1)
- `Sessao expirada` → `Sessão expirada. Reenvie o arquivo.`
- `P. Medio` → `Preço médio` (ver requisito de preço médio acima)
- `Erro ao processar arquivo` → `Erro ao processar o arquivo`
- `Erro ao confirmar importacao` → `Erro ao confirmar a importação`

#### Scenario: Mensagem de sessão expirada acentuada

- **WHEN** `previewError = true`
- **THEN** o parágrafo dentro de `data-testid="import-expired-message"` exibe "Sessão expirada. Reenvie o arquivo."

#### Scenario: Cabeçalho da coluna de preço médio acentuado

- **WHEN** o Step 2 renderiza qualquer uma das duas tabelas
- **THEN** o `<th>` da coluna de preço médio exibe `Preço médio` (com acento em "é" e nome completo)

#### Scenario: Mensagens de erro acentuadas

- **WHEN** o upload falha
- **THEN** a mensagem em `data-testid="import-upload-error"` é "Erro ao processar o arquivo"
- **WHEN** o commit falha
- **THEN** a mensagem em `data-testid="import-commit-error"` é "Erro ao confirmar a importação"

### Requirement: Preview de import inclui trade-control por linha

O `POST /api/import/preview` DEVE retornar, em cada item de
`auto_matched` (asset pré-existente) e `unmatched` (asset a ser
criado), os três campos de trade-control:
`buy_enabled`, `sell_enabled`, `currency_code`.

Para linhas auto-matched, o valor DEVE ser o estado atual do
`Asset` no banco (buy_enabled/sell_enabled/currency_code
existentes). Para linhas unmatched, o valor DEVE ser o default
do projeto: `buy_enabled=true, sell_enabled=true,
currency_code="BRL"`.

Esses campos são editáveis no modal de review antes do commit.

#### Scenario: Preview auto-matched preserva toggle atual

- **WHEN** usuário faz upload de CSV que referencia um asset que
  ele previamente toggleou para `sell_enabled=false`
- **THEN** o preview mostra `sell_enabled=false` para essa linha
- **AND** o usuário pode re-habilitar antes do commit

#### Scenario: Preview unmatched sugere defaults

- **WHEN** usuário faz upload de CSV que introduz um asset novo
  (não existente no banco)
- **THEN** o preview mostra
  `buy_enabled=true, sell_enabled=true, currency_code="BRL"`
  como valores iniciais editáveis

### Requirement: Modal de review renderiza controles de trade-control

O modal de review DEVE renderizar, por linha das tabelas
`data-testid="import-existing-table"` e
`data-testid="import-unmatched-table"`, três controles:

- Toggle "Compra" (vinculado a `buy_enabled`).
- Toggle "Venda" (vinculado a `sell_enabled`).
- Select "Moeda" (vinculado a `currency_code`, opções
  `BRL` / `USD`).

Os valores iniciais vêm do preview (estado atual do asset ou
defaults). Mudanças nos controles atualizam o
`$store.importModal.assignments` mas NÃO disam PATCH
antecipado — apenas o commit final persiste.

#### Scenario: Toggle "Compra" atualiza assignment

- **WHEN** usuário desmarca o toggle "Compra" de uma linha
  auto-matched
- **THEN** `$store.importModal.assignments[broker_ticker].buy_enabled = false`
- **AND** nenhum request HTTP é feito até o commit

#### Scenario: Select "Moeda" respeita binding gotcha

- **WHEN** o select de moeda é renderizado dentro do modal
- **THEN** usa o padrão `x-init $nextTick` + `x-effect` (regra
  AGENTS.md "Alpine binding gotcha") para resolver o valor
  inicial após o `<template x-for>` popular as `<option>`

### Requirement: Commit de import persiste trade-control

O `POST /api/import/commit` DEVE aceitar `buy_enabled`,
`sell_enabled`, e `currency_code` por linha no body e persistir:

- Auto-matched: atualiza os 3 campos do `Asset` existente.
- Unmatched: cria o novo `Asset` com os 3 campos fornecidos.
- `currency_code` fora de `{"BRL", "USD"}` → 422 com mensagem
  clara.

#### Scenario: Commit atualiza flags de asset existente

- **WHEN** usuário confirma import com `buy_enabled=false` para
  um asset auto-matched
- **THEN** o `Asset.buy_enabled` é atualizado para `false` no
  banco

#### Scenario: Commit cria asset novo com currency customizada

- **WHEN** usuário confirma import com um asset unmatched e
  selecionou `currency_code="USD"` no preview
- **THEN** o novo `Asset` é criado com `currency_code="USD"`
  e os buy/sell flags conforme selecionados

#### Scenario: Commit rejeita currency inválida

- **WHEN** usuário submete commit com `currency_code="EUR"`
- **THEN** response é 422 e nenhum asset é criado ou atualizado
