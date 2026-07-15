## 1. Template — Replace text labels with icons

**R30 learnings:** Portfolio `<td>` elements now carry `data-table-td` class (added by R30). The buy/sell toggle `<td>` already has this class. Do not strip it when editing toggle markup.

- [ ] 1.1 In `_patrimonio_class_section.html`, replace the buy toggle inner
  `<span x-text="a.buy_enabled ? 'Liberado' : 'Bloqueado'">` with a
  Material Symbols Outlined icon: `<span class="material-symbols-outlined icon--sm"
  x-text="a.buy_enabled ? 'check_circle' : 'lock'"></span>`
- [ ] 1.2 Add `:aria-label` binding to the buy toggle button:
  `:aria-label="a.buy_enabled ? 'Compra: Liberado' : 'Compra: Bloqueado'"`
- [ ] 1.3 Apply the same icon replacement to the sell toggle inner span
- [ ] 1.4 Add `:aria-label` binding to the sell toggle button:
  `:aria-label="a.sell_enabled ? 'Venda: Liberado' : 'Venda: Bloqueado'"`

## 2. CSS — Compact toggle sizing

- [ ] 2.1 In `app.css`, reduce `.trade-toggle` `min-width` from `5.5rem`
  to `2rem` to suit icon content
- [ ] 2.2 Verify `.trade-toggle--on` and `.trade-toggle--off` color
  classes still apply correctly to the icon

## 3. Tests — Update assertions

- [ ] 3.1 Search for browser/e2e tests that assert inner text
  "Liberado" or "Bloqueado" on `asset-buy-toggle` / `asset-sell-toggle`
  and update assertions to match the new icon representation or
  `aria-label` values
- [ ] 3.2 Verify all `data-testid` selectors still resolve correctly

## 4. Verification

- [ ] 4.1 Run `uv run task test-unit` — all pass
- [ ] 4.2 Run `uv run task lint` — no new violations
- [ ] 4.3 Run `uv run openspec validate f29-compra-e-venda-com-emoji-toggle --json` — valid
- [ ] 4.4 Run `refresh-for-test` and visually confirm buy/sell columns
  show icons with correct color coding in the browser
