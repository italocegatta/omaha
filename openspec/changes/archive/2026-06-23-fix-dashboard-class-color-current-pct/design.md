## Context

O `classSection()` factory no `src/omaha/templates/dashboard.html`
é o componente Alpine que renderiza cada seção de classe no
dashboard. Ele recebe um blob `initial` (criado pelo Jinja na
linha 80) e copia campos para propriedades camelCase. O bug é
simples: dois campos (`color` e `current_pct`) existem no blob
mas não são copiados, então o template tenta usar `classColor`
e `classCurrentPct` que não existem, e Alpine grita no console.

## Goals / Non-Goals

**Goals:**
- Eliminar os dois warnings do console.
- Fazer o swatch de cor e o pill "Atual NN%" renderizarem os
  valores reais do servidor.

**Non-Goals:**
- Reestruturar o factory (não precisa).
- Adicionar cobertura BDD para o visual (já temos BDD para o
  inline edit; o visual é trivial e o lint + browser console
  cobre o que importa).
- Mexer no servidor.

## Decisions

### D1. Adicionar 2 linhas no factory

```js
classColor: initial.color,
classCurrentPct: initial.current_pct,
```

Sem renomeação, sem aliases, sem getters. A correspondência
snake_case → camelCase segue o padrão já estabelecido no
factory (id → classId, etc.).

### D2. Sem teste de unidade Alpine

Alpine getters não são testáveis sem DOM. A verificação é
trilha: browser console (zero warnings) + render visual
manual no headed browser. Coberto pelo runbook de verificação
manual do change `fix-inline-edit-off-100-blocking` (operator
roda `task serve` e abre a UI).

## Risks / Trade-offs

- **Compatibilidade**: o change não remove nem renomeia nada
  existente. Apenas adiciona 2 propriedades. Zero risco de
  regressão.
- **Performance**: 2 atribuições adicionais por classe renderizada
  no dashboard. Negligenciável.

## Open Questions

_Nenhuma._
