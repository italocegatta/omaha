## Estado anterior

Esta change foi implementada uma vez mas os fixes foram revertidos (incidente
2026-07-16: apply agent sobrescreveu commit do usuário). Os 3 bugs continuam
abertos. As soluções abaixo foram validadas e testadas — reaplicar exatamente
como descrito.

## 1. Bug 1 — Quebra de linha na coluna Ativo

- [ ] 1.1 Adicionar regra CSS em `src/omaha/static/app.css`

**Exato onde:** após a regra `.asset-table td { ... }` (aprox. linha 1399), adicionar:

```css
/* f40-bug1: allow line wrap in the Ativo column (first td) so long
   asset names break inside the cell instead of overflowing. */
.asset-table td:first-child {
  white-space: normal;
  overflow-wrap: break-word;
}
```

- [ ] 1.2 Verificar no browser que nomes longos de ativos quebram linhas

## 2. Bug 2 — Conteúdo ausente em colunas Classe/Desvio e Carteira

- [ ] 2.1 Adicionar método `formatDeviationPp` no Alpine scope

**Exato onde:** em `src/omaha/templates/_patrimonio_add_asset_modal.html`,
logo após a função `signIcon` (aprox. linha 735), adicionar:

```javascript
      // f40-bug2: standalone formatDeviationPp needed by asset table cells
      // (class-deviation, portfolio-deviation). Delegates to shared module
      // with inline fallback for null/NaN.
      formatDeviationPp: function (value) {
        var f = window.__tableFormatters;
        return f ? f.formatDeviationPp(value) : (value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : (Number(value) >= 0 ? '+' : '') + Number(value).toFixed(0) + '%');
      },
```

**Por que:** o template chama `formatDeviationPp(...)` em 4 pontos (class
totals + asset rows), mas o método só existia no módulo assíncrono
`table-formatters.js`. Alpine avaliava a expressão, não encontrava a função,
e renderizava `undefined` (vazio).

- [ ] 2.2 Verificar no browser que colunas Classe/Desvio, Carteira/Atual e Carteira/Desvio exibem conteúdo

## 3. Bug 3 — Painel de filtros não abre

- [ ] 3.1 Corrigir CSS em `src/omaha/static/app.css`

**Exato onde:** na regra `.asset-table th` (aprox. linha 1388), trocar:

```css
/* ANTES */
  overflow: hidden;

/* DEPOIS */
  /* f40-bug3: overflow: hidden clips the filter panel (position: absolute
     inside <th>). Switch to visible so the panel renders correctly. */
  overflow: visible;
```

**Por que:** o painel de filtro é `position: absolute` dentro do `<th>`.
`overflow: hidden` recorta o painel. `white-space: nowrap` já previne overflow
visual do texto do header.

- [ ] 3.2 Verificar no browser que painel de filtros abre ao clicar no ícone

## 4. Validação

- [ ] 4.1 Rodar `uv run task test-unit` — esperado: 434+ passed
- [ ] 4.2 Rodar `uv run task lint` — esperado: all Passed
- [ ] 4.3 Verificar visualmente no browser: quebra de linha, filtros, conteúdo das colunas

## Arquivos afetados

| Arquivo | Mudança |
|---------|---------|
| `src/omaha/static/app.css` | +10 linhas (2 regras CSS) |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | +7 linhas (1 método JS) |

##IMPORTANTE

- Estes fixes são CIRÚRGICOS. Não mexer em mais nada.
- Não alterar colgroup, colunas, padding, margin, ou outros estilos.
- Não reintegrar coluna Moeda (foi removida intencionalmente no commit 1c0b0fc).
- Seguir PRD §4.14: fix cirúrgico, não reescrever código funcional.
