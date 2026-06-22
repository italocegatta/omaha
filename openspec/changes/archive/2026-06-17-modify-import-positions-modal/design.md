## Context

A modal de import (`src/omaha/templates/dashboard.html` linhas 427-603) tem dois blocos `.import-review-section` que listam posições auto-matched (`data-testid="import-existing-table"`) e unmatched (`data-testid="import-unmatched-table"`). Hoje o backend (`src/omaha/routes/imports.py:361`) devolve `asset_classes` como `[{"id": ac.id, "name": ac.name}]` — sem `color`. A coluna "Classe" usa o mesmo padrão de `<select>` + `<template x-for>` documentado em `AGENTS.md` (gotcha do `x-init $nextTick` + `x-effect`). O CSS do modal vive em `src/omaha/static/app.css` linhas 1237-1409 e o painel está fixado em `max-width: 720px`. O dashboard já usa `style="background:{{ c.color }}"` no `.class-color-swatch` (linha 57 do template) para um sinal visual de classe.

## Goals / Non-Goals

**Goals:**

- Reduzir redundância visual (Ticker + Nome do ativo duplicam informação já no payload) e dar mais espaço para "Total atual".
- Passar a cor da classe no payload JSON do `/api/import/preview` para o frontend, espelhando o que o dashboard já tem (mesma paleta `_CLASS_COLORS`, índice por posição — `AssetClass` não tem coluna `color`).
- Aumentar `max-width` do modal para `960px` e ajustar o breakpoint mobile.
- Reforçar a separação visual entre as duas seções do Step 2.
- Corrigir quatro erros de ortografia sem mudar a semântica.

**Non-Goals:**

- Não alteramos o schema do banco (`AssetClass.color` já existe).
- Não trocamos o parser de CSV nem a lógica de match.
- Não reescrevemos o Alpine store — só adicionamos uma função utilitária `formatBRL(value)` e expomos `assetClassesById` derivado.
- Não mexemos nas rotas standalone `/import` e `/import/review` (legado) — só no modal do dashboard.
- Não adicionamos testes E2E novos além do mínimo necessário para a coluna de Total atual e cor no swatch; mantemos a suíte verde.

## Decisions

### 1. Cálculo do "Total atual" no frontend (não no backend)

- **Decisão**: calcular `qty * current_price` no Alpine (`x-text`) usando `Number(qty) * Number(current_price)`.
- **Rationale**: `current_price` já vem como string no payload; o backend já calcula valor de posição em outras tabelas (dashboard), mas aqui o cálculo é trivial e expor um campo novo no JSON (`current_total`) acoplaria a serialização ao formato de exibição. Manter no frontend evita round-trip e mantém o payload enxuto.
- **Alternativas consideradas**:
  - Backend retorna `current_total` pré-formatado → rejeitado: amarra o payload à moeda, dificulta i18n futuro, e força round-trip para qualquer correção de fórmula.
  - Usar uma lib tipo `Intl.NumberFormat` → escolhido: nativo do browser, sem dependência nova.

### 2. Cor da classe via swatch + borda (não `<select>` colorido)

- **Decisão**: colocar um `<span class="class-color-swatch">` à esquerda do `<select>` + borda esquerda colorida de 4px no contêiner da célula.
- **Rationale**: o `<select>` nativo não aceita `background-color` por option de forma cross-browser. Reaproveitar o componente `.class-color-swatch` (mesma classe do dashboard, `app.css:150-156`) garante consistência visual.
- **Alternativas consideradas**:
  - Substituir `<select>` por custom dropdown → rejeitado: muito código, perde acessibilidade nativa do `<select>` (teclado, screen reader).
  - Colorir só o `<select>` com `style="border-color: ..."` → escolhido como complemento (borda esquerda 4px do cell wrapper).

### 3. Backend adiciona `color` no payload de `asset_classes`

- **Decisão**: alterar `_build_preview_response` em `imports.py:361` para `[{"id": ac.id, "name": ac.name, "color": _CLASS_COLORS[index % len(_CLASS_COLORS)]}]`.
- **Rationale**: a cor é derivada no momento da resposta usando o mesmo índice que `portfolio_aggregates` (em `routes/pages.py`) usa para o dashboard. `AssetClass` não tem coluna `color`; a paleta vive em `pages._CLASS_COLORS` (8 hex codes). Sem mudança de modelo, sem migration. Reaproveita a fonte única da paleta para garantir que a cor vista na revisão bate byte a byte com a cor do dashboard.
- **Alternativas consideradas**:
  - Frontend busca as classes em um endpoint separado → rejeitado: adiciona round-trip e timing de loading.

### 4. Visual separation via border-left + tint de fundo

- **Decisão**: cada `.import-review-section` recebe uma variante `--existing` (verde/positivo) ou `--new` (azul/accent) com `border-left: 4px solid var(--positive|var(--accent))` e fundo `color-mix(in srgb, var(--positive) 5%, var(--surface))`.
- **Rationale**: usa tokens CSS existentes, não introduz cor nova, contraste WCAG AA mantida.
- **Alternativas consideradas**:
  - Cards totalmente coloridos → rejeitado: pesado demais para a UI atual (visual minimalista).
  - Apenas ícone distinto → rejeitado: o usuário pediu "separação visual" e isso pede mais do que ícone.

### 5. Largura do modal 960px

- **Decisão**: `.import-modal-panel { max-width: 960px; }` no desktop, `100%` no mobile (≤768px).
- **Rationale**: 960px é um valor comum para modais amplos (Bootstrap, Material) e cabe em laptops ≥1024px sem overflow. Mobile já tinha `100%` via media query existente.

### 6. Ortografia em strings hardcoded

- **Decisão**: substituir as 4 strings no template diretamente. Sem i18n (a app é pt-BR only).
- **Rationale**: simples, sem sistema de tradução. Manter coerência com o resto do app.

## Risks / Trade-offs

- **Risco**: mudança no payload JSON quebra clientes que validam schema estrito → **Mitigação**: o frontend é o único cliente; testes em `tests/test_s04_t01_import_preview.py` e `tests/e2e/test_s04_import_modal.py` já cobrem a estrutura; atualizar asserts conforme necessário.
- **Risco**: `Number(current_price)` pode dar `NaN` se vier `""` ou string inválida → **Mitigação**: garantir fallback para 0 (`Number(current_price) || 0`).
- **Risco**: `color-mix` não suportado em browsers antigos → **Mitigação**: app já usa `color-mix` em outros lugares (`app.css:1331, 1332`), baseline de browser já assume suporte.
- **Trade-off**: swatch + borda adiciona ~12px de largura na coluna "Classe" → aceito: o usuário pediu explicitamente a cor visível, e o ganho de largura do modal (720→960) compensa.

## Migration Plan

1. Editar `src/omaha/routes/imports.py:361` para incluir `color` no dict.
2. Atualizar markup do modal em `src/omaha/templates/dashboard.html` (Step 2).
3. Atualizar CSS em `src/omaha/static/app.css` (`.import-modal-panel`, swatch, variantes de seção).
4. Adicionar/atualizar testes: `tests/test_s04_t01_import_preview.py` (assert `color` em `asset_classes`); `tests/e2e/test_s04_import_modal.py` (assert nova coluna, swatch, ausência das colunas removidas).
5. Verificar lint (`task lint` se disponível) e suíte (`task test-unit && task test-integration`).
6. Manual smoke: subir dev server (`uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`), abrir dashboard em `http://192.168.1.7:8000`, clicar "Importar CSV", enviar CSV com posições mistas (algumas matched, outras novas).

Rollback: reverter os 3 arquivos (`imports.py`, `dashboard.html`, `app.css`). Sem migration de banco, sem dado corrompido.

## Open Questions

- Confirmar se a coluna "Nome do ativo" (input editável) deve ser **removida** ou apenas **escondida por padrão** com toggle. A spec atual assume remoção total — confirmar com o usuário antes de implementar.
- Confirmar tom de verde/azul para as variantes `--existing` / `--new` (proposta: `--positive` + `--accent` que já existem em `app.css`).
