# language: pt
Funcionalidade: Ajuste da alocação alvo (PATCH)
  Como operador da carteira
  Eu quero ajustar a alocação alvo de cada classe e de cada ativo
  Para refletir uma rebalanceação manual sem recriar a carteira

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: PATCH per-class target reflects in dashboard
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    Quando clico no campo "Alocação alvo da carteira" da classe "RF Pós"
    E digito "70"
    E pressiono "Enter"
    Então a alocação salva da classe "RF Pós" é "70%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: PATCH per-asset target reflects in dashboard
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    E abro o formulário de ativo da classe "RF Pós"
    E preencho o campo "Nome do ativo" com "Tesouro Selic 2029"
    E preencho o campo "Alocação alvo" do modal de ativo com "100"
    E clico em "Adicionar ativo"
    Quando clico no campo "Alocação dentro da classe" do ativo "Tesouro Selic 2029"
    E digito "70"
    E pressiono "Enter"
    Então a alocação salva do ativo "Tesouro Selic 2029" é "70%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Validação sum != 100 per-class
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "Ações"
    E preencho o campo "Alocação alvo" com "100"
    E clico em "Salvar"
    E abro o formulário de ativo da classe "Ações"
    E preencho o campo "Nome do ativo" com "PETR4"
    E preencho o campo "Alocação alvo" do modal de ativo com "60"
    E clico em "Adicionar ativo"
    E abro o formulário de ativo da classe "Ações"
    E preencho o campo "Nome do ativo" com "VALE3"
    E preencho o campo "Alocação alvo" do modal de ativo com "50"
    E clico em "Adicionar ativo"
    Então o modal de ativo mostra a mensagem de erro "100"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
