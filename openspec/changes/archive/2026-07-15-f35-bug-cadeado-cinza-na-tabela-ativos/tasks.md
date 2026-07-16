## 1. CSS — Corrigir cores do toggle off-state

- [ ] 1.1 Em `app.css` (line ~1552), atualizar `.trade-toggle--off` para usar
  cores vermelhas (negative) em vez de cinza:
  ```css
  .trade-toggle--off {
    background: color-mix(in srgb, var(--negative) 18%, var(--surface));
    border-color: color-mix(in srgb, var(--negative) 30%, transparent);
    color: var(--negative);
  }
  ```
- [ ] 1.2 Adicionar nova regra `.trade-toggle--sell.trade-toggle--off` logo
  após `.trade-toggle--sell.trade-toggle--on` (line ~1566):
  ```css
  .trade-toggle--sell.trade-toggle--off {
    background: color-mix(in srgb, var(--positive) 18%, var(--surface));
    border-color: color-mix(in srgb, var(--positive) 30%, transparent);
    color: var(--positive);
  }
  ```

## 2. Testes — Atualizar assertions de cor

- [ ] 2.1 Buscar testes que assertam a cor/estilo do toggle off-state
  (buy_enabled=false, sell_enabled=false) e atualizar para as novas cores
- [ ] 2.2 Verificar que testes de toggle on-state não são afetados

## 3. Verificação

- [ ] 3.1 `task test-unit` — todos passam
- [ ] 3.2 `task lint` — sem violações novas
- [ ] 3.3 `refresh-for-test` — visualizar no browser:
  - Compra Liberado = check_circle verde ✓
  - Compra Bloqueado = lock vermelho ✗
  - Venda Liberado = check_circle vermelho ✓
  - Venda Bloqueado = lock verde ✗
  - Nenhum cadeado cinza visível
