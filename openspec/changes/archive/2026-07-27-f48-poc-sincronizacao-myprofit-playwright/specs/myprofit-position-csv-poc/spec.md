## ADDED Requirements

### Requirement: PoC usa credenciais exclusivamente do ambiente

A PoC SHALL ler e-mail/CPF e senha a partir de `MYPROFIT_EMAIL` e
`MYPROFIT_PASSWORD`, disponíveis no ambiente carregado de `.env`. A PoC MUST
falhar antes de abrir o navegador quando qualquer variável estiver ausente e
MUST NOT imprimir os valores em logs, mensagens de erro, screenshots ou traces.

#### Scenario: Credenciais ausentes interrompem execução

- **WHEN** `MYPROFIT_EMAIL` ou `MYPROFIT_PASSWORD` não está definido
- **THEN** a PoC falha com erro orientando configurar `.env`
- **AND** nenhum navegador é iniciado

#### Scenario: Credenciais presentes não aparecem no output

- **WHEN** a PoC é executada com as duas variáveis configuradas
- **THEN** o fluxo usa os valores para preencher o formulário
- **AND** logs e erros não contêm e-mail/CPF nem senha

### Requirement: PoC autentica usando fluxo observado

A PoC SHALL navegar para `https://myprofitweb.com/Login.aspx`, preencher
`#email` e `#password`, e acionar `#buttonLogin`. Após o login, SHALL aceitar o
redirecionamento para a área autenticada.

#### Scenario: Login redireciona para área MyProfit

- **WHEN** credenciais válidas são submetidas
- **THEN** o botão `#buttonLogin` é acionado uma vez
- **AND** a navegação chega à área `https://myprofitweb.com/App/`

### Requirement: Modal opcional de 2FA é recusado quando presente

Se o modal opcional de configuração de 2FA estiver visível, a PoC SHALL clicar
no botão visível com texto `Mais tarde` (`button.bootbox-cancel`) e continuar.
Se o modal não aparecer, a PoC SHALL continuar sem erro e sem aguardar
indefinidamente.

#### Scenario: Modal de segurança aparece

- **WHEN** o diálogo `+ Segurança pra você!` aparece após o login
- **THEN** a PoC clica no botão `Mais tarde`
- **AND** o fluxo continua para a página autenticada

#### Scenario: Modal de segurança não aparece

- **WHEN** nenhum diálogo opcional é exibido após o login
- **THEN** a PoC não tenta clicar em elemento inexistente
- **AND** o fluxo continua dentro do timeout definido

### Requirement: PoC captura CSV de posição

A PoC SHALL navegar para `https://myprofitweb.com/App/StockDetail.aspx`, clicar
no controle `button[aria-label="Export"]` e selecionar
`a.dropdown-item[data-type="csv"]`. O clique CSV SHALL ser envolvido por captura
de download do Playwright.

#### Scenario: Exportação inicia download automático

- **WHEN** a página StockDetail está carregada e o menu Export é aberto
- **THEN** a opção `CSV` é selecionada
- **AND** um arquivo é capturado pelo evento de download
- **AND** o conteúdo capturado fica disponível como bytes para validação

#### Scenario: Exportação não produz download

- **WHEN** o clique CSV termina sem evento de download dentro do timeout
- **THEN** a PoC falha identificando a etapa de exportação
- **AND** não grava dados parcialmente capturados no repositório

### Requirement: CSV capturado é compatível com parser existente

A PoC SHALL passar os bytes capturados pelo mesmo caminho de decodificação UTF-8
e `parse_positions` usado pela importação, sem recomputar valores e sem gravar
`Asset`, `Position` ou `ImportPreview`.

#### Scenario: CSV MyProfit tem estrutura compatível

- **WHEN** o download contém CSV UTF-8 com posições reconhecidas
- **THEN** `parse_positions` retorna ao menos uma posição
- **AND** a PoC informa sucesso de validação
- **AND** nenhuma linha é persistida no banco

#### Scenario: CSV inválido ou vazio

- **WHEN** o download está vazio, não é UTF-8 ou não contém posições
- **THEN** a PoC falha com diagnóstico específico de validação
- **AND** nenhuma linha é persistida no banco

### Requirement: Execução externa é assistida e offline por padrão

A PoC SHALL possuir testes offline para configuração, decisões condicionais,
captura simulada e compatibilidade do parser. A navegação real no MyProfit MUST
ser opt-in e a implementação/calibração de cada etapa SHALL ser confirmada pelo
owner antes da etapa seguinte ser automatizada.

#### Scenario: Suite de testes não acessa MyProfit

- **WHEN** a suite padrão de testes é executada
- **THEN** nenhum request é enviado ao domínio `myprofitweb.com`
- **AND** testes usam doubles ou fixtures locais

#### Scenario: Owner não confirmou próxima etapa

- **WHEN** uma etapa do fluxo ainda não foi observada ou aprovada pelo owner
- **THEN** a PoC não adiciona automação para essa etapa
- **AND** a execução para com contexto suficiente para retomada assistida
