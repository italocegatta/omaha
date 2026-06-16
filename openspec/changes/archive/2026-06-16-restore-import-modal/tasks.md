## 1. Diagnosticar dano colateral

- [x] 1.1 Verificar `git diff a8b1d13 HEAD -- src/omaha/static/app.css` para CSS perdido do modal
- [x] 1.2 Verificar `git diff a8b1d13 HEAD -- src/omaha/routes/` para rotas afetadas
- [x] 1.3 Verificar `git diff a8b1d13 HEAD -- tests/` para testes quebrados pelo merge

## 2. Restaurar dashboard.html

- [x] 2.1 Substituir `src/omaha/templates/dashboard.html` pela versão do commit `a8b1d13`
- [x] 2.2 Verificar que o botão "Importar CSV" + modal estão presentes no HTML
- [x] 2.3 Verificar que inline editing, CRUD de ativos, colapsável, e classSum estão presentes

## 3. Restaurar CSS (se necessário)

- [x] 3.1 Se CSS do modal estiver faltando em app.css, restaurar do commit `a8b1d13`
- [x] 3.2 Verificar que `import-btn`, `import-modal-overlay`, `import-modal-panel` e classes relacionadas existem

## 4. Verificar consistência

- [x] 4.1 Rodar `uv run ruff check src/omaha/templates/dashboard.html` (lint)
- [x] 4.2 Rodar testes não-e2e: `uv run pytest tests/ -v --ignore=tests/e2e/`
- [x] 4.3 Rodar smoke test e2e: `uv run pytest tests/e2e/test_s04_user_journey.py -v`
