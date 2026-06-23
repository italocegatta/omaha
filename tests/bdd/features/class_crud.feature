# language: pt
Funcionalidade: CRUD de classes via formulário snapshot, inline add e PATCH
  Como operador da carteira
  Eu quero criar e ajustar a alocação alvo das classes
  Para refletir a estratégia da família

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Snapshot create 2 classes
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    Quando abro o editor de classes
    E clico em "Adicionar classe"
    E preencho o campo "Nome da classe" da linha 0 com "RF Pós"
    E preencho o campo "Alocação alvo" da linha 0 com "50"
    E clico em "Adicionar classe"
    E preencho o campo "Nome da classe" da linha 1 com "RF Dinâmica"
    E preencho o campo "Alocação alvo" da linha 1 com "50"
    E clico em "Salvar classes"
    Então o dashboard mostra 2 seções de classe
    E a seção "RF Pós" mostra "50%"
    E a seção "RF Dinâmica" mostra "50%"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |

  Esquema do Cenário: Inline add + PATCH class target
    Dado que estou na página "/login"
    Quando preencho o campo "username" com "<profile>"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    E clico no botão do perfil "<profile>"
    E clico em "+ Nova classe"
    E preencho o campo "Nome da classe" com "Reserva"
    E preencho o campo "Alocação alvo" com "10"
    E clico em "Salvar"
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
    E preencho o campo "Nome da classe" com "RF Pós"
    E preencho o campo "Alocação alvo" com "50"
    E clico em "Salvar"
    Então o modal mostra a mensagem de erro "Já existe"

    Exemplos:
      | profile   |
      | Italo     |
      | Ana |
