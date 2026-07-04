#!/usr/bin/env bash
# SSH tunnel: local port → Contabo supabase_db (127.0.0.1:5432 on VPS only).
# Postgres UI: https://supabase.<DOMAIN> (Supabase Studio — no tunnel needed for browser).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Load realestate-assistant .env if present
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.env"
  set +a
fi

HOMELAB_ENV="${HOMELAB_ENV:-$ROOT/../homelab-contabo/homelab.env}"
if [ -f "$HOMELAB_ENV" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$HOMELAB_ENV"
  set +a
fi

SERVER_IP="${CONTABO_SSH_HOST:-${SERVER_IP:-}}"
SSH_USER="${CONTABO_SSH_USER:-${SSH_USER:-root}}"
LOCAL_PORT="${CONTABO_LOCAL_PG_PORT:-5433}"
REMOTE_PG_PORT="${CONTABO_REMOTE_PG_PORT:-5432}"
DOMAIN="${DOMAIN:-minaki.me}"
STUDIO_URL="${SUPABASE_STUDIO_URL:-https://supabase.${DOMAIN}}"

if [ -z "$SERVER_IP" ]; then
  echo "❌ Set CONTABO_SSH_HOST or SERVER_IP (homelab-contabo/homelab.env)." >&2
  exit 1
fi

SSH_OPTS=(-o ConnectTimeout=10 -o ServerAliveInterval=30 -o ServerAliveCountMax=3)
if [ -n "${CONTABO_SSH_KEY:-${SSH_KEY:-}}" ]; then
  key="${CONTABO_SSH_KEY:-$SSH_KEY}"
  SSH_OPTS+=(-i "${key/#\~/$HOME}")
fi

if lsof -nP -iTCP:"$LOCAL_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "✅ Postgres tunnel already listening on 127.0.0.1:${LOCAL_PORT}"
  echo "   Studio UI: ${STUDIO_URL}"
  exit 0
fi

echo "🔗 Opening SSH tunnel → ${SSH_USER}@${SERVER_IP}"
echo "   localhost:${LOCAL_PORT} → VPS supabase_db:${REMOTE_PG_PORT}"
ssh "${SSH_OPTS[@]}" -f -N \
  -L "127.0.0.1:${LOCAL_PORT}:127.0.0.1:${REMOTE_PG_PORT}" \
  "${SSH_USER}@${SERVER_IP}"

sleep 0.5
if lsof -nP -iTCP:"$LOCAL_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "✅ Tunnel up — use POSTGRES_URI @ 127.0.0.1:${LOCAL_PORT}"
  echo "   Studio UI: ${STUDIO_URL}"
  echo "   (Login: DASHBOARD_USERNAME / DASHBOARD_PASSWORD from homelab-contabo .env)"
else
  echo "❌ Tunnel failed to bind port ${LOCAL_PORT}" >&2
  exit 1
fi
