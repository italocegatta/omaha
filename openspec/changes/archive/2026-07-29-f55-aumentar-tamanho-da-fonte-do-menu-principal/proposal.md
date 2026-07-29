## Why

Os nomes das páginas na tab nav superior (Patrimônio, Rebalanceamento, Rentabilidade, Proventos) estão pequenos demais para o registro visual maximal do app (0.9rem desktop / 0.85rem mobile). O owner pediu +50% de presença tipográfica nesses labels — sem alterar nada além do tamanho.

## What Changes

- `.tab-nav__btn` (desktop): `font-size` de `0.9rem` → **`1.35rem`** (+50%) em `src/omaha/static/app.css` (~L721).
- Override mobile `@media (max-width: 480px)`: `font-size` de `0.85rem` → **`1.275rem`** (+50%) (~L2007).
- Scope guard: SOMENTE `font-size` muda. `font-family`, `font-weight`, cor, `gap`, `padding` e `line-height` intocados (padding/line-height só se o crescimento quebrar visualmente o header — decisão registrada em design.md).
- Snapshot visual baselines de páginas com a tab nav visível ficarão deslocados — regenerar no apply (`tests/visual/test_snapshots.py`).
- Contrato de tamanho ancorado em spec: novo requirement em `typography-tokens` pinando os dois valores.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `typography-tokens`: adiciona requirement que pin o `font-size` dos labels da tab nav principal (`1.35rem` desktop, `1.275rem` mobile ≤480px) como parte do registro tipográfico maximal.

## Impact

- `src/omaha/static/app.css` — 2 linhas (`font-size` em `.tab-nav__btn` desktop + override mobile).
- `src/omaha/templates/base.html` — NENHUMA alteração (referência apenas; nav L94-112).
- `tests/visual/baselines/` — regeneração de snapshots afetados pela nova altura visual dos labels.
- Sem mudanças em rotas, modelos, seed, migrações, JS/Alpine ou outras folhas de CSS.
