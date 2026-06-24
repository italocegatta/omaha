## Context

O editor inline do dashboard (`src/omaha/templates/dashboard.html`)
possui três funções de commit — `commitEditClassPct` (linha 966),
`commitEdit` (linha 1053) e `commitEditTotal` (linha 1123) — que
fazem pre-validação client-side antes de chamar o PATCH. As
pre-validações contradizem o contrato do servidor (D006):
`routes/assets.py:375-378` aceita qualquer valor per-row 0-100
sem checar soma per-classe, e `routes/classes.py:417-419` aceita
qualquer `target_pct` per-classe 0-100 sem checar soma do
portfolio. O resultado: usuário digita valor válido, client
bloqueia, valor não persiste, user pensa que o sistema "engoliu"
o input.

A spec `dashboard-inline-editing` já declara em
`Edit acceptance is unconditional` (linha 234-243 do spec atual)
que o client "MUST NOT block the commit when the local preview's
per-class sum differs from 100%". A spec foi cumprida no servidor
mas não no client.

## Goals / Non-Goals

**Goals:**
- Alinhar o comportamento do client ao contrato D006 já
  declarado no servidor e na spec.
- Manter o advisory visual (badge "Sobra X%" / "Falta X%") que
  ajuda o usuário a entender a saúde da alocação.
- Adicionar um cenário BDD que prova o contrato com browser
  real, evitando regressão futura.

**Non-Goals:**
- Reescrever o editor inteiro (sem mudança de layout, sem
  mudança de testids, sem mudança de CSS).
- Tocar no servidor (já está correto).
- Tocar nos tests `_disabled/` (será tratado em change
  separado).
- Reativar a suíte e2e completa (escopo separado; ver
  `M002_RESSALVA_DIAGNOSIS.md`).

## Decisions

### D1. Remover guards; manter re-entrance guard

Cada uma das 3 funções fica:

```js
commitEditClassPct: function () {
  if (this.editingClassPct === false) return;  // re-entrance
  var self = this;
  self.savingClassPct = true;
  self.editClassPctError = '';
  fetch('/api/classes/' + self.classId, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_pct: self.editClassPctValue }),
  })
    .then(/* ... cadeia idêntica, server detail → editClassPctError ... */);
},
```

Alternativas consideradas:
- **Manter o guard só para `parsed < 0` ou `parsed > 100`**
  (range) e remover o sum-block — rejeitado porque o servidor já
  retorna 422 com mensagem idêntica; duplicar a validação no
  client é fonte de drift de mensagens.
- **Mostrar confirmação ("Tem certeza?") antes de PATCH off-100**
  — rejeitado. O usuário foi explícito: "interface não pode
  bloquear o usuário de inserir um valor". Confirmação é outra
  forma de bloqueio; o advisory badge já dá o feedback ao vivo.
- **Desabilitar o `@blur` quando classDelta é não-vazio** —
  rejeitado. Mesmo problema: bloqueia.

### D2. `classDelta`/`classDeltaMessage` ficam como advisory

Os getters (linhas 846-862) continuam computando a soma per-classe
em tempo real. Eles alimentam o `class-delta-badge` no header da
classe (linha 117) e o `asset-group-header-alert` no group header
do asset table (linhas 182-186). Esse é o canal correto para
mostrar a Sobra/Falta — o usuário vê a alocação em movimento
enquanto edita, sem o PATCH ser bloqueado.

### D3. Cenário BDD cobre o caso do user

O cenário novo em `tests/bdd/features/target_pct.feature`
replica o passo-a-passo do report:

1. Login + classe "RF Pós" 50%
2. Adicionar 2 ativos "Tesouro Selic 2029" 40% + "Tesouro IPCA
   2029" 40% (soma per-classe 80%, "Falta 20%")
3. Editar o "alvo % classe" de Selic de 40 para 80 (soma
   resultante 80+40=120, "Sobra 20%")
4. Pressionar Enter
5. **Assert:** o valor "80.00%" persiste na célula.

Cobre os dois profiles (Italo + Ana) via `Esquema do Cenário` +
`Exemplos`. Reusa steps já existentes em
`tests/bdd/step_defs/{common,asset,target}_steps.py` — zero
step novo.

Alternativa considerada: cobrir só a classe (não o ativo) — o
report do user menciona "alvo % classe" que mapeia mais
naturalmente para a coluna do ativo na tabela. O sintoma
"digito 100, não registra" só acontece no caminho do ativo
(o `commitEditClassPct` não tem sum-block).

### D4. Sem mudança nos tests `_disabled/`

O test `tests/e2e/_disabled/test_s01_inline_edit.py:418` chama-se
`test_inline_edit_blocks_when_sum_neq_100` e asserTA o
comportamento bugado como se fosse feature. Foi explicitamente
deixado para outra change conforme decisão do operador. Manter
intocado aqui evita misturar escopos e mantém o test
desativado até o rework da suíte e2e.

## Risks / Trade-offs

- **Mais PATCHes em sequência** (o user pode rapid-fire 100
  no input, Enter, e o PATCH sai mesmo se a soma explode) →
  aceitável; o servidor trata 422 idempotentemente e o
  advisory badge segue em tempo real.
- **O `@blur` agora dispara o PATCH mesmo em casos onde o
  Enter já disparou** → mitigado pelo re-entrance guard
  (`if (this.editingXxx === null) return;`). O guard já
  existe em `commitEdit` (linha 1054); precisa ser
  adicionado a `commitEditClassPct` e `commitEditTotal`.
- **Regressão visual do advisory**: o advisory badge
  "Sobra/Falta" já está renderizado. Sem mudança. Não
  há perda de feedback.
- **Inconsistência com o test `_disabled`**: o test
  `test_inline_edit_blocks_when_sum_neq_100` falhará
  quando reativado. Aceito — o rework da suíte e2e é
  escopo separado.

## Open Questions

_Nenhuma. Os decisions cobrem o escopo. O BDD cenário é
direto; o fix no client é mecânico._
