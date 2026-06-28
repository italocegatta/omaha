# Change: rebalance-page

## Why

`rebalance-route` (archived 2026-06-27) shipped the HTTP contract
(`POST /api/rebalance` → `RebalancePlanResponse` JSON) and the
glue/orchestration. The user-facing surface that consumes the
contract is still missing: the sidebar has 3 buttons (Importar CSV,
+ Novo ativo, + Nova classe), there is no "Rebalancear" affordance,
and the operator has no way to type an aporte value and see a plan.

`.planning/REBALANCE_PLAN.md` Gaps C + D + parte da F (Fase 5).
Fase 3 (rota + UI) foi explicitamente dividida em `rebalance-route`
(contrato) + `rebalance-page` (UI que consome o contrato) — ver
`openspec/changes/archive/2026-06-27-rebalance-route/proposal.md`
"Next change: `rebalance-page`".

Phase 4 (`rebalance-engine`, CVXPY) é independente e não começa
nesta change.

## What Changes

- **ADDED** página `/rebalance` (GET renderiza template
  `rebalance.html`, POST re-renderiza o mesmo template com o plano
  no contexto). Server-side render via Jinja2; Alpine para sort
  de tabela + máscara de input + toggle do stub banner.
- **ADDED** form "Rebalancear" no sidebar (input `Aporte (R$)` +
  botão submit), presente em todas as páginas autenticadas
  (dashboard + `/rebalance`). Form action = `/rebalance` (POST).
- **ADDED** 4º botão visual na sidebar ("Rebalancear" ativo em
  `/rebalance`). Sidebar extraída para Jinja include
  (`templates/_sidebar.html`) — `dashboard.html` + `rebalance.html`
  importam via `{% include %}`.
- **ADDED** header navigation row na página `/rebalance`: dois
  links `Dashboard` (`/`) e `Plano de aporte` (`/rebalance`, ativo
  quando o plano está renderizado). Anchor + estilo consistente
  com `.app-sidebar`.
- **ADDED** layout de plano: 6 metric cards em grid 3×2 (reusa
  estética `.portfolio-stat`), warnings panel (código + mensagem
  PT-BR), asset plan table (8 cols visíveis + `data-asset-key`),
  category summary (4 cols), stub banner via `<details>`
  (`applied_policy === "stub-fixture-v1"`).
- **MODIFIED** `src/omaha/rebalance/schemas.py`: `RebalanceRequest.
  contribution` aceita qualquer `float` (remove `gt=0`). Suporta
  aporte 0 (rebalance sem dinheiro novo) e negativo (saque — gate
  no client-side, contract aberto para a engine).
- **MODIFIED** `openspec/specs/rebalance-route/spec.md`: requisito
  "Request validates contribution greater than zero" vira
  "Request validates contribution as a finite float". Sem 422 por
  valor zero/negativo — 422 só por tipo errado ou campo faltando.
- **MODIFIED** `src/omaha/templates/dashboard.html`: refator para
  usar `{% include "_sidebar.html" %}` em vez do bloco inline da
  sidebar. Sem mudança de comportamento observável.
- **ADDED** `tests/test_rebalance_page.py` (integration): GET
  renderiza, POST renderiza, valida aporte, zero-classes empty
  state, sort works.
- **ADDED** `tests/e2e/test_rebalance_page.py` (Playwright smoke):
  sidebar form visível, submit navega para `/rebalance`, plano
  renderiza, empty state quando zero classes.
- **MODIFIED** `tests/conftest.py::_INTEGRATION_PREFIXES` para
  incluir `tests/test_rebalance_page.py` (regra AGENTS.md).
- **MODIFIED** `src/omaha/static/app.css`: classes novas para
  `.rebalance-card`, `.rebalance-stat-grid`, `.rebalance-stat`,
  `.rebalance-action-badge`, `.rebalance-stub-banner`,
  `.rebalance-warnings`, `.rebalance-table`. Reusa tokens
  existentes (`--accent`, `--positive`, `--negative`, `--surface`,
  `--border`). Sem novos tokens de cor.

## Capabilities

### New Capabilities

- `rebalance-page`: renderização server-side do plano de rebalance
  na URL `/rebalance`, alimentada por form no sidebar. Cobre
  empty state (zero classes), sort de tabela, badges de ação,
  warnings e stub banner.

### Modified Capabilities

- `rebalance-route`: schema `RebalanceRequest.contribution` aceita
  qualquer float finito (0, positivo, negativo). Removido 422
  por valor ≤ 0. Sem mudança nos demais requisitos do contrato
  (response shape, error mapping, glue orchestration).

## Impact

- **Code novo:**
  - `src/omaha/templates/rebalance.html` (~200 linhas)
  - `src/omaha/templates/_sidebar.html` (~50 linhas — extraído do
    dashboard)
  - `src/omaha/routes/pages.py` (+~80 linhas: `GET /rebalance` +
    `POST /rebalance`)
- **Code modificado:**
  - `src/omaha/rebalance/schemas.py` (1 linha: `gt=0` → removido)
  - `src/omaha/templates/dashboard.html` (sidebar inline vira
    `{% include %}` — refactor transparente, ~10 linhas a menos)
  - `src/omaha/static/app.css` (+~120 linhas de CSS scoped a
    `.rebalance-*`)
  - `openspec/specs/rebalance-route/spec.md` (delta no requisito
    de validação)
- **Tests:**
  - `tests/test_rebalance_page.py` (novo, integration marker)
  - `tests/e2e/test_rebalance_page.py` (novo, Playwright smoke)
  - `tests/conftest.py::_INTEGRATION_PREFIXES` (+1 prefix)
- **Sem mudança** em `src/omaha/rebalance/glue.py`,
  `solver_stub.py`, `models.py`, fixtures, `routes/rebalance.py`
  (a rota POST /api/rebalance continua válida para testes e
  consumidores externos; a página usa `run_rebalance()` direto
  server-side).
- **Sem mudança** em `pyproject.toml` (CVXPY entra na Fase 4).

## Non-Goals

- **CVXPY solver.** Phase 4 (`rebalance-engine`) — fora do escopo.
  A página consome `run_rebalance()` que hoje retorna o stub
  fixture. Quando a engine chegar, a página automaticamente
  reflete o output real (a interface é estável).
- **Withdrawals (saque real).** Contract aceita aporte negativo
  (preparado para a engine), mas o client-side bloqueia `< 0` com
  copy explicativo. A engine Phase 4 decidirá como solver trata
  withdrawal. Esta change não implementa execução de ordens.
- **Persistência do plano.** Decisão locked: stateless. Cada
  visit a `/rebalance` requer novo submit do form. Sem
  `rebalance_runs` table, sem cache.
- **Mobile.** Decisão locked: desktop only. CSS não trata
  breakpoints abaixo de 1024px para a página `/rebalance`.
- **Server-side rendering do `POST /api/rebalance` route JSON.**
  A página usa o glue `run_rebalance()` Python function direto,
  não faz fetch para `/api/rebalance`. A rota JSON permanece
  intacta para testes e (futuro) integrações externas.

## Sequence

1. Estende spec `rebalance-route` (delta) + schema (remove `gt=0`).
2. Extrai sidebar para `_sidebar.html` include.
3. Refatora `dashboard.html` para usar o include.
4. Cria `rebalance.html` template com header nav + sidebar include
   + main area (placeholder de plano vazio).
5. Adiciona `GET /rebalance` em `pages.py` (carrega profile, checa
   zero-classes, renderiza template vazio).
6. Adiciona `POST /rebalance` em `pages.py` (parseia form, valida
   aporte, chama `run_rebalance()`, renderiza template com plano).
7. Implementa sort Alpine na tabela asset plan (reusa padrão
   `sortBy` + `sortIndicator` do dashboard).
8. Implementa action badges (Comprar / Vender / Manter) com bg-color
   sutil + ink forte, border-radius 4px (consistente com `.empty-
   state`).
9. Implementa stub banner `<details>` condicional em `applied_
   policy === "stub-fixture-v1"`.
10. Implementa warnings panel (lista com code + message).
11. Implementa empty state (zero classes): main area com copy PT-BR
    + link para `/` (sidebar form fica presente mas visualmente
    inert, com botão disabled).
12. Implementa gate client-side para aporte < 0: input `min="0"`
    + mensagem inline "Saques serão suportados em versão futura.
    Por enquanto, deixe o aporte em zero ou positivo."
13. CSS para todas as classes `.rebalance-*`.
14. Tests: integration (route + sort + validation + empty state) +
    Playwright smoke (sidebar form → /rebalance → plano visível).
15. Verifica prek + pytest + browser manual via `refresh-for-test`.
