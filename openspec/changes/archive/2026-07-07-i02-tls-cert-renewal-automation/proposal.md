## Why

`prod.yml` monta `./certs:/etc/nginx/certs:ro` no nginx (cert chain operador-supridada) e `nginx/nginx.conf` já roteia `/.well-known/acme-challenge/` para o webroot certbot (`/var/www/certbot`). PRD §3.4 cita TLS renewal como requisito operacional; hoje é 100% manual — o operador roda `certbot renew` na mão, copia os arquivos para `./certs/`, e executa `docker compose exec nginx nginx -s reload`. Cert Let's Encrypt expira a cada 90 dias; janela de erro humano é grande (esqueceu de renovar = downtime em produção).

## What Changes

- Adicionar serviço `certbot` em `prod.yml` que executa `certbot renew` periodicamente (loop in-container, mesmo padrão do I01).
- Volume `./certs:/etc/letsencrypt` com write access para o certbot atualizar `live/`, `archive/`, `renewal/`.
- Volume compartilhado `./certs/webroot:/var/www/certbot:ro` no nginx (já está bind mount em `:ro`) — usado pelo ACME http-01 challenge.
- `--deploy-hook` que executa `nginx -s reload` dentro do container nginx (via `docker compose exec` ou socket compartilhado) quando uma renewal produz novos certificados.
- README documenta o setup: como o cert inicial é obtido (`certbot certonly --webroot -w /var/www/certbot -d <domain>`) e como a renovação automática fica cabeada.

## Capabilities

### New Capabilities
- `tls-cert-renewal`: capability descreve o ciclo de renewal automático, o `certbot` container, o `--deploy-hook` que recarrega nginx, e o estado de falha (renewal falha → loga, scheduler continua tentando).

### Modified Capabilities

Nenhuma. O contrato de TLS termination em si (cipher suites, OCSP stapling, fullchain path) é coberto pelo `nginx/nginx.conf` existente; esta fatia só adiciona a automação de renewal, não muda os parâmetros do TLS.

## Impact

- `prod.yml` (novo serviço `certbot`).
- `README.md` (seção Operação / TLS).
- Sem mudança em código de aplicação (`src/omaha/**`), templates, solver, cotação, auth.
- `./certs/` continua sendo bind mount no host (rsync-off-host pelo operador). Adicionar `./certs/webroot/` para o ACME challenge path — diretório vazio commitado com `.gitkeep`.
