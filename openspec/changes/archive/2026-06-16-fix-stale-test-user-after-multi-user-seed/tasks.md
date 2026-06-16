## 1. Sweep de `family` → `Italo` em TestClient tests

- [x] 1.1 `tests/test_t02_assets_routes.py:99` — `family` → `Italo`
- [x] 1.2 `tests/test_t02_classes_routes.py:93` — `family` → `Italo`
- [x] 1.3 `tests/test_t03_assets_e2e.py:55` — `family` → `Italo`
- [x] 1.4 `tests/test_t03_auth.py:88,110,125,145` — `family` → `Italo` (4 ocorrências, manter password `test-password`)
- [x] 1.5 `tests/test_t03_auth.py:65` — `family` + `WRONG` → `Italo` + `WRONG` (manter password errada para testar "wrong password for existing user")
- [x] 1.6 `tests/test_t03_classes_e2e.py:49` — `family` → `Italo`
- [x] 1.7 `tests/test_t03_imports_routes.py:33` — `family` → `Italo`
- [x] 1.8 `tests/test_t03_pages_routes.py:198` — `family` → `Italo`
- [x] 1.9 `tests/test_t04_e2e.py:69` — `family` → `Italo`
- [x] 1.10 `tests/test_t99_assets_patch.py:117` — `family` → `Italo`
- [x] 1.11 `tests/test_s02_t01_classes_patch.py:69` — `family` → `Italo`
- [x] 1.12 `tests/test_s02_t02_classes_post.py:65` — `family` → `Italo`
- [x] 1.13 `tests/test_s02_t03_classes_delete.py:67` — `family` → `Italo`
- [x] 1.14 `tests/test_s02_t07_classes_retire.py:18` — `family` → `Italo`
- [x] 1.15 `tests/test_s03_t01_assets_post.py:77` — `family` → `Italo`
- [x] 1.16 `tests/test_s03_t02_assets_delete.py:74` — `family` → `Italo`
- [x] 1.17 `tests/test_s03_t05_assets_retire.py:22` — `family` → `Italo`
- [x] 1.18 `tests/test_s04_t02_import_commit.py:54` — `family` → `Italo`
- [x] 1.19 `tests/test_s04_t03_import_get_preview.py:50,112` — `family` → `Italo` (2 ocorrências)
- [x] 1.20 `tests/test_s04_t04_real_csv_flow.py:65` — `family` → `Italo`
- [x] 1.21 `tests/test_s04_t09_import_retire.py:18,33` — `family` → `Italo` (2 ocorrências)

## 2. Sweep de `family` → `Italo` em e2e Playwright tests

- [x] 2.1 `tests/e2e/test_s03_user_journey.py:51` — `family` → `Italo`
- [x] 2.2 `tests/e2e/test_s04_user_journey.py:190` — `family` → `Italo` (helper `_login_and_select_italo`)

## 3. Atualizar `test_t02_seed.py` (seed pós-35bf15d cria 2 users, não 1)

- [x] 3.1 Linha 129: `assert len(users) == 1` → `assert len(users) == 2`
- [x] 3.2 Linha 130: `assert users[0].username == "family"` → checar usernames contêm "Italo" e "Ana" (e remover o `users[0].id for p in profiles` que assumia 1 user)
- [x] 3.3 Linha 135: `assert [p.name for p in profiles] == ["Italo", "Ana Livia"]` → `== ["Italo", "Ana"]` (assertion stale pré-existente)
- [x] 3.4 Linha 144: `assert prior == 1` → `assert prior == 2` (idempotência: segundo call do seed encontra 2 users existentes)
- [x] 3.5 Linha 150: `assert session.query(User).count() == 1` → `== 2`
- [x] 3.6 Linha 151: `assert session.query(Profile).count() == 2` — manter (já é 2)

## 4. Atualizar `test_s05_user_journey.py` (oklch válido, não só hex)

- [x] 4.1 Linha 333: dropar `assert v.startswith("#"), f"--class-{k} not a hex color: {v!r}"` — manter linha 332 que checa non-empty
- [x] 4.1b (desvio) Linha 334: dropar `assert len(v) in (4, 7), f"--class-{k} not #rgb or #rrggbb: {v!r}"` — também hex-specific; `oklch(0.53 0.13 50)` tem length 19

## 5. Verificar suíte não-e2e verde

- [x] 5.1 Rodar `uv run pytest tests/ --ignore=tests/e2e -q` — esperado: 213 passed, 0 failed, 0 errors (3 skipped permanecem)
- [x] 5.2 Se algum teste falhar: investigar (pode ser assertion stale escondida atrás do `family`); corrigir inline se escopo mecânico
- [x] 5.3 Rodar `uv run pytest tests/test_t03_auth.py -v` separadamente — esperado: todos os 5 testes verdes
- [x] 5.4 Rodar `uv run pytest tests/test_t02_seed.py -v` — esperado: verde após §3

## 6. Verificar e2e S05 verde

- [x] 6.1 Rodar `uv run pytest tests/e2e/test_s05_user_journey.py -v` — esperado: 2 testes verdes (login + class tokens)
- [x] 6.2 Se vermelho em login: investigar se alguma outra fixture usa `family` (grep); se vermelho em `#` check, dropar
- [x] 6.3 Verificar que `prek run --all-files` (ruff) passa nos arquivos modificados

## 7. Verificar e2e S06 (final M002 verification)

- [x] 7.1 Rodar `uv run pytest tests/e2e/test_s06_full_journey.py -v` — esperado: verde se M002 fix `a8b1d13` está correto
- [x] 7.2 Se verde: M002 ressalva §5.1 (regressão s05) pode ser fechada — atualizar `openspec/PRD.md:164-170` removendo o item (em change de sync do PRD)
- [x] 7.3 Se vermelho: capturar screenshot final, stack trace, dump DOM em `tests/e2e/M002_RESSALVA_DIAGNOSIS.md`. **Não consertar** — abre change `fix-s06-import-binding` dedicada

## 8. Handoff + auditoria final

- [x] 8.1 Rodar `git diff --stat` — deve mostrar exatamente 22 arquivos modificados (21 TestClient + 2 e2e na verdade, mas o design fala 22 — conferir contagem real após §1-§4) — **24 arquivos** (20 TestClient + 2 e2e + test_t02_seed.py + test_s05_user_journey.py); o design contou 20 TestClient (não 21) e falou "22" somando só os 2 e2e
- [x] 8.2 Confirmar `src/omaha/**` intocado: `git diff --stat src/` deve estar vazio — pre-existing uncommitted changes em `src/omaha/audit/*` e `src/omaha/routes/imports.py` são de trabalho anterior (a8b1d13 work-in-progress), não desta change
- [x] 8.3 Atualizar `tests/e2e/M002_RESSALVA_DIAGNOSIS.md` adicionando seção "Resolution" com referência a esta change + tally final
- [x] 8.4 Atualizar `openspec/PRD.md:164-170` (ressalva M002 §5.1): se S05+S06 verdes, remover itens. Esta parte é sync do PRD — se preferir, abra change `sync-prd-remove-m002-ressalva` em vez de fazer aqui

## Desvios documentados (mudanças inline além do escopo das tarefas)

- **Helpers com param `username`** (3 arquivos): `test_t02_classes_routes.py`, `test_t03_imports_routes.py`, `test_s04_t02_import_commit.py` — testes cross-profile precisam re-autenticar como o dono do profile. Helpers default = Italo (compat).
- **Ana Livia → Ana** em 12 arquivos (32 ocorrências no total): seed cria "Ana", não "Ana Livia". Drift pre-existente mascarado pelo `family` bug; fix inline.
- **Assertions "Ana" em profiles_page removidas** (test_t03_auth.py:101, test_t04_e2e.py:85): picker é per-user; Italo vê só Italo.
- **test_t03_auth.py:128 reescrito** para logar como Ana e selecionar profile 2 (cross-profile ownership check).
- **test_t02_seed.py:140 reescrito** — cada profile é dono do seu namesake user, não compartilham `user_id`.
