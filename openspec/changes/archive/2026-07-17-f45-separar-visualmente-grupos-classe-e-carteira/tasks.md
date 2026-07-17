## 1. HTML — Add separator classes to group headers

- [x] 1.1 Add class `rebalance-table-th--group-end` to the "Classe" `<th>` in `_patrimonio_class_section.html` (line 109)
- [x] 1.2 Add class `rebalance-table-th--group-start` to the "Carteira" `<th>` in `_patrimonio_class_section.html` (line 110)

## 2. CSS — Add separator border rules

- [x] 2.1 Add `.rebalance-table-th--group-end` rule with `border-right: 2px solid var(--accent)` in `app.css` after `.rebalance-table-th` block
- [x] 2.2 Add `.rebalance-table-th--group-start` rule with `border-left: 2px solid var(--accent)` in `app.css`

## 3. Verification

- [x] 3.1 Run `task serve` and visually confirm the border break between "Classe" and "Carteira" group headers
