## 1. Atualizar wrappers full-width

- [x] 1.1 Em `src/omaha/static/app.css`, trocar `max-width: 1800px` → `1920px`, `margin: 0` → `0 auto`, `padding: 0.5rem 0` → `1rem 0.75rem` em `.patrimonio-page`, `.rebalance-page`, `.rebalance-card`, `.class-editor`, `.asset-editor`, `.import-page`, `.import-review`.

## 2. Remover órfão CSS

- [x] 2.1 Deletar linhas 931-933 (`/* Rebalance page wrapper... */ padding: 0.75rem 1rem; }`) — declaração solta sem seletor.

## 3. Atualizar breakpoint mobile

- [x] 3.1 No `@media (max-width: 480px)` (~linha 2122-2130), trocar `padding: 0.25rem 0` → `padding: 0.5rem 0.25rem`.

## 4. Verificar resultado

- [ ] 4.1 Rodar `refresh-for-test` e inspecionar no browser: wrappers centralizados, padding simétrico, tabelas com respiração.
- [ ] 4.2 Confirmar que stub pages e login não foram afetados.
