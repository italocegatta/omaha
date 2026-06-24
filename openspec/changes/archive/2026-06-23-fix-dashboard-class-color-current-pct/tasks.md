## 1. Adicionando campos faltantes no classSection()

- [x] 1.1 Em `src/omaha/templates/dashboard.html`, dentro de `classSection()` (linha ~736), adicionar `classColor: initial.color,` e `classCurrentPct: initial.current_pct,` logo após `classTargetPct: initial.target_pct,`.

## 2. Verificação

- [x] 2.1 Restart do dev server + browser test ad-hoc (Playwright): console limpo, sem `classColor`/`classCurrentPct` warnings.
- [x] 2.2 `task lint` — passed.
- [x] 2.3 `test-unit` (124) e `test-integration` (192) — passed.
- [x] 2.4 `openspec validate fix-dashboard-class-color-current-pct` — coerência dos artefatos.

## 3. Finalização

- [x] 3.1 Arquivar a change após validação.
