# language: pt
Funcionalidade: Importação de posições via modal
  Como operador da carteira
  Eu quero fazer upload de um CSV de posições
  Para popular a carteira com dados do broker

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Import 4-row CSV happy (revisão de classe sugerida)
    Dado que estou logado como "<profile>"
    E criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%
    Quando abro o modal "Importar posições"
    E seleciono o arquivo "tiny_portfolio.csv"
    Então o modal mostra 4 linhas não correspondidas
    Quando clico em "Confirmar"
    Então o dashboard mostra 4 linhas de ativos
    E a seção "RF Pós" contém 2 ativos
    E a seção "RF Dinâmica" contém 2 ativos

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Import CSV vazio
    Dado que estou logado como "<profile>"
    Quando abro o modal "Importar posições"
    E seleciono o arquivo "tiny_empty.csv"
    Então o modal mostra a mensagem de erro "reconhecida"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
