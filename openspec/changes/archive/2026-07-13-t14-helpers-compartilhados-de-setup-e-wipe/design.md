## Context

O harness de testes repete lógica de bootstrap, cleanup e lifecycle em vários pontos: `tests/conftest.py` prepara DB seguro e seed de sessão; `tests/e2e/conftest.py`, `tests/bdd/conftest.py` e `tests/visual/conftest.py` repetem variações de browser/uvicorn/wipe; `tests/e2e/test_import_user_journey.py` carrega setup de fluxo manualmente; `scripts/seed_from_csv/modes.py` mantém wipe destrutivo próprio.

Objetivo aqui é centralizar suporte compartilhado, não mudar contrato visível. Nomes de fixtures, ports, DBs, seletors, dados seed e asserts continuam iguais.

## Goals / Non-Goals

**Goals:**
- Centralizar helpers comuns de bootstrap, browser e cleanup.
- Reutilizar mesma primitive de wipe entre suítes de teste e seed reset.
- Reduzir duplicação e risco de drift sem alterar semântica.
- Manter conftests como pontos de integração/fixture.

**Non-Goals:**
- Sem mudança de comportamento do app, rotas, templates ou seed data.
- Sem mudar ports, URLs, DB paths, TTLs, browser args ou cookie/session semantics.
- Sem alterar asserts do import journey ou marker rules.
- Sem tocar slices fora de setup/wipe compartilhado.

## Decisions

1. Criar pacote `tests/support/` com módulos pequenos por domínio.
   - `db.py` para primitives de cleanup de SQLite e bootstrap seguro de DB.
   - `browser.py` para resolve/launch/shutdown de chromium e uvicorn.
   - `import_flow.py` para login/class/asset seeding do fluxo S04.
   - Alternativa: um helper único gigante. Rejeitado porque aumenta acoplamento e risco de import cycles.

2. Manter `conftest.py` como camada fina de pytest.
   - As fixtures continuam localizadas onde pytest as descobre hoje.
   - Alternativa: mover fixtures para suporte compartilhado e importar via alias. Rejeitado porque piora leitura e deixa descoberta mais frágil.

3. Extrair wipe destrutivo do seed para helper interno compartilhado.
   - `scripts/seed_from_csv/modes.py` passa a compor primitives, não duplicar SQL.
   - Alternativa: duplicar wipe entre seed e testes. Rejeitada por drift e manutenção ruim.

4. Preservar ordem e defaults atuais como contrato.
   - `busy_timeout`, ports, host, args do Chromium, env vars e ordem de delete permanecem idênticos.
   - Alternativa: simplificar trocando defaults. Rejeitada porque seria mudança funcional disfarçada de refactor.

## Risks / Trade-offs

- [Import cycles entre `tests/support/*` e `conftest.py`] → manter suporte sem decorators pytest e com dependências em uma direção só.
- [Fixture resolution quebra após extração] → preservar nomes/signatures atuais e deixar wrappers em `conftest.py`.
- [Semântica de wipe diverge entre seed e tests] → usar mesma primitive interna e cobrir helper com teste focado.
- [Fragmentação excessiva] → parar no menor conjunto de módulos que remove duplicação real.

## Migration Plan

1. Criar módulos de suporte sem remover código antigo ainda.
2. Redirecionar conftests e import journey para helpers compartilhados.
3. Redirecionar `scripts/seed_from_csv/modes.py` para primitive compartilhada.
4. Remover duplicação residual depois de validar suíte alvo.
5. Rollback: reverter imports wrappers; helpers novos podem ficar sem uso até limpeza final.

## Open Questions

- Nenhuma bloqueante. Nomes exatos dos módulos podem seguir o menor conjunto que mantenha imports acíclicos.
