## Why

O sistema atual de alerta de desvio tem 3 níveis de severidade (OK / WARN / DANGER), onde o nível WARN usa amber com borda verde fraca — contraste ruim no tema escuro Catppuccin Frappe. O badge amber lê como "neutro" em vez de "atenção", e a borda verde fraca quase desaparece contra o fundo `--surface`. Simplificar para 2 estados (OK / deviação) com uma única cor de destaque vermelha melhora a legibilidade e reduz ambiguidade visual.

## What Changes

- **Remove nível WARN**: colapsar WARN e DANGER em um único estado "deviação" usando vermelho (`--alert-danger` / `--negative`)
- **Mantém OK**: verde para on-target (sem desvio) — inalterado
- **Unifica cor de destaque**: qualquer desvio > 0.01 usa a mesma cor vermelha, eliminando a tier intermediária amber
- **Remove `--alert-warn` token usage** do sistema de alerta de desvio (token CSS permanece disponível para outros usos)
- **Atualiza severidade threshold**: de 3 tiers (≤0.01 → OK, 0.01-5 → WARN, >5 → DANGER) para 2 tiers (≤0.01 → OK, >0.01 → deviação vermelha)

## Capabilities

### Modified Capabilities

- `asset-allocation-alerts`: Requirement "Severity coloring" muda de 3-tier para 2-tier. Scenarios "Small deviation uses warn color" e "Large deviation uses danger color" são substituídos por único scenario "Deviation uses danger color". Thresholds de severidade simplificados.

## Impact

- **CSS** (`src/omaha/static/app.css`): regras `--warn` modifiers removidas do sistema de alerta; `--danger` usada para todo desvio
- **Template** (`src/omaha/templates/_patrimonio_class_section.html`): Alpine bindings de severidade simplificados — sem tier intermediária
- **Spec** (`openspec/specs/asset-allocation-alerts/spec.md`): requirement "Severity coloring" atualizada
- **Visual**: badges de desvio ficam todos vermelhos em vez de amber para pequenos desvios
- **Sem mudança de comportamento**: lógica de reatividade, tolerância 0.01, e sticky card permanecem idênticas
