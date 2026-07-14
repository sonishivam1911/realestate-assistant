#!/usr/bin/env bash
# Dev: homelab SSH tunnel (Postgres) + FastAPI (8080) + Next.js (3000)
# Pattern: real-time-minaki-poc/api/start_dev.sh + scripts/homelab_tunnel.sh
#
# Usage:
#   ./start_dev.sh                 # tunnel if USE_HOMELAB_TUNNEL=1 in .env
#   ./start_dev.sh --tunnel        # always tunnel
#   ./start_dev.sh --no-tunnel     # never tunnel
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

TUNNEL_FLAG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tunnel | -t) TUNNEL_FLAG=1; shift ;;
    --no-tunnel) TUNNEL_FLAG=0; shift ;;
    -h | --help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) echo "Unknown option: $1 (try --tunnel or --no-tunnel)" >&2; exit 1 ;;
  esac
done

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.env"
  set +a
fi

export TUNNEL_SKIP_REDIS=1

# shellcheck source=scripts/homelab_tunnel.sh
source "$ROOT/scripts/homelab_tunnel.sh"

if [[ -n "$TUNNEL_FLAG" ]]; then
  USE_TUNNEL="$TUNNEL_FLAG"
else
  USE_TUNNEL="${USE_HOMELAB_TUNNEL:-${CONTABO_TUNNEL:-1}}"
fi

[ -d venv ] && source venv/bin/activate
export PYTHONPATH="${PYTHONPATH:-}:$ROOT"

PY_VER="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PY_VER" == "3.13" ]]; then
  echo "ERROR: Python 3.13 not supported (ai-sdk-stream-python needs 3.10–3.12)."
  exit 1
fi

BACKEND_PID=""

cleanup() {
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  if [[ "${USE_TUNNEL:-0}" == "1" ]]; then
    homelab_tunnel_stop
  fi
}
trap cleanup EXIT INT TERM

# Kill stale SSH forwards from old tunnel-contabo (5433) so we bind LOCAL_PG_PORT cleanly
_stale_ports="${CONTABO_LOCAL_PG_PORT:-5433} ${LOCAL_PG_PORT:-15432}"
for _port in $_stale_ports; do
  _pids=$(lsof -tiTCP:"$_port" -sTCP:LISTEN 2>/dev/null || true)
  for _pid in $_pids; do
    if ps -p "$_pid" -o command= 2>/dev/null | grep -q "ssh.*${_port}:127.0.0.1"; then
      kill "$_pid" 2>/dev/null || true
      echo "Stopped stale SSH tunnel on port $_port (pid $_pid)"
    fi
  done
done

if [[ "${USE_TUNNEL:-0}" == "1" ]]; then
  homelab_tunnel_start
fi

# Minaki pattern: POSTGRES_URI_CONTABO points at LOCAL_PG_PORT — tunnel only opens the port.
LOCAL_PG="${LOCAL_PG_PORT:-15432}"
if [[ -z "${POSTGRES_URI_CONTABO:-}" ]]; then
  HOMELAB_DOTENV="${HOMELAB_DOTENV:-$ROOT/../homelab-contabo/.env}"
  if [[ -f "$HOMELAB_DOTENV" ]]; then
    pg_pass="$(grep '^POSTGRES_PASSWORD=' "$HOMELAB_DOTENV" | cut -d= -f2- | tr -d '"' | tr -d "'")"
    if [[ -n "$pg_pass" ]]; then
      export POSTGRES_URI_CONTABO="postgresql://postgres:${pg_pass}@127.0.0.1:${LOCAL_PG}/postgres"
      echo "✅ POSTGRES_URI_CONTABO → 127.0.0.1:${LOCAL_PG} (from homelab-contabo/.env)"
    fi
  fi
fi
export POSTGRES_URI="${POSTGRES_URI:-${POSTGRES_URI_CONTABO:-}}"

if [[ -n "${POSTGRES_URI:-}" ]]; then
  if ! nc -z 127.0.0.1 "$LOCAL_PG" 2>/dev/null; then
    echo "❌ Postgres tunnel not reachable on 127.0.0.1:${LOCAL_PG}" >&2
    echo "   URI expects port ${LOCAL_PG} but nothing is listening." >&2
    echo "   Stop ./start_dev.sh and run again, or fix LOCAL_PG_PORT / POSTGRES_URI_CONTABO." >&2
    exit 1
  fi
fi

DOMAIN="${DOMAIN:-minaki.me}"
STUDIO_URL="${SUPABASE_STUDIO_URL:-https://supabase.${DOMAIN}}"
LOCAL_PG="${LOCAL_PG_PORT:-15432}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CMA Chat — full stack"
echo "  API     http://localhost:8080/health"
echo "  UI      http://localhost:3000"
if [[ "${USE_TUNNEL:-0}" == "1" ]]; then
  echo "  Postgres tunnel  127.0.0.1:${LOCAL_PG}"
  echo "  Studio UI        ${STUDIO_URL}"
fi
if [[ -n "${POSTGRES_URI_CONTABO:-}" || -n "${POSTGRES_URI:-}" ]]; then
  echo "  DB               Contabo via tunnel"
else
  echo "  DB               not configured (conversations will 503)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!
sleep 1

if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies…"
  (cd frontend && npm install)
fi

cd frontend && npm run dev
