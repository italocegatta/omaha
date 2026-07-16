## Context

O sistema de alerta de desvio (`asset-allocation-alerts`) usa 3 tiers de severidade:
- OK (≤0.01): verde (`--alert-ok`)
- WARN (>0.01, ≤5): amber (`--alert-warn`) — **problema de contraste**
- DANGER (>5): vermelho (`--alert-danger`)

O tier WARN usa amber com borda que lê como verde fraco no tema escuro Catppuccin Frappe.
O contraste é ruim: amber oklch(0.844 0.08 83.5) sobre surface oklch(0.46 0.037 273.0) tem
contraste ~3.2:1, abaixo do WCAG AA 4.5:1 para texto normal. A borda verde fraca
quase desaparece contra o fundo.

Arquivos afetados:
- `src/omaha/static/app.css` — regras `--warn` modifiers (linhas ~1435-1449)
- `src/omaha/templates/_patrimonio_class_section.html` — Alpine bindings de severidade
- `openspec/specs/asset-allocation-alerts/spec.md` — requirement "Severity coloring"

## Goals / Non-Goals

**Goals:**
- Eliminar tier intermediário amber/WARN do sistema de alerta de desvio
- Unificar todo desvio > 0.01 em uma única cor vermelha (`--alert-danger`)
- Manter OK (vermelho) para on-target — sem mudança
- Melhorar contraste e legibilidade dos badges de desvio

**Non-Goals:**
- Remover token `--alert-warn` do `:root` (pode ser usado em outros contextos)
- Alterar lógica de reatividade ou tolerância 0.01
- Alterar sticky card ou per-class delta pill behavior
- Alterar sistema de alerta em rebalance (cards de classe já usam ok/over)

## Decisions

### D1 — 2-tier severity (OK + deviação vermelha)

**Escolha:** Colapsar WARN e DANGER em um único estado "deviação" usando `--alert-danger` / `--negative`.

**Alternativa considerada:** Manter 3 tiers mas trocar amber por uma cor com melhor contraste (ex: laranja mais escuro). Rejeitado: adicionaria complexidade sem resolver o problema fundamental de que 3 tiers são desnecessários para desvio de alocação — o usuário quer saber "está certo" vs "não está certo".

**Rationale:** Desvio de alocação é binário na prática: ou está dentro da tolerância (OK) ou precisa de atenção. A tier intermediária amber criava falsa sensação de "quase certo" sem ação clara.

### D2 — Cor vermelha consistente com token existente

**Escolha:** Reutilizar `--alert-danger` (que aponta para `--negative`) como a cor única de desvio.

**Alternativa considerada:** Criar novo token `--alert-deviation`. Rejeitado: `--negative` já é o token de "atenção/erro" no sistema e tem contraste verificado (oklch 0.717 0.124 19.4 sobre surface).

### D3 — CSS modifier simplificado

**Escolha:** Remover classes `--warn` do sistema de alerta. Manter `--ok` e `--danger` como os dois únicos modificadores.

**Impacto:** As regras CSS `.asset-allocation-alert--warn`, `.asset-allocation-alert-class--warn`, `.asset-group-header-alert--warn` (app.css ~1443-1449) deixam de ser usadas pelo sistema de alerta. Podem ser removidas ou mantidas como dead code — decisão de implementação.

## Risks / Trade-offs

- **[Risco] Perda de granularidade visual** → Mitigação: desvio de alocação é informação binária ("precisa ajustar?"); granularidade amber não agregava decisão
- **[Risco] Badge vermelho para pequenos desvios pode parecer alarmante** → Mitigação: desvio > 0.01 já é significativo (o sistema aceita com tolerância 0.01); se o badge aparece, é porque realmente precisa de atenção
- **[Trade-off] Menos informação visual** → Aceitável: a informação numérica (X%) continua presente no badge; a cor só sinaliza "atenção necessária"
