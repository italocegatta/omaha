## Context

Owner abriu frente visual 2026-07-06 com queixa de que a paleta
"não está bonita" e "não ajuda a entender informação". Sessão
exploratória em `openspec/.temp_assets/design-system-redesign-session-2026-07-06.md`
capturou matriz Roubar/Rejeitar/Reframear contra Status Invest
(Referência 1), mockups ASCII das opções A/B/C/D, 4 bugs concretos
da paleta atual, e 7 gates abertos.

PRD §4.10 antes de D02 era prescritiva (tokens em HEX, regras
estritas de warmth + chroma + hue family). Essa prescrição limitou
F05 a "swap de tokens sem re-derivar lógica", o que gerou paleta
dark warm-neutral esteticamente correta mas cromaticamente fraca
para uso analítico (slot 3 vs `--negative` indistinguíveis, accent
vs positive ambiguidade cromática).

D02 liberta §4.10 da prescrição e a converte em memorial descritivo
do register escolhido. Tokens concretos passam a viver em DESIGN.md
(como referência canônica para implementação) e em `app.css :root`
(como implementação runtime). Os gates 1-7 owner-resolvidos alinham
D02 com decisões reais em vez de opções em aberto.

## Goals / Non-Goals

**Goals:**

- Memorializar as 7 decisões owner (register, class-3 hue, display
  face, sidebar, toggle, warmth, escopo) em spec auditável
- Re-escrever PRD §4.10 como memorial descritivo (não prescritivo)
- Atualizar DESIGN.md §Color strategy + §Typography + §Component
  inventory + §Iconography + §Anti-patterns para refletir register
  SI maximal + decisões owner
- Marcar PRD §5.3 com gate D02 resolvido, liberando F08-F12 (F11
  effectively Blocked, F13 Blocked)
- Não tocar código runtime — D02 é puramente documental; F08+
  aplicam decisões em código

**Non-Goals:**

- Não re-derivar tokens em `app.css` (F08 faz)
- Não adicionar font face URL em `base.html` (F09 faz)
- Não adicionar CSS de 5 estados / table pattern / compare bar
  (F10 faz)
- Não adicionar Material Symbols font URL (F12 faz)
- Não re-ativar sidebar (decisão owner = NÃO; F11 effectively Blocked)
- Não introduzir light/dark toggle (decisão owner = NÃO; F13 Blocked)
- Não rodar audit / snapshot / seed (zero impacto runtime)

## Decisions

### D-D02.1: Register escolhido = "Status Invest maximal sem sidebar"

Status Invest é fintech brasileiro com hierarquia visual rigorosa:
eyebrow labels uppercase, dividers hairline, compare bars com
target/atual/over-target, tabelas com sticky headers e total row
emphasis, portfolio header com eyebrow + value + delta inline.
Owner pediu "máximo do Status Invest" mas rejeitou sidebar
(reintroduzida seria F02 reversal — não justificável dado que F02
resolveu um problema real de nav consistente cross-page).

Decisão: aplicar **toda** anatomia componente-por-componente da
sessão §7 (eyebrow + dividers + compare bar + portfolio hero +
tabela sticky/hover + rebalance warnings + form R$ prefix) mas
manter top nav F02. Sidebar NÃO reintroduzida (F11 effectively
Blocked — manter slice no roadmap para auditoria, mas não promover).

**Alternativas consideradas**:
- A puro (com sidebar) — rejeitado por owner
- B híbrido — escolhido com rejeição só do sidebar
- C Moleskine+ — rejeitado por owner (preferência por SI maximal)

### D-D02.2: Class-3 hue destino = 350 magenta-red

Bug 1 da sessão §Bugs: `--class-3` (hue 25 orange-red) colide com
`--negative` (hue 25 red-400), indistinguíveis em body escuro.
Owner escolheu 350 magenta-red para slot 3, criando nova família
cromática (rose) que não compete com negative nem positive.

**Alternativas consideradas**:
- 15 orange-red (atual) — colide com `--negative`
- 350 magenta-red (escolhido) — separa family
- Slot 3 = loss color (reusa `--negative`) — sacrifica distinção
  classe vs número negativo, rejeitado por owner

### D-D02.3: Display face = Red Hat Display

Sans geométrica com peso 700+ é a escolha do Status Invest para
portfolio header. Combina com register SI maximal.

**Alternativas consideradas**:
- Source Serif 4 (serif atual) — combina com register C (Moleskine+),
  rejeitado porque owner escolheu SI maximal
- Red Hat Display (escolhido) — match literal SI
- IBM Plex Sans — character sans intermediário, não necessário dado
  Red Hat Display
- Fraunces variable — serif decorativo, rejeitado pelo mesmo motivo
  que Source Serif 4

### D-D02.4: Sidebar reintroduzida = NÃO

Owner rejeitou sidebar. F02 top nav preservada. F11 (sidebar
reintroduce) effectively Blocked por incompatibilidade com register
escolhido. Slice F11 permanece no roadmap para auditoria mas não
promove.

### D-D02.5: Light/dark toggle = NÃO

F05 archived deliberadamente dark-only (D-F05.10). Owner não pediu
toggle nesta sessão. F13 (light/dark toggle) continua Blocked por
default — só promove se owner ativamente pedir em sessão futura.

### D-D02.6: Body warmth = hue 60 mantém

Warm-neutral sutil (chroma ~0.012) é a personalidade "domestic" do
PRD §4.10 original. Owner escolheu manter — combinando com
register B/SI-maximal.

**Alternativas consideradas**:
- Hue 60 mantém (escolhido) — combina com B/SI-maximal
- Hue 60 + chromar up (0.018-0.025) — mais "Moleskine", rejeitado
- Neutro (chroma 0) — mais "fintech puro", rejeitado por owner
- Hue 30 (orange-tan) — pouco usual, rejeitado

### D-D02.7: Escopo de entrega = 3 fatias (F08 + F09 + F10)

F08 (palette) é foundational (re-deriva tokens). F09 (typography) é
independente (font face URL + feature-settings). F10 (componentes)
depende de ambos (estados + table pattern precisam de tokens e
font definidos). F08 + F09 podem rodar em paralelo (cap 2 visual).
F10 após ambos. R05 (hex audit) depende de F08. T06 (visual
regression) depende de F08 + F09 + F10 aplicados.

Owner escolheu 3 fatias (não 1 slice grande) para preservar
atomicidade de gate e respeitar cap 2 WIP visual.

**Alternativas consideradas**:
- 1 slice grande (F08+F09+F10 consolidadas) — violaria "next atômico",
  review difícil, apply longo. Rejeitado.
- 3 fatias separadas (escolhido) — preserva atomicidade, F08+F09
  paralelo, F10 sequencial após ambos
- 4 fatias (paleta → typo → componentes → layout) — virou 3 porque
  layout = sidebar = NÃO

## Risks / Trade-offs

- **[Risk] D02 sem código significa que erros nas decisões só
  aparecem em F08+** → Mitigation: F08+ fazem regressão visual
  (refresh-for-test) e contraste WCAG via `tests/test_dark_mode_tokens.py`.
  Owner pode revisar DESIGN.md + PRD §4.10 memorial antes de F08
  propor.
- **[Risk] §4.10 vira memorial descritivo pode ser lido como
  "regra relaxada"** → Mitigation: spec `design-register-decision`
  explicita que as 7 decisões owner são o contrato. PRD §4.10
  memorializa em prosa, mas spec é a fonte de verdade audível.
- **[Trade-off] F11 + F13 permanecem no roadmap como slices
  effectively Blocked** → Aceito: auditoria de "decidimos não" tem
  valor. Owner pode `restore` se mudar de ideia.
- **[Risk] Red Hat Display vs Inter feature-settings podem ter
  contraste cromático diferente em portfolio header** → Mitigation:
  F09 valida com sample de portfolio header antes de apply final;
  se tnum fraco, fallback para Inter Bold no value (não display).
- **[Trade-off] 350 magenta-red slot 3 ainda fica próximo ao
  spectrum de negative (25) em lightness alta** → Mitigation:
  F08 deriva chroma/luminance que garante hue 350 perceptualmente
  distinto mesmo em dark surface; spec `color-tokens` ganha
  requirement de "slot 3 SHALL be perceptually distinguishable from
  --negative under WCAG color-blindness simulators".