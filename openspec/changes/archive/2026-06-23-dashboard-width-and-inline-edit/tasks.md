## 1. Widening dashboard

- [x] 1.1 Em `src/omaha/static/app.css:473`, trocar `max-width: 760px` por `max-width: 1400px` no override do `<main>` do dashboard. Confirmar que a regra global em `:201` (640px) e as `@media (max-width: 480px)` permanecem intactas.

## 2. Removendo botões dos editores inline

- [x] 2.1 Em `src/omaha/templates/dashboard.html:109-118`, remover os dois botões (`class-inline-edit-commit`, `class-inline-edit-cancel`) do editor de target % da classe. Manter o input, o `keyup.enter`, o `keyup.escape.window` e a `<span>` de erro inline.

- [x] 2.2 Em `src/omaha/templates/dashboard.html:239-242`, remover os dois botões (`asset-inline-edit-commit`, `asset-inline-edit-cancel`) do editor de `alvo % classe` do ativo. Manter o input e os handlers existentes.

- [x] 2.3 Em `src/omaha/templates/dashboard.html:274-277`, remover os dois botões (`asset-target-pct-total-edit-commit`, `asset-target-pct-total-edit-cancel`) do editor de `alvo % total` do ativo. Manter o input, o hint e o span de erro.

## 3. Adicionando commit on blur

- [x] 3.1 No input `class-inline-edit-input` (`:98-108`), adicionar `@blur="commitEditClassPct()"` ao lado do `@keyup.enter` existente.

- [x] 3.2 No input `asset-inline-edit-input` (`:226-238`), adicionar `@blur="commitEdit()"` ao lado do `@keyup.enter` existente.

- [x] 3.3 No input `asset-target-pct-total-edit-input` (`:261-273`), adicionar `@blur="commitEditTotal()"` ao lado do `@keyup.enter` existente.

- [x] 3.4 Verificar que as funções `commitEditClassPct`, `commitEdit` e `commitEditTotal` (`:965`, `:1052`, `:1122`) já guardam contra `NaN` antes de chamar o PATCH — em caso afirmativo, não há trabalho adicional; em caso negativo, adicionar a guarda no topo de cada uma.

## 4. Removendo CSS morto

- [x] 4.1 Em `src/omaha/static/app.css`, deletar as regras `.asset-inline-edit-actions` (`:704-709`) e `.asset-inline-edit-commit` / `.asset-inline-edit-cancel` (`:711-737`).

- [x] 4.2 Em `src/omaha/static/app.css`, deletar as regras `.class-inline-edit-commit` e `.class-inline-edit-cancel` (`:903-930`).

- [x] 4.3 Rodar `uv run task lint` para garantir que nenhuma outra regra referencia as classes removidas.

## 5. Atualizando testes

- [x] 5.1 Em `tests/e2e/test_s01_inline_edit.py:75-77`, remover as entradas `asset_inline_edit_commit` e `asset_inline_edit_cancel` do dicionário de seletores (a entrada `asset_inline_edit_input` permanece).

- [x] 5.2 Em `tests/e2e/test_s10_asset_table.py:27-28`, remover as entradas `asset_target_pct_total_edit_commit` do dicionário de seletores.

- [x] 5.3 Em `tests/e2e/test_s10_asset_table.py:310-313`, trocar `target_row.locator('[data-testid="asset-inline-edit-commit"]').first.click()` por `page.keyboard.press("Enter")` (ou equivalente Playwright após `.fill()`). (Também em `:215` — mesmo arquivo, mesmo padrão.)

- [x] 5.4 Em `tests/test_t03_pages_routes.py:367-369`, remover as três asserts de string que verificam `data-testid="asset-inline-edit-input"`, `data-testid="asset-target-pct-total-edit-input"` e `data-testid="asset-target-pct-total-edit-commit"` no HTML bruto. (As duas primeiras referenciam inputs que permanecem — substituir por asserts sobre os testids corretos sem botão.)

- [x] 5.5 Rodar `uv run task test-unit` e `uv run task test-integration` para confirmar zero regressão.

## 6. Verificação manual

- [ ] 6.1 Subir o dev server via `task serve`, abrir a URL LAN via `bash scripts/print_lan_url.sh`, e confirmar visualmente: (a) `<main>` ocupa ~73% da largura de um monitor 1920px, (b) clicar no % da classe abre input sem botões, (c) Enter salva, (d) clicar fora do input salva, (e) Escape cancela.

- [ ] 6.2 Repetir 6.1c-6.1e para a célula `alvo % classe` e para a célula `alvo % total` da tabela de ativos.

- [ ] 6.3 Inspecionar o DOM no DevTools e confirmar que `document.querySelector('[data-testid="class-inline-edit-commit"]')` retorna `null` quando o editor da classe está aberto (e equivalente para os outros três testids de botão).

## 7. Finalização

- [x] 7.1 Rodar `uv run task check` (lint + unit) e garantir que passa.

- [x] 7.2 Rodar `uv run task test-integration` e garantir que passa.

- [x] 7.3 Rodar `openspec validate dashboard-width-and-inline-edit` para confirmar que os artefatos estão coerentes antes de arquivar.
