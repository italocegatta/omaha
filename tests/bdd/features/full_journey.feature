# language: pt
Funcionalidade: Jornada completa do operador em uma única sessão
  Como Italo, operador da carteira
  Eu quero configurar 2 classes com 2 ativos cada via interface
  Para validar que o fluxo login → classe → ativo funciona de ponta a ponta

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Cenário: Jornada completa via modal de importação (perfil "Italo")
    Dado que estou logado como "Italo"
    E criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%
    Quando abro o modal "Importar posições"
    E seleciono o arquivo "tiny_portfolio.csv"
    E clico em "Enviar"
    Então o modal mostra 0 linhas não correspondidas
    Quando clico em "Confirmar"
    Então o dashboard mostra 4 linhas de ativos
    E a seção "RF Pós" contém 2 ativos
    E a seção "RF Dinâmica" contém 2 ativos
