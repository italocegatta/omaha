## Context

A correção do row-pin foi aplicada no change
`fix-inline-edit-off-100-blocking` (commit subsequente ao
archive do change). O comportamento coberto:

1. Usuário clica numa linha do asset table
2. `startEdit` captura o índice atual do ativo em `sortedAssets`
   e seta `frozenAssetId` + `frozenIndex`
3. Usuário digita valor e pressiona Enter
4. `commitEdit` PATCH o servidor; servidor retorna 200; o
   getter `sortedAssets` re-ordena e em seguida chama
   `_pinFrozen`, que re-insere o ativo no `frozenIndex` capturado
5. O asset fica visualmente estável na linha que o usuário
   clicou; o restante da tabela é re-ordenado normalmente

Pin é liberado em `sortBy` (próximo sort é do usuário) e em
`cancelEdit*` (Escape / blur sem PATCH). **Não** é liberado em
PATCH bem-sucedido — caso contrário a linha pularia no instante
em que a resposta chegasse.

## Goals / Non-Goals

**Goals:**
- Codificar o contrato em cenário BDD que roda no CI (real
  browser via Playwright, mesmo pipeline do cenário
  "Inline edit off-100 é aceito").
- Cobrir o caminho "pino liberado no próximo sort click".

**Non-Goals:**
- Reescrever o row-pin (já está correto).
- Cobrir a interação com `frozenIndex` inválido (clamp já
  implementado em `_pinFrozen`).
- Adicionar cobertura unitária do getter `sortedAssets` —
  Alpine getters não são testáveis sem DOM.

## Decisions

### D1. Step ordinal "o ativo X é o N-ésimo da classe Y"

Novo step em `tests/bdd/step_defs/dashboard_steps.py`:

```python
@then(parsers.parse('o ativo "{ticker}" é o {ordinal:d}º da classe "{class_name}"'))
def asset_ordinal_in_class(page, ticker, ordinal, class_name):
    rows = page.locator(
        f'[data-testid="dashboard-asset-row"]:has([data-testid="asset-row-class"]:text-is("{class_name}"))'
    )
    nth = rows.nth(ordinal - 1)
    nth.wait_for(state="visible", timeout=5000)
    name = nth.locator('[data-testid="asset-row-name-text"]').inner_text()
    assert name == ticker, f"esperava {ticker!r} no {ordinal}º lugar, vi {name!r}"
```

Localiza todas as linhas da classe (filtra pela coluna
`asset-row-class`), pega a N-ésima (1-indexed), assere que o
nome é o esperado. Reusa os `data-testid` que o template já
emite (`dashboard-asset-row`, `asset-row-class`,
`asset-row-name-text`).

### D2. Cenário no arquivo `asset_crud.feature`

`target_pct.feature` cobre os fluxos de PATCH (alvo da classe,
alvo do ativo, off-100). O row-pin é ortogonal — o setup é
"criar ativos", não "PATCH percentagens". Coloco o cenário em
`asset_crud.feature` (que já tem o cenário "Per-class sum
off-100 é aceito" do change anterior).

### D3. Setup com soma ≠ 100 para forçar o re-sort

A correção do row-pin foi motivada justamente pelo caso onde a
nova `target_pct` empurra a soma per-classe para fora de 100.
O cenário usa Alpha=10, Bravo=20, Charlie=30 (soma=60) e edita
Alpha para 80 (soma=130) — cobre o caminho "linha pula sem o
freeze". Cobre Italo + Ana via `Exemplos`.

### D4. Reusa workflows existentes

`create_one_class` + `add_one_asset` em `_workflows.py` já
fazem o setup. Zero step novo de setup.

## Risks / Trade-offs

- **Browser real**: igual aos outros cenários BDD, depende
  do Playwright + dev server. Mitigado pelo pipeline
  `test-bdd` que já roda os outros 37 cenários.
- **Sort default pode mudar**: se alguém trocar o
  `sortKey: 'class'` default, o cenário precisa atualizar
  o setup para que Alpha fique no topo. Aceitável — o
  cenário documenta a expectativa atual.

## Open Questions

_Nenhuma._
