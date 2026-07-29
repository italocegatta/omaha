## Context

A tab nav superior (`<nav class="tab-nav" data-testid="app-tab-nav">` em `base.html` L94-112) usa 4 `<a class="tab-nav__btn">` — Patrimônio, Rebalanceamento, Rentabilidade, Proventos. Os labels hoje renderizam em `0.9rem` desktop (`.tab-nav__btn` em `app.css` ~L721) e `0.85rem` no override mobile `@media (max-width: 480px)` (~L2007). O owner aprovou +50% nos dois breakpoints, com scope guard explícito: nada mais muda.

O registro tipográfico do app (spec `typography-tokens`) pin face/peso dos display selectors — incluindo `.tab-nav__btn--active` em Red Hat Display 700 — mas não pin tamanho dos labels da nav. Este change adiciona esse pin.

## Goals / Non-Goals

**Goals:**
- `font-size` dos labels da tab nav: `1.35rem` desktop, `1.275rem` mobile (≤480px).
- Anchor de spec para os dois valores em `typography-tokens` (ADDED requirement).
- Snapshots visuais regenerados no apply para refletir o novo baseline.

**Non-Goals:**
- Alterar `font-family`, `font-weight`, cor, `letter-spacing`, `gap`, `padding` ou `line-height` (salvo exceção justificada abaixo).
- Mexer em `base.html`, rotas, JS/Alpine, tokens de design em DESIGN.md além do valor de font-size.
- Redesenhar a tab nav (underline, espaçamento entre tabs, estrutura).

## Decisions

**D1 — Dois valores, mesma proporção (+50%).** `0.9rem → 1.35rem` e `0.85rem → 1.275rem`. Mantém a diferença de hierarquia existente entre desktop/mobile (delta de 0.075rem preservado proporcionalmente). Alternativa: valor único para os dois breakpoints — rejeitada porque o override mobile existe de propósito (densidade menor em telas pequenas) e removê-lo mudaria comportamento além do escopo aprovado.

**D2 — Scope guard estrito: só `font-size`.** `padding: 0.4rem 0.1rem` (desktop) / `0.3rem 0.1rem` (mobile) e a ausência de `line-height` explícito ficam como estão. O botão é `inline-flex` com `align-items: center`, então o crescimento do em-box expande a altura do header de forma tolerável. `padding`/`line-height` só podem ser tocados se o crescimento quebrar visualmente o header (overflow, colisão com o profile switcher, clip do underline de 2px) — e qualquer ajuste nesse caso fica registrado como desvio no apply com justificativa, nunca silencioso.

**D3 — Não criar novo capability.** O tamanho da nav é um apêndice do registro tipográfico existente; um capability novo para 2 linhas de CSS seria overhead. Delta ADDED em `typography-tokens`.

**D4 — Baselines visuais regenerados, não ignorados.** `tests/visual/test_snapshots.py` compara screenshots de páginas que incluem a tab nav; o delta de altura desloca pixels. O apply regenera os baselines afetados via mecanismo padrão do suite visual e roda a lane correspondente via taskipy antes de declarar done.

## Risks / Trade-offs

- [Header cresce ~0.45rem de altura desktop] → Aceito pelo owner; D2 garante que nenhum outro ajuste compense sem justificativa. Verificar visualmente via refresh-for-test.
- [Labels mobile podem estourar em telas muito estreitas] → A nav mobile já tem `gap: 0.75rem` + `flex-wrap: wrap` (~L1998-2004), então quebra de linha é comportamento já previsto; o teste é o snapshot mobile se existir na lane visual.
- [Diff de snapshot barulhento] → Só baselines de páginas com a nav visível mudam; regenerar exatamente os afetados, não o diretório inteiro às cegas.

## Migration Plan

Rollback trivial: reverter as 2 linhas de `font-size` e regenerar baselines. Sem migração de dados, sem feature flag.
