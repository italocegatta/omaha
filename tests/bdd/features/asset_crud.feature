# language: pt
Funcionalidade: CRUD manual de ativos no dashboard
  Como operador da carteira
  Eu quero adicionar ativos diretamente pelo dashboard
  Para popular uma classe sem usar a importação CSV

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Manual add 4 ativos não-igual por classe
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "RF Dinâmica"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"

    Quando abro o formulário de ativo da classe "RF Pós"
    E preencho o campo "Nome do ativo" com "Tesouro Selic 2029"
    E preencho o campo "Alocação alvo" do modal de ativo com "60"
    E clico em "Adicionar ativo"
    E abro o formulário de ativo da classe "RF Pós"
    E preencho o campo "Nome do ativo" com "Tesouro Selic 2031"
    E preencho o campo "Alocação alvo" do modal de ativo com "40"
    E clico em "Adicionar ativo"

    E abro o formulário de ativo da classe "RF Dinâmica"
    E preencho o campo "Nome do ativo" com "Tesouro IPCA+ 2035"
    E preencho o campo "Alocação alvo" do modal de ativo com "30"
    E clico em "Adicionar ativo"
    E abro o formulário de ativo da classe "RF Dinâmica"
    E preencho o campo "Nome do ativo" com "Tesouro IPCA+ 2045"
    E preencho o campo "Alocação alvo" do modal de ativo com "70"
    E clico em "Adicionar ativo"

    Então o dashboard mostra 4 linhas de ativos
    E a seção "RF Pós" contém 2 ativos
    E a seção "RF Dinâmica" contém 2 ativos

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Negative — per-class sum != 100
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "Ações"
    E preencho o campo "Alocação alvo" com "100"
    E clico em "Salvar"
    Quando abro o formulário de ativo da classe "Ações"
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
