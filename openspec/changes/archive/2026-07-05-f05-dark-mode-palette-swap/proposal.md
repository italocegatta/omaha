## Why

Owner pediu dark mode para reduzir cansaço visual em sessão longa (PRD §5.3
marcou como direção ativa). O register "domestic, sem ornamento" (PRD §4.10) se
preserva — só a paleta inverte. A surface continua plana, o accent continua
verde-feto (um único), sem glassmorphism, sem gradient. Implica reescrever
§4.10 do PRD (a regra atual crava "off-white verdadeiro") e re-derivar
todos os pares de tokens da `color-tokens` spec com contraste WCAG AA sobre
o novo fundo escuro.

## What Changes

- Reescrever `:root` em `src/omaha/static/app.css` invertendo os pares
  cromáticos: `--bg` vira OKLCH escuro neutro, `--ink` vira claro
  levemente quente, `--surface` ligeiramente mais claro que `--bg` (cards
  "levantam" via claridade), `--surface-sunk` ligeiramente mais escuro
  (form wells descem). Hue/chroma de accent/positive/negative preservados —
  já funcionam em ambos os polos. Calcular novos `--accent-ink`,
  `--positive-ink`, `--negative-ink` para contraste AAA sobre os fills.
- Atualizar swatches `--class-{1..6}` para variantes que mantenham ≥4.5:1
  contra o novo `--bg` escuro. Hex legados migram para OKLCH na mesma
  passada (a fase 1 já listou os alvos; F05 fecha a migração para os 6).
- Reescrever `DESIGN.md` §Color strategy + tabela "Tokens (current)" com
  os novos valores, novas razões de contraste e rationale da inversão.
  §Component inventory mantém os pares fg/bg — só os valores trocam.
- Reescrever PRD §4.10 trocando "off-white verdadeiro" por "body escuro
  neutro, calor vive no accent e em textura de superfície (não no
  tint)" — registro continua domestic. PRD §5.3 marca F como entregue.
- Substituir `tests/test_phase02_tokens.py` por
  `tests/test_dark_mode_tokens.py` que re-deriva cada par e exige
  contraste mínimo documentado (mesmo contrato, valores novos). Teste de
  cor do body (`body { background: var(--bg); }`) garante que a surface
  renderiza com o novo fundo.

Sem mudança de rotas, templates, modelos, providers, ou solver. Sem
migration. Sem nova dependência de runtime.

## Capabilities

### New Capabilities

Nenhuma. F05 inverte tokens existentes; a capability `color-tokens`
absorve o delta.

### Modified Capabilities

- `color-tokens`: os pares fg/bg e a tabela de contraste são reescritos.
  As três requirements existentes ("Design tokens define unambiguous
  foreground/background pairs", "Each token pair has documented minimum
  contrast ratio", "DESIGN.md reflects corrected token values with
  rationale") são MODIFIED — os cenários passam a ser exercidos sobre o
  fundo escuro. Nenhum REMOVED, nenhum ADDED.

## Impact

- `src/omaha/static/app.css` — `:root` reescrito; classes que hardcodam
  cor podem precisar de ajuste (auditar `grep -nE '#[0-9a-fA-F]{3,6}'`
  no arquivo antes do apply).
- `DESIGN.md` — §Color strategy, tabela de tokens, §Migration path.
- `openspec/PRD.md` — §4.10 (brand register) e §5.3 (estado).
- `tests/test_phase02_tokens.py` → substituído por
  `tests/test_dark_mode_tokens.py` (mesmo contrato, valores novos).
- Não toca: `src/omaha/templates/`, `src/omaha/routes/`,
  `src/omaha/models.py`, `src/omaha/quotes/`, `src/omaha/rebalance/`,
  `src/omaha/seed.py`, Alembic.
