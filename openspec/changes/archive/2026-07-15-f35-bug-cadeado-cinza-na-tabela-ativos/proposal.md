# F35 — Bug cadeado cinza na tabela ativos

## Problema

Os toggles de compra/venda na tabela de ativos do patrimônio exibem um **terceiro
estado visual inválido**: um cadeado cinza neutro. O comportamento correto (e o
que existia antes de F29) é binário:

- **Liberado** — ícone `check_circle` verde
- **Bloqueado** — ícone `lock` vermelho

O cadeado cinza aparece quando o toggle está no estado `--off` (desabilitado).
O CSS `.trade-toggle--off` usa cores neutras (`var(--bg-hover)`, `var(--border)`,
`var(--ink)`) para **ambos** compra e venda, ignorando a semântica de cada coluna.

## Causa raiz

F29 (compra-e-venda-com-emoji-toggle) trocou o texto "Liberado"/"Bloqueado" por
ícones Material Symbols (`check_circle`/`lock`), mas **não adicionou regras CSS
específicas** para os estados off diferenciados por tipo de toggle:

### Estado atual do CSS (app.css:1547-1566)

| Regra | Especificidade | Cor | Usado por |
|-------|---------------|-----|-----------|
| `.trade-toggle--on` | 0-1-0 | verde (positive) | buy-on ✓, sell-on (overridden) |
| `.trade-toggle--off` | 0-1-0 | **cinza** (bg-hover/ink) | buy-off ✗, sell-off ✗ |
| `.trade-toggle--buy.trade-toggle--on` | 0-2-0 | verde (positive) | buy-on ✓ |
| `.trade-toggle--sell.trade-toggle--on` | 0-2-0 | vermelho (negative) | sell-on ✓ |

### Regras faltantes

| Regra necessária | Cor esperada | Motivo |
|-----------------|-------------|--------|
| `.trade-toggle--buy.trade-toggle--off` | **vermelho** (negative) | lock vermelho = compra bloqueada |
| `.trade-toggle--sell.trade-toggle--off` | **vermelho** (negative) | lock vermelho = venda bloqueada |

### Bug secundário: `.trade-toggle--off` usa cinza

A regra genérica `.trade-toggle--off` (line 1552) aplica cinza para ambos os
tipos. As regras específicas com maior especificidade (0-2-0 > 0-1-0) deverão
prevalecer, mas a regra genérica precisa ser atualizada para refletir o estado
mais comum (vermelho = bloqueado).

## Escopo

- **Corrigir**: CSS das regras `.trade-toggle--off` no `app.css`
- **Não alterar**: template HTML, JS, lógica de toggle, API, modelos
- **Não alterar**: ícones (`check_circle` / `lock`) — estão corretos

## Não-escopo

- Mudar a lógica de toggle (buy/sell flags)
- Alterar o template HTML (já correto pós-F29)
- Modificar o import modal (usa checkbox, padrão diferente)
- Adicionar bulk toggle
- Alterar o catálogo de ícones (lock já é usado, catálogo é concern separado)
