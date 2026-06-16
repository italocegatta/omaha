## Why

O dropdown de seleção de classe no modal de import (`src/omaha/templates/dashboard.html:510,554`) usa o padrão `<select :value="...">` com options renderizadas via `<template x-for>`. Esse padrão está quebrado: `<select value="X">` não é atributo HTML padrão (a seleção de `<select>` é determinada por `selected` em cada `<option>`), e Alpine não re-aplica o valor após as options renderizarem porque a expressão `getClassId(...)` não muda. Resultado: o usuário abre o modal, vê "Selecione..." em todas as linhas, clica Confirmar, e o commit envia `class_id === ''` para todas — o endpoint `/api/import/commit` pula essas linhas e nada é inserido. O backend já devolve `suggested_class_id` correto; o e2e (`test_s06`) mascara o bug setando o store via `page.evaluate()` em vez de ler o `<select>` do DOM.

## What Changes

- Trocar `<select :value="getClassId(...)" @change="setClassId(...)">` por `<select x-model="assignments[ticker].class_id">` em ambos os selects do modal (auto-matched, linha 510; unmatched, linha 554) — `x-model` é o padrão canônico do Alpine para `<select>` com options dinâmicas e re-aplica o valor automaticamente quando as options aparecem.
- Remover os helpers `getClassId`/`setClassId` (linhas 1133-1141) que ficam redundantes com `x-model`, ou mantê-los apenas se outras partes do código os usam.
- Adicionar e2e que valida o `select.value` real no DOM (não o store) após upload — garantir que o dropdown mostra a classe sugerida pelo servidor.

## Capabilities

### New Capabilities
- `import-modal-class-binding`: Garantir que o dropdown de classe no modal de import exiba o `suggested_class_id` retornado pelo servidor, tanto para linhas auto-matched (com `asset_class_id` da carteira existente) quanto para linhas unmatched (com `suggested_class_id` do match por categoria).

### Modified Capabilities
Nenhuma — os requisitos funcionais já existem (proposta `import-class-auto-suggest`). Esta change corrige a implementação que descumpre o spec.

## Impact

- `src/omaha/templates/dashboard.html`: 2 binds de `<select>` (linhas ~510 e ~554), remoção de 2 helpers no store Alpine (linhas ~1133-1141)
- `tests/e2e/test_s06_full_journey.py`: substituir o `page.evaluate` que seta `s.assignments[ticker].class_id` por uma asserção no `select.value` real
- Risco: baixo — `x-model` é a recomendação oficial do Alpine para `<select>`; o contrato JS (`assignments[ticker] = {class_id, asset_name}`) não muda
