## Why

O merge `849749f` (merge milestone/M002 → main) resolveu conflito em `dashboard.html` mantendo a versão da main antiga (288 linhas), descartando a versão do branch M002 (1281 linhas) que continha o modal de import, botão "Importar CSV", e demais funcionalidades do workspace M002.

Resultado: o botão de import sumiu da interface e todos os recursos M002 no dashboard foram perdidos.

## What Changes

- **Restaurar** `dashboard.html` para o estado M002 (versão do commit `a8b1d13`, 1281 linhas), que inclui:
  - Botão "Importar CSV" + modal de import com 2 steps (upload + review/commit)
  - Edição inline do target % da classe
  - Botão × para remover classe com confirmação
  - Seções colapsáveis (chevron)
  - Formulário inline "+ Ativo" por classe
  - Botão × para remover ativo com confirmação
  - Total da soma de classes (class-summary-total)
  - Alpine stores `classSum` e `importModal`
- **Reaplicar** o fix `a8b1d13` (select binding `x-init $nextTick` + `x-effect`) sobre a versão restaurada
- **Verificar** se existe dano colateral em `app.css`, `routes/`, ou testes que também foram afetados pelo merge

## Capabilities

### New Capabilities

- `import-modal`: Modal de import CSV com upload, revisão (auto-matched + unmatched), e commit — substitui as páginas standalone /import e /import/review (que redirecionam para /)
- `dashboard-inline-editing`: Edição inline de target % de classes e ativos, criação e remoção de ativos diretamente no dashboard

### Modified Capabilities

- `import-modal-class-binding`: Reqs já definidas e corretas; spec não muda — apenas re-ativar a implementação
- `import-class-auto-suggest`: Reqs já definidas e corretas; spec não muda — apenas re-ativar a implementação

## Impact

- `src/omaha/templates/dashboard.html` — ~1000 linhas restauradas
- `src/omaha/static/app.css` — CSS do modal + inline editing (pode estar intacto, verificar)
- `src/omaha/routes/imports.py` — rotas /import e /import/review já redirecionam para / (não precisa mudar)
- Testes: `tests/e2e/test_s04_*`, `tests/e2e/test_s06_*` — devem passar após restauração
