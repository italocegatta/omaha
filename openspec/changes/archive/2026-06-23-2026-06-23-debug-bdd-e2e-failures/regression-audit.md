# Regression audit — testids `.feature` ↔ `dashboard.html`

**Date:** 2026-06-23
**Scope:** todos os testids referenciados por `tests/bdd/features/*.feature`
(ou por `_PT_LABEL_TO_TESTID_SLUG` em `tests/bdd/step_defs/common_steps.py:89-96`)
mapeados para o testid correspondente em `src/omaha/templates/*.html`.

## Metodologia

1. Extraí testids de `tests/bdd/features/*.feature` via selector
   textual (`button:has-text("X")`, `input[name="X"]`,
   `label:has-text("X")`).
2. Extraí testids de `src/omaha/templates/*.html` via
   `rg 'data-testid="[^"]+"'`.
3. Cruzei cada testid referenciado contra o set existente.

## Tabela de testids referenciados

| Origem (feature / slug)                | Testid esperado                    | Existe em template?       | Linha template    | Status |
|----------------------------------------|------------------------------------|---------------------------|-------------------|--------|
| slug: "Nome da classe"                 | `new-class-name-input`             | ✓ `dashboard.html`        | :367             | OK     |
| slug: "Alocação alvo"                  | `new-class-pct-input`              | ✓ `dashboard.html`        | :378             | OK (mas label no HTML é "Alvo %", não "Alocação alvo" — alias no slug funciona) |
| slug: "Nome do ativo"                  | `dashboard-add-asset-name`         | ✓ `dashboard.html`        | (modal)          | OK     |
| slug: "Alocação alvo do modal de ativo"| `dashboard-add-asset-target-pct`   | ✓ `dashboard.html`        | (modal)          | OK     |
| text: `+ Nova classe`                  | `new-class-plus-btn`               | ✓ `dashboard.html`        | :351             | **AMBIGUOUS** — também `empty-state-create-class` em :336 |
| text: `+ Nova classe`                  | `empty-state-create-class`         | ✓ `dashboard.html`        | :336             | **AMBIGUOUS** — vide acima |
| text: `Salvar` (inline class)          | `new-class-form-save`              | ✓ `dashboard.html`        | :390             | OK     |
| text: `Adicionar classe` (editor)      | `class-editor-add`                 | ✓ `classes.html`          | :68              | OK     |
| text: `Salvar classes`                 | `class-editor-save`                | ✓ `classes.html`          | :72              | OK     |
| `class-editor` direct                  | `class-editor-name`                | ✓ `classes.html`          | :33              | OK     |
| `class-editor` direct                  | `class-editor-pct`                 | ✓ `classes.html`          | :44              | OK     |
| `class-editor` direct                  | `class-editor-remove`              | ✓ `classes.html`          | :50              | OK     |
| `class-editor` direct                  | `class-editor-total`               | ✓ `classes.html`          | :60              | OK     |
| R12 inline edit input                  | `class-inline-edit-input`          | ✓ `dashboard.html`        | :103             | OK     |
| R12 inline edit error                  | `class-inline-edit-error`          | ✓ `dashboard.html`        | :111             | OK     |
| R12 view span                          | `class-target-pct-view`            | ✓ `dashboard.html`        | :95, :180        | OK (duplicado em asset-group-header; clickable só em :95) |
| R12 edit container                     | `class-target-pct-edit`            | ✓ `dashboard.html`        | :96              | OK     |
| asset row direct                       | `dashboard-asset-row`              | ✓ `dashboard.html`        | :192             | OK     |
| asset row name                         | `asset-row-name`                   | ✓ `dashboard.html`        | :193             | OK     |
| asset row class                        | `asset-row-class`                  | ✓ `dashboard.html`        | :202             | OK     |
| asset table sortable headers           | `asset-table-th-{name,class,qty,current-value,target-pct-class,current-pct-class,target-pct-total,current-pct-total}` | ✓ `dashboard.html` | :165-172 | OK |
| asset current value                    | `asset-current-value`              | ✓ `dashboard.html`        | :204             | OK     |
| asset current pct class                | `asset-current-pct-class`          | ✓ `dashboard.html`        | :233             | OK     |
| asset target pct class                 | `asset-target-pct-class`           | ✓ `dashboard.html`        | :205             | OK     |
| asset target pct class editing         | `asset-target-pct-class-editing`   | ✓ `dashboard.html`        | :214             | OK     |
| asset target pct total                 | `asset-target-pct-total`           | ✓ `dashboard.html`        | :237             | OK     |
| asset target pct total editing         | `asset-target-pct-total-editing`   | ✓ `dashboard.html`        | :246             | OK     |
| asset target pct total edit input      | `asset-target-pct-total-edit-input`| ✓ `dashboard.html`        | :254             | OK     |
| asset inline edit input (generic)      | `asset-inline-edit-input`          | ✓ `dashboard.html`        | :222             | OK     |
| asset delete                           | `dashboard-asset-delete-btn`       | ✓ `dashboard.html`        | :197             | OK     |
| asset delete confirm                   | `dashboard-asset-delete-confirm`   | ✓ `dashboard.html`        | :287             | OK     |
| import form                            | `import-form`                      | ✓ `import.html`           | :17              | OK     |
| import file input                      | `import-file`                      | ✓ `import.html`           | :25              | OK     |
| import submit                          | `import-submit`                    | ✓ `import.html`           | :28              | OK     |
| import error                           | `import-error`                     | ✓ `import.html`           | :9               | OK     |
| import review form                     | `import-review-form`               | ✓ `import_review.html`    | :21              | OK     |
| import review auto row                 | `import-review-auto-row`           | ✓ `import_review.html`    | :27              | OK     |
| import review unmatched row            | `import-review-unmatched-row`      | ✓ `import_review.html`    | :56              | OK     |
| import review confirm                  | `import-review-confirm`            | ✓ `import_review.html`    | :100             | OK     |
| import review class select             | `import-review-class-select`       | ✓ `import_review.html`    | :67              | OK     |
| import review name input               | `import-review-name-input`         | ✓ `import_review.html`    | :82              | OK     |
| import review expired                  | `import-review-expired`            | ✓ `import_review.html`    | :9               | OK     |
| import review auto/unmatched count     | `import-review-auto-count` / `import-review-unmatched-count` | ✓ `import_review.html` | :17-18 | OK |
| import review file category            | `import-review-file-category`      | ✓ `import_review.html`    | :62              | OK     |
| import review reupload                 | `import-review-reupload`           | ✓ `import_review.html`    | :11              | OK     |
| login error                            | `login-error`                      | ✓ `login.html`            | :7               | OK     |
| empty state                            | `empty-state`                      | ✓ `dashboard.html`        | :331             | OK     |
| empty state CTA                        | `empty-state-create-class`         | ✓ `dashboard.html`        | :336             | **AMBIGUOUS** (vide acima) |
| empty assets                           | `empty-assets`                     | ✓ `dashboard.html`        | :319             | OK     |
| portfolio header                       | `portfolio-header`                 | ✓ `dashboard.html`        | :19              | OK     |
| portfolio invested                     | `portfolio-invested`               | ✓ `dashboard.html`        | :20              | OK     |
| portfolio total                        | `portfolio-total`                  | ✓ `dashboard.html`        | :24              | OK     |
| portfolio gain                         | `portfolio-gain`                   | ✓ `dashboard.html`        | :29              | OK     |
| class summary                          | `class-summary`                    | ✓ `dashboard.html`        | :17              | OK     |
| class summary row                      | `class-summary-row`                | ✓ `dashboard.html`        | :84              | OK     |
| class section name                     | `class-section-name`               | ✓ `dashboard.html`        | :87, :179        | OK (duplicado em asset-group-header) |
| class color swatch                     | `class-color-swatch`               | ✓ `dashboard.html`        | :86, :178        | OK (duplicado) |
| class current pct                      | `class-current-pct`                | ✓ `dashboard.html`        | :116, :181       | OK (duplicado) |
| class delete                           | `class-delete-btn`                 | ✓ `dashboard.html`        | :90              | OK     |
| class delete confirm                   | `class-delete-confirm`             | ✓ `dashboard.html`        | :121             | OK     |
| class delete confirm yes/no/error      | `class-delete-confirm-{yes,no,error}` | ✓ `dashboard.html`    | :128/:136/:141   | OK     |
| class compare bar                      | `class-compare-bar`                | ✓ `dashboard.html`        | :147             | OK     |
| class delta badge                      | `class-delta-badge`                | ✓ `dashboard.html`        | :117             | OK     |
| dashboard actions                      | `dashboard-actions`                | ✓ `dashboard.html`        | :6               | OK     |
| dashboard import btn                   | `dashboard-import-btn`             | ✓ `dashboard.html`        | :9               | OK     |
| dashboard distribution                 | `dashboard-distribution`           | ✓ `dashboard.html`        | :37              | OK     |
| dashboard class section                | `dashboard-class-section`          | ✓ `dashboard.html`        | :85              | OK     |
| dashboard add asset open               | `dashboard-add-asset-open`         | ✓ `dashboard.html`        | :46              | OK     |
| dashboard add asset modal              | `dashboard-add-asset-modal`        | ✓ `dashboard.html`        | (modal)          | OK     |
| dashboard add asset submit             | `dashboard-add-asset-submit`       | ✓ `dashboard.html`        | (modal)          | OK     |
| dashboard add asset cancel             | `dashboard-add-asset-cancel`       | ✓ `dashboard.html`        | (modal)          | OK     |
| dashboard add asset error              | `dashboard-add-asset-error`        | ✓ `dashboard.html`        | (modal)          | OK     |
| dashboard add asset modal class select | `dashboard-add-asset-modal-class`  | ✓ `dashboard.html`        | (modal)          | OK     |
| allocation alert                       | `asset-allocation-alert`           | ✓ `dashboard.html`        | :59              | OK     |
| allocation alert portfolio             | `asset-allocation-alert-portfolio` | ✓ `dashboard.html`        | :61              | OK     |
| allocation alert class                 | `asset-allocation-alert-class`     | ✓ `dashboard.html`        | :69              | OK     |
| profile name                           | `profile-name`                     | ✓ `dashboard.html`        | :4               | OK     |
| main nav                               | `main-nav`                         | ✓ `base.html`             | :24              | OK     |
| nav dashboard                          | `nav-dashboard`                    | ✓ `base.html`             | :25              | OK     |

## Resumo

- **Total referenciado:** ~70 testids.
- **Faltando:** 0.
- **Renomeados sem update de .feature:** 0.
- **AMBIGUOUS (2 botões com mesmo texto):** `+ Nova classe` casa
  tanto `empty-state-create-class` (linha 336) quanto
  `new-class-plus-btn` (linha 351). `loc.first.click()` no BDD step
  pega o empty-state, que tem handler broken (vide
  `diagnosis.md` §Sintoma 1).

## Outras observações

1. **Label mismatch "Alocação alvo" vs "Alvo %":** o slug
   `_PT_LABEL_TO_TESTID_SLUG["Alocação alvo"]` funciona, mas a label
   visível no HTML é "Alvo %" (`dashboard.html:374`). Debt: se alguém
   remover a entrada do slug, o teste quebra sem warning. Sugestão:
   adicionar `x-test-label="Alocação alvo"` no input ou trocar a
   label visível para alinhar.

2. **Duplicação de testids em `class-target-pct-view`,
   `class-section-name`, `class-color-swatch`, `class-current-pct`**
   entre `class-section-header` (linhas 86-117) e `asset-group-header`
   (linhas 178-181). O step `click_class_field` em
   `common_steps.py:153-167` lida com a ambiguidade pegando `.first`
   do escopo da seção, mas fragil — se a ordem do DOM mudar, quebra.
   Sugestão: dar testids únicos (ex.: `asset-group-target-pct-view`).

3. **`asset-pct` com `hidden` attribute** (linha 234) existe no DOM
   mas está `hidden`. Não referenciado por nenhum step (verifiquei),
   então é dead code ou usado internamente. Remover se dead.

4. **Textos em português com/sem acento** — `_PT_LABEL_TO_TESTID_SLUG`
   usa "Alocação alvo" (sem til em "alvo", mas sem problema — "alvo"
   não tem til; é "alocação" que tem til). Conferi: "Alocação" tem
   til no "ç", mas o slug usa só a chave de label, e Playwright
   `has-text` não normaliza acento, então se alguém digitar
   "Alocacao" no .feature, não casa. Os .feature files usam "Alocação"
   (com til), consistente com HTML — OK.
