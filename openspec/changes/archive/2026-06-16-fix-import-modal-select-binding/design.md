## Context

O modal de import (`src/omaha/templates/dashboard.html`, Alpine store `importModal` linhas 1118-1285) usa dois `<select>` para a classe de cada linha: um na seção "Ativos existentes" (linha 510) para auto-matched, outro na seção "Novos ativos" (linha 554) para unmatched. Ambos seguem o mesmo padrão:

```html
<select :value="$store.importModal.getClassId(row.broker_ticker)"
        @change="$store.importModal.setClassId(row.broker_ticker, $event.target.value)">
  <option value="">Selecione...</option>
  <template x-for="ac in $store.importModal.assetClasses" :key="ac.id">
    <option :value="ac.id" x-text="ac.name"></option>
  </template>
</select>
```

Esse padrão está quebrado. `<select :value="...">` em Alpine compila para `el.setAttribute('value', ...)` no bind, mas a propriedade `value` de um `<select>` HTML é determinada pelo atributo `selected` em cada `<option>` filho — não por um atributo `value` no próprio `<select>`. O setter `selectEl.value = 6` só funciona se a `<option value="6">` correspondente já existir no DOM.

Como as options são adicionadas de forma assíncrona via `<template x-for>` após o `<select>` ser renderizado, o `setAttribute('value', '6')` é executado antes da option existir, o browser ignora, e a option default `value=""` (Selecione...) fica selecionada. Alpine não re-aplica o bind depois porque a expressão `getClassId(...)` não muda — o store já tem o valor correto desde o upload, mas o DOM não reflete.

O usuário abre o modal, vê todas as linhas em "Selecione...", clica Confirmar, e o `commit()` filtra `class_id === ''` (linha 1245), enviando lista vazia para `/api/import/commit`. Resultado: nenhuma linha é inserida.

O backend funciona (verificado via API: `suggested_class_id` é retornado corretamente para PETR4/MXRF11/XPLG11). O bug é puramente na renderização do DOM. O e2e `test_s06_full_journey` mascara o problema setando o store via `page.evaluate()` em vez de ler o `select.value` real.

## Goals / Non-Goals

**Goals:**
- O `<select>` do modal exibe a classe pré-selecionada automaticamente ao abrir o step 2 (sem ação do usuário)
- O usuário ainda pode trocar a classe manualmente — o `x-model` mantém o two-way binding
- O `assignments[ticker].class_id` continua sendo a fonte de verdade do que é enviado no commit
- Adicionar e2e que valida o `select.value` real (não o store) para garantir que o bug não regrida

**Non-Goals:**
- Mudar o endpoint `/api/import/preview` (já retorna `suggested_class_id` correto)
- Mudar o endpoint `/api/import/commit` (já usa `class_id` do assignment corretamente)
- Alterar fixtures CSV
- Refatorar o store Alpine além do necessário

## Decisions

**Decisão 1: Trocar `:value`+`@change` por `x-model`**
- Razão: `x-model` é a recomendação canônica do Alpine para `<select>` (documentação oficial seção "Select inputs"). Alpine internamente escuta `change`, faz `el.value = boundValue` no init E sempre que as options mudam, e popula o store no `change` event.
- Alternativa: adicionar `x-effect` que re-aplica `select.value` quando `assetClasses` muda. Funciona mas é mais verboso e não idiomático.
- Alternativa 2: renderizar options inline em vez de via `x-for` para garantir que existam no DOM antes do `setAttribute`. Possível mas perde a reatividade de `assetClasses`.
- Escolha: `x-model` — é o caminho recomendado e o mínimo de mudança.

**Decisão 2: Manter o objeto `assignments[ticker] = {class_id, asset_name}` no store**
- Razão: `commit()` (linha 1234) já itera `self.assignments` e lê `class_id`/`asset_name`. Manter a shape evita mexer no `commit()`.
- `x-model="assignments[row.broker_ticker].class_id"` faz two-way binding direto com esse objeto.

**Decisão 3: Remover `getClassId`/`setClassId`**
- Razão: viram dead code. O getter/setter eram workarounds para o `:value`+`@change` pattern; com `x-model` não precisa mais.
- Verificar que nada mais no store ou nos templates chama esses métodos antes de remover.

**Decisão 4: E2e valida `select.value` real no DOM, não `Alpine.store`**
- Razão: o bug é justamente que store e DOM divergem. Ler o store mascara o problema.
- Adicionar asserção que lê `document.querySelector('[data-testid="import-assignment-class"]').value` e compara com o `suggested_class_id` esperado.
- Manter o `page.evaluate` que seta assignments para categorias sem match (BR Dividendos, Cripto, etc.) — esse é um caso legítimo de override via store, não uma máscara do bug.

## Risks / Trade-offs

- **[Baixo]** Mudança no template pode quebrar testes que dependem de markup exato. Mitigação: a única mudança é `:value`+`@change` → `x-model`, e os `data-testid` continuam os mesmos.
- **[Baixo]** `assignments[row.broker_ticker].class_id` no template exige que `assignments[ticker]` já exista antes do Alpine renderizar a linha. Como o template está dentro de `<template x-for>` que itera `unmatched`/`autoMatched`, e essas listas vêm do mesmo fetch que popula `assignments` (linhas 1192-1223), a ordem é garantida: store popula assignments ANTES de step=2 disparar a renderização.
- **[Médio]** Se o `x-model` falhar silenciosamente em alguma versão do Alpine, o mesmo bug volta. Mitigação: o e2e novo lê `select.value` direto do DOM, então qualquer regressão quebra o teste.
- **[Baixo]** Co-existência com o `setClassId` se for mantido: `setClassId` faz `parseInt(val, 10)`, `x-model` armazena string. O `commit()` envia `rawClassId` para o backend, e a string "6" funciona porque FastAPI/Pydantic faz coerce para int no `AssignmentItem.class_id: int`. Mas é mais limpo remover o `setClassId` para evitar confusão.

## Migration Plan

- Aplicar mudança em `src/omaha/templates/dashboard.html` (template + store Alpine)
- Atualizar `tests/e2e/test_s06_full_journey.py` para ler `select.value` do DOM e remover o `page.evaluate` que seta store para as linhas com match (manter para as que não têm match, que é um caso legítimo)
- Rodar e2e (precisa de browser — Playwright não tem binário no host, então a verificação fica para a próxima vez que rodar e2e em ambiente com browser)
- Nenhuma migração de banco ou mudança de schema

## Open Questions

- Nenhuma — a correção é direta.
