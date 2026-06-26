# import-modal Specification (delta)

## Purpose

Modal de import CSV no dashboard com upload, preview (auto-matched +
unmatched), e commit. Substitui as páginas standalone /import e
/import/review.

## ADDED Requirements

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
