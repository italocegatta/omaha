# Design — F35 Bug cadeado cinza na tabela ativos

## Contexto

F29 trocou labels de texto por ícones Material Symbols nos toggles de
compra/venda. O template está correto — usa `check_circle` (on) e `lock` (off).
O problema é exclusivamente no CSS: a regra `.trade-toggle--off` usa cinza
neutro para ambos buy e sell, quando deveria usar cores semânticas.

## Estados visuais esperados (4 combinações)

| Toggle | Alpine class | Ícone | Cor CSS | Significado |
|--------|-------------|-------|---------|-------------|
| Compra | `--buy --on` | check_circle | **verde** (positive) | Liberado |
| Compra | `--buy --off` | lock | **vermelho** (negative) | Bloqueado |
| Venda | `--sell --on` | check_circle | **vermelho** (negative) | Liberado |
| Venda | `--sell --off` | lock | **verde** (positive) | Bloqueado |

**Nota**: Venda on = vermelho é intencional (F29 design D1: "sell = risco/atenção").
Venda off = verde (posição protegida, venda bloqueada).

## Estado atual do CSS (app.css:1547-1566)

| Regra | Especificidade | Cor | Correta? |
|-------|---------------|-----|----------|
| `.trade-toggle--on` | 0-1-0 | verde | ✓ (buy-on fallback) |
| `.trade-toggle--off` | 0-1-0 | **cinza** | ✗ (deveria ser vermelho) |
| `.trade-toggle--buy.trade-toggle--on` | 0-2-0 | verde | ✓ |
| `.trade-toggle--sell.trade-toggle--on` | 0-2-0 | vermelho | ✓ |

**Regra faltante**: `.trade-toggle--sell.trade-toggle--off` (verde)

## Alterações CSS

### 1. Atualizar `.trade-toggle--off` → vermelho (negative)

A regra genérica passa de cinza para vermelho. Serve como fallback e cobre
buy-off (compra bloqueada = vermelho).

```css
.trade-toggle--off {
  background: color-mix(in srgb, var(--negative) 18%, var(--surface));
  border-color: color-mix(in srgb, var(--negative) 30%, transparent);
  color: var(--negative);
}
```

### 2. Adicionar `.trade-toggle--sell.trade-toggle--off` → verde (positive)

Override específico para venda bloqueada (posição protegida = verde).
Especificidade 0-2-0 vence a regra genérica 0-1-0.

```css
.trade-toggle--sell.trade-toggle--off {
  background: color-mix(in srgb, var(--positive) 18%, var(--surface));
  border-color: color-mix(in srgb, var(--positive) 30%, transparent);
  color: var(--positive);
}
```

### 3. `.trade-toggle--buy.trade-toggle--off` não necessária

A regra genérica atualizada já cobre buy-off (vermelho). Regra específica
seria redundante (mesmos valores que a genérica).

## Não-alterar

- Template HTML — correto pós-F29
- `table-formatters.js` — não afeta toggles
- Lógica de toggle (toggleTradeFlag) — API/model inalterados
- Catálogo de ícones (lock) — concern separado

## Riscos

- **Testes de cor**: assertions que esperam cinza no toggle off → atualizar
- **Sell-on vermelho**: fora do escopo F35, pode ser revisitado em slice futuro
