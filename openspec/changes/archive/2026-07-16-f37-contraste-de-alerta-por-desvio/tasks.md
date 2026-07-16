## 1. Simplificar lógica de severidade (JS)

- [x] 1.1 Alterar `severityForDelta()` no Alpine store `classSum` (`_patrimonio_add_asset_modal.html` ~linha 1527): remover tier `warn`, retornar `'danger'` para qualquer `abs > 0.01`. Nova lógica: `<=0.01 → ok, else danger`
- [x] 1.2 Atualizar comentário acima de `severityForDelta` (~linha 1523) para refletir 2-tier em vez de 3-tier

## 2. Remover regras CSS warn do sistema de alerta

- [x] 2.1 Remover bloco CSS `.asset-allocation-alert--warn, .asset-allocation-alert-class--warn, .asset-group-header-alert--warn` (`app.css` ~linhas 1443-1449)
- [x] 2.2 Verificar que regras `--ok` e `--danger` permanecem intactas

## 3. Atualizar spec principal

- [x] 3.1 Atualizar `openspec/specs/asset-allocation-alerts/spec.md` requirement "Severity coloring": mudar de 3-tier para 2-tier, remover cenários "Small deviation uses warn color", atualizar cenário "Large deviation uses danger color" para cobrir todo desvio > 0.01

## 4. Verificação

- [x] 4.1 Rodar `task test-unit` — garantir zero regressão
- [ ] 4.2 Rodar `task serve` e verificar visualmente que badges de desvio aparecem vermelhos (não amber)
- [ ] 4.3 Verificar que badge OK (verde) permanece para classes on-target
