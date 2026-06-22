## Context

A change `modify-import-positions-modal` (anterior, ainda em
`openspec/changes/`, nunca arquivada) introduziu a feature de colorir o
campo "Classe" com a cor da `AssetClass` selecionada. A implementação
atual usa inline `:style` com `color-mix()` em vários elementos
(`<td>`, swatch, `<select>`). O e2e automatizado (Playwright/Chromium)
verifica `getComputedStyle` e prova que a cor é aplicada em condições
de teste.

**Achados do diagnóstico (revisado após feedback do usuário):**

O usuário reportou 4 rounds que a cor não aparece, mesmo após fixes
que passam no e2e. A proposta anterior desta change diagnosticou
incorretamente que o problema era o "estado transparent em linhas sem
classe" (BPAC11). O usuário corrigiu:

> "quando o ativo é importado ele já tem uma classe selecionada e eu
> tentei mudar a classe manualemnte, e em nenhum destes casos a cor
> foi alterada."

Ou seja: a cor não atualiza MESMO quando há classe selecionada. O
problema NÃO é o estado "sem classe" — é que o mecanismo de cor
(`inline :style` com `color-mix()`) não está funcionando no browser do
usuário.

**Causa raiz provável (revisada):**

1. **Cache stale do browser** (primário): a rota `GET /` (dashboard)
   não emite `Cache-Control` header. Browser pode servir HTML antigo
   (sem `:style` no `<select>`) em soft refresh. O usuário pode estar
   vendo uma versão pré-fix do template.

2. **`:style` directive não confiável no browser do usuário**
   (secundário, só confirmável com DevTools no browser dele): pode haver
   uma incompatibilidade específica do browser com `:style` em
   `<select>` que é child de `<template x-for>` que tem `x-data` no
   `<tr>` pai. `color-mix()` no inline style também pode ser
   interpretado de forma diferente em alguns browsers.

**Correção à proposta anterior (importante):**

- A proposta anterior adicionava "pre-seleção de `asset_classes[0].id`
  como fallback" para linhas unmatched sem `suggested_class_id`. **Isso
  foi removido.** Atribuir uma classe arbitrária a um ativo sem match
  é classificação errada — o usuário prefere estado "pendente"
  explícito.

- O sinal visual "pendente" (borda dashed + fundo neutro) é mantido,
  mas só para o caso raro de "perfil sem `asset_classes`".

## Goals / Non-Goals

**Goals:**

- Garantir que a cor apareça para QUALQUER classe selecionada (matched,
  suggested, ou escolhida manualmente), em qualquer browser.
- Eliminar cache stale do HTML do dashboard (forçar refresh sempre
  fresh).
- Usar mecanismo de cor mais portável (classe CSS modificadora em vez
  de inline `:style` no `<select>`/`<td>`), para defesa em profundidade
  caso o cache não seja o problema.
- Manter sinal visual "pendente" para o único caso em que a cor fica
  ausente: linha unmatched sem `suggested_class_id` E perfil sem
  `asset_classes`.

**Non-Goals:**

- Não adicionar pre-seleção de fallback (descartado pelo usuário).
- Não reescrever o parser CSV ou a lógica de match.
- Não mudar a paleta `_CLASS_COLORS` ou o modelo `AssetClass`.
- Não modificar o modal legacy `/import` e `/import/review`.

## Decisions

### 1. Mecanismo de cor via classe CSS modificadora (defesa primária)

- **Decisão:** substituir `inline :style="cellStyle()"` no `<td>` e no
  `<select>` por `x-bind:class` que aplica uma classe modificadora
  `.import-class-cell--cls-N` onde N é o índice da classe no array
  `assetClasses` (0-7, batendo com `_CLASS_COLORS`).
- **Rationale:** classes CSS são mais portáveis que inline `:style` em
  diferentes browsers. `x-bind:class` é diretiva mais simples que
  `:style` e tem menos edge cases. Cada classe modificadora tem uma
  regra CSS fixa que define `--class-color` e o background via
  `color-mix()`. O swatch mantém `inline :style="background: ..."` (já
  testado e funciona).
- **Alternativas consideradas:**
  - Manter inline `:style` + adicionar `Cache-Control`: rejeitado como
    única solução, porque se o browser do usuário tiver alguma
    incompatibilidade com `:style`, o problema persiste.
  - Usar `!important` no inline style: rejeitado, `!important` em
    inline style já é redundante (inline style sempre vence), e não
    resolve incompatibilidades de interpretação do browser.

### 2. Cache-Control no-store (defesa secundária)

- **Decisão:** adicionar middleware que injeta `Cache-Control:
  no-store` em respostas `text/html` de rotas autenticadas.
- **Rationale:** garante que o browser sempre pega a versão mais
  recente do template. Sem isso, mesmo fixes corretos podem ficar
  invisíveis para o usuário até ele fazer hard refresh (Ctrl+Shift+R).
- **Alternativas consideradas:**
  - Adicionar só na rota `/`: rejeitado, outros templates também podem
    ter mudanças durante dev.
  - Adicionar `ETag` baseado em mtime do template: mais complexo, mesmo
    benefício, mas requer revalidação explícita.

### 3. Sem pre-seleção de fallback (correção à proposta anterior)

- **Decisão:** manter o comportamento atual — `assignments[ticker].class_id`
  é inicializado com `asset_class_id` (matched) ou `suggested_class_id`
  (unmatched com match) ou `''` (unmatched sem match). Sem fallback
  para `assetClasses[0].id`.
- **Rationale:** o usuário foi explícito que atribuir uma classe
  arbitrária a um ativo sem match é classificação errada. O estado
  "pendente" (sem cor) é preferível a "classificação silenciosamente
  errada".
- **Alternativas consideradas:**
  - Pre-selecionar primeira classe: rejeitado pelo usuário.
  - Sugerir classe baseada em substring do nome do ativo: rejeitado,
    escopo maior, "smart matching" é mudança de produto.

### 4. Sinal visual "pendente" mantido apenas para perfil sem classes

- **Decisão:** quando `assignments[ticker].class_id === ''` E
  `assetClasses.length === 0`, aplicar `.import-class-cell--pending`
  (borda dashed + fundo neutro) na `<td>`. Para todos os outros casos
  (incluindo linha unmatched sem `suggested_class_id` mas COM classes
  no perfil), o campo fica com a cor da classe pré-selecionada via
  sugestão do backend.
- **Rationale:** estado "pendente" só ocorre em 1 cenário: perfil sem
  classes configuradas. Caso raro, sinaliza erro de configuração
  upstream.

## Risks / Trade-offs

- **Risco:** classe CSS modificadora `.import-class-cell--cls-N` requer
  8 regras CSS hardcoded (uma por índice de `_CLASS_COLORS`). Se a
  paleta mudar, é preciso atualizar o CSS. **Mitigação:** comentário
  explícito no CSS referenciando `_CLASS_COLORS` em `pages.py` para
  manter sincronizado.

- **Risco:** `Cache-Control: no-store` em todas as rotas HTML
  autenticadas aumenta tráfego (HTML de ~340KB a cada page load).
  **Mitigação:** aceitável para dev e produção interna. Se virar
  problema em escala, mudar para `no-cache` + `ETag` baseado em
  mtime.

- **Risco:** se o browser do usuário tem incompatibilidade com
  `color-mix()` (improvável em Chrome/Edge/Firefox/Safari ≥2023), o
  background pode não aparecer mesmo com classe CSS. **Mitigação:**
  fallback para cor sólida da paleta se `color-mix` não for
  suportado, via `@supports not (background: color-mix(in srgb, red,
  blue))`.

## Migration Plan

1. Adicionar middleware em `src/omaha/main.py` que injeta
   `Cache-Control: no-store` em respostas `text/html` autenticadas.
2. Em `src/omaha/templates/dashboard.html` (markup de ambas as
   tabelas):
   - Substituir `inline :style="cellStyle()"` no `<td>` por
     `:class="cellColor === 'transparent' ? 'import-class-cell import-class-cell--pending' : 'import-class-cell import-class-cell--cls-' + getClassIndex(cellColor)"`.
   - Manter `inline :style="background: ${cellColor}"` no swatch.
   - Adicionar método `getClassIndex(color)` no per-row `x-data` que
     retorna o índice em `assetClasses` da classe com aquela cor, ou
     -1 se não encontrada.
3. Em `src/omaha/static/app.css`, adicionar regras:
   ```css
   .import-class-cell--cls-0 { background: color-mix(in srgb, #0a66c2 38%, var(--surface)); border-left: 4px solid #0a66c2; }
   .import-class-cell--cls-1 { background: color-mix(in srgb, #2e7d32 38%, var(--surface)); border-left: 4px solid #2e7d32; }
   /* ... até --cls-7 */
   .import-class-cell--pending { border: 1px dashed var(--border-strong); background: var(--surface-sunk); border-left: 4px solid transparent; }
   ```
4. Atualizar e2e `test_s04_import_modal.py`:
   - Assersão: linhas com classe têm `class` attribute contendo
     `import-class-cell--cls-N` (N correto).
   - Assersão: `getComputedStyle(td).backgroundColor` reflete a cor
     esperada (via `color-mix`).
   - Assersão: `getComputedStyle(td).borderLeftColor` é a cor da
     classe.
5. Adicionar teste de header `Cache-Control: no-store` no response de
   `GET /` autenticado.
6. Rodar suíte: `pytest -m unit && pytest -m integration &&
   pytest tests/e2e/test_s04_import_modal.py`.
7. Manual smoke: hard refresh em `http://192.168.1.6:8000`, importar
   CSV misto, verificar que todas as linhas COM classe têm cor
   visível.

**Rollback:** reverter os 3 arquivos (`main.py`, `dashboard.html`,
`app.css`) e os testes. Sem migration, sem dado corrompido.

## Open Questions

- Confirmar com o usuário se o mecanismo via classe CSS é aceitável
  (vs. inline `:style` com `color-mix`). Sugestão: ir com classe CSS
  (mais portável, defesa em profundidade).
- Confirmar se `@supports not (color-mix)` fallback é necessário. Se o
  usuário confirmar que o browser é recente, pode-se omitir.
