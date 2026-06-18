## Context

Fase 2 (Palette) do roadmap — pesquisa completa em `.planning/phases/02-palette/`. 3 tarefas de execução pendentes. Bloqueia Fases 3-5.

## Goals / Non-Goals

**Goals:**
1. Corrigir tokens CSS `:root` no `app.css` com pares foreground/background em OKLCH
2. Garantir contraste WCAG AA (≥4.5:1 texto normal, ≥3:1 texto grande) em todos os tokens
3. Substituir `color: #fff` hardcoded por `var(--negative-ink)` em botões delete-confirm
4. Atualizar DESIGN.md com tabela de contraste e swatches
5. Criar teste automatizado de verificação de contraste

**Non-Goals:**
- Não alterar estrutura visual (layout, spacing, typography)
- Não mexer em Fase 3 (componentes) — apenas tokens

## Decisions

- **OKLCH como espaço de cor** — já adotado na Fase 1, consistente com ferramentas auditivas existentes (coloraide)
- **Token pairs foreground/background explícitos** — cada token de cor tem par fg/bg documentado com contraste computado
- **Teste com tinycss2 + coloraide** — reusa infra de teste da Fase 1 (test_audit_css_parser.py, test_audit_color_resolver.py)
- **Contraste mínimo WCAG AA** — 4.5:1 texto normal, 3:1 texto grande (≥18px ou ≥14px bold)

## Risks / Trade-offs

- [Medium] Alterar tokens pode afetar cores de classe existentes — verificar visualmente no dashboard
- [Low] Conversão para OKLCH pode mudar levemente a cor percebida — aceitável como parte da correção de contraste
