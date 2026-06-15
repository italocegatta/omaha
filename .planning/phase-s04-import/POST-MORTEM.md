# POST-MORTEM: S04 Import — Class Association Fix

## Resumo

Correção da associação automática de classes durante importação de CSV.
Três bugs encadeados impediam o funcionamento correto: (1) auto-matched com classe em branco,
(2) unmatched sem sugestão automática, (3) ativos sem classe sendo importados silenciosamente.

## Bugs Encontrados

### Bug 1: Alpine x-model com bracket notation (CAUSA RAIZ)

**Sintoma**: Selects de classe no modal de importação mostravam "Selecione..."
mesmo com `class_id` preenchido no store. Inputs de nome também não refletiam.

**Causa**: `x-model="$store.importModal.assignments[row.broker_ticker].class_id"`
contém bracket notation `[row.broker_ticker]` (chave dinâmica). Alpine.js falha
silenciosamente no SET direction ao converter expressão para path dot-separado.

**Fix**: Substituir `x-model` por `:value` + `@change`/`@input` com métodos
dedicados no store (`getClassId`, `setClassId`, `getAssetName`, `setAssetName`).
`:value` é one-way (store → DOM), `@change` é evento puro (DOM → store) —
nenhum depende do parser de caminho do Alpine.

**Arquivo**: `src/omaha/templates/dashboard.html`
- Store: adicionados 4 métodos auxiliares
- Template: 4 selects + 4 inputs trocados de `x-model` para `:value`+`@change`

### Bug 2: Default de classe para unmatched (COMPORTAMENTO)

**Sintoma**: Ativos sem categoria correspondente no CSV recebiam a primeira
classe disponível como default, sem conhecimento do usuário.

**Causa**: `uploadFile()` usava `defaultId = classes[0].id` como fallback
quando `suggested_class_id` era `null`.

**Fix**: Fallback vira `''` (vazio). Se o usuário não selecionar classe
manualmente, o ativo não é importado.

**Arquivo**: `src/omaha/templates/dashboard.html` — `uploadFile()`
```javascript
// Antes: class_id: suggested != null ? suggested : defaultId
// Depois: class_id: suggested != null ? suggested : ''
```

### Bug 3: Auto-matched sem visibilidade (UX)

**Sintoma**: Ativos já existentes mostravam apenas contador resumido,
sem tabela com classe editável.

**Causa**: Template renderizava `import-matched-summary` (texto + botão
"Ver detalhes") em vez de tabela completa.

**Fix**: Substituir por tabela "Ativos existentes na carteira" com select
de classe pré-preenchido e editável, mesma estrutura da tabela de novos ativos.

**Arquivo**: `src/omaha/templates/dashboard.html` — step 2 UI

### Bug 4: Auto-matched ignoravam assignment no commit (COMPORTAMENTO)

**Sintoma**: Mesmo se usuário alterasse classe de auto-matched no frontend,
o commit ignorava e usava classe original.

**Causa**: `commit_import()` processava `result.auto_matched` e
`result.unmatched` em loops separados, e auto-matched usava sempre o
`asset_id` original ignorando `assignment_map`.

**Fix**: Loop unificado sobre `raw` com 3 regras:
- Auto-matched sem assignment explícito → mantém classe original
- Auto-matched com assignment → usa classe do assignment
- Unmatched sem assignment ou class_id=None → skip

**Arquivo**: `src/omaha/routes/imports.py` — `commit_import()`

### Bug 5: Classe inválida gerava 422 (COMPORTAMENTO)

**Sintoma**: Se usuário selecionasse classe que não pertence ao profile,
o commit retornava erro HTTP 422.

**Causa**: `HTTPException(422)` no loop de unmatched.

**Fix**: Skip silencioso em vez de erro. Classe inválida → `continue`.

**Arquivo**: `src/omaha/routes/imports.py` — `commit_import()`

## Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `src/omaha/routes/imports.py` | `AssignmentItem.class_id` opcional; `_build_preview_response()` inclui `asset_class_id`; `commit_import()` loop unificado; skip classe inválida |
| `src/omaha/templates/dashboard.html` | Store: métodos `getClassId`/`setClassId`/`getAssetName`/`setAssetName`; template: `:value`+`@change`; duas tabelas (existentes + novos); `uploadFile()` sem default de classe |
| `tests/test_s04_t01_import_preview.py` | Verifica `asset_class_id` no shape |
| `tests/test_s04_t02_import_commit.py` | `test_commit_invalid_class_id_skips_row`; `test_commit_skips_rows_without_class_id` |
| `tests/test_s04_t03_import_get_preview.py` | Verifica `asset_class_id` no shape |
| `tests/e2e/test_s04_import_modal.py` | Selectors atualizados; preenche classes de todos os 5 unmatched |
| `tests/e2e/test_s04_user_journey.py` | Selectors atualizados; comentários |

## Fluxo Final

```
Upload CSV → Preview JSON (auto_matched + unmatched)
  ↓
Step 2: Duas tabelas
  ├─ "Ativos existentes na carteira" — classe pré-preenchida, editável
  └─ "Novos ativos" — classe vazia se sem sugestão, usuário define
  ↓
Usuário clica "Confirmar"
  ↓
Frontend filtra linhas sem classe
  ↓
Backend (loop unificado):
  ├─ Auto-matched sem assignment → classe original
  ├─ Auto-matched com assignment → classe do assignment
  └─ Unmatched com class_id → busca/cria asset, upsert position
  ↓
Linhas sem classe → skipadas
Preview deletado
Page reload
```

## Decisões de Design

1. **Auto-matched sem assignment mantém classe original** — compatibilidade
   com clientes antigos que enviam `assignments: []`
2. **Skip silencioso vs HTTP 422** — preferimos importação parcial (o que
   der pra importar) a bloquear todo o lote
3. **`:value`+`@change` em vez de `x-model`** — contorna limitação do Alpine
   com bracket notation, sem depender de versão específica
4. **`Object.assign({}, this.assignments)`** — força reatividade do Alpine
   para mutação de propriedade aninhada

## Riscos Residuais

- **Auto-matched com classe alterada**: posição antiga (no asset original)
  permanece, nova posição criada no asset da nova classe. Pode haver duplicata
  se o usuário não perceber. Aceito por design — o usuário explicitamente
  escolheu classe diferente.
- **CSV com suggested_category=None**: todas as linhas unmatched ficam sem
  classe default. Usuário precisa preencher manualmente.

## Testes

- 87 testes de import (unit + e2e + API) passando
- 229 total, 2 pre-existing flaky e2e (timeout de rede, não relacionados)
