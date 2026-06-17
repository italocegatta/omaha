## Purpose

Mecanismo de coloração do campo "Classe" no modal de import via classe CSS modificadora (em vez de inline `:style`) para portabilidade entre browsers.

## Requirements

### Requirement: Cor da classe aplicada via classe CSS modificadora (não inline :style)

Para cada linha das tabelas de revisão (`data-testid="import-existing-table"` e `data-testid="import-unmatched-table"`) que tem uma classe selecionada (matched com `asset_class_id`, OU unmatched com `suggested_class_id`, OU classe escolhida manualmente pelo usuário), o `<td class="import-class-cell">` MUST receber uma classe CSS modificadora `.import-class-cell--cls-N` onde N é o índice (0-7) da classe correspondente no array `assetClasses` retornado pelo backend. A cor é então aplicada via regra CSS fixa (não via `inline :style`), usando `color-mix()` para tingir o background e `border-left` na cor cheia.

O motivo de usar classe CSS em vez de `inline :style` é portabilidade entre browsers — `x-bind:class` é mais simples e tem menos edge cases que `:style`, especialmente em `<select>` que é child de `<template x-for>` que tem `x-data` no `<tr>` pai. O swatch à esquerda do `<select>` mantém `inline :style="background: <color>"` (já é robusto, testado).

Quando `assignments[ticker].class_id === ''` (perfil sem `asset_classes`), o `<td>` recebe a classe `.import-class-cell--pending` (borda dashed + fundo neutro) sinalizando estado pendente.

#### Scenario: Linha com classe recebe classe CSS modificadora correta

- **WHEN** a linha tem `assignments[ticker].class_id` igual ao id de uma classe
- **THEN** o `<td class="import-class-cell">` tem `class` attribute contendo `import-class-cell--cls-N` onde N é o índice dessa classe no array `assetClasses`
- **AND** o `getComputedStyle(td).backgroundColor` reflete `color-mix(in srgb, <color> 38%, var(--surface))`
- **AND** o `getComputedStyle(td).borderLeftColor` é a cor da classe
- **AND** o swatch mantém `style="background: <color>"` (inline, não muda)

#### Scenario: Classe CSS modificadora corresponde ao índice correto

- **WHEN** a classe selecionada é a segunda do array `assetClasses` (índice 1)
- **THEN** o `<td>` tem classe `import-class-cell--cls-1`
- **AND** o background computado é o resultado de `color-mix(in srgb, #2e7d32 38%, var(--surface))` (cor da paleta no índice 1)

#### Scenario: Linha sem classe (perfil vazio) recebe classe pending

- **WHEN** `assignments[ticker].class_id === ''` E `assetClasses.length === 0`
- **THEN** o `<td>` tem classe `import-class-cell--pending`
- **AND** o `getComputedStyle(td).borderStyle === 'dashed'`
- **AND** o `getComputedStyle(td).backgroundColor === getComputedStyle(body).backgroundColor` (fundo neutro)

#### Scenario: Trocar classe manualmente atualiza a classe CSS modificadora

- **WHEN** o usuário troca a classe via `<select>` (de classe índice 2 para classe índice 5)
- **THEN** o `<td>` tem classe `import-class-cell--cls-5` (não mais `import-class-cell--cls-2`)
- **AND** o background computado reflete a cor da nova classe (não da antiga)

### Requirement: HTML do dashboard não é cacheado pelo browser

A resposta da rota `GET /` (dashboard autenticado) MUST incluir `Cache-Control: no-store` no response header, garantindo que o browser sempre pegue a versão mais recente do template em qualquer tipo de refresh (F5, Ctrl+R, navegação). Aplica-se a todas as rotas autenticadas que renderizam templates HTML Jinja2. NÃO se aplica a `/static/*` (que tem cache de 1 ano via nginx, intencional) nem a `/api/*` (que tem semântica REST apropriada).

#### Scenario: Dashboard GET retorna Cache-Control no-store

- **WHEN** o usuário faz `GET /` autenticado
- **THEN** o response header contém `Cache-Control: no-store`

#### Scenario: Static files mantêm cache de 1 ano

- **WHEN** o usuário faz `GET /static/app.css`
- **THEN** o response header contém `Cache-Control: public, immutable` (inalterado)
- **AND** `Expires` header é ~1 ano no futuro
