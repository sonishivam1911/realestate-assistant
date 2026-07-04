#!/usr/bin/env bash
# Dev: Contabo Postgres tunnel (optional) + FastAPI (8080) + Next.js (3000)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

[ -d venv ] && source venv/bin/activate
export PYTHONPATH="${PYTHONPATH:-}:$ROOT"

# Load .env for tunnel + postgres URI
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.env"
  set +a
fi

PY_VER="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$PY_VER" == "3.13" ]]; then
  echo "ERROR: Python 3.13 not supported (ai-sdk-stream-python needs 3.10–3.12)."
  echo "Run: rm -rf venv && ~/.pyenv/versions/3.11.11/bin/python3 -m venv venv && pip install -r requirements.txt"
  exit 1
fi

CONTABO_TUNNEL="${CONTABO_TUNNEL:-true}"
TUNNEL_STARTED=false
BACKEND_PID=""

cleanup() {
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  if [ "$TUNNEL_STARTED" = true ] && [ "${CONTABO_TUNNEL_STOP_ON_EXIT:-false}" = true ]; then
    bash "$ROOT/scripts/stop-tunnel-contabo.sh" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if [ "$CONTABO_TUNNEL" = true ]; then
  if bash "$ROOT/scripts/tunnel-contabo.sh"; then
    TUNNEL_STARTED=true
    # Prefer tunneled Contabo URI when POSTGRES_URI is empty
    if [ -z "${POSTGRES_URI:-}" ] && [ -n "${POSTGRES_URI_CONTABO:-}" ]; then
      export POSTGRES_URI="$POSTGRES_URI_CONTABO"
    fi
  else
    echo "⚠️  Contabo tunnel skipped — chat works without Postgres history"
  fi
fi

DOMAIN="${DOMAIN:-minaki.me}"
STUDIO_URL="${SUPABASE_STUDIO_URL:-https://supabase.${DOMAIN}}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CMA Chat — full stack"
echo "  API     http://localhost:8080/health"
echo "  UI      http://localhost:3000"
if [ "$CONTABO_TUNNEL" = true ]; then
  echo "  Postgres tunnel  127.0.0.1:${CONTABO_LOCAL_PG_PORT:-5433}"
  echo "  Studio UI        ${STUDIO_URL}"
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
