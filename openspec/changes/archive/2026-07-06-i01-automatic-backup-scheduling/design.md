## Context

Hoje `prod.yml` define um serviço `backup` com `profiles: ["backup"]` — só roda via `docker compose -f prod.yml run --rm backup`, ou seja, manual. O operador precisa lembrar de executar isso periodicamente. PRD §3.4 lista modos de operação e cita "scheduled" como alvo; sem timer cabeado, esse modo é aspiracional.

`scripts/backup.py` já faz o trabalho (snapshot SQLite via `sqlite3.Connection.backup()` para `data/portfolio-<timestamp>.db`, retorna exit 0 / não-zero conforme sucesso). `task backup` invoca esse script em dev. Falta apenas o agendador.

## Goals / Non-Goals

**Goals:**
- Periodicidade automática em produção sem intervenção do operador.
- Reusar verbatim o `command` do serviço `backup` existente.
- Frequência configurável via env var (`BACKUP_INTERVAL`, default 86400s = 24h).
- Logs visíveis (`docker compose logs backup-scheduler`) com timestamp ISO-8601 UTC por execução.
- Falha de uma execução individual não derruba o serviço — loga o erro e tenta de novo no próximo ciclo.

**Non-Goals:**
- Política de retenção (rotate / delete snapshots antigos) — fora; primeira iteração é só "gera snapshot", o operador decide o que fazer com `./backups/` via rsync-off-host (já documentado em prod.yml).
- Notificações (e-mail, Slack) em caso de falha — fora; container exit não-zero já é suficiente para monitoring externo.
- Backup incremental / WAL shipping — fora; só snapshot full copy.
- Integração com serviços externos de backup (S3, B2) — fora.

## Decisions

**D-I01.1 — Scheduler como container sidecar com loop `sleep`, não cron host nem timer systemd.** Containers efêmeros, dev/prod parity, e PRD §4.8 mandata taskipy — não há espaço para systemd timer em ambiente container. systemd seria a escolha idiomática em VM bare-metal mas não em Docker. Loop in-container é o padrão portável que sobrevive a reboot do host e mantém tudo versionado em `prod.yml`.

**D-I01.2 — Reusar `omaha:prod` image + mesmo `command` do serviço `backup` existente.** Zero código novo em `scripts/backup.py`. Scheduler é só uma casca de loop. Diff em `prod.yml` mínimo: 1 serviço novo (~15 linhas).

**D-I01.3 — Frequência default 24h via `BACKUP_INTERVAL` (segundos).** 24h é o ponto de partida conservador para portfólio pessoal (perda máxima de 1 dia). Env var em segundos (não cron expression) porque `sleep $SECONDS` é trivial e não exige parser. Outras granularidades (1h, 6h) ficam a 1 env var de distância.

**D-I01.4 — Sem perfil Docker (sobe com `up -d` por padrão), mas desabilitável via perfil `no-backup-scheduler`.** Backup scheduled é o default esperado em produção. Operador que quiser desligar (ex: dev local, debug) usa `docker compose -f prod.yml --profile no-backup-scheduler up` ou desativa o serviço no override file.

**D-I01.5 — Falha não derruba o container; loga e segue.** O serviço roda indefinidamente; uma falha pontual (DB locked por migration, disco cheio) não justifica parar o agendador. Exit code != 0 fica em `docker compose logs` para o operador ver.

**D-I01.6 — Volume `./backups` continua bind mount (não named volume).** Já é assim no serviço `backup`; snapshots ficam no host para rsync-off-host pelo operador. Manter consistência.

## Risks / Trade-offs

- **Loop infinito consome memória desprezível (~10MB) e CPU zero entre execuções** → aceitável; tradeoff aceito vs. complexidade de timer real.
- **Container que "trava" no meio de um backup deixa o snapshot parcial** → `scripts/backup.py` já faz `sqlite3.Connection.backup()` que é atômico (cópia consistente ponto-a-ponto via `sqlite3`); risco residual é só crash de kernel.
- **Múltiplas execuções sobrepostas se BACKUP_INTERVAL < duração do backup** → script é rápido (~1s para DB de 50MB); se operador setar intervalo patológico (<60s), execuções podem empilhar. Mitigação documentada no README: BACKUP_INTERVAL deve ser > 60s.
- **Sem retenção automática** → `./backups/` cresce indefinidamente. Mitigação: responsabilidade do operador (cron externo / logrotate off-host). Primeira iteração não inclui rotate para manter escopo pequeno.
- **`docker compose down` não derruba o scheduler se operador esquece** → `restart: unless-stopped` é o comportamento desejado (sobrevive a reboot do host).

## Migration Plan

- Deploy: `git pull && docker compose -f prod.yml up -d` adiciona o `backup-scheduler` automaticamente.
- Rollback: `docker compose -f prod.yml stop backup-scheduler` (ou `docker compose -f prod.yml rm backup-scheduler`) — sem impacto em `web` ou `nginx`.
- Sem migração de dados — `scripts/backup.py` é byte-equivalente.

## Open Questions

- (Nenhuma bloqueante.) Política de retenção fica para slice futura se o operador pedir.
