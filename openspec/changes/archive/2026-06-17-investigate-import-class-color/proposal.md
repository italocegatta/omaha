## Why

Correção ao diagnóstico errado da versão anterior desta change. O usuário
reportou que **mesmo quando uma classe ESTÁ selecionada** (matched rows com
`asset_class_id`, ou unmatched rows com `suggested_class_id`, ou após o
usuário trocar manualmente a classe via `<select>`), **a cor do campo Classe
não muda**. A hipótese anterior de que "BPAC11 sem classe = estado válido
transparente" estava ERRADA.

**Evidência manual do usuário (reproduzida no DevTools):**
- O `<select>` do campo Classe não tem `:style` attribute no DOM após Alpine
  processar a página.
- O usuário inspecionou `tr:nth-child(2)` da tabela unmatched, que é BPAC11
  (categoria `(Não configurado)`, sem classe pré-selecionada). Mas o
  usuário também testou linhas matched (que TÊM classe) e linhas unmatched
  com `suggested_class_id` — em nenhum caso a cor apareceu.
- O usuário tentou trocar a classe manualmente via dropdown — a cor
  continuou não mudando.

**Causa raiz provável (corrigida):**

1. **Cache do browser sem headers `Cache-Control`** — a rota `GET /`
   (dashboard autenticado) não emite nenhum header de cache. O browser
   pode servir HTML antigo (sem `:style` no `<select>`) em soft refresh
   (F5). O usuário pode estar vendo a versão pré-fix do template, que não
   tinha `:style` no `<select>` (apenas no `<td>` e no swatch). Combinado:
   cache stale + interpretação do estado "transparent" como bug →
   usuário experimenta "cor não funciona".

2. **Alpine pode não estar processando `:style` no `<select>` em
   condições específicas do browser do usuário** (e.g., `:style` em
   `<select>` que é child de `<template x-for>` que tem `x-data` no
   `<tr>` pai). O e2e (Playwright/Chromium) não reproduz, mas o
   usuário está em browser real. Hipótese secundária — só pode ser
   confirmada com DevTools aberto no browser do usuário.

**O que NÃO fazer (correção à proposta anterior):**
- **NÃO adicionar pre-seleção de `asset_classes[0].id` como fallback**
  para linhas unmatched sem `suggested_class_id`. O usuário foi
  explícito: "somente nos casos onde não tem match é que o campo pode
  ficar sem cor, pq o ativo não tem classe atribuida". Atribuir uma
  classe arbitrária a um ativo sem match seria classificação errada —
  o usuário prefere "sem cor" a "cor errada".

**O que fazer:**

- **Garantir que a cor apareça para QUALQUER classe selecionada** (matched,
  suggested, ou escolhida manualmente). O mecanismo atual (inline `:style`
  com `color-mix`) está correto no papel e passa no e2e; o problema é o
  browser do usuário estar vendo HTML antigo.
- **Adicionar `Cache-Control: no-store` na rota `/`** para forçar o
  browser a sempre buscar a versão mais recente do template.
- **Manter o sinal visual "pendente"** (borda dashed + fundo neutro) para
  o único caso em que a cor realmente deve ficar ausente: linha unmatched
  sem `suggested_class_id` E perfil sem `asset_classes`. Esse caso é
  raro (perfil mal configurado) e o sinal comunica "ainda precisa
  escolher" sem confundir com bug.
- **Adicionar defesa em profundidade** caso o cache não seja o problema:
  usar classe CSS modificadora (`.import-class-cell--color-N` onde N é
  o índice da classe) em vez de inline `:style` no `<select>`. CSS
  classes via `x-bind:class` são mais portáveis que `:style` em alguns
  browsers.

## What Changes

- **`Cache-Control: no-store` em rotas HTML autenticadas** (primário).
  Garante que o browser sempre pega o template mais recente. Aplica-se a
  `GET /` e outras rotas que renderizam templates Jinja2. Não afeta
  `/static/*` (cache de 1 ano via nginx) nem `/api/*`.
- **Mecanismo de cor via CSS class + variável CSS** (defesa em
  profundidade). Substituir o inline `:style="cellStyle()"` no `<td>` e
  no `<select>` por `x-bind:class` que aplica uma classe modificadora
  `.import-class-cell--cls-N` (N = índice da classe no `assetClasses`).
  Cada classe tem uma regra CSS que define `--class-color` via
  `:nth-of-type` ou via classe explícita. Isso elimina a dependência de
  `color-mix()` no inline style e de reatividade do Alpine no `:style`.
- **Sinal visual pendente** (mantido): quando `cellColor === 'transparent'`,
  adicionar `import-class-cell--pending` com borda dashed + fundo neutro.
  Caso raro (perfil sem classes).
- **Sem pre-seleção de fallback** (removido da proposta anterior).
  Atribuir uma classe arbitrária a um ativo sem match é classificação
  errada. O usuário prefere estado "pendente" explícito a "classificação
  silenciosamente errada".

## Capabilities

### New Capabilities

- `import-class-color-via-css-class`: cor da classe aplicada via classe CSS
  modificadora (`.import-class-cell--cls-N`) em vez de inline `:style`.
  Mais portável entre browsers, elimina dependência de `color-mix()` no
  inline style.
- `import-modal-cache-control`: rotas HTML autenticadas retornam
  `Cache-Control: no-store` para evitar cache stale do template.

### Modified Capabilities

- `import-modal`: cor aplicada via classe CSS modificadora (não mais
  inline `:style` no `<select>`/`<td>`). Mantém o sinal visual pendente
  para o único caso em que a cor fica ausente.
- `import-class-placeholder-visual`: ajustado para refletir que pre-seleção
  de fallback foi removida (não é mais uma capability separada; o sinal
  pendente fica dentro de `import-modal`).

## Impact

- **Backend:** `src/omaha/main.py` — middleware que injeta
  `Cache-Control: no-store` em respostas `text/html` de rotas
  autenticadas.
- **Frontend:** `src/omaha/templates/dashboard.html` (markup de ambas
  as tabelas) — substituir inline `:style="cellStyle()"` por
  `x-bind:class` que aplica `.import-class-cell--cls-N`. Swatch mantém
  inline `style="background: ..."` (já é robusto, testado).
- **CSS:** `src/omaha/static/app.css` — adicionar regras para 8 classes
  modificadoras (uma por índice de `_CLASS_COLORS`) +
  `.import-class-cell--pending`.
- **Testes:** e2e `test_s04_import_modal.py` — asserções de
  `getComputedStyle` no `<select>` e no `<td>` (já existem, podem precisar
  de ajuste para verificar classe CSS em vez de inline style). Adicionar
  teste de `Cache-Control: no-store` no response header.
- **Sem migration**, sem mudança de schema.
- **Sem breaking change** para usuários.
- **Sem mudança de payload JSON** do backend.

## Evidence trail (para histórico do change)

| Round | Fix tentado | E2E | User report |
|-------|-------------|-----|-------------|
| 1 | Adicionou `color` no payload `asset_classes` (backend) + inline `style` no swatch + CSS var `--class-color` no `<td>` | Pass | "cor não aparece" |
| 2 | Inline `style="background: ${cellColor}"` no swatch + `style="border-left: 4px solid ${cellColor}"` no `<td>` | Pass | "nada mudou" |
| 3 | Inline `style="background: color-mix(...); border-color: ..."` no `<select>` (sobrepõe `background: #fff` do CSS) | Pass | "ainda sem cor — o select não tem `:style`" |
| 4 (proposta anterior, rejeitada) | Pre-seleção de `asset_classes[0].id` como fallback + classe `--pending` | N/A | "root cause errado — cor não muda MESMO com classe selecionada" |
| 5 (esta proposta) | Cache-Control no-store + classe CSS modificadora (defesa em profundidade) + sem pre-seleção | Pendente | Pendente |
