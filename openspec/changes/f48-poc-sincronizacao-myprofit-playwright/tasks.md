## 1. Estrutura e configuração segura

### Handoff checkpoint — 2026-07-21

- Entregue: módulo `scripts/myprofit_poc.py`, campos de configuração, `.env.example`, comando `task myprofit-poc` e testes offline.
- Verificado: `task test-one tests/test_myprofit_poc.py`, `task test-unit` e `task lint` passaram.
- Pausado por decisão do owner: nenhum login, navegação, modal 2FA ou exportação Playwright foi implementado/executado.
- Próxima etapa: implementar somente login headful assistido, sem exportação; pedir confirmação do owner antes de executar navegação real.
- Não fazer: pedir credenciais no chat, adicionar botão/UI, chamar endpoints de importação, gravar DB, habilitar trace ou salvar screenshots.

- [x] 1.1 Definir módulo/script isolado da PoC e comando de execução manual, sem adicionar fluxo à aplicação web.
- [x] 1.2 Adicionar `MYPROFIT_EMAIL` e `MYPROFIT_PASSWORD` ao `.env.example` sem valores reais e validar falha antes de iniciar navegador quando ausentes.
- [x] 1.3 Garantir que logs, exceções, traces, screenshots e argumentos de processo não exponham credenciais ou conteúdo financeiro.

## 2. Navegação assistida no MyProfit

- [x] 2.1 Implementar login usando `#email`, `#password` e `#buttonLogin`; parar e pedir confirmação do owner após validar redirecionamento.
- [x] 2.2 Implementar detecção limitada do modal opcional `+ Segurança pra você!`; clicar `Mais tarde` somente quando o botão estiver visível; pedir confirmação do owner após validar comportamento com e sem modal.
- [ ] 2.3 Implementar navegação para `https://myprofitweb.com/App/StockDetail.aspx`; parar e pedir confirmação do owner antes de automatizar exportação.
- [ ] 2.4 Abrir `button[aria-label="Export"]`, selecionar `a.dropdown-item[data-type="csv"]` e capturar download com `page.expect_download()` após confirmação do owner.

## 3. Validação do CSV sem persistência

- [x] 3.1 Salvar download apenas em diretório temporário, ler bytes, validar UTF-8 e remover artefato temporário após uso.
- [x] 3.2 Passar conteúdo capturado por `parse_positions` e retornar diagnóstico de sucesso, vazio, encoding inválido ou nenhuma posição reconhecida.
- [x] 3.3 Provar por teste que a PoC não chama endpoints de importação e não grava `Asset`, `Position` ou `ImportPreview`.

## 4. Testes e encerramento da PoC

- [x] 4.1 Criar testes offline para configuração, seleção condicional do modal, captura simulada do download e compatibilidade com fixture CSV existente.
- [x] 4.2 Garantir que suite padrão não acessa `myprofitweb.com` e que navegação real seja opt-in/manual.
- [x] 4.3 Rodar lint e testes definidos pelo repositório usando tarefas taskipy; registrar limitações observadas no MyProfit.
- [ ] 4.4 Atualizar roadmap para `Applied` somente após revisão do owner e registrar que PoC não inclui botão `Sincronizar` nem integração com modal.
