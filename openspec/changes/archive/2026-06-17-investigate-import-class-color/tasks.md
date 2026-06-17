## 1. Backend: Cache-Control no-store em rotas HTML autenticadas

- [x] 1.1 Em `src/omaha/main.py`, adicionar middleware que injeta `Cache-Control: no-store` em responses com `Content-Type: text/html` que venham de rotas autenticadas (excluir `/login`, `/static/*`, `/api/*`, `/healthz`).
- [x] 1.2 Verificar via curl: `GET /` autenticado retorna `Cache-Control: no-store`.
- [x] 1.3 Verificar via curl: `GET /static/app.css` retorna `Cache-Control: public, immutable` (não afetado).
- [x] 1.4 Verificar via curl: `GET /api/import/preview` (POST/GET) NÃO tem `Cache-Control: no-store`.

## 2. Frontend: classe CSS modificadora no lugar de inline :style

- [x] 2.1 Em `src/omaha/templates/dashboard.html` (markup de ambas as tabelas), substituir `inline :style="cellStyle()"` no `<td>` por `x-bind:class`:
  ```html
  <td class="import-class-cell" 
      :class="cellColor === 'transparent' 
        ? 'import-class-cell--pending' 
        : 'import-class-cell--cls-' + getClassIndex(cellColor)"
      ...>
  ```
- [x] 2.2 Adicionar método `getClassIndex(color)` no per-row `x-data` do `<tr>`:
  ```js
  getClassIndex(color) {
    if (!color || color === 'transparent') return -1;
    var self = this;
    var idx = -1;
    var list = Alpine.store('importModal').assetClasses;
    for (var i = 0; i < list.length; i++) {
      if (list[i].color === color) { idx = i; break; }
    }
    return idx;
  }
  ```
- [x] 2.3 Manter `inline :style="background: ${cellColor}"` no swatch (já testado, robusto).
- [x] 2.4 Remover `cellStyle()` do `x-data` (não é mais necessário — classe CSS substitui).

## 3. CSS: 8 classes modificadoras + pending

- [x] 3.1 Em `src/omaha/static/app.css`, adicionar 8 regras hardcoded (uma por índice de `_CLASS_COLORS`):
  ```css
  .import-class-cell--cls-0 { background: color-mix(in srgb, #0a66c2 38%, var(--surface)); border-left: 4px solid #0a66c2; }
  .import-class-cell--cls-1 { background: color-mix(in srgb, #2e7d32 38%, var(--surface)); border-left: 4px solid #2e7d32; }
  .import-class-cell--cls-2 { background: color-mix(in srgb, #c62828 38%, var(--surface)); border-left: 4px solid #c62828; }
  .import-class-cell--cls-3 { background: color-mix(in srgb, #ef6c00 38%, var(--surface)); border-left: 4px solid #ef6c00; }
  .import-class-cell--cls-4 { background: color-mix(in srgb, #6a1b9a 38%, var(--surface)); border-left: 4px solid #6a1b9a; }
  .import-class-cell--cls-5 { background: color-mix(in srgb, #00838f 38%, var(--surface)); border-left: 4px solid #00838f; }
  .import-class-cell--cls-6 { background: color-mix(in srgb, #5d4037 38%, var(--surface)); border-left: 4px solid #5d4037; }
  .import-class-cell--cls-7 { background: color-mix(in srgb, #455a64 38%, var(--surface)); border-left: 4px solid #455a64; }
  ```
  Adicionar comentário no CSS referenciando `_CLASS_COLORS` em `pages.py` para manter sincronizado.
- [x] 3.2 Adicionar regra `.import-class-cell--pending`:
  ```css
  .import-class-cell--pending {
    border: 1px dashed var(--border-strong);
    background: var(--surface-sunk);
    border-left: 4px solid transparent;
  }
  ```
- [ ] 3.3 (Opcional) Adicionar fallback `@supports not (background: color-mix(in srgb, red, blue))` que usa cor sólida da paleta.

## 4. Testes automatizados

- [x] 4.1 Em `tests/e2e/test_s04_import_modal.py`, ajustar asserções:
  - Verificar que `<td>` tem `class` attribute contendo `import-class-cell--cls-N` (N correto).
  - Verificar `getComputedStyle(td).backgroundColor` reflete `color-mix`.
  - Verificar `getComputedStyle(td).borderLeftColor` é a cor da classe.
- [x] 4.2 Em `tests/e2e/test_s04_import_modal.py`, novo caso `test_import_modal_pending_visual`:
  - Setup: perfil com 0 classes, importar CSV.
  - Assert: `<td>` tem `import-class-cell--pending`.
  - Assert: `getComputedStyle(td).borderStyle === 'dashed'`.
  - Assert: `getComputedStyle(td).backgroundColor === body bg` (fundo neutro).
- [x] 4.3 Adicionar teste em `tests/test_t03_pages_routes.py` (ou similar):
  - `GET /` autenticado retorna `Cache-Control: no-store`.
  - `GET /static/app.css` retorna `Cache-Control: public, immutable`.
- [x] 4.4 Rodar suíte: `pytest -m unit && pytest -m integration && pytest tests/e2e/test_s04_import_modal.py`.

## 5. Verificação manual + lint

- [x] 5.1 `uv run ruff check src tests` — sem novos warnings.
- [x] 5.2 Reiniciar dev server: `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000` (matar o antigo primeiro).
- [x] 5.3 Em `http://192.168.1.7:8000`, **janela anônima** (Ctrl+Shift+N) para descartar cache, hard refresh (Ctrl+Shift+R), importar CSV misto. Verificar:
  - Linhas matched (43): todas com cor visível, swatch com cor, border-left colorida.
  - Linhas unmatched com sugestão (MXRF11, XPLG11): com cor da classe correspondente.
  - Linhas unmatched sem sugestão (BPAC11, HGLG11, VINO11): com cor da PRIMEIRA classe (pre-selecionada pelo sistema via `suggested_class_id` ou — se não houver — devem ter a primeira classe pré-selecionada? NÃO, conforme correção: sem pre-seleção, ficam com a primeira classe sugerida pelo sistema, que é `null` para essas linhas, então ficam "pendentes" COM classe configurada → comportamento atual).
  - **Espera, ver clarificação:** o sistema JÁ pré-seleciona via `suggested_class_id`. Linhas unmatched SEM `suggested_class_id` ficam com `class_id = ''` → "pendentes" (borda dashed) APENAS se `assetClasses.length === 0`. Se há classes no perfil mas a linha não tem match, o estado é "transparente" (sem style, sem cor) — o usuário aceita isso.
- [x] 5.4 Inspecionar DevTools → Network → `GET /`:
  - Response Headers inclui `Cache-Control: no-store`.
- [x] 5.5 Soft refresh (F5) várias vezes: HTML sempre fresh.
- [ ] 5.6 Commit: `git add -A && git commit -m "fix(import-modal): css class for class color + no-store cache"` (NÃO commitar sem aprovação do usuário).
