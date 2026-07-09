## Context

O plano de rebalanceamento já expõe `buy_amount` e `sell_amount` em BRL e usa
preços de mercado resolvidos no pipeline de `rebalance.glue`. A UI mostra valor
financeiro da movimentação, mas não mostra quantas cotas/ações isso representa.

Há assimetria importante para ativos em `USD`: o valor recomendado de compra ou
venda vem em BRL, enquanto o preço unitário do ticker vem em dólar. O cálculo da
quantidade precisa respeitar a moeda do preço para não dividir BRL por USD.

## Goals / Non-Goals

**Goals:**
- Expor quantidade operacional por ativo negociável no plano de rebalanceamento.
- Garantir cálculo correto para ativos BRL e USD.
- Manter UI como renderizador simples, sem lógica financeira duplicada em Alpine.
- Preservar layout atual para ativos sem negociação em bolsa ou sem preço apto.

**Non-Goals:**
- Alterar solver, política de rebalanceamento, ou persistência de portfolio.
- Introduzir arredondamento final por lote, fração mínima, ou regra de corretora.
- Adicionar suporte a outras moedas além de BRL e USD neste slice.

## Decisions

### D1: Calcular `trade_quantity` no backend

**Decision:** adicionar campo derivado no payload de `RebalanceAssetPlanRow` e
calculá-lo no backend a partir do valor de compra/venda e do preço atual.

**Rationale:** backend já conhece moeda do ativo, preço atual, e semântica de
tradeable vs sentinel. Isso evita duplicar regra em template/Alpine e permite
teste unitário do cálculo.

**Alternative considered:** calcular no template. Rejeitada: template não deve
embutir conversão BRL/USD nem lógica de elegibilidade.

### D2: Conversão USD antes da divisão

**Decision:** para `currency_code = "USD"`, converter `buy_amount` ou
`sell_amount` de BRL para USD usando a cotação BRL/USD implícita no próprio row:
`current_value / quantity_atual` ou, preferencialmente, campo de preço unitário já
disponível no pipeline de rebalance.

**Rationale:** valor operacional continua em reais no plano, mas quantidade deve
ser expressa na unidade do ticker negociado. Sem conversão, resultado fica
numericamente errado.

**Alternative considered:** mostrar quantidade em "equivalente BRL". Rejeitada:
operador precisa quantidade real da ordem, não valor sintético.

### D3: Elegibilidade por ativo negociável

**Decision:** preencher `Qtd` apenas quando ativo tiver preço unitário finito e
representar ativo negociável. Rows com sentinela de não-negociável ou sem preço
mostram célula vazia/placeholder.

**Rationale:** evita inventar quantidade para ativos marcados via sentinela
`qty=1` ou instrumentos cuja movimentação não vira ordem em bolsa.

## Risks / Trade-offs

- **[Fonte de preço unitário]** Se pipeline atual não carregar preço unitário
  explícito no row final, cálculo pode depender de derivação indireta. →
  Mitigation: durante apply, preferir reutilizar campo já resolvido em
  `quotes`/glue; só derivar indiretamente se contrato atual não expor melhor base.

- **[Arredondamento operacional]** Corretora pode aceitar fração para alguns
  ativos e lote inteiro para outros. → Mitigation: slice entrega quantidade
  matemática; regras de arredondamento/lote ficam para follow-up se owner pedir.

- **[Semântica de negociável]** Alguns ativos podem ter `buy_enabled`/`sell_enabled`
  desligados mas ainda serem cotados. → Mitigation: usar critério de ativo
  negociável já adotado pelo plano, não inferir só pela existência de cotação.
