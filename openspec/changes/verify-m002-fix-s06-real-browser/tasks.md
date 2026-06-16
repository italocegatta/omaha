## 1. Tornar conftest do e2e resiliente ao host

- [x] 1.1 Modificar `tests/e2e/conftest.py:177-191` (fixture `_browser`) para ler `E2E_CHROMIUM_PATH` da env, com fallback para o binário do Playwright em `~/.cache/ms-playwright/chromium-*/chrome-linux/chrome`, e erro explícito se nenhum dos dois existir
- [x] 1.2 Manter `/usr/bin/chromium-browser` como fallback terciário (compatibilidade com hosts que já têm system chromium)
- [x] 1.3 Adicionar `try/except` específico em volta de `p.chromium.launch(...)` para traduzir erros de "shared library not found" em mensagem acionável

## 2. Atualizar README com setup real

- [x] 2.1 Substituir `README.md:237` ("needs Playwright + a one-time `playwright install chromium`") por instrução completa: `uv run playwright install chromium --with-deps` + nota sobre a env var `E2E_CHROMIUM_PATH`
- [x] 2.2 Adicionar nota em `README.md` sobre o fallback `/usr/bin/chromium-browser` e quando ele se aplica

## 3. (já feito) Playwright chromium instalado

- [x] 3.1 Chromium 1226 em `~/.cache/ms-playwright/chromium-1226/chrome-linux64/chrome` (265 MB)
- [x] 3.2 Headless shell em `~/.cache/ms-playwright/chromium_headless_shell-1226/chrome-headless-shell-linux64/chrome-headless-shell` (180 MB)
- [x] 3.3 Markers `DEPENDENCIES_VALIDATED` + `INSTALLATION_COMPLETE` presentes (system deps OK)

## 4. Verificar S06 (validação principal do M002 fix)

- [x] 4.1 Executar `uv run pytest tests/e2e/test_s06_full_journey.py -v` e capturar output completo
- [ ] 4.2 ~~Se verde: confirmar que `TestS06PosicaoItaloImport::test_import_posicao_italo_with_class_association` passou~~ — N/A (test 4.3 disparou)
- [x] 4.3 Se vermelho: capturar screenshot final (`/tmp/s06_e2e_debug/`), stack trace, e dump do DOM. Anotar em `tests/e2e/M002_RESSALVA_DIAGNOSIS.md` qual assertion falhou. **Não consertar** — abrir change dedicada
- [ ] 4.4 ~~Verificar que screenshots de debug em `/tmp/s06_e2e_debug/` (gerados por `_debug_dump`) mostram o modal com `<select>` pré-selecionado nas linhas matched~~ — N/A (test 4.3 disparou)

## 5. Diagnosticar S05 (regressão ressalva M002)

- [x] 5.1 Executar `uv run pytest tests/e2e/test_s05_user_journey.py -v` e capturar output completo
- [ ] 5.2 ~~Se verde: regressão listada em M002 ressalva §5.1 não se reproduz — atualizar `openspec/PRD.md:164-170` removendo o item `test_s05_user_journey.py` (em change separada de sync do PRD)~~ — N/A (test 5.3 disparou em ambos os testes do S05)
- [x] 5.3 Se vermelho: capturar screenshot final + stack trace. Anotar em `tests/e2e/M002_RESSALVA_DIAGNOSIS.md`. Não consertar nesta change
- [x] 5.4 Comparar screenshots de S05 (visual polish: swatches, compare bars, progress bars) com os screenshots esperados do S05 docstring para isolar se é regressão de código ou flake de timing CSS — confirmado: regressão é stale `family` login + `#` hard-coded check, NÃO flake de timing

## 6. Verificar que unit/integration suite continua verde

- [x] 6.1 Executar `uv run pytest tests/ --ignore=tests/e2e -v` e confirmar verde — **vermelho pré-existente**: 83 failed + 12 errors, mesmo antes desta change (verificado com `git stash` + re-run). Causa: stale `family` user assumption em `test_t04_e2e.py` e cascata. NÃO causado por esta change
- [x] 6.2 Se algum teste não-e2e quebrar: provavelmente a modificação do conftest vazou para fora de `tests/e2e/` (não deveria). Investigar imports; corrigir se necessário — confirmado: falha **não** é desta change. Conftest vive em `tests/e2e/` e não afeta a coleta não-e2e

## 7. Verificação final + handoff

- [x] 7.1 Listar arquivos modificados: deve ser exatamente `tests/e2e/conftest.py` e `README.md` — confirmado (`git diff --stat` retorna os 2 arquivos + 87 insertions, 12 deletions)
- [x] 7.2 Confirmar que `src/omaha/**` não foi tocado (`git diff --stat src/omaha/` deve estar vazio) — confirmado (vazio)
- [x] 7.3 Anotar resultado em `tests/e2e/M002_RESSALVA_DIAGNOSIS.md` (criar arquivo mesmo se S05+S06 passam, com timestamp e referência ao run) — escrito
- [x] 7.4 Se S05 vermelho: abrir issue ou change `fix-s05-regression` com referência a esta change — **NÃO vermelho por S05 específico**, mas por stale `family` user + stale `#` assertion. Acompanhamento: change `fix-stale-test-user-after-multi-user-seed` documentada no diagnosis. Não é escopo desta change.
