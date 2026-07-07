# language: pt
Funcionalidade: CRUD de classes via formulário inline e PATCH
  Como operador da carteira
  Eu quero criar e ajustar a alocação alvo das classes
  Para refletir a estratégia da família

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Inline create 2 classes — soma 100%
    Dado que estou logado como "<profile>"
    E criei as 2 classes padrão RF Pós 50% e RF Dinâmica 50%
    Então o dashboard mostra 2 seções de classe
    E a seção "RF Pós" mostra "50%"
    E a seção "RF Dinâmica" mostra "50%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Inline create 2 classes — soma 90%
    Dado que estou logado como "<profile>"
    E criei as 2 classes padrão RF Pós 60% e RF Dinâmica 30%
    Então o dashboard mostra 2 seções de classe
    E a seção "RF Pós" mostra "60%"
    E a seção "RF Dinâmica" mostra "30%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Inline create 2 classes — soma 110%
    Dado que estou logado como "<profile>"
    E criei as 2 classes padrão RF Pós 70% e RF Dinâmica 40%
    Então o dashboard mostra 2 seções de classe
    E a seção "RF Pós" mostra "70%"
    E a seção "RF Dinâmica" mostra "40%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Inline add + PATCH class target
    Dado que estou logado como "<profile>"
    E criei a classe "Reserva" com "10%"
    Então o dashboard mostra 1 seções de classe
    Quando clico no campo "Alocação alvo da carteira" da classe "Reserva"
    E digito "15"
    E pressiono "Enter"
    Então a seção "Reserva" mostra "15%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Negative — duplicate class name
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando clico em "Nova classe"
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    Então o modal de classe mostra a mensagem de erro "Já existe"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
