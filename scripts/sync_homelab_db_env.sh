#!/usr/bin/env bash
# Export POSTGRES_URI / POSTGRES_URI_CONTABO for tunneled Contabo (same pattern as minaki api/.env).
# Reads POSTGRES_PASSWORD from homelab-contabo/.env when POSTGRES_URI_CONTABO is unset.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_PG_PORT="${LOCAL_PG_PORT:-15432}"
HOMELAB_DOTENV="${HOMELAB_DOTENV:-$ROOT/../homelab-contabo/.env}"

if [[ -n "${POSTGRES_URI_CONTABO:-}" ]]; then
  export POSTGRES_URI="${POSTGRES_URI:-$POSTGRES_URI_CONTABO}"
  exit 0
fi

if [[ ! -f "$HOMELAB_DOTENV" ]]; then
  echo "sync_homelab_db_env: missing $HOMELAB_DOTENV — set POSTGRES_URI_CONTABO in .env" >&2
  exit 0
fi

pg_pass="$(grep '^POSTGRES_PASSWORD=' "$HOMELAB_DOTENV" | cut -d= -f2- | tr -d '"' | tr -d "'")"
if [[ -z "$pg_pass" ]]; then
  echo "sync_homelab_db_env: POSTGRES_PASSWORD not found in homelab-contabo/.env" >&2
  exit 1
fi

export POSTGRES_URI_CONTABO="postgresql://postgres:${pg_pass}@127.0.0.1:${LOCAL_PG_PORT}/postgres"
export POSTGRES_URI="${POSTGRES_URI:-$POSTGRES_URI_CONTABO}"
echo "sync_homelab_db_env: POSTGRES_URI → 127.0.0.1:${LOCAL_PG_PORT} (Contabo via tunnel)" >&2
