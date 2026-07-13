## 1. Extração de helpers compartilhados

- [x] 1.1 Criar pacote `tests/support/` com helpers pequenos para cleanup de DB, bootstrap de browser/uvicorn e setup do fluxo de import.
- [x] 1.2 Extrair primitive compartilhada de wipe em `scripts/seed_from_csv/` e manter `modes.py` como camada de orquestração.

## 2. Rewire dos consumidores

- [x] 2.1 Trocar `tests/conftest.py`, `tests/e2e/conftest.py`, `tests/bdd/conftest.py` e `tests/visual/conftest.py` para usar wrappers finos sobre helpers compartilhados.
- [x] 2.2 Trocar `tests/e2e/test_import_user_journey.py` para reutilizar helpers compartilhados de login, criação de classes, seed de assets e debug dump.
- [x] 2.3 Remover duplicação residual e ajustar imports internos sem mudar nomes de fixtures, ports, DB paths ou asserts.

## 3. Verificação

- [x] 3.1 Rodar suíte focada dos helpers e do seed mode para confirmar wipe, bootstrap e importações novas.
- [x] 3.2 Rodar testes afetados de e2e, bdd e visual e confirmar que isolamento, ports e contagens finais continuam iguais.
- [x] 3.3 Revisar diff final para garantir que a mudança ficou restrita a setup/wipe compartilhado.
