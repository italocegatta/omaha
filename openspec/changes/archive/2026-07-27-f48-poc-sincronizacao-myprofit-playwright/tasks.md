## 1. Estrutura e configuração segura

### Conclusão experimental sanitizada — 2026-07-27

- Playwright via WSL recebeu `403` antes do login; login normal no navegador funcionou.
- Nenhum modal 2FA foi observado ao vivo; nenhum bypass foi tentado.
- Código e testes F48 foram removidos, junto com toda configuração, taskipy e allow-list exclusivos da PoC.

- [x] 1.1 Definir módulo/script isolado da PoC e comando de execução manual, sem adicionar fluxo à aplicação web.
- [x] 1.2 Adicionar `MYPROFIT_EMAIL` e `MYPROFIT_PASSWORD` ao `.env.example` sem valores reais e validar falha antes de iniciar navegador quando ausentes.
- [x] 1.3 Garantir que logs, exceções, traces, screenshots e argumentos de processo não exponham credenciais ou conteúdo financeiro.

## 2. Navegação assistida no MyProfit

- [x] 2.1 Implementar login usando `#email`, `#password` e `#buttonLogin`; parar e pedir confirmação do owner após validar redirecionamento.
- [x] 2.2 Implementar detecção limitada do modal opcional `+ Segurança pra você!`; clicar `Mais tarde` somente quando o botão estiver visível; pedir confirmação do owner após validar comportamento com e sem modal.
- [x] 2.3 Implementar navegação para `https://myprofitweb.com/App/StockDetail.aspx`; parar e pedir confirmação do owner antes de automatizar exportação.
- [x] 2.4 Abrir `button[aria-label="Export"]`, selecionar `a.dropdown-item[data-type="csv"]` e capturar download com `page.expect_download()` após confirmação do owner.

## 3. Validação do CSV sem persistência

- [x] 3.1 Salvar download apenas em diretório temporário, ler bytes, validar UTF-8 e remover artefato temporário após uso.
- [x] 3.2 Passar conteúdo capturado por `parse_positions` e retornar diagnóstico de sucesso, vazio, encoding inválido ou nenhuma posição reconhecida.
- [x] 3.3 Provar por teste que a PoC não chama endpoints de importação e não grava `Asset`, `Position` ou `ImportPreview`.

## 4. Testes e encerramento da PoC

- [x] 4.1 Criar testes offline para configuração, seleção condicional do modal, captura simulada do download e compatibilidade com fixture CSV existente.
- [x] 4.2 Garantir que suite padrão não acessa `myprofitweb.com` e que navegação real seja opt-in/manual.
- [x] 4.3 Rodar lint e testes definidos pelo repositório usando tarefas taskipy; registrar limitações observadas no MyProfit.
