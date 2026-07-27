## Why

Omaha importa posições por CSV, mas hoje o operador precisa entrar no MyProfit,
navegar até a posição e baixar o arquivo manualmente. Esta fatia reduz risco de
integração validando, em uma PoC isolada, se o fluxo autenticado e o download
podem ser automatizados com Playwright sem alterar banco ou UI de produção.

## What Changes

- Criar PoC Playwright Python para login no MyProfit usando seletores observados:
  `#email`, `#password` e `#buttonLogin`.
- Tratar modal opcional de configuração do 2FA clicando em `Mais tarde` quando
  estiver presente; continuar normalmente quando não estiver presente.
- Navegar para `App/StockDetail.aspx`, abrir Export e selecionar CSV.
- Capturar o download automático com Playwright e disponibilizar seus bytes para
  validação.
- Validar o arquivo baixado com o parser CSV existente, sem persistir posições.
- Documentar variáveis de credencial no `.env.example`; valores reais ficam
  somente no `.env` local e nunca entram em código, logs, traces ou screenshots.
- Registrar testes determinísticos para parser/captura usando fixture, sem
  depender do MyProfit em CI.
- Não criar ainda botão `Sincronizar`, job de produção, endpoint, polling,
  commit de importação ou alteração de banco.

## Capabilities

### New Capabilities

- `myprofit-position-csv-poc`: PoC assistida para autenticar no MyProfit e
  capturar o CSV de posição para validação local.

### Modified Capabilities

- Nenhuma. A integração com o modal de importação será uma fatia posterior.

## Impact

- Código de PoC sob `scripts/` ou módulo dedicado de integração e testes
  associados.
- `.env.example` e configuração para nomes de variáveis MyProfit sem valores
  secretos.
- Playwright Python já está em `pyproject.toml`; não há framework novo previsto.
- Dependência externa: disponibilidade do MyProfit, estabilidade dos seletores,
  sessão autenticada e download CSV.
- A execução da PoC será acompanhada pelo owner etapa a etapa. O agente não deve
  inferir ou automatizar etapas adicionais do site sem confirmação explícita.
