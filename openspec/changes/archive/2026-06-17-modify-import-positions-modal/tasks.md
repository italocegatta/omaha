## 1. Backend: incluir `color` em `asset_classes`

- [x] 1.1 Editar `src/omaha/routes/imports.py:361` — mudar para `[{"id": ac.id, "name": ac.name, "color": _CLASS_COLORS[i % len(_CLASS_COLORS)]} for i, ac in enumerate(class_rows)]` (importar `_CLASS_COLORS` de `omaha.routes.pages`; `AssetClass` não tem coluna `color`).
- [x] 1.2 Atualizar `tests/test_s04_t01_import_preview.py` — adicionar assert de que cada item de `asset_classes` contém `color` (string hex).

## 2. Frontend: markup do Step 2 do modal

- [x] 2.1 Em `src/omaha/templates/dashboard.html` linhas 489-531 (tabela `import-existing-table`):
  - remover `<th>Ticker</th>` e a célula `<td x-text="row.broker_ticker">`.
  - remover `<th>Nome do ativo</th>` e o bloco `<input data-testid="import-existing-name">`.
  - adicionar `<th>Total atual</th>` e célula `R$ <span x-text="formatBRL(Number(row.qty) * Number(row.current_price))"></span>`.
  - adicionar `<th>Classe</th>` (mantém, mas com swatch e borda colorida — ver 2.3).
  - renomear cabeçalho `<th>P. Medio</th>` → `<th>P. Médio</th>`.
- [x] 2.2 Repetir para linhas 534-575 (tabela `import-unmatched-table`): mesmas remoções + adições; ajustar `data-testid="import-assignment-name"` removido.
- [x] 2.3 Em ambas as tabelas, envolver o `<select>` de classe num container com swatch:
  ```html
  <td class="import-class-cell" :style="`--class-color: ${getClassColor($store.importModal.assignments[row.broker_ticker].class_id)}`">
    <span class="class-color-swatch import-class-swatch"></span>
    <select ...>...</select>
  </td>
  ```
  Adicionar `data-testid="import-class-cell-{existing|assignment}"` para teste.
- [x] 2.4 Corrigir ortografia: linha 478 `Sessao expirada` → `Sessão expirada`; linha 459 mantém; linha 1220 `Erro ao processar arquivo` → `Erro ao processar o arquivo`; linha 1265 `Erro ao confirmar importacao` → `Erro ao confirmar a importação`.

## 3. Alpine store: utilitários novos

- [x] 3.1 Em `src/omaha/templates/dashboard.html` (store `importModal`, ~linha 1120), adicionar:
  ```js
  formatBRL: function (v) {
    var n = Number(v) || 0;
    return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  getClassColor: function (classId) {
    if (!classId) return '';
    var c = this.assetClasses.find(function (a) { return String(a.id) === String(classId); });
    return c ? c.color : '';
  },
  ```
- [x] 3.2 Garantir que `assetClasses` continua sendo populado a partir de `data.asset_classes` (já está, linha 1189) — sem mudança de fluxo.

## 4. CSS: largura do modal, swatch, variantes de seção

- [x] 4.1 Em `src/omaha/static/app.css:1252` — mudar `.import-modal-panel { max-width: 720px; }` para `max-width: 960px;`.
- [x] 4.2 Em `.import-modal-panel` media query mobile (~linha 897) — manter `max-width: 100%` para `<768px` (já existe).
- [x] 4.3 Adicionar regras:
  ```css
  .import-class-cell {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border-left: 4px solid var(--class-color, transparent);
    padding-left: 0.5rem;
    transition: border-color 0.15s;
  }
  .import-class-swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    background: var(--class-color, var(--border));
    border: 1px solid var(--border);
    flex-shrink: 0;
  }
  .import-review-section--existing {
    border-left: 4px solid var(--positive);
    background: color-mix(in srgb, var(--positive) 5%, var(--surface));
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }
  .import-review-section--new {
    border-left: 4px solid var(--accent, #3b82f6);
    background: color-mix(in srgb, var(--accent, #3b82f6) 5%, var(--surface));
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }
  ```
  (Se `--accent` não existir, definir fallback no `:root` com `#3b82f6`.)
- [x] 4.4 Atualizar markup em `dashboard.html:489` e `:534` para incluir classe modificadora: `<div class="import-review-section import-review-section--existing">` e `<div class="import-review-section import-review-section--new">`.
- [x] 4.5 Adicionar cor de destaque nos `<h3>` de cada seção (`color: var(--positive)` / `color: var(--accent)`).

## 5. Testes

- [x] 5.1 `tests/test_s04_t01_import_preview.py` — adicionar asserção de `color` em cada item de `asset_classes` na resposta 200.
- [x] 5.2 `tests/test_s04_t03_import_get_preview.py` — mesma asserção para o GET re-fetch.
- [x] 5.3 `tests/e2e/test_s04_import_modal.py` — adicionar casos:
  - Tabela existente NÃO contém `<th>Ticker</th>` nem `<th>Nome do ativo</th>`.
  - Tabela existente contém `<th>Total atual</th>` e a célula mostra `R$ X.XXX,XX`.
  - Selecionar uma classe via `<select>` muda o `background-color` do swatch para o `color` correspondente.
- [x] 5.4 Rodar suíte: `task test-unit && task test-integration && task test-e2e` (ajustar conforme `Taskfile.yml`).

## 6. Verificação manual + lint

- [x] 6.1 `task lint` (ou `ruff check src tests`) — corrigir warnings.
- [ ] 6.2 Subir dev server: `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`.
- [ ] 6.3 Em `http://192.168.1.6:8000`, importar um CSV com ~5 linhas mistas (3 matched + 2 novas). Verificar:
  - Modal tem ~1100px de largura.
  - Tabelas mostram Preço médio e Total atual formatados em R$ sem casas decimais.
  - Swatch à esquerda do `<select>` muda de cor ao escolher classe (cor inline `style="background:..."`).
  - Seção "Ativos existentes" tem borda/fundo verde; "Novos ativos" tem borda/fundo azul.
  - Textos do modal acentuados (Sessão, Preço médio, posições, importação).
- [ ] 6.4 Capturar screenshot antes/depois (opcional, para review).
- [ ] 6.5 Commit: `git add -A && git commit -m "feat(import-modal): widen, drop ticker/asset-name cols, add total + class color"` (NÃO commitar sem aprovação do usuário).

## 7. Pós-feedback do usuário (round 2)

- [x] 7.1 Renomear `P. Médio` → `Preço médio` (cabeçalho em ambas as tabelas).
- [x] 7.2 Formatar `Preço médio` como moeda (`R$ X.XXX`) com 0 casas decimais.
- [x] 7.3 Arredondar `Total atual` para 0 casas decimais.
- [x] 7.4 Corrigir ortografia `Importar posicoes` → `Importar posições` (linha 436) e `posicoes` → `posições` (linha 446).
- [x] 7.5 Cor da classe aplicada via `style="background: <color>"` inline no swatch + `style="border-left: 4px solid <color>"` inline no `<td>` (substituiu abordagem CSS-var que falhava em alguns cenários).
- [x] 7.10 **Fundo do campo Classe** tingido com `color-mix(in srgb, ${cellColor} 38%, var(--surface))` via `cellStyle()` no `<td>` — verdadeiramente visual.
- [x] 7.11 **Fundo do `<select>`** tingido com `color-mix(in srgb, ${cellColor} 30%, white); border-color: ${cellColor}` via inline `:style` — sobrepõe o `background: #fff` de `app.css:1391`. Sem isso o `<select>` continua branco e o usuário não vê a cor (root cause identificado via DevTools pelo usuário).
- [x] 7.6 `getClassColor` agora retorna `'transparent'` em vez de string vazia (string vazia em inline `style` é silenciosamente inválida para `background`/`border-color`).
- [x] 7.7 Swatch maior (18×18 em vez de 14×14) e com `display: inline-block` para visibilidade.
- [x] 7.8 Largura do modal: 960px → 1100px.
- [x] 7.9 E2E test verifica `getComputedStyle(swatch).backgroundColor` retorna `rgb(46, 125, 50)` (cor Acoes) — não só o inline style string.
