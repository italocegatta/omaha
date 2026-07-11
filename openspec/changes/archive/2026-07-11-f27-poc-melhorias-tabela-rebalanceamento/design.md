## Context

F22 (AG Grid Community) foi implementada e depois descartada pelo owner — a lib não atendeu a expectativa visual da tabela de rebalanceamento. A decisão é reverter para a tabela legada (handmade, Alpine.js) e evoluí-la iterativamente.

O owner pede uma página de teste isolada (`/teste`) que clone a tabela atual do rebalanceamento sem nenhuma melhoria visual no primeiro apply. Isso permite experimentar mudanças de layout, filtros, ordenação e estilos sem risco para a rota de produção `/rebalanceamento`.

A página de teste F21 que usava AG Grid foi arquivada e seu template excluído (`src/omaha/templates/test/` está vazio). Precisamos recriar o diretório e o template do zero, mas com a tabela legada em vez de AG Grid.

## Goals / Non-Goals

**Goals:**
- Rota `GET /teste` funcional, auth-protected, que renderiza tabela de rebalanceamento com dados reais.
- Template HTML com Alpine.js que clona a tabela legada (11 colunas, sort, filtros multi-select, busca).
- Nenhuma alteração em `/rebalanceamento` ou em qualquer rota existente.
- Reuso total de CSS existente — zero novos estilos.
- Rota stateless: sem persistência de aporte, sem mutação de sessão.

**Non-Goals:**
- Nenhuma melhoria visual ou de UX no primeiro apply.
- Nenhuma alteração no engine de rebalanceamento ou nos schemas.
- Nenhuma alteração nos testes existentes.

## Decisions

### D1 — Rota GET /teste em pages.py (não em rota separada)

A rota reusa `require_user`, `require_active_profile` e `_common_context` já definidos em `src/omaha/routes/pages.py`. Criar um router separado adicionaria complexidade sem benefício — o `@router.get("/teste")` convive pacificamente com as demais rotas.

**Alternativa rejeitada:** Router separado `test_routes.py`. Motivo: duplicação de imports de auth e helpers de contexto.

### D2 — Template herda de base.html com block content

O template `rebalance_table_poc.html` estende `base.html` para manter header, navegação e profile-switcher. Isso permite testar visualmente no contexto real do app.

### D3 — Alpine state inline no template (não em script global)

O estado Alpine (`plan`, `sortKey`, `sortDir`, `selectedClasses`, `selectedActions`, `searchTerm`, filtros) é definido inline via `x-data` no mesmo padrão de `rebalance.html`/`_rebalance_plan.html`. O template contém seu próprio `<script>` com as funções Alpine, sem modificar ou depender do `rebalancePage` global existente.

### D4 — Sem partialização inicial

O template é autocontido (não usa `{% include "_rebalance_plan.html" %}`). Isso evita acoplamento com a estrutura de production e permite evoluir o template de teste independentemente.

### D5 — Nome do template em `test/` subdiretório

Segue o padrão estabelecido por F21. O diretório `src/omaha/templates/test/` já foi usado anteriormente e está vazio.

### D6 — Sem params bar, sem class deviation cards, sem estados vazios

O foco é exclusivamente na tabela de ativos. Nenhum dos componentes auxiliares do `/rebalanceamento` (barra de aporte/thresholds, cards de classe, placeholder, empty state) é incluído.

### D7 — Chamada run_rebalance direta com contribution=0

A rota chama `run_rebalance(db, profile, 0)` diretamente, sem passar por `_materialize_rebalance_plan` (que persiste aporte na sessão). A resposta `RebalancePlanResponse` é passada ao template como `plan`.

### D8 — Alpine filter/search state segue o mesmo padrão de _rebalance_plan.html

As propriedades computadas `uniqueClasses`, `uniqueActions`, `filteredRows`, `toggleClassFilter`, `toggleActionFilter`, `isClassSelected`, e `searchTerm` são copiadas do Alpine component existente para garantir comportamento idêntico.

## Risks / Trade-offs

- **Risco:** Duplicação de lógica Alpine entre `_rebalance_plan.html` e o template de teste. **Mitigação:** Aceito — a duplicação é intencional para permitir evolução independente. Quando a versão final for aprovada, a lógica será unificada.
- **Risco:** Testes de `/teste` podem quebrar se `run_rebalance` mudar. **Mitigação:** Testes de integração da nova rota usam o mesmo seeded DB session-scoped dos demais testes.
- **Risco:** Rota `/teste` esquecida em produção. **Mitigação:** Rota não tem side effects e fica visível no router; decisão de remover será tomada quando a tabela final substituir a legada em `/rebalanceamento`.
