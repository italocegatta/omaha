# Diretrizes da revisão de testes (omaha)

> Arquivo de contexto para o OpenCode e outros agentes. Atualizado em 2026-06-23.

## Regra de ouro: quando um teste falha, investigar ANTES de culpar o teste

Se durante a revisão/apply você encontrar um teste quebrado, **antes de assumir
que o teste está errado**, investigue:

1. O teste está exercitando o comportamento atual do código corretamente?
2. O código mudou e o teste não foi atualizado?
3. **Ou o teste está apontando para um bug real no código de produção?**

### Como decidir entre "consertar teste" vs "consertar código"

| Sintoma | Provável causa | Ação |
|---|---|---|
| Setup do teste usa SQL cru pra "forçar" estado (ex: `sqlite3` direto) | Estado impossível via UI/API — pode ser proteção legítima do código, ou pode ser burlando uma validação que existe pra um motivo | Investigar: o validador está sendo burlado? Se sim, é o teste que é fraco (decisão #5 do plano de revisão: migrar pra UI/API). Se o estado for realmente impossível, **o código tá certo**. |
| Teste espera 0 unmatched mas vê 4 (cenário `full_journey`) | Bug de binding do `<select>` ou de normalização | Decisão #3: consertar o código (não o teste) — provavelmente é o mesmo bug do `AGENTS.md` (Alpine select + template x-for). |
| Teste usa `MagicMock` pra simular `OperationalError` | Mascarando comportamento real | Decisão #2: substituir por cenário real ou documentar que o teste é de contrato, não de integração. |
| Teste stub (`assert True`) | Cinto de segurança sem carro | Decisão #4: deletar. |
| Teste duplica outro | Trabalho redundante | Decisão #4: deletar o pior (o que cobre menos cenários). |

### Regra de implementação de fix no código de produção

**Pode implementar direto** se o fix for:
- ≤ ~20 linhas
- Localizado (1 arquivo)
- Não muda contrato/interface pública
- Não tem efeito colateral além do comportamento que está sendo corrigido
- Não exige migração de dados ou alteração de schema

**Pare e proponha spec (OpenSpec / `opsx-propose`)** se o fix for:
- Espalhado em vários arquivos
- Toca contrato HTTP, schema de banco, ou serialização
- Exige migração de dados existentes
- Toca regras de negócio que podem ter ramificações em outros fluxos
- Tem mais de uma forma razoável de resolver (decisão de design)

### Restrições absolutas

- ❌ Não toque em `src/` sem antes confirmar via `clarify` que o fix é direto.
- ❌ Não introduza novos endpoints / schemas só pra "fazer o teste passar".
- ❌ Não comente testes que falham — conserte ou delete.
- ✅ Se o teste apontar pra bug real e o fix for grande: parar, reportar pra o Ítalo via `clarify`, anexar evidência (logs, HTML, traceback).
