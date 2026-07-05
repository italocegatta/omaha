## Context

F05 fecha a direção marcada em PRD §5.3: dark mode. O register
"domestic, sem ornamento" (PRD §4.10) se preserva — só a paleta cromática
inverte. A `color-tokens` spec documenta hoje 17 tokens calibrados para um
fundo off-white (`--bg: oklch(0.975 0.003 60)`, lightness ≈ 0.975). F05
inverte lightness em ~0.80 e re-deriva cada par para manter WCAG AA no
novo contexto.

Source-of-truth: `src/omaha/static/app.css :root` + `DESIGN.md §Color
strategy` + `openspec/specs/color-tokens/spec.md`. `tests/test_phase02_tokens.py`
é o gate de contrato atual; F05 o substitui por `tests/test_dark_mode_tokens.py`
(mesmo contrato, novos valores).

## Goals / Non-Goals

**Goals:**
- Inverter pares cromáticos em `app.css :root`: `--bg`, `--surface`,
  `--surface-sunk`, `--ink`, `--ink-muted`, `--border`, `--border-strong`.
- Recalibrar `--accent`, `--accent-ink`, `--positive`, `--positive-ink`,
  `--negative`, `--negative-ink`, `--error-bg`, `--error-fg`,
  `--color-focus` para o novo contexto escuro, preservando hue/chroma
  relativos (mesmo "verde-feto", "coral", "azul-foco").
- Lightness-lift das swatches `--class-{1..6}` para manter ≥4.5:1 sobre
  `--bg` escuro. Swatch 2 (verde) desloca hue ~15° para não colidir
  visualmente com `--positive`.
- Atualizar `DESIGN.md` §Color strategy + tabela "Tokens (current)" +
  §Component inventory + §Migration path.
- Atualizar PRD §4.10 (brand register) e §5.3 (estado).
- Substituir `tests/test_phase02_tokens.py` por
  `tests/test_dark_mode_tokens.py` re-derivando cada par.

**Non-Goals:**
- Toggle light/dark (single register dark; sem `prefers-color-scheme`).
- Migração para nova arquitetura de theming (CSS layers, `:has()`,
  framework). F05 é reescrita do `:root`; nada além.
- Mudança em rotas, templates, modelos, providers, solver, seed.
- Glassmorphism, blur, gradient, animation de transição entre temas.
- Print stylesheet (PRD não menciona; mantemos o que houver).

## Decisions

### D-F05.1 — Inversão por lightness, hue preservado

Body `--bg`: `oklch(0.18 0.01 60)`. Ink `--ink`: `oklch(0.94 0.005 60)`.
Hue 60 (warm-neutral) mantido em ambos os lados. Rationale: inversão por
lightness evita que o modo escuro vire "blue-black" (estilo OLED) ou
"azul-cinza frio" (estilo GitHub dark clássico), mantendo calor no mesmo
canal da paleta original. Chroma baixo (~0.01) evita saturação perceptível
no escuro. Alternativa considerada: hue 220 (neutro frio, "tech"). Rejeitada
porque quebra a leitura "domestic" do register.

### D-F05.2 — Surface lift por lightness, não shadow

`--surface: oklch(0.22 0.012 60)` (≈+0.04 sobre `--bg`). `--surface-sunk:
oklch(0.15 0.01 60)` (≈-0.03 sobre `--bg`). Mantém a regra "cards são flat
ou shadowed, nunca ambos" do DESIGN.md — sem reintroduzir `box-shadow` nos
cards. O lift é só lightness; elevation vem de contraste cromático.

### D-F05.3 — Accent/positive/negative lightness-lift, hue idêntico

`--accent: oklch(0.68 0.13 150)` (era `oklch(0.42 0.09 150)`). Hue 150 e
família "verde-feto" mantidos; lightness sobe ~0.26 para contrastar AAA
sobre `--bg` escuro. `--positive: oklch(0.70 0.16 145)` — mesmo shift,
hue 145 (vs accent 150) mantido. `--negative: oklch(0.70 0.18 25)` —
coral, lightness lift. `--*-ink` tokens viram escuro (`oklch(0.18 0.01 60)`)
para contraste AAA sobre os fills claros. Alternativa considerada: accent
escuro + ink claro dentro do accent. Rejeitada porque accent escuro sobre
bg escuro vira "dipping into the surface" — perde o papel de marca.

### D-F05.4 — Swatch 2 desloca hue para não colidir com positive

`--class-2: oklch(0.72 0.13 130)` (era `#2e7d32` alvo `oklch(0.50 0.13 145)`).
Lightness sobe ~0.22, hue desloca 130 vs positive 145. Justificativa: positive
também é verde (hue 145) e lightness 0.70. Se swatch 2 fica em 145 + 0.72,
colide visualmente com a leitura de "ganho" no compare-bar. Hue 130 puxa
para "leaf-green" (mais amarelo) e separa o "verde de marca" do "verde de
ganho". Demais swatches mantêm hue e só fazem lightness-lift:
- `--class-1: oklch(0.65 0.15 250)` (azul)
- `--class-3: oklch(0.72 0.18 25)` (vermelho)
- `--class-4: oklch(0.75 0.13 50)` (laranja queimado)
- `--class-5: oklch(0.65 0.12 300)` (ameixa)
- `--class-6: oklch(0.72 0.10 200)` (teal)

### D-F05.5 — Borders hairline via lightness incremental

`--border: oklch(0.30 0.008 60)` (~+0.12 sobre `--bg`). `--border-strong:
oklch(0.38 0.01 60)` (~+0.20). Borders não são foreground de texto; ficam
"presentes sem competir". Sem `border-color: white` (estilo high-contrast
que fere o register domestic).

### D-F05.6 — Color focus mantém papel de marca, lightness ajustado

`--color-focus: oklch(0.65 0.15 250)` (era `#2563eb`). Hue 250 preserva o
azul de foco original; lightness 0.65 garante ≥3:1 sobre `--bg` escuro para
anéis de foco. Continua distinto de `--class-1` (também hue 250) porque
class-1 lightness 0.65 mas chroma 0.15; focus chroma 0.15 também, mas uso é
sempre com outline offset — não competem visualmente.

### D-F05.7 — Erro feedback invertido em lightness

`--error-bg: oklch(0.30 0.04 25)` (era claro `0.95`). `--error-fg:
oklch(0.80 0.10 25)` (era escuro `0.45`). Background do erro fica
"afundado + vermelho", texto claro por cima. Mantém a regra "sem side-
stripe alert" — bloco inteiro colore.

### D-F05.8 — PRD §4.10 reescrito, register preservado

Texto atual: "Cor de body é off-white verdadeiro, não creme/sand/bege.
Calor vive no accent (verde-feto dessaturado, hue 150), nunca no tint do
fundo." Substituir por: "Cor de body é **neutro escuro quente** (lightness
~0.18, hue 60, chroma ~0.01), não preto puro nem cinza frio. Calor vive no
accent (verde-feto, hue 150) e em lifts sutis de lightness em surfaces
(superfícies levantam por claridade, não por sombra). Swatches de classe
são versões clareadas dos mesmos hues para manter contraste AA no fundo
escuro. Inverter não é允许 ornamentação — sem gradient, sem glow, sem
glassmorphism, sem transition entre temas. Inverter não é introduzir
ornamentação: a estética permanece a mesma surface plana, só com
luminosidade trocada."

(Detalhe PT-BR/EN: o register continua domestic — sem exclamação, sem
"Welcome!", sem marketing. Mesma voz.)

### D-F05.9 — Teste renomeado, contrato idêntico

`tests/test_phase02_tokens.py` → `tests/test_dark_mode_tokens.py`.
Contrato: itera tokens definidos em `:root`, computa par fg/bg via
heurística (mesmo script de auditoria), exige ≥4.5:1 para pares de texto
e ≥3:1 para `color-focus`. Cada token sem par conhecido falha o teste com
mensagem apontando a correção. Não introduz nova dependência; reusa
`scripts/generate_contrast_audit.py` se possível.

### D-F05.10 — Sem toggle, sem `prefers-color-scheme`

Owner não pediu switch. F05 é o **novo default** — a app passa a ser dark.
Não introduzimos `@media (prefers-color-scheme: dark)` porque não há modo
claro para alternar. Se o owner quiser toggle depois, isso vira nova fatia
(F ou R) reusando tokens via custom property override por classe
(`body.light { --bg: ... }`) — fora do escopo F05.

## Risks / Trade-offs

- **Hardcoded hex fora do `:root`** pode sobreviver à reescrita de tokens
  e quebrar leitura no dark. Mitigation: rodar
  `grep -nE '#[0-9a-fA-F]{3,6}|rgb\(|rgba\(|hsl\(|hsla\(' src/omaha/static/app.css`
  antes de iniciar a reescrita; auditar cada match.
- **Class swatch 2 colidindo com positive** se mantivermos hue 145. Já
  endereçado em D-F05.4.
- **Regressão de contraste em pares não documentados** (ex.: sombras com
  `rgba(0,0,0,0.05)` herdadas da era light). Mitigation: o teste
  `test_dark_mode_tokens.py` falha se algum `--*-ink` token perder par;
  sombras hardcoded ficam fora do contrato — auditoria manual no apply.
- **Print stylesheet** não foi alvo de revisão. Se existir, vai imprimir
  fundo escuro com texto claro — provavelmente não é o desejado, mas PRD
  não menciona. Aplicar escopo mínimo: se houver `@media print`, ajustar
  inline no apply (não vira requirement).
- **Imagens/svg com fundo embutido** (logos, etc.) podem ficar
  visualmente erradas. Auditoria visual no `refresh-for-test` cobre.
- **PRD §4.10 é regra de ouro** (PRD §4). Mudar a redação da regra
  dispara o gate "Mudanças precisam de aprovação do owner". F05 carrega
  essa aprovação no contexto (owner pediu dark mode em PRD §5.3). Sem
  nova aprovação no apply, mas o teste final do owner é o
  `refresh-for-test` smoke.

## Migration Plan

1. Edit `src/omaha/static/app.css :root` com os novos valores.
2. `task test-unit` (gate de tokens: `test_dark_mode_tokens.py` verde).
3. Edit `DESIGN.md` (tabela + §Color strategy + §Migration path).
4. Edit PRD §4.10 e §5.3.
5. `openspec validate f05-dark-mode-palette-swap` (gate de spec).
6. `refresh-for-test` (visual smoke: Italo/Ana/Família + import form +
   class editor + rebalance page).
7. Archive via `openspec-archive-change`.

Rollback: `git checkout HEAD -- src/omaha/static/app.css DESIGN.md
openspec/PRD.md` reverte os três artefatos. Test file
`test_phase02_tokens.py` foi renomeado — restore via `git checkout HEAD --
tests/test_phase02_tokens.py` (recria) e remove
`tests/test_dark_mode_tokens.py` se necessário.

## Open Questions

- Swatch 2 hue final (130 vs 135) — confirmar no apply com screenshot
  side-by-side Italo (verde-feto accent) vs classe 2 (verde-folha).
- `--color-focus` chroma (0.15 vs 0.12) — se colidir visualmente com
  `--class-1` durante smoke, baixar chroma do focus.
- Bordas em `:focus-visible` sobre `--surface-sunk` (form wells) —
  verificar leitura no editor de classe.
