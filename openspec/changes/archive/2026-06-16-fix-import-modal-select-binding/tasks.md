## 1. Substituir o binding do select no template do modal

- [x] 1.1 Trocar `<select :value="getClassId(...)" @change="setClassId(...)">` por `<select x-model="assignments[row.broker_ticker].class_id">` na seção "Ativos existentes" (auto-matched) — `src/omaha/templates/dashboard.html:510-517`
- [x] 1.2 Trocar o mesmo binding na seção "Novos ativos" (unmatched) — `src/omaha/templates/dashboard.html:554-561`
- [x] 1.3 Verificar que o `data-testid` em cada `<select>` continua `import-existing-class` e `import-assignment-class` (não muda)
- [x] 1.4 Verificar que os `data-testid` dos inputs de asset_name (`import-existing-name`, `import-assignment-name`) continuam usando `:value`+`@input` — não precisam de `x-model` porque o `setAssetName` faz Object.assign, mas confirmar que continuam funcionando

## 2. Limpar o store Alpine

- [x] 2.1 Localizar todos os usos de `getClassId` e `setClassId` em `src/omaha/templates/dashboard.html` (grep) para confirmar que nenhum outro trecho chama esses métodos
- [x] 2.2 Remover o método `getClassId` do store Alpine (linhas 1133-1136) — agora redundante
- [x] 2.3 Remover o método `setClassId` do store Alpine (linhas 1137-1141) — agora redundante
- [x] 2.4 Confirmar que `commit()` continua lendo `self.assignments[ticker].class_id` corretamente (deve continuar funcionando porque `x-model` popula esse mesmo campo)

## 3. Atualizar e2e para validar o DOM real

- [x] 3.1 Em `tests/e2e/test_s06_full_journey.py`, substituir o `page.evaluate` que seta `s.assignments[ticker].class_id = X` para linhas com match (linhas 366-388) por uma asserção no `select.value` do DOM: `page.locator(f'[data-testid="import-assignment-class"]').nth(i).input_value() == expected_id`
- [x] 3.2 Manter o `page.evaluate` para as linhas SEM match (BR Dividendos, Cripto, (Não configurado)) — esse é um caso legítimo de override manual, não uma máscara do bug
- [x] 3.3 Adicionar uma asserção nova logo após o upload (antes do commit) que confirma `select.value` correto para pelo menos uma linha auto-matched e uma unmatched com match

## 4. Verificar

- [x] 4.1 Inspecionar o dashboard no browser (manual ou via curl + render) para confirmar que o `<select>` agora tem `value` correto quando o modal abre
- [x] 4.2 Conferir que `commit()` ainda funciona (revisão de código, sem precisar rodar e2e aqui)
- [x] 4.3 Atualizar a change anterior `fix-import-class-suggestion` (opcional): linkar a esta change na seção de "Issues discovered after applying" para rastreabilidade
