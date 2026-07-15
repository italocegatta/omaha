## Context

`tests/conftest.py` mantém duas allow-lists explícitas para classificação de markers:
- `_INTEGRATION_PREFIXES`: arquivos que usam TestClient, SessionLocal, ou DB → `@pytest.mark.integration`.
- `_UNIT_FILES`: arquivos de funções puras → `@pytest.mark.unit`.

Arquivos que não aparecem em nenhuma lista caem no default `unit` com warning `UnknownTestPath`. Dois arquivos que claramente pertencem à integration (`test_admin_recovery.py` e `test_db_mutations.py`) estão nesse limbo — rodam no unit lane incorretamente.

`test_db_snapshot.py` foi analisado: usa apenas `tmp_path` e `sqlite3` em arquivos temporários, sem `TestClient` nem `SessionLocal`. Docstring está correta. Não precisa de correção.

## Goals / Non-Goals

**Goals:**
- Mover `test_admin_recovery.py` e `test_db_mutations.py` para `_INTEGRATION_PREFIXES`.
- Eliminar `UnknownTestPath` warning para esses dois arquivos.
- Reduzir ~1.5s do unit lane (pre-commit).

**Non-Goals:**
- Alterar `test_db_snapshot.py` (genuinamente unit).
- Reescrever testes ou mudar comportamento de produto.
- Alterar a lógica de `pytest_collection_modifyitems`.

## Decisions

### D1 — Adicionar ao `_INTEGRATION_PREFIXES`, não mover arquivos

**Alternativas consideradas:**
1. Mover arquivos para `tests/integration/` — rejeitado: quebra imports relativos, exige atualizar paths em hooks/CI, e a convenção do repo é manter `tests/test_*.py` na raiz.
2. Adicionar `pytestmark = pytest.mark.integration` no topo dos arquivos — funcional, mas viola o contrato de allow-list explícita (o comment em conftest.py diz "location-based so we don't have to touch every existing test file").
3. Adicionar paths a `_INTEGRATION_PREFIXES` — escolhido: segue o padrão existente, uma linha por arquivo, revisável no diff.

**Rationale:** A opção 3 é a mais simples, reversível, e alinhada com o contrato documentado em `unit-test-effectiveness` spec.

### D2 — Ordem alfabética no tuple

Os entries em `_INTEGRATION_PREFIXES` estão em ordem alfabética. As duas novas entradas serão inseridas na posição correta:
- `"tests/test_admin_recovery.py"` → após `"tests/test_assets_trade_flags.py"` (já que `admin` < `assets`... wait, `a` < `a`, `d` < `s` → `admin` < `assets`). Posição: após `"tests/test_auth.py"` → na verdade `admin_recovery` < `auth` (d < u). Posição correta: após `"tests/test_assets_trade_flags.py"`, antes de `"tests/test_auth.py"`.
- `"tests/test_db_mutations.py"` → após `"tests/test_db_reset_both_profiles.py"`, antes de `"tests/test_e2e.py"`.

## Risks / Trade-offs

- **[Risco mínimo]** Adicionar 2 arquivos ao integration lane aumenta ~1.5s nesse gate. Absorvido pelo paralelismo (pytest-xdist). Trade-off aceitável: pre-commit fica mais rápido.
- **[Nenhum risco de regressão]** Nenhuma alteração em código de produção. Apenas classificação de markers.
