## 1. Criar template da página de teste

- [ ] 1.1 Criar diretório `src/omaha/templates/test/`
- [ ] 1.2 Criar `src/omaha/templates/test/rebalance_table_poc.html` estendendo `base.html` com `{% block content %}`
- [ ] 1.3 Incluir estrutura da tabela com 11 colunas (Classe, Ativo, Valor atual, Alvo, Desvio R$, Desvio %, Compra, Venda, Qtd, Projetado, Ação) usando classes CSS legadas (`.rebalance-table`, `.rebalance-table-th`, `.rebalance-asset-cell`, etc.)
- [ ] 1.4 Incluir `<script>` Alpine com estado `x-data` para: `plan`, `sortKey`, `sortDir`, `selectedClasses`, `selectedActions`, `searchTerm`
- [ ] 1.5 Implementar funções Alpine: `sortBy()`, `sortIndicator()`, `actionLabel()`, `formatBRL()`, `formatPct()`, `formatQuantity()`, `formatDeviationPp()`, `rowClass()`, `filteredRows`, `uniqueClasses`, `uniqueActions`, `toggleClassFilter()`, `toggleActionFilter()`, `isClassSelected()`, `toggleAllClasses()`, `toggleAllActions()`, `searchTerm` binding
- [ ] 1.6 Renderizar linhas do `<tbody>` com `<template x-for="row in filteredRows">` e atributo `data-asset-key`
- [ ] 1.7 Renderizar badge de ação traduzido (Comprar/Vender/Manter) com classes `.rebalance-action-badge--{buy|sell|hold}`
- [ ] 1.8 Incluir barra de filtros com Classe multi-select, Ação multi-select e campo de busca, usando classes `.rebalance-filter-bar`, `.rebalance-filter-group`, `.rebalance-filter-trigger`, `.rebalance-filter-panel`, `.rebalance-filter-option`, `.rebalance-filter-search`

## 2. Adicionar rota GET /teste

- [ ] 2.1 Adicionar `@router.get("/teste", response_class=HTMLResponse)` em `src/omaha/routes/pages.py` com `Depends(require_user)` + `Depends(require_active_profile)`
- [ ] 2.2 Importar `run_rebalance` de `omaha.rebalance.glue`
- [ ] 2.3 Na rota: obter perfil ativo, chamar `run_rebalance(db, profile, 0)` com thresholds default, obter `_common_context`, passar plan ao template
- [ ] 2.4 Rota retorna `_templates(request).TemplateResponse(request, "test/rebalance_table_poc.html", context)`
- [ ] 2.5 Rota não persiste aporte na sessão e não tem side effects

## 3. Adicionar testes

- [ ] 3.1 Criar `tests/test_rebalance_table_poc.py`
- [ ] 3.2 Testar `GET /teste` com usuário autenticado → HTTP 200, tabela presente
- [ ] 3.3 Testar `GET /teste` sem sessão → HTTP 303 redirect para `/login`
- [ ] 3.4 Testar `GET /teste` com perfil vazio → HTTP 200, tabela sem linhas
- [ ] 3.5 Adicionar prefixo `tests/test_rebalance_table_poc.py` a `_INTEGRATION_PREFIXES` em `tests/conftest.py`

## 4. Verificar integridade

- [ ] 4.1 Rodar `task test-unit` e confirmar que testes existentes continuam passando
- [ ] 4.2 Rodar `task test-integration` e confirmar que novos testes passam
- [ ] 4.3 Verificar que `GET /rebalanceamento` permanece inalterado
