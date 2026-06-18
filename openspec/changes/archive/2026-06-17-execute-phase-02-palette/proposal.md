## Why

Fase 2 (Palette) do roadmap — pesquisa 100% pronta, execução 0%. Contraste `--accent` vs `--ink` falha WCAG AA (2.23:1). 3 tarefas concretas pendentes. Bloqueia Fases 3-5 (Components, Validation, Regression).

## What Changes

1. **CSS tokens** (`app.css`): corrigir `--class-4` e `--class-6`, adicionar `--negative-ink`/`--positive-ink`, converter `--error-bg`/`--error-fg` para OKLCH
2. **Botões delete-confirm**: substituir `color: #fff` hardcoded por `var(--negative-ink)`
3. **DESIGN.md**: reescrever seções de cor com tabela de contraste (D-02), swatches corrigidos (D-04)
4. **Teste automatizado**: criar `tests/test_phase02_tokens.py` com verificação de contraste WCAG AA via tinycss2 + coloraide

## Capabilities

### New Capabilities

- `palette-tokens`: color token system with WCAG AA contrast guarantees, OKLCH color space, CSS custom properties

### Modified Capabilities

- *(no existing spec changes — palette-tokens is a new capability)*

## Impact

- `src/omaha/static/app.css`: token values
- `src/omaha/templates/*.html`: hardcoded `#fff` in delete buttons
- `DESIGN.md`: color section rewrite
- `tests/test_phase02_tokens.py`: new file
