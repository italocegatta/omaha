## Context

`nginx/nginx.conf:25-27` já roteia `/.well-known/acme-challenge/` para `/var/www/certbot` (webroot preparado). `prod.yml:71-77` monta `./certs:/etc/nginx/certs:ro` no nginx — o operador-suprido fullchain + private key. Mas não existe container certbot, nem script de renewal, nem `--deploy-hook`. Operador precisa rodar manualmente: `certbot certonly --webroot -w /var/www/certbot -d <domain>`, copiar para `./certs/`, e `docker compose exec nginx nginx -s reload`. Let's Encrypt expira a cada 90 dias; sem automação, downtime por cert stale é questão de tempo.

`scripts/backup.py` (referenciado pelo I01) já tem precedente de "snapshot service that writes to a bind-mounted host directory"; I02 segue o mesmo padrão (loop in-container + bind mount + deploy hook para efeito colateral).

## Goals / Non-Goals

**Goals:**
- Renewal automático de certs Let's Encrypt em produção sem intervenção do operador.
- Reusar o webroot ACME http-01 challenge que `nginx/nginx.conf` já serve.
- Recarregar nginx automaticamente após renewal bem-sucedido (deploy hook).
- Frequência default 12h (`certbot renew` é idempotente — só age se <30 dias para expirar).
- Falha de uma renewal individual não derruba o agendador.

**Non-Goals:**
- DNS-01 challenge (precisa de credenciais API do DNS provider; http-01 já está cabeado).
- Wildcard certs (Let's Encrypt wildcard exige DNS-01).
- Múltiplos domínios com renewal policies diferentes (primeira iteração trata o domínio único configurado).
- Initial cert bootstrap (`certbot certonly` inicial é one-shot manual; renewal subsequente é o que automatizamos).
- Integração com HSM / Vault para private key (overkill para portfólio pessoal).

## Decisions

**D-I02.1 — Imagem base `certbot/certbot` (oficial), não sidecar Python.** Imagem oficial é Debian-slim + certbot puro, ~50MB. Reusar `omaha:prod` image exigiria instalar certbot no runtime (camada extra, footprint desnecessário) e introduziria risco de conflito de versões entre certbot e o que está no Ubuntu archive da `python:3.12-slim`. Separação é mais limpa.

**D-I02.2 — `certbot renew` em loop com sleep, mesma arquitetura do I01.** `certbot renew` é projetado para rodar frequentemente — só age se o cert estiver perto de expirar (default: <30 dias). Loop in-container com `sleep 43200` (12h) é o padrão recomendado pela documentação oficial do certbot. systemd timer seria a alternativa bare-metal mas Docker não tem.

**D-I02.3 — `--deploy-hook` via `docker compose exec nginx nginx -s reload`.** Após renewal bem-sucedido, certbot invoca o hook. Dentro do container certbot, a rede Docker resolve `nginx` como hostname do serviço; `docker compose exec` funciona se o certbot tiver o socket docker montado (D-I02.4) ou se compartilharmos o socket. Alternativa: nginx recarrega via signal (`nginx -s reload`) requer o binário dentro do certbot — overhead. Deploy hook via exec é o mínimo.

**D-I02.4 — Sem socket Docker compartilhado. Hook chama `nginx` direto via network alias.** Reaproveita o docker network `omaha-prod` (default criado por `docker compose`). `nginx` é resolvível como hostname (docker DNS). O certbot container ganha `network_mode: service:nginx` ou apenas compartilha o network default; `nginx -s reload` no PID do nginx requer privilégios. **Decisão revisada abaixo (D-I02.4-r1):** sem privilégios extras, hook usa um arquivo sentinel (`/tmp/nginx-reload`) e nginx container tem `ENTRYPOINT` que faz `while true; do [ -f /tmp/nginx-reload ] && rm /tmp/nginx-reload && nginx -s reload; sleep 1; done` — heavyweight. **Decisão final (D-I02.4-r2):** `--deploy-hook` chama `docker compose -f /path/to/prod.yml exec -T nginx nginx -s reload` via socket Docker montado (`:ro` em `/var/run/docker.sock`). Trade-off: surface de ataque do socket vs. simplicidade. **Aceite**: portfólio pessoal, host single-tenant; risco aceito.

**D-I02.5 — `./certs` é rw no certbot, ro no nginx, rw-only-on-renewal via permissões do certbot user.** Certbot precisa escrever em `live/`, `archive/`, `renewal/` durante renewal; nginx só lê. Bind mount `./certs:/etc/letsencrypt` no certbot com permissões放宽adas (certbot runs as root na imagem oficial; UID 0 escreve, nginx container user `nginx` UID 101 só lê). Sem necessidade de POSIX ACL — RW no host dir é suficiente.

**D-I02.6 — Frequência 12h default via `CERTBOT_RENEW_INTERVAL`.** 12h é meio período Let's Encrypt (cert expira em 90d, renewal só age em <30d; rodar 2x/dia garante janela). Configurável via env var em segundos.

**D-I02.7 — Initial cert bootstrap fica manual.** Operador roda uma vez: `docker compose -f prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d <domain> --email <email> --agree-tos --no-eff-email`. Após isso, o scheduler pega. Documentado no README.

## Risks / Trade-offs

- **`/var/run/docker.sock` montado no certbot container é superfície de ataque** → risco aceito (portfólio pessoal single-tenant); mitigação futura: trocar por signal-based reload via TCP socket se virar problema.
- **Renovação que falha (rede offline, CA indisponível) não derruba o agendador** → loga e tenta no próximo ciclo; janela de 12h é tolerável.
- **Race entre renewal e reload** → certbot escreve o novo cert atomicamente (rename no filesystem) ANTES de invocar `--deploy-hook`; nginx recarrega lê os novos paths; ordem é garantida pelo certbot.
- **Initial cert precisa ser obtido manualmente antes do scheduler subir** → deployment runbook precisa explicitar a ordem (initial cert → então `up -d`).
- **`./certs/webroot/` precisa existir no host antes do primeiro certbot run** → bind mount falha silenciosamente se diretório não existe; documentado + entry no README.

## Migration Plan

- Pre-deploy: operador roda `mkdir -p ./certs/webroot` e obtém cert inicial via one-shot `docker compose -f prod.yml run --rm certbot certonly --webroot ...`.
- Deploy: `git pull && docker compose -f prod.yml up -d` adiciona o `certbot` automaticamente.
- Rollback: `docker compose -f prod.yml stop certbot` (e remover o serviço do `prod.yml` se quiser limpar). nginx continua usando o cert que já está em `./certs/`.
- Sem migração de dados — `nginx/nginx.conf` é byte-equivalente, `./certs/` continua bind mount.

## Open Questions

- (Nenhuma bloqueante.) Múltiplos domínios ficam para slice futura se virar necessidade.
