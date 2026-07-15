## Context

Suite de testes do omaha: 388 integration tests, ~124s paralelo, ~268s serial. Mutation testing (mutmut) no módulo rebalance mostra 94.5% kill rate — mas alguns testes sobrevivem não porque protegem comportamento, mas porque o código é trivial ou o teste é redundante.

Análise concreta identificou 6 testes problemáticos em 3 arquivos.

## Goals / Non-Goals

**Goals:**
- Remover testes que não provam comportamento real do sistema
- Eliminar duplicação que gasta ~31s sem benefício
- Manter cobertura existente via testes que já exercitam o mesmo código

**Non-Goals:**
- Reescrever toda a suite (T25 faz isso)
- Mover testes entre categorias (T24 faz isso)
- Otimizar fixtures ou setup (T23 faz isso)
- Tocar em `data/seed/` (PRD §4.3)

## Decisions

### D1: Remover skips redundantes em vez de corrigir fixture

**Escolha:** Deletar os 2 testes skipped.

**Alternativa considerada:** Corrigir a fixture `SessionLocal` + `pytest.raises` em `test_rebalance_engine_glue.py` para reativar o teste.

**Rationale:** O comportamento já é validado em 2 outros testes (validation unit + route 400). Corrigir fixture complexa para duplicar cobertura é custo sem benefício. Skip com reason detalhada já documenta a decisão.

### D2: Merge em vez de parametrize para audit_inventory

**Escolha:** Fundir `test_inventory_for_patrimonio_produces_rows` + `test_inventory_rows_carry_template_field` em 1 teste que valida ambas asserções.

**Alternativa considerada:** Parametrizar com `@pytest.mark.parametrize` sobre asserções.

**Rationale:** Ambos rodam `inventory_for_page("patrimonio.html")` — mesma pipeline pesada (CSS parse + Jinja render + inventory loop). Parametrizaria sobre asserções mas ainda rodaria a pipeline 2x. Merge roda pipeline 1x e valida tudo.

### D3: Remover triviais em vez de reescrever

**Escolha:** Deletar `test_find_interactive_empty_html_returns_empty` e `test_find_interactive_no_interactive_elements_returns_empty`.

**Alternativa considerada:** Reescrever com HTML real do sistema.

**Rationale:** `find_interactive` já é exercitado por `test_find_interactive_finds_tag` com templates reais (patrimonio, classes, login). Testes com strings hardcoded não adicionam cobertura — se `find_interactive` quebrar com HTML real, os outros testes pegam.

## Risks / Trade-offs

- **[Risk] Remover teste que protegia edge case não mapeado** → Mitigação: ambos os testes triviais testam strings fixas, não código de produção. Mutation testing não os mata. Outros testes cobrem a mesma função com dados reais.
- **[Risk] Merge de audit_inventory perde granularidade de falha** → Mitigação: se a pipeline quebrar, o teste merged falha com mensagem clara (rows == 0 ou template field missing). Diagnóstico não se perde.

## Migration Plan

Sem migração — mudanças são deletar/editar testes. Rollback: `git checkout` nos 3 arquivos.
