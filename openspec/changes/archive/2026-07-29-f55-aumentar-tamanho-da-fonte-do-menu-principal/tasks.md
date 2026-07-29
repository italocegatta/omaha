## 1. CSS edit (escopo: somente `font-size`)

- [x] 1.1 Em `src/omaha/static/app.css` (~L721), mudar `.tab-nav__btn { font-size: 0.9rem; }` → `font-size: 1.35rem`. Nenhuma outra declaração do bloco muda.
- [x] 1.2 No override mobile `@media (max-width: 480px)` (~L2007), mudar `.tab-nav__btn { font-size: 0.85rem; }` → `font-size: 1.275rem`. `padding: 0.3rem 0.1rem` intacto.
- [x] 1.3 Scope-guard check: `git diff src/omaha/static/app.css` mostra exatamente 2 linhas alteradas (`0.9rem → 1.35rem`, `0.85rem → 1.275rem`). Se o crescimento quebrar o header (overflow/clip do underline), ajustar `padding`/`line-height` SOMENTE com justificativa registrada neste change antes de prosseguir.
- [x] 1.4 Confirmar que `src/omaha/templates/base.html` NÃO foi alterado (`git diff` vazio para o arquivo).

## 2. Visual baselines

- [x] 2.1 Rodar `uv run task test-visual`; esperar falhas de comparação nos snapshots das páginas com a tab nav visível.
- [x] 2.2 Regenerar baselines afetados: `UPDATE_VISUAL_BASELINES=1 uv run task test-visual` (ou o comando equivalente da lane visual), depois re-rodar `uv run task test-visual` limpo para confirmar paridade.
- [x] 2.3 Inspecionar os diffs de imagem regenerados (pasta `tests/visual/results/` se gerada) e confirmar que só a região do header/nav mudou — sem regressões em conteúdo abaixo da nav.

## 3. Verificação e entrega

- [x] 3.1 Rodar `uv run task test-unit` — verde (inclui `tests/test_typography_tokens.py`, que não pin tamanho e deve passar intacto).
- [x] 3.2 Verificação browser: computed `font-size` de `[data-testid="app-tab-btn-patrimonio"]` = `21.6px` desktop e `20.4px` em viewport ≤480px; label ativo segue Red Hat Display 700.
- [x] 3.3 Invocar o skill `refresh-for-test` e emitir o delivery receipt (PRD §4.9) — change toca static asset, então o serve + LAN URL são obrigatórios antes de declarar done.
