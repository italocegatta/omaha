## Context

Omaha já usa Playwright Python para E2E e já possui `parse_positions` e
`POST /api/import/preview` para o CSV. O MyProfit exige uma sessão de navegador:
login em `Login.aspx`, possível modal opcional de configuração do 2FA, navegação
para `App/StockDetail.aspx` e dois cliques para iniciar o download CSV.

Esta é uma PoC de descoberta técnica, não uma entrega de produto. O owner
acompanhará cada avanço no site e confirmará os seletores antes de o agente
codificar a próxima etapa.

## Goals / Non-Goals

**Goals:**

- Confirmar login automatizado com credenciais vindas do ambiente.
- Confirmar tratamento idempotente do modal opcional `Mais tarde`.
- Confirmar navegação e captura do download automático.
- Entregar bytes CSV e demonstrar que o parser existente os reconhece.
- Manter execução reproduzível sem mutação de banco.

**Non-Goals:**

- Botão `Sincronizar`, endpoint, polling ou job persistente.
- Commit de posições ou chamada de `/api/import/preview` real.
- Armazenar cookies, senha, CSV financeiro ou trace no repositório.
- Bypassar CAPTCHA, 2FA real ou qualquer controle de segurança do MyProfit.
- Executar navegação externa automaticamente sem confirmação do owner.

## Decisions

- **Playwright Python:** reutilizar dependência e padrões já presentes em
  `tests/e2e/`; tem suporte nativo a sessão, locators e `expect_download`.
  Selenium adicionaria outra API e HTTP puro não modela com segurança o estado
  de uma página ASP.NET/WebForms.
- **Credenciais server-side:** usar `MYPROFIT_EMAIL` e `MYPROFIT_PASSWORD` do
  `.env`, carregados pela configuração existente. O browser recebe os valores
  somente durante a execução local da PoC; eles não aparecem em argumentos de
  linha de comando ou logs.
- **Seletores observados:** começar com `#email`, `#password`, `#buttonLogin`,
  `button[aria-label="Export"]` e `a.dropdown-item[data-type="csv"]`. O botão
  opcional será localizado por role/texto `Mais tarde`, limitado ao modal
  visível, para não clicar em elemento homônimo fora do diálogo.
- **Download como bytes:** envolver o clique em CSV com `page.expect_download()`;
  salvar em diretório temporário controlado, ler bytes, validar tamanho/encoding
  e apagar o arquivo temporário após a validação.
- **Validação sem persistência:** chamar `parse_positions` diretamente sobre o
  conteúdo capturado. A PoC não chama endpoints de importação e não abre sessão
  de banco para escrita.
- **Testes offline:** testar configuração, tratamento de modal, seletores e
  parser com doubles/fixture local. Navegação real será manual/opt-in, nunca
  requisito de CI.

## Risks / Trade-offs

- **[Seletores ou markup mudam]** -> centralizar seletores e falhar com mensagem
  clara contendo a etapa; atualizar somente após nova observação acompanhada.
- **[Modal opcional bloqueia o fluxo]** -> aguardar apenas um intervalo curto e
  seguir quando o modal não existir; não tratar ausência como erro.
- **[Download demora ou falha]** -> timeout explícito, erro por etapa e limpeza
  garantida do temporário; não tentar repetir login indefinidamente.
- **[Segredo vaza em artefato Playwright]** -> não habilitar trace por padrão,
  não registrar HTML/screenshots, mascarar mensagens e nunca incluir valores de
  ambiente em asserções ou relatórios.
- **[MyProfit bloqueia automação]** -> respeitar controles do site; parar e
  pedir decisão ao owner em vez de tentar contornar proteção.
- **[PoC confundida com sincronização pronta]** -> comando/documentação deixam
  explícito que não há persistência nem integração com o modal nesta fatia.
