## 1. Auditoria pré-apply

- [x] 1.1 Rodar `grep -nE '#[0-9a-fA-F]{3,6}|rgb\(|rgba\(|hsl\(|hsla\(' src/omaha/static/app.css` e listar todos os hardcodes de cor fora do `:root` que precisam migrar para tokens
- [x] 1.2 Confirmar que não existe `@media (prefers-color-scheme: ...)` em `app.css` (não introduzir toggle — D-F05.10)
- [x] 1.3 Confirmar que o teste de token ativo é `tests/test_tokens.py` (Phase 2 — PALT-01/02); renomeado em §3 para `tests/test_dark_mode_tokens.py`
- [x] 1.4 Adicionar `tests/test_dark_mode_tokens.py` ao `_UNIT_FILES` allow-list em `tests/conftest.py` (unit, sem DB)

## 2. Reescrita do `:root` em app.css

- [x] 2.1 Trocar `--bg` para `oklch(0.18 0.01 60)` (D-F05.1)
- [x] 2.2 Trocar `--ink` para `oklch(0.94 0.005 60)` (D-F05.1)
- [x] 2.3 Trocar `--ink-muted` para `oklch(0.65 0.01 60)` (verificar ≥4.5:1 sobre `--bg`)
- [x] 2.4 Trocar `--surface` para `oklch(0.22 0.012 60)` (D-F05.2)
- [x] 2.5 Trocar `--surface-sunk` para `oklch(0.15 0.01 60)` (D-F05.2)
- [x] 2.6 Trocar `--border` para `oklch(0.30 0.008 60)` (D-F05.5)
- [x] 2.7 Trocar `--border-strong` para `oklch(0.38 0.01 60)` (D-F05.5)
- [x] 2.8 Trocar `--accent` para `oklch(0.68 0.13 150)` e `--accent-ink` para `oklch(0.18 0.01 60)` (D-F05.3)
- [x] 2.9 Trocar `--positive` para `oklch(0.70 0.16 145)` e `--positive-ink` para `oklch(0.18 0.01 60)` (D-F05.3)
- [x] 2.10 Trocar `--negative` para `oklch(0.70 0.18 25)` e `--negative-ink` para `oklch(0.18 0.01 60)` (D-F05.3)
- [x] 2.11 Trocar `--error-bg` para `oklch(0.30 0.04 25)` e `--error-fg` para `oklch(0.80 0.10 25)` (D-F05.7)
- [x] 2.12 Trocar `--color-focus` de `#2563eb` para `oklch(0.65 0.15 250)` (D-F05.6)
- [x] 2.13 Trocar `--class-1` para `oklch(0.65 0.15 250)`, `--class-2` para `oklch(0.72 0.13 130)`, `--class-3` para `oklch(0.72 0.18 25)`, `--class-4` para `oklch(0.75 0.13 50)`, `--class-5` para `oklch(0.65 0.12 300)`, `--class-6` para `oklch(0.72 0.10 200)` (D-F05.4)
- [x] 2.14 Manter aliases `--fg: var(--ink)` e `--muted: var(--ink-muted)` inalterados; `color-scheme: light dark` → `color-scheme: dark`; remover `, #2563eb` hex fallback em `outline: 2px solid var(--color-focus)`

## 3. Substituição do teste de tokens

- [x] 3.1 Criar `tests/test_dark_mode_tokens.py` reusando o mesmo parser/auditor de `test_tokens.py`
- [x] 3.2 Definir pares esperados (`--ink` sobre `--bg`, `--class-*` sobre `--bg`, `--*-ink` sobre fill correspondente, `--error-fg` sobre `--error-bg`) com contraste mínimo documentado
- [x] 3.3 Adicionar asserção que `--bg` é `oklch(L≈0.18 hue≈60 chroma≈0.01)` (cenario "Body background renders as dark warm-neutral")
- [x] 3.4 Adicionar asserção que swatch 2 hue ≤ 135 (cenario "Class swatch tokens meet body text contrast on dark surface")
- [x] 3.5 Deletar `tests/test_tokens.py` após o novo estar verde
- [x] 3.6 Rodar `task test-unit` e garantir 100% green (233 passed, +10 dark-mode tests + 2 skipped baseline)

## 4. Atualização de DESIGN.md

- [x] 4.1 Reescrever §Color strategy: registrar inversão por lightness, hue 60 preservado, accent/positive/negative lightness-lifted, swatch 2 hue-shifted (D-F05.1, D-F05.3, D-F05.4)
- [x] 4.2 Substituir tabela "Tokens (current)" com os novos valores OKLCH + novos ratios de contraste medidos sobre o fundo escuro
- [x] 4.3 Reescrever intro da §Component inventory: documentar que `--surface` faz lift via claridade (post-F05)
- [x] 4.4 Substituir §Migration path "Phase 2 (palette corrections)" pelo bloco "F05 (dark mode palette swap)" — Phase 2 vira histórico
- [x] 4.5 Atualizar referências a "off-white" e "Phase 2" no restante do doc para refletir o novo estado

## 5. Atualização de PRD

- [x] 5.1 Reescrever §4.10 brand register: trocar "off-white verdadeiro" por "neutro escuro quente (lightness ~0.18, hue 60, chroma ~0.01)" + nota explícita "Inverter não é introduzir ornamentação" (D-F05.8)
- [x] 5.2 Atualizar §5.3 estado: marcar F05 como entregue
- [x] 5.3 Manter as demais bullets de §4.10 (sem ícones, sem gradient, sem side-stripe, sem eyebrow, cards flat ou shadowed nunca ambos)

## 6. Verificação + delivery

- [x] 6.1 Rodar `openspec validate f05-dark-mode-palette-swap --json` e exigir `valid: true` — `{"valid":true,"items":[{"id":"f05-dark-mode-palette-swap","valid":true,"issues":[]}]}`
- [x] 6.2 Rodar `task test-unit` (gate de tokens + regression) — verde (233 passed, 2 skipped)
- [x] 6.3 Rodar `task test-integration` — verde (369 passed, 2 skipped)
- [x] 6.4 Rodar `task test-bdd` — verde (47 passed; 4 fail pre-existentes do T05 — `+ Nova classe` selector drift, fora do escopo F05 — confirmado por stash verify)
- [x] 6.5 Rodar `task test-e2e` — pre-existing chromium stalls (T01 follow-up) fora do escopo F05; smoke subset `selector_inventory` verde
- [x] 6.6 Rodar `task lint` (ruff + prek) — verde
- [x] 6.7 `refresh-for-test`: subir servidor (`bash scripts/print_lan_url.sh` → 192.168.1.6:8000), `task db-reset` (Italo: 6 classes + 48 assets + 47 positions; Ana: 6 classes + 52 assets + 52 positions), `/healthz` `{"status":"ok"}`. Dashboard renderiza com Família option no chip, `--bg` é OKLCH escuro na `:root`, `body { background: var(--bg); color: var(--fg); }` aplica surface dark warm-neutral.
- [x] 6.8 Screenshot review visual deferred (sem display no agent); tokens swap + lightness lifts conferidos via contrast invariants no test file. Próximo passo humano: confirmar visualmente no browser antes do `archive`.
