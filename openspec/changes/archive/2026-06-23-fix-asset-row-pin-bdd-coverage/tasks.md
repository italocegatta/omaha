## 1. Adicionando step ordinal + cenário row-pin

- [x] 1.1 Em `tests/bdd/step_defs/dashboard_steps.py`, adicionar o step `@then(parsers.parse('o ativo "{ticker}" é o {ordinal:d}º da classe "{class_name}"'))` que localiza a N-ésima linha da classe e assere que o nome é o esperado.

- [x] 1.2 Em `tests/bdd/features/asset_crud.feature`, adicionar (após o cenário "Per-class sum off-100 é aceito (D006)" existente) um novo `Esquema do Cenário: Edição inline preserva a posição visual da linha (row pin)`. Setup: criar classe "RF Test" 100% + 3 ativos "Alpha" 10%, "Bravo" 20%, "Charlie" 30% (soma per-classe 60). Ação: clicar na célula "Alocação alvo da carteira" do ativo "Alpha" (linha 1 do sort `target_pct` asc), digitar "80", pressionar "Enter" (soma resultante 80+20+30=130, "Sobra 70%"). Asserts: `o ativo "Alpha" é o 1º da classe "RF Test"` E `a alocação salva do ativo "Alpha" é "80.00%"`. Cobre Italo + Ana via `Exemplos`.

- [ ] 1.3 Cenário "row pin é liberado no próximo clique de sort" — descartado nesta change; o release-on-sort é trivial (`sortBy` zera o freeze) e o risco de regressão é baixo. Pode entrar em change futura se houver sinal de bug nessa transição.

## 2. Verificação

- [x] 2.1 Rodar `uv run task test-bdd` e confirmar que o cenário novo passa. (5/5 runs OK quando estável; **flakiness pre-existente** confirmada em 5 runs sem este change: 2/5 falham em `test_italo_classes_invisible_to_ana` e `test_full_journey_import_modal` — mesma classe de flake, suite-wide, não regressão deste change.)
- [x] 2.2 Rodar `uv run task lint` para garantir formatação.
- [x] 2.3 Rodar `uv run task test-unit` (124) e `uv run task test-integration` (192) para confirmar zero regressão.
- [x] 2.4 Rodar `openspec validate fix-asset-row-pin-bdd-coverage` para coerência dos artefatos.

## 3. Finalização

- [x] 3.1 Arquivar a change após validação.
