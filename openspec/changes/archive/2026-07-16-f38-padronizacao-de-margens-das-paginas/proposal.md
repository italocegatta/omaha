## Why

A sessão anterior reduziu margens pela metade e zerou padding horizontal nos wrappers de página. Tabelas ficam flush nas bordas do card, sem respiração. Wrappers não são simétricos (`margin: 0` = alinhado à esquerda em telas largas). Existe também um órfão CSS (declaração solta sem seletor) que precisa ser removido.

## What Changes

- Padronizar wrappers de página full-width: `max-width: 1920px`, `margin: 0 auto`, `padding: 1rem 0.75rem`.
- Atualizar breakpoint mobile (480px): padding simétrico `0.5rem 0.25rem`.
- Remover órfão CSS na linha ~931-933 (declaração `padding` solta sem seletor).
- Manter stub pages e login page intocados.

## Capabilities

### Modified Capabilities

- `visual-regression-baseline`: padding/margin mudam — baselines visuais podem precisar de regeneração.

## Impact

- `src/omaha/static/app.css` (linhas 814-879, 931-933, 2117-2130)
