## Why

Browser console emite warnings de Alpine durante o carregamento
do dashboard:

```
Alpine Expression Error: classColor is not defined
Alpine Expression Error: classCurrentPct is not defined
```

O template `src/omaha/templates/dashboard.html:178` referencia
`classColor` no `:style="'background:' + classColor"` e a
linha 181 referencia `classCurrentPct` no
`x-text="Number(classCurrentPct).toFixed(2)"`. O factory
`classSection()` no mesmo arquivo (linha 736) só mapeia
`initial.id` → `classId`, `initial.name` → `className`,
`initial.target_pct` → `classTargetPct` — os outros dois campos
existem no blob `class_data` (Jinja linha 80: `c.color` e
`c.current_pct`) mas não são copiados para o objeto Alpine.

Não bloqueia o PATCH nem quebra a UI (Alpine renderiza a
expressão como string vazia), mas polui o console e esconde
outros warnings reais que poderiam aparecer.

## What Changes

- Em `src/omaha/templates/dashboard.html`, dentro de
  `classSection()` (linha ~736), adicionar duas linhas que
  copiam `initial.color` → `classColor` e
  `initial.current_pct` → `classCurrentPct`. Os dados já
  existem no blob `class_data` (Jinja linha 80) — só faltam
  os dois campos na desestruturação.
- Sem mudança no servidor.
- Sem mudança nos tests.

## Capabilities

### Modified Capabilities

- `dashboard-inline-editing`: requirement novo
  "classSection expõe color e current_pct do class_data"
  codifica a invariante "todos os campos do blob `class_data`
  usado no template estão disponíveis como propriedades
  camelCase no objeto `classSection`".

## Impact

- **Template**: 2 linhas adicionadas em `classSection()` +
  1 spec requirement.
- **Servidor**: zero.
- **Tests**: zero.
- **CSS / testids**: zero.
- **Risk**: baixíssimo. As expressões Alpine que dependem
  dessas propriedades já estão no template; só faltava
  inicialização. Antes da correção, o `:style` renderizava
  `:style="background:"` (string vazia concatenada) e o
  `x-text` mostrava `"NaN%"` (`Number(undefined).toFixed(2)`)
  — após a correção, ambos mostram o valor real do servidor.
