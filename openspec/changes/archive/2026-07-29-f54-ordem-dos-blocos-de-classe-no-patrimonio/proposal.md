## Why

Os blocos de tabelas de classe do `/patrimonio` aparecem hoje na ordem `RF Dinâmica, RF Pós, Internacional, FII, Cripto, Ações` porque a coluna `display_order` dos CSVs de seed (fonte única de seed, PRD §4.3) codifica essa ordem e a rota já ordena os blocos por `AssetClass.display_order`. O owner definiu uma ordem normativa de leitura (`RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`) — já aplicada no `/rebalanceamento` pelo F53 — e quer a mesma sequência no `/patrimonio`, sem alterar conteúdo, estilo, agregações, filtros ou rotas.

## What Changes

- Renumeração da coluna `display_order` em `data/seed/ana_classes.csv` e `data/seed/italo_classes.csv` para o mapa normativo: `RF Pós=0, RF Dinâmica=1, FII=2, Ações=3, Internacional=4, Cripto=5`, com as linhas fisicamente reordenadas em `display_order` crescente (convenção do arquivo).
- Efeito visível obtido apenas pelo mecanismo já existente (`pages.py` `order_by(AssetClass.display_order)` → loop Jinja em `_patrimonio_class_section.html`) + `task db-reset` — **zero mudança em código de produção**.
- Aceitar rotação de cores: `_CLASS_COLORS` (pages.py L935-951) é posicional e permanece intocado; cada classe herda a cor da nova posição (decisão owner 2026-07-28).
- Atualizar baseline visual `patrimonio` (posição dos blocos desloca com a nova ordem).
- NÃO alterar conteúdo/estilo dos blocos, agregações, filtros, rotas, templates, CSS ou solver. Visão família segue automática (ordena por min `display_order` dos membros).

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `data-driven-seed`: adiciona requisito estabelecendo que a coluna `display_order` dos CSVs de classe codifica a ordem normativa dos blocos de classe do `/patrimonio` (`RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`) em ambos os perfis de seed.

## Impact

- Seed: `data/seed/ana_classes.csv`, `data/seed/italo_classes.csv` (somente coluna `display_order` + ordem das linhas; `name`, `target_pct`, `quote_kind`, header e contagem de linhas inalterados; soma `target_pct` continua 100% por arquivo).
- DB: `AssetClass.display_order` dos dois perfis muda após `task db-reset`.
- UI: blocos do `/patrimonio` passam a renderizar na ordem normativa; cores de classe (posicionais) rotacionam com a posição (aceito pelo owner); visão família herda a ordem. Conteúdo/agregações/filtros/estilo inalterados.
- Código: nenhum. `src/omaha/routes/pages.py`, templates, CSS e solver intocados.
- Testes: `tests/test_seed_from_csv.py` segue verde (comparação CSV↔DB dinâmica, L233-238); baseline visual `patrimonio` precisa ser regenerado.
- Sem impacto em API, dependências, schema ou rotas.
