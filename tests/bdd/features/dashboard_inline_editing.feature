# language: pt
Funcionalidade: Edição inline de target % sem fricção no dashboard
  Como operador da carteira
  Eu quero editar os campos de alocação alvo em um único clique
  Para que limpar e re-digitar salve zero (não 422) e o cursor já
  esteja no input logo após o clique

  Contexto:
    Dado o servidor de testes do BDD está no ar
    E o banco de dados de teste foi inicializado com a senha compartilhada
    E os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Esquema do Cenário: Clique único no alvo da classe foca o input
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando clico na pill "Alvo" da classe "RF Pós" com um único clique
    Então o input "class-inline-edit-input" da classe "RF Pós" está focado
    E o input "class-inline-edit-input" da classe "RF Pós" tem o valor pré-selecionado

    Exemplos:
      | profile |
      | Italo   |
      | Ana     |

  Esquema do Cenário: Clique único no alvo % classe do ativo foca o input
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "40%"
    E clico no campo alvo % classe do ativo "Tesouro Selic 2029" com um único clique
    Então o input "asset-inline-edit-input" do ativo "Tesouro Selic 2029" está focado

    Exemplos:
      | profile |
      | Italo   |
      | Ana     |

  Esquema do Cenário: Clique único no alvo % total do ativo foca o input
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "40%"
    E clico no campo alvo % total do ativo "Tesouro Selic 2029" com um único clique
    Então o input "asset-target-pct-total-edit-input" do ativo "Tesouro Selic 2029" está focado

    Exemplos:
      | profile |
      | Italo   |
      | Ana     |

  Esquema do Cenário: Limpar o alvo da classe e pressionar Enter salva zero
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "25%"
    Quando clico na pill "Alvo" da classe "RF Pós" com um único clique
    E limpo o input e pressiono "Enter"
    Então a alocação salva da classe "RF Pós" é "Alvo 0%"

    Exemplos:
      | profile |
      | Italo   |
      | Ana     |

  Esquema do Cenário: Limpar o alvo % classe do ativo e pressionar Enter salva zero
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "50%"
    Quando adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "12%"
    E clico no campo alvo % classe do ativo "Tesouro Selic 2029" com um único clique
    E limpo o input e pressiono "Enter"
    Então a alocação salva da célula alvo % classe do ativo "Tesouro Selic 2029" é "—"

    Exemplos:
      | profile |
      | Italo   |
      | Ana     |

  Esquema do Cenário: Limpar o alvo % total do ativo e pressionar Enter salva zero
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "25%"
    Quando adicionei o ativo "Tesouro Selic 2029" à classe "RF Pós" com "100%"
    E clico no campo alvo % total do ativo "Tesouro Selic 2029" com um único clique
    E limpo o input e pressiono "Enter"
    Então a alocação salva do ativo "Tesouro Selic 2029" é "—"
    E o derivado "Tesouro Selic 2029" na carteira é "—"

    Exemplos:
      | profile |
      | Italo   |
      | Ana     |

  Esquema do Cenário: Tirar o foco de input vazio da classe salva zero
    Dado que estou logado como "<profile>"
    E criei a classe "RF Pós" com "25%"
    Quando clico na pill "Alvo" da classe "RF Pós" com um único clique
    E limpo o input e tiro o foco
    Então a alocação salva da classe "RF Pós" é "Alvo 0%"

    Exemplos:
      | profile |
      | Italo   |
      | Ana     |
