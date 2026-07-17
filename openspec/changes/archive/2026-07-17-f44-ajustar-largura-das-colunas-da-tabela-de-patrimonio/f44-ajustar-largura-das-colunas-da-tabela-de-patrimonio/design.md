## Context

A tabela de patrimônio usa `table-layout: fixed` com larguras definidas por variáveis CSS em `:root` (app.css:1690-1705). As larguras atuais são:

```css
--col-ativo: 205px;
--col-qtd: 65px;
--col-avg-price: 120px;
--col-gain: 140px;
--col-position: 130px;
--col-position-deviation: 110px;
--col-class-current: 100px;
--col-class-target: 110px;
--col-class-deviation: 100px;
--col-portfolio-current: 110px;
--col-portfolio-target: 110px;
--col-portfolio-deviation: 100px;
--col-buy: 95px;
--col-sell: 95px;
```

Total: ~1520px. Colunas de percentuais (Classe/Carteira) somam ~630px (41% do total), mas contêm dados compactos (valores de 0-100%).

## Goals / Non-Goals

**Goals:**
- Aumentar largura da coluna "Ativo" para acomodar nomes longos (ex: "Tesouro Renda+ Aposentadoria Extra 2065")
- Reduzir largura das colunas de percentual que desperdiçam espaço
- Manter legibilidade e alinhamento visual

**Non-Goals:**
- Mudar largura de colunas que já estão bem dimensionadas (Qtd, Preço médio, Ganho, Compra, Venda)
- Alterar comportamento de ordenação ou filtros
- Modificar estrutura HTML da tabela

## Decisions

1. **Aumentar `--col-ativo` de 205px para ~250px (+22%)** — Nomes longos precisam de mais espaço para evitar quebra de linha excessiva.

2. **Reduzir colunas de percentual em 10-20%:**
   - `--col-position`: 130px → 110px (-15%)
   - `--col-class-current`: 100px → 80px (-20%)
   - `--col-class-target`: 110px → 90px (-18%)
   - `--col-portfolio-current`: 110px → 90px (-18%)
   - `--col-portfolio-target`: 110px → 90px (-18%)

3. **Reduzir colunas de desvio em 5-10%:**
   - `--col-class-deviation`: 100px → 90px (-10%)
   - `--col-portfolio-deviation`: 100px → 90px (-10%)

4. **Alternativa considerada:** Usar porcentagens em vez de pixels — Rejeitado porque `table-layout: fixed` com pixels dá controle mais preciso e previsível.

## Risks / Trade-offs

- **Risco baixo:** Ajuste CSS puro, sem impacto em comportamento
- **Trade-off:** Coluna "Ativo" mais larga vs. colunas de percentual mais apertadas — justificado pela importância do nome do ativo
- **Rollback:** Reverter valores das variáveis CSS se resultado não for satisfatório
