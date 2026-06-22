#!/usr/bin/env bash
# scripts/print_lan_url.sh — detecta o IP LAN do dev host e imprime a URL do app.
#
# Uso: bash scripts/print_lan_url.sh
# Saída: http://<IP>:8000 (apenas a URL, sem texto extra)
#
# Por que existe: o IP desta máquina muda entre boots (WSL espelha IP do
# Windows via DHCP). Hardcodar IP na doc (AGENTS.md, README, etc) é frágil.
# Este script detecta em runtime via `ip -4 addr` e prioriza:
#   1. LAN IPv4 (192.168.x.x ou 10.x.x.x — exclui loopback e docker)
#   2. Tailscale (100.x.x.x)
#   3. Fallback: 127.0.0.1 (mas isso só funciona local — não é o caso comum)

set -euo pipefail

# Extrai IPs LAN elegíveis (exclui loopback 127.0.0.0/8 e docker 172.17.x.x)
LAN_IP=$(ip -4 addr show 2>/dev/null \
  | grep -oP 'inet \K[\d.]+' \
  | grep -vE '^(127\.|172\.17\.|10\.255\.255\.)' \
  | grep -E '^(192\.168\.|10\.)' \
  | head -1)

# Fallback: Tailscale
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP=$(ip -4 addr show 2>/dev/null \
    | grep -oP 'inet \K[\d.]+' \
    | grep -E '^100\.' \
    | head -1)
fi

# Último fallback (não ideal, mas evita erro)
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP="127.0.0.1"
fi

echo "http://${LAN_IP}:8000"
