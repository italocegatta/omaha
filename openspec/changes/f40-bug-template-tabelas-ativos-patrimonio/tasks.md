# F40 — Bug template tabelas ativos patrimonio

## Contexto da sessão 2026-07-16

Esta change foi implementada mas revertida após incidente (apply agent
sobrescreveu commit `1c0b0fc` do usuário). As soluções dos 3 bugs foram
validadas funcionalmente mas perdidas no revert. Este documento contém
**toda a informação necessária** para reaplicar em < 5 minutos.

### Estado do repo

- **Commit base:** `1c0b0fc` (fix(patrimonio): align table headers, remove Moeda column)
- **NÃO MEXER** no commit do usuário — ele corrigiu headers, removeu Moeda,
  e ajustou formatação. Qualquer mudança além dos 3 fixes é proibida.

### O que foi descoberto

| Bug | Causa raiz | Localização exata | Solução |
|-----|-----------|-------------------|---------|
| 1. Word wrap | `white-space: nowrap` herdado impede quebra | `app.css` regra `.asset-table td` ~L1391 | Adicionar override em `td:first-child` |
| 2. Colunas vazias | `formatDeviationPp` não existe no scope Alpine | `_patrimonio_add_asset_modal.html` ~L735 | Adicionar método standalone |
| 3. Filtro não abre | `overflow: hidden` em `<th>` recorta painel | `app.css` regra `.asset-table th` ~L1386 | Trocar por `overflow: visible` |

### O que NÃO fazer (lição do incidente)

- NÃO alterar colgroup, colunas, ou larguras CSS existentes
- NÃO alterar padding, margin, ou espaçamento
- NÃO reintegrar coluna Moeda (removida intencionalmente)
- NÃO reescrever CSS que está funcionando
- NÃO adicionar regras "melhoradas" — manter exatamente o código abaixo
- Seguir PRD §4.14: fix cirúrgico = troca pontual, nada mais

---

## 1. Bug 1 — Quebra de linha na coluna Ativo

**Problema:** nomes longos de ativos (ex: "Fiagro Brasil Agro" com 20+ chars)
transbordam a célula porque `.asset-table td` herda `white-space: nowrap`.

**Cadeia de herança CSS:**
```
.asset-table td { padding; border; vertical-align; overflow-wrap: break-word }
  ↓ herda
.asset-table tbody td { white-space: nowrap ← ESTÁ AQUI O PROBLEMA }
  ↓ herda
td:first-child (coluna Ativo) — precisa de override
```

**Fix exato** — `src/omaha/static/app.css`:

Após a regra `.asset-table td { ... }` (que termina em ~L1399), adicionar:

```css
/* f40-bug1: allow line wrap in the Ativo column (first td) so long
   asset names break inside the cell instead of overflowing. */
.asset-table td:first-child {
  white-space: normal;
  overflow-wrap: break-word;
}
```

**Validação:** nomes de 30+ caracteres devem quebrar em 2-3 linhas dentro
da célula sem afetar largura de outras colunas.

---

## 2. Bug 2 — Conteúdo ausente em colunas Classe/Desvio e Carteira

**Problema:** 4 células mostram vazio — Classe/Desvio, Carteira/Atual,
Carteira/Desvio tanto nos totais da classe quanto nas linhas de ativo.

**Cadeia de chamada:**
```
Template (class totals):
  L143: x-text="formatDeviationPp(classDeviationPctClass)"
  L189: x-text="formatDeviationPp(classPortfolioDeviationPct)"

Template (asset rows):
  L275: x-text="formatDeviationPp(a.class_deviation_pct)"
  L325: x-text="formatDeviationPp(a.portfolio_deviation_pct)"

Alpine scope: classSection { ... }
  ↓ tem: formatPctRounded (L704), formatMoney (L712), signClass (L728), signIcon (L732)
  ↓ NÃO tem: formatDeviationPp ← PROBLEMA
  ↓ existe em: window.__tableFormatters.formatDeviationPp (carregado async)
```

**Por que falha:** Alpine avalia `formatDeviationPp(...)` no scope do componente.
O método não existe lá. O módulo `table-formatters.js` carrega assincronamente
e popula `window.__tableFormatters`, mas o template chama a função diretamente
como se fosse método do componente. Resultado: `undefined` → vazio.

**Fix exato** — `src/omaha/templates/_patrimonio_add_asset_modal.html`:

Após a função `signIcon` (que termina em ~L735), adicionar:

```javascript
      // f40-bug2: standalone formatDeviationPp needed by asset table cells
      // (class-deviation, portfolio-deviation). Delegates to shared module
      // with inline fallback for null/NaN.
      formatDeviationPp: function (value) {
        var f = window.__tableFormatters;
        return f ? f.formatDeviationPp(value) : (value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : (Number(value) >= 0 ? '+' : '') + Number(value).toFixed(0) + '%');
      },
```

**Validação:** todas as 4 células devem mostrar valores com sinal (+/-) e %.

---

## 3. Bug 3 — Painel de filtros não abre

**Problema:** ao clicar no ícone de filtro de qualquer coluna, o painel não
aparece. Funciona na tabela de rebalanceamento mas não na de ativos.

**Cadeia de herança CSS:**
```
.asset-table th {
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden ← ESTÁ AQUI O PROBLEMA
}

Filter panel (macro filter_controls):
  <div class="rebalance-filter-panel" style="position: absolute">
    ↓ é filho de <th>
    ↓ <th> tem overflow: hidden
    ↓ painel é RECORTADO invisível
```

**Por que rebalanceamento funciona:** os `<th>` da tabela de rebalanceamento
não têm `overflow: hidden`. O painel escapa normalmente.

**Fix exato** — `src/omaha/static/app.css`:

Na regra `.asset-table th` (~L1388), trocar `overflow: hidden` por:

```css
.asset-table th {
  text-align: left;
  padding: 0.5rem 0.4rem;
  border-bottom: 2px solid var(--border);
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
  /* f40-bug3: overflow: hidden clips the filter panel (position: absolute
     inside <th>). Switch to visible so the panel renders correctly. */
  overflow: visible;
}
```

**Validação:** clicar no ícone de filtro em qualquer coluna → painel aparece.

---

## 4. Validação

- [ ] 4.1 `uv run task test-unit` — esperado: 434+ passed, 0 failed
- [ ] 4.2 `uv run task lint` — esperado: all Passed
- [ ] 4.3 Browser: quebra de linha no Ativo, conteúdo em desvio, filtro abre
- [ ] 4.4 `git diff` deve mostrar APENAS as 3 adições acima (~17 linhas)

## Arquivos afetados

| Arquivo | Linhas | Mudança |
|---------|--------|---------|
| `src/omaha/static/app.css` | ~L1388 | `overflow: hidden` → `overflow: visible` em `.asset-table th` |
| `src/omaha/static/app.css` | ~L1399 | +6 linhas: regra `.asset-table td:first-child` |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | ~L735 | +7 linhas: método `formatDeviationPp` |

**Total: ~17 linhas adicionadas, 1 linha modificada. Zero removidas.**
