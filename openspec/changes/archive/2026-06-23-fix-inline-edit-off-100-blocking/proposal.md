## Why

O editor inline do dashboard bloqueia a edição quando o valor
digitado faria a soma per-classe sair de 100% (ou quando o valor
digitao na classe sai de 0-100). O user reporta dois sintomas:
(a) digita valor, pressiona Enter, campo fica vermelho, clicar
fora "reseta" o valor; (b) digita 100 num asset, não fica vermelho
mas o valor não persiste. O comportamento contradiz o contrato
D006 já implementado no servidor (`routes/assets.py:375-378` e
`routes/classes.py:417-419` declaram explicitamente "off-100 is
accepted") e o requirement `Edit acceptance is unconditional`
declarado em `specs/dashboard-inline-editing/spec.md:234-243`.
A spec diz "MUST NOT block"; o cliente bloqueia em 3 funções
(`commitEditClassPct`, `commitEdit`, `commitEditTotal`).

## What Changes

- **Remover pre-validações client-side nas 3 funções de commit do
  editor inline** em `src/omaha/templates/dashboard.html`:
  `commitEditClassPct` (range 0-100), `commitEdit` (per-class sum
  block via `classDeltaMessage !== ''`), `commitEditTotal` (3 guards:
  range 0-100, classe âncora 0, resultante 0-100). Cada função vira
  um PATCH incondicional; o servidor retorna 200 dentro do range
  per-row, ou 422 com `detail` user-friendly fora do range. O
  `classDelta`/`classDeltaMessage` continua existindo como
  **advisory** (alimenta o badge "Sobra/Falta" ao vivo) mas não
  bloqueia mais o PATCH.
- **Adicionar cenário BDD** em `tests/bdd/features/target_pct.feature`
  que cobre exatamente o caso reportado: editar o "alvo % classe" de
  um ativo de forma a empurrar a soma per-classe para 120% e
  confirmar que o valor persiste. Cobre os dois profiles (Italo +
  Ana) via `Esquema do Cenário`.
- **Sem mudança no servidor.** `routes/assets.py` e `routes/classes.py`
  já cumprem o contrato D006. O fix é puramente client.
- **Sem mudança nos tests `_disabled/`.** O test que codifica o
  bug como feature (`tests/e2e/_disabled/test_s01_inline_edit.py:418`)
  será tratado em change separado conforme decisão do operador.

## Capabilities

### New Capabilities

_Nenhuma._

### Modified Capabilities

- `dashboard-inline-editing`: requirement novo "Client MUST NOT
  pre-validate inline edits" codifica o contrato que o client
  violou — PATCH incondicional, server é source of truth, advisory
  badge segue mostrando Sobra/Falta ao vivo. Cenário BDD novo
  ("Inline edit off-100 é aceito") em `target_pct.feature`
  documenta a expectativa do user.

## Impact

- **Template**: `src/omaha/templates/dashboard.html:966-1021`
  (`commitEditClassPct`), `:1053-1115` (`commitEdit`), `:1123-1180`
  (`commitEditTotal`). ~30 linhas de guards removidas.
- **BDD**: `tests/bdd/features/target_pct.feature` — 1 cenário
  novo de ~10 linhas. Usa steps já existentes
  (`tests/bdd/step_defs/{common,target,asset}_steps.py`).
- **Servidor**: zero. `routes/assets.py:320-382` e
  `routes/classes.py:404-447` já estão corretos.
- **Tests de integração**: zero. `tests/test_t02_assets_routes.py`
  e `tests/test_t02_classes_routes.py` já validam o range
  per-row 0-100; nada muda.
- **CSS / testids**: zero. Nenhum botão ou testid novo/removido.
- **Risk**: baixo. Comportamento novo é o que o servidor já
  fazia — observability aumenta (mais PATCHes enviados, mais
  cases do advisory badge visíveis), UX fica não-bloqueante
  conforme pedido. O `@blur` que dispara `commitEdit*` em
  segunda chamada é idempotente: o guard removido também
  protegia contra re-execução, então mantemos um
  `if (this.editingAssetId === null) return;` (já presente em
  `commitEdit` linha 1054) como guarda de re-entrância.
