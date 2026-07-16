## Context

Wrappers de página full-width (`.patrimonio-page`, `.rebalance-page` + `.rebalance-card`, `.class-editor`, `.asset-editor`, `.import-page`, `.import-review`) compartilham o mesmo padrão CSS com `max-width: 1800px`, `margin: 0`, `padding: 0.5rem 0`. Resultado: conteúdo grudado na borda esquerda em telas largas, sem simetria horizontal. A sessão anterior cortou padding pela metade.

## Goals / Non-Goals

**Goals:**
- Simetria horizontal: `margin: 0 auto` centraliza wrapper em telas largas.
- Padding generoso: `1rem 0.75rem` dá respiração entre borda do card e conteúdo.
- `max-width: 1920px` para telas ultra-wide.
- Mobile (≤480px): padding simétrico `0.5rem 0.25rem`.
- Remover órfão CSS (declaração solta sem seletor).

**Non-Goals:**
- Não alterar stub pages (`.stub-page`) ou login.
- Não alterar rotas, templates, modelos, ou seeds.
- Não mudar borda, background, ou border-radius dos wrappers.

## Decisions

### 1. Padrão unificado para todos os wrappers full-width

Todos os 6 wrappers recebem o mesmo bloco: `max-width: 1920px; width: 100%; margin: 0 auto; padding: 1rem 0.75rem`. Background, border, border-radius permanecem inalterados.

**Why:** consistência visual e manutenção simples — um padrão, não seis variações.

### 2. `margin: 0 auto` para centralização

Em telas >1920px, o wrapper fica centralizado horizontalmente.

**Why:** simetria visual. `margin: 0` causava alinhamento à esquerda.

### 3. Remover órfão CSS

Linhas 931-933 contêm `padding: 0.75rem 1rem; }` sem seletor — declaração morta. Remover.

**Why:** lixo CSS que confunde auditores e pode causar parse inesperado.

## Exact CSS Changes

### Wrapper pattern (linhas 814-879) — 6 blocos idênticos

Trocar em cada wrapper:
```css
/* DE */
max-width: 1800px;
margin: 0;
padding: 0.5rem 0;

/* PARA */
max-width: 1920px;
margin: 0 auto;
padding: 1rem 0.75rem;
```

Wrappers afetados:
- `.patrimonio-page` (linha 814)
- `.rebalance-page` (linha 825) + `.rebalance-card` (linha 830)
- `.class-editor` (linha 838)
- `.asset-editor` (linha 849)
- `.import-page` (linha 860)
- `.import-review` (linha 871)

### Orphan removal (linhas 931-933)

Remover bloco:
```css
/* Rebalance page wrapper — shape defined in PAGE WRAPPERS block above */
  padding: 0.75rem 1rem;
}
```

### Mobile breakpoint (linhas 2122-2130)

```css
/* DE */
padding: 0.25rem 0;

/* PARA */
padding: 0.5rem 0.25rem;
```

## Risks / Trade-offs

- [Risk] Baselines visuais podem quebrar → [Mitigation] regenerar PNGs afetados no mesmo change.
- [Risk] `1920px` pode não cobrir todos os monitores ultra-wide → [Mitigation] 1920px é padrão industrial; `margin: 0 auto` fallback seguro.

## Migration Plan

1. Editar `src/omaha/static/app.css` — 6 wrappers + orphan + mobile.
2. Verificar no browser via `refresh-for-test`.
3. Regenerar baselines visuais se necessário.
