# language: pt
Funcionalidade: Importação de posições via modal
  Como operador da carteira
  Eu quero fazer upload de um CSV de posições
  Para popular a carteira com dados do broker

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Import 4-row CSV happy (auto-match por categoria)
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
    Quando abro o modal "Importar posições"
    E seleciono o arquivo "tiny_portfolio.csv"
    E clico em "Enviar"
    Então o modal mostra 0 linhas não correspondidas
    E clico em "Confirmar importação"
    Então o dashboard mostra 4 linhas de ativos
    E a seção "RF Pós" contém 2 ativos
    E a seção "RF Dinâmica" contém 2 ativos

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Import CSV vazio
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    Quando abro o modal "Importar posições"
    E seleciono o arquivo "tiny_empty.csv"
    E clico em "Enviar"
    Então o modal mostra a mensagem de erro "vazio"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
